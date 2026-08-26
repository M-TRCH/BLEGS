"""ประเมินแบบจำลองชดเชยด้วยข้อมูล "เชิงพลวัต" ครบทุกภาระโหลด (cross-condition validation)

ทำไมต้องมีสคริปต์นี้
--------------------
`train_compensation_model.py` fit แล้ว predict บนชุดข้อมูลเดียวกัน ค่าที่ได้ใน
`output/models/training_summary.txt` จึงเป็น in-sample ทั้งหมด และจัดอันดับให้
Random Forest ชนะขาด (RMSE 0.40 mm, R² 0.97) ซึ่งเป็นอาการ overfit ตามปกติของ
แบบจำลองที่ยืดหยุ่นสูง **ห้ามนำตารางนั้นไปรายงานเป็นความแม่นยำของแบบจำลอง**

สคริปต์นี้ประเมินตามที่บทความอธิบายไว้จริง คือเอาแบบจำลองไปทำงานในวงรอบควบคุม
แล้ววัดความคลาดเคลื่อนที่ยัง "คงเหลือ" ที่ปลายขา จากวิดีโอที่บันทึกไว้เงื่อนไขละคลิป
(4 ภาระโหลด x {ไม่ชดเชย + 5 แบบจำลอง} = 24 คลิป) ไปป์ไลน์การวัดเหมือน
`vision_based_trajectory_eval.py` ทุกขั้น ต่างกันแค่ทำครบทุกโฟลเดอร์ภาระโหลด

นอกจากค่ารวม ยังแยกความคลาดเคลื่อนออกเป็นสององค์ประกอบตามที่บทที่ 3 ต้องใช้
  * offset - ระยะที่จุดศูนย์กลางของวิถีเลื่อนจากจุดที่สั่ง
  * shape  - รัศมีที่ลากได้เทียบรัศมีที่สั่ง และค่าคลาดเคลื่อนคงเหลือของการฟิตวงกลม
เพราะตัวชี้วัดค่าเดียว (RMS รอบวงอุดมคติ) ถูกครอบงำด้วย offset จนมองไม่เห็นว่า
รูปวิถีแทบไม่เปลี่ยน

    python dynamic_model_evaluation.py [n_workers]
"""
import concurrent.futures
import csv
import os
import sys

import numpy as np
import cv2
import cv2.aruco as aruco

_DIR = os.path.dirname(os.path.abspath(__file__))
CALIB_FILE = os.path.join(_DIR, 'output', 'params', 'calibration_olympus25f1.2.npz')
OUT_CSV = os.path.join(_DIR, 'output', 'data', 'dynamic_eval.csv')

VIDEO_ROOT = r'D:\THESIS'
LOADS = ['no_load', '1kg', '2kg', '3kg']
MODELS = ['original', 'model_mlp', 'model_poly3', 'model_poly4',
          'model_forest', 'model_svr']
NICE = {'original': 'None (off)', 'model_mlp': 'MLP', 'model_poly3': 'POLY3',
        'model_poly4': 'POLY4', 'model_forest': 'RF', 'model_svr': 'SVR'}
LOAD_NICE = {'no_load': 'No-load', '1kg': '1 kg', '2kg': '2 kg', '3kg': '3 kg'}

TARGET_ID = 4                       # ArUco ที่ปลายขา
REF_WORLD = {0: np.array([-42.5, 0.0]),    # ข้อต่อมอเตอร์ซ้าย (ตรึงอยู่กับที่)
             1: np.array([+42.5, 0.0])}    # ข้อต่อมอเตอร์ขวา

CENTER_X_MM = 0.0                   # จุดศูนย์กลางวงโคจรที่สั่ง
CENTER_Y_MM = -170.0
RADIUS_MM = 30.0


# ── การวัดจากวิดีโอ (เหมือน vision_based_trajectory_eval.py) ──────────────────

def _marker_centers(corners, ids):
    out = {}
    if ids is None:
        return out
    for i, mid in enumerate(ids.flatten()):
        c = corners[i][0]
        out[int(mid)] = np.array([np.mean(c[:, 0]), np.mean(c[:, 1])], dtype=np.float64)
    return out


def _build_transform(centers):
    """pixel→mm similarity (มี reflection เพราะแกน y ของภาพชี้ลง) จาก id0/id1"""
    if 0 not in centers or 1 not in centers:
        return None
    p0, p1 = centers[0], centers[1]
    dx_px, dy_px = p1[0] - p0[0], p1[1] - p0[1]
    dx_mm = REF_WORLD[1][0] - REF_WORLD[0][0]
    dy_mm = REF_WORLD[1][1] - REF_WORLD[0][1]
    denom = dx_px ** 2 + dy_px ** 2
    a = (dx_mm * dx_px - dy_mm * dy_px) / denom
    b = (dx_mm * dy_px + dy_mm * dx_px) / denom
    tx = REF_WORLD[0][0] - a * p0[0] - b * p0[1]
    ty = REF_WORLD[0][1] - b * p0[0] + a * p0[1]
    M = np.array([[a, b, tx], [b, -a, ty]], dtype=np.float64)
    return lambda pt: M @ np.array([pt[0], pt[1], 1.0])


def track_video(video_path):
    with np.load(CALIB_FILE) as data:
        mtx, dist = data['camera_matrix'], data['dist_coeffs']

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError('Cannot open video: %s' % video_path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    new_mtx, _ = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 0)

    detector = aruco.ArucoDetector(
        aruco.getPredefinedDictionary(aruco.DICT_6X6_250),
        aruco.DetectorParameters())

    pts, seen, skipped = [], 0, 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        seen += 1
        undist = cv2.undistort(frame, mtx, dist, None, new_mtx)
        gray = cv2.cvtColor(undist, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)
        centers = _marker_centers(corners, ids)
        tf = _build_transform(centers)
        if tf is not None and TARGET_ID in centers:
            pts.append(tf(centers[TARGET_ID]))
        else:
            skipped += 1
    cap.release()
    return np.array(pts), seen, skipped


