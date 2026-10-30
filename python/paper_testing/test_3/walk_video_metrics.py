"""Section-2.3.2 metrics from the walking videos: robot pose on the runway frame by frame, then the
lateral deviation, heading change, distance and speed of each run.

Per video (lens-corrected with a camera_calibration_v2.py file):
  1. detect every ArUco tag on every STEP-th frame (cached next to the output, so re-runs are quick)
  2. camera pose from the runway floor tags (IDs 4..17: 2 columns x 7 rows, 80 x 40 cm) - median over
     the clip, so a robot passing over a tag does not matter
  3. each robot tag (IDs 0-3) is placed on its own plane z by intersecting the camera ray with it;
     the robot pose is the rigid fit of the visible tags (all 4, else the rear/front pair)
  4. metrics, following section 2.3.2: the first and last second of the clip are the release and final
     states; d = lateral shift (cm, + = right), D = distance along the runway (cm),
     delta = d / D (cm per metre), phi = heading change (deg, + = counter-clockwise seen from above)

World frame: origin at floor tag 4, +x toward tag 5, +y along the runway, heading 90 deg = +y.

    python walk_video_metrics.py --calib output/params/calib_20mm_APSC_v2.npz --out output/video/metrics_0kg.csv ^
        D:\\THESIS\\Walk-Test\\261030-0-kg\\ML-1.MP4 D:\\THESIS\\Walk-Test\\261030-0-kg\\WO-1.MP4 ...
"""
import argparse
import multiprocessing as mp
import os
import pickle
import re
import time

import cv2
import cv2.aruco as aruco
import numpy as np

COL_X = {0: 0.0, 1: 80.0}
ROW_PITCH = 40.0
ROBOT_IDS = (0, 1, 2, 3)