# ── ตัวชี้วัด ────────────────────────────────────────────────────────────────

def kasa_circle_fit(xy):
    """ฟิตวงกลมด้วยกำลังสองน้อยที่สุดเชิงพีชคณิต — ไม่ตรึงศูนย์กลาง/รัศมีล่วงหน้า"""
    x, y = xy[:, 0], xy[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    sol, *_ = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)
    xc, yc = sol[0] / 2.0, sol[1] / 2.0
    r = float(np.sqrt(sol[2] + xc ** 2 + yc ** 2))
    resid = np.hypot(x - xc, y - yc) - r
    return float(xc), float(yc), r, float(np.sqrt(np.mean(resid ** 2)))


def evaluate(job):
    load, model, path = job
    xy, seen, skipped = track_video(path)
    if len(xy) == 0:
        raise RuntimeError('no marker data tracked in %s' % path)
    err = np.hypot(xy[:, 0] - CENTER_X_MM, xy[:, 1] - CENTER_Y_MM) - RADIUS_MM
    xc, yc, r, fit_rms = kasa_circle_fit(xy)
    return dict(
        load=load, model=model, n=len(xy), frames=seen, skipped=skipped,
        rms=float(np.sqrt(np.mean(err ** 2))),
        mean=float(np.mean(err)), std=float(np.std(err)),
        maxabs=float(np.max(np.abs(err))),
        xc=xc, yc=yc, radius=r, fit_rms=fit_rms,
        offset=float(np.hypot(xc - CENTER_X_MM, yc - CENTER_Y_MM)),
        radius_err=float(r - RADIUS_MM),
    )


# ── รายงาน ───────────────────────────────────────────────────────────────────

def _pick(rows, load, model):
    for r in rows:
        if r['load'] == load and r['model'] == model:
            return r
    return None


def report(rows):
    print('\n' + '=' * 78)
    print('ตารางที่ 2 — องค์ประกอบของความคลาดเคลื่อน: offset เทียบ shape')
    print('=' * 78)
    print('%-26s' % 'Quantity' + ''.join('%10s' % LOAD_NICE[l] for l in LOADS))
    spec = [('radius', 'original', 'Radius, comp. off (mm)', '%10.2f'),
            ('radius', 'model_poly4', 'Radius, POLY4 (mm)', '%10.2f'),
            ('yc', 'original', 'Centre y, comp. off (mm)', '%10.2f'),
            ('yc', 'model_poly4', 'Centre y, POLY4 (mm)', '%10.2f'),
            ('offset', 'original', 'Centre offset, off (mm)', '%10.2f'),
            ('offset', 'model_poly4', 'Centre offset, POLY4 (mm)', '%10.2f'),
            ('fit_rms', 'original', 'Fit RMS, comp. off (mm)', '%10.2f'),
            ('fit_rms', 'model_poly4', 'Fit RMS, POLY4 (mm)', '%10.2f')]
    for key, model, label, fmt in spec:
        line = '%-26s' % label
        for load in LOADS:
            r = _pick(rows, load, model)
            line += (fmt % r[key]) if r else '%10s' % '-'
        print(line)

    print('\n' + '=' * 78)
    print('ตารางที่ 3 — ความคลาดเคลื่อนคงเหลือที่ปลายขาขณะแบบจำลองทำงานจริง (mm RMS)')
    print('=' * 78)
    print('%-12s' % 'Model' + ''.join('%9s' % LOAD_NICE[l] for l in LOADS) + '%9s' % 'Mean')
    ranked = []
    for model in MODELS:
        rs = [_pick(rows, load, model) for load in LOADS]
        if any(r is None for r in rs):
            continue
        ranked.append((model, [r['rms'] for r in rs],
                       float(np.mean([r['rms'] for r in rs]))))
    head = [t for t in ranked if t[0] == 'original']
    rest = sorted([t for t in ranked if t[0] != 'original'], key=lambda t: t[2])
    for model, vals, mean in head + rest:
        print('%-12s' % NICE[model] + ''.join('%9.2f' % v for v in vals)
              + '%9.2f' % mean)
    if head and rest:
        spread = rest[-1][2] - rest[0][2]
        print('\nช่วงระหว่างแบบจำลองที่ดีที่สุดกับแย่ที่สุด = %.2f mm '
              '(เทียบกับที่ลดลงจากไม่ชดเชย %.2f mm)'
              % (spread, head[0][2] - rest[0][2]))


def main():
    jobs = []
    for load in LOADS:
        for model in MODELS:
            path = os.path.join(VIDEO_ROOT, load, model + '.MOV')
            if os.path.exists(path):
                jobs.append((load, model, path))
            else:
                print('[warn] missing %s' % path)
    print('clips to process: %d' % len(jobs), flush=True)

    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(evaluate, jobs):
            rows.append(r)
            print('  %-8s %-12s n=%4d skipped=%3d  rms=%6.2f  offset=%6.2f  '
                  'radius=%6.2f' % (r['load'], NICE[r['model']], r['n'],
                                    r['skipped'], r['rms'], r['offset'],
                                    r['radius']), flush=True)

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    keys = ['load', 'model', 'n', 'frames', 'skipped', 'rms', 'mean', 'std',
            'maxabs', 'xc', 'yc', 'radius', 'fit_rms', 'offset', 'radius_err']
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in keys})
    report(rows)
    print('\nบันทึก → %s' % OUT_CSV)


if __name__ == '__main__':
    main()