def floor_world(i):
    k = i - 4
    return (COL_X[k % 2], ROW_PITCH * (k // 2), 0.0)


def detect(video, K, d, step, cache):
    cap = cv2.VideoCapture(video)
    w, h, fps, nfr = int(cap.get(3)), int(cap.get(4)), cap.get(5), int(cap.get(7))
    if os.path.exists(cache):
        old = pickle.load(open(cache, 'rb'))
        if old['nfr'] == nfr and old['step'] == step and np.allclose(old['K'], K):
            return old
    cv2.setNumThreads(2)
    maps = cv2.initUndistortRectifyMap(K, d, None, K, (w, h), cv2.CV_16SC2)
    det = aruco.ArucoDetector(aruco.getPredefinedDictionary(aruco.DICT_6X6_250), aruco.DetectorParameters())
    idx, out = 0, {}
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if idx % step == 0:
            g = cv2.cvtColor(cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR), cv2.COLOR_BGR2GRAY)
            c, ids, _ = det.detectMarkers(g)
            out[idx] = {int(i): cc[0].copy() for i, cc in zip(ids.ravel(), c)} if ids is not None else {}
        idx += 1
    res = dict(frames=out, nfr=nfr, step=step, K=K, size=(w, h), fps=fps)
    pickle.dump(res, open(cache, 'wb'))
    return res


def camera_pose(frames, K):
    allf = list(frames.values())
    ids = [i for i in range(4, 18) if np.mean([i in f for f in allf]) > 0.3]
    W = np.array([floor_world(i) for i in ids], np.float64)
    P = np.array([np.median(np.array([f[i].mean(0) for f in allf if i in f]), 0) for i in ids], np.float64)
    ok, rv, tv = cv2.solvePnP(W, P, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
    R, _ = cv2.Rodrigues(rv)
    proj, _ = cv2.projectPoints(W, rv, tv, K, None)
    return R, (-R.T @ tv).ravel(), np.linalg.norm(proj[:, 0] - P, axis=1).mean(), len(ids)


def robot_poses(res, K, z_rear, z_front, along_cm):
    R, C, err, nfl = camera_pose(res['frames'], K)
    Ki = np.linalg.inv(K)

    def plane(uv, z):
        ray = R.T @ (Ki @ np.array([uv[0], uv[1], 1.0]))
        return C + (z - C[2]) / ray[2] * ray

    rows = []
    for fi in sorted(res['frames']):
        f = res['frames'][fi]
        pts = {i: plane(f[i].mean(0), z_rear if i < 2 else z_front)[:2] for i in ROBOT_IDS if i in f}
        if len(pts) < 2:
            continue
        if len(pts) == 4:
            u = ((pts[1] - pts[0]) + (pts[3] - pts[2])) / 2
            fw = ((pts[2] - pts[0]) + (pts[3] - pts[1])) / 2
            fw = fw / np.linalg.norm(fw)
            ctr = np.mean([pts[i] for i in ROBOT_IDS], axis=0)
        else:
            if 0 in pts and 1 in pts:
                u = pts[1] - pts[0]; mid = (pts[0] + pts[1]) / 2; sgn = +1
            elif 2 in pts and 3 in pts:
                u = pts[3] - pts[2]; mid = (pts[2] + pts[3]) / 2; sgn = -1
            else:
                continue
            fw = np.array([-u[1], u[0]]) / np.linalg.norm(u)
            ctr = mid + sgn * (along_cm / 2) * fw
        rows.append((fi / res['fps'], ctr[0], ctr[1], float(np.degrees(np.arctan2(fw[1], fw[0]))), len(pts)))
    return np.array(rows), dict(cam_h=C[2], cam_y=C[1], cam_x=C[0], floor_err_px=err, n_floor=nfl)


def metrics(name, rows, info):
    t, x, y, hd, nt = rows.T
    hd = np.unwrap(np.radians(hd)); hd = np.degrees(hd)
    fps_eff = len(t) / (t[-1] - t[0]) if t[-1] > t[0] else 0
    k1 = t <= t[0] + 1.0
    k2 = t >= t[-1] - 1.0
    x0, y0, h0 = np.median(x[k1]), np.median(y[k1]), np.median(hd[k1])
    x1, y1, h1 = np.median(x[k2]), np.median(y[k2]), np.median(hd[k2])
    D = y1 - y0
    dx = x1 - x0
    # movement window: first/last time the robot is more than 4 cm from its start / final spot
    ms = t[np.argmax(np.hypot(x - x0, y - y0) > 4.0)] if (np.hypot(x - x0, y - y0) > 4.0).any() else np.nan
    me_idx = np.where(np.hypot(x - x1, y - y1) > 4.0)[0]
    me = t[me_idx[-1]] if len(me_idx) else np.nan
    moving = (t >= ms) & (t <= me) if np.isfinite(ms) and np.isfinite(me) else np.zeros_like(t, bool)
    speed = D / (me - ms) if np.isfinite(ms) and np.isfinite(me) and me > ms else np.nan
    lat = x - x0
    return dict(run=name, clip_s=round(t[-1], 1), poses=len(t), four_tags_pct=round(100 * np.mean(nt == 4)),
                D_cm=round(D, 1), d_cm=round(dx, 1), delta_cm_per_m=round(dx / (D / 100.0), 2) if abs(D) > 1 else np.nan,
                dphi_deg=round(h1 - h0, 2), phi0_deg=round(h0, 1), speed_cm_s=round(speed, 2),
                move_start_s=round(ms, 1), move_end_s=round(me, 1), walk_s=round(me - ms, 1) if np.isfinite(me) and np.isfinite(ms) else np.nan,
                max_abs_lat_cm=round(np.abs(lat).max(), 1), y_end_cm=round(y1, 1), x_start_cm=round(x0, 1),
                cam_height_cm=round(info['cam_h']), floor_tag_err_px=round(info['floor_err_px'], 2))


def work(args):
    video, calib, step, zr, zf, along, cache_dir = args
    z = np.load(calib)
    K, d = z['camera_matrix'], z['dist_coeffs']
    name = os.path.splitext(os.path.basename(video))[0]
    t0 = time.time()
    res = detect(video, K, d, step, os.path.join(cache_dir, name + '_det.pkl'))
    rows, info = robot_poses(res, K, zr, zf, along)
    m = metrics(name, rows, info)
    np.save(os.path.join(cache_dir, name + '_pose.npy'), rows)
    print('  %-8s done in %.0f s: D %.0f cm, d %+.1f cm, delta %+.1f cm/m, dphi %+.1f deg' % (name, time.time() - t0, m['D_cm'], m['d_cm'], m['delta_cm_per_m'], m['dphi_deg']), flush=True)
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('videos', nargs='+')
    ap.add_argument('--calib', required=True)
    ap.add_argument('--out', required=True, help='summary CSV')
    ap.add_argument('--step', type=int, default=2, help='detect on every Nth frame')
    ap.add_argument('--z-rear-cm', type=float, default=26.0)
    ap.add_argument('--z-front-cm', type=float, default=27.5)
    ap.add_argument('--along-mm', type=float, default=373.0)
    ap.add_argument('--jobs', type=int, default=4)
    a = ap.parse_args()
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'cache_' + os.path.splitext(os.path.basename(a.out))[0])
    os.makedirs(cache_dir, exist_ok=True)
    jobs = [(v, a.calib, a.step, a.z_rear_cm, a.z_front_cm, a.along_mm / 10.0, cache_dir) for v in a.videos]
    with mp.Pool(min(a.jobs, len(jobs))) as pool:
        res = pool.map(work, jobs)
    import csv
    with open(a.out, 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
        wr.writeheader()
        wr.writerows(res)
    print('wrote', a.out)


if __name__ == '__main__':
    mp.freeze_support()
    main()
