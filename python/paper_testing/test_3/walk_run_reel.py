"""One walking run as a vertical 9:16 clip (1080 x 1920, 60p) for sharing: the lens-corrected video turned 90 deg
so the robot walks up the frame, with the measured path, a straight reference line from the start pose, live
pose numbers, the run condition, a small top-down homography warp of the floor in a corner, and a closing
results card.  Uses the cached detections and poses of walk_video_metrics.py, so nothing is detected again.

The camera records 25 fps; each 60p output frame shows the nearest source frame (no motion interpolation), while
the drawn pose is interpolated linearly between the 12.5 Hz pose samples so the overlay moves smoothly.

    python walk_run_reel.py --video D:\\THESIS\\Walk-Test\\261103-0-kg\\ML-01.MP4 --calib output/params/calib_20mm_APSC_v2.npz ^
        --cache output/video/cache_metrics_0kg_r22 --metrics output/video/metrics_0kg_r22.csv --run ML-01 ^
        --log output/log/movement_+3150mm_20261103_152130.csv --out D:\\THESIS\\Walk-Test\\261103-0-kg\\output\\reel_ML-01.mp4
"""
import argparse
import os
import pickle

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

import walk_video_metrics as wvm

OW, OH, OFPS = 1080, 1920, 60
FONT = r'C:\Windows\Fonts\segoeui.ttf'
FONT_B = r'C:\Windows\Fonts\segoeuib.ttf'
MONO = r'C:\Windows\Fonts\consola.ttf'
PATH_COL = (40, 120, 255)      # BGR: path
REF_COL = (255, 255, 255)      # straight reference
BODY_COL = (255, 230, 60)      # footprint
HEAD_COL = (255, 80, 230)      # heading arrow


def font(p, s):
    return ImageFont.truetype(p, s)


def panel(draw, box, alpha=150):
    draw.rounded_rectangle(box, radius=22, fill=(10, 12, 16, alpha))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True)
    ap.add_argument('--calib', required=True)
    ap.add_argument('--cache', required=True, help='cache dir of walk_video_metrics.py (<run>_det.pkl, <run>_pose.npy)')
    ap.add_argument('--metrics', required=True)
    ap.add_argument('--run', required=True)
    ap.add_argument('--log', default=None, help='walk_test log of this run, for the condition line')
    ap.add_argument('--out', required=True)
    ap.add_argument('--compare', default='WO', help='prefix of the other condition in --metrics, averaged on the end card')
    ap.add_argument('--inset', default='left', choices=('left', 'right'))
    ap.add_argument('--along-mm', type=float, default=373.0)
    ap.add_argument('--across-mm', type=float, default=140.0)
    ap.add_argument('--pre-s', type=float, default=2.0)
    ap.add_argument('--post-s', type=float, default=2.5)
    ap.add_argument('--card-s', type=float, default=5.0)
    a = ap.parse_args()

    z = np.load(a.calib)
    K, dist = z['camera_matrix'], z['dist_coeffs']
    det = pickle.load(open(os.path.join(a.cache, a.run + '_det.pkl'), 'rb'))
    pose = np.load(os.path.join(a.cache, a.run + '_pose.npy'))
    R, C, ferr, nfl = wvm.camera_pose(det['frames'], K)
    rvec, _ = cv2.Rodrigues(R)
    tvec = (-R @ C).reshape(3, 1)
    met = pd.read_csv(a.metrics).set_index('run')
    m = met.loc[a.run]
    other = met[met.index.str.startswith(a.compare)]
    Lcm, Wcm = a.along_mm / 10.0, a.across_mm / 10.0

    # pose: same start reference as walk_video_metrics.metrics (median of the first second)
    t, x, y, hd = pose[:, 0], pose[:, 1], pose[:, 2], np.degrees(np.unwrap(np.radians(pose[:, 3])))
    k1 = t <= t[0] + 1.0
    x0, y0, h0 = np.median(x[k1]), np.median(y[k1]), np.median(hd[k1])
    ker = np.ones(3) / 3
    xs = np.convolve(np.pad(x, 1, mode='edge'), ker, 'valid')
    ys = np.convolve(np.pad(y, 1, mode='edge'), ker, 'valid')
    hs = np.convolve(np.pad(hd, 1, mode='edge'), ker, 'valid')

    def pose_at(tt):
        return np.interp(tt, t, xs), np.interp(tt, t, ys), np.interp(tt, t, hs)

    cond = []
    if a.log and os.path.exists(a.log):
        lg = pd.read_csv(a.log)
        wk = lg[lg.phase == 'WALK']
        g = lambda c, d='?': wk[c].iloc[0] if c in wk and len(wk) else d
        cond = ['ML compensation %s' % ('ON' if int(g('ml_on', 0)) else 'OFF'),
                'gain %.2f' % float(g('ml_gain', 0)), 'steer trim %+.0f %%' % float(g('steer_trim_pct', 0)),
                'payload %s kg' % g('payload_kg'), 'code %s' % g('code_id')]

    cap = cv2.VideoCapture(a.video)
    W, H, fps, nfr = int(cap.get(3)), int(cap.get(4)), cap.get(5), int(cap.get(7))
    maps = cv2.initUndistortRectifyMap(K, dist, None, K, (W, H), cv2.CV_16SC2)
    sc = OW / H                      # rotated frame is H x W; H -> 1080

    def to_out(uv):
        uv = np.asarray(uv, np.float64).reshape(-1, 2)
        return np.column_stack(((uv[:, 1]) * sc, (W - 1 - uv[:, 0]) * sc))   # 90 deg CCW, then scale

    def pj(p3):
        q, _ = cv2.projectPoints(np.array(p3, np.float64).reshape(-1, 3), rvec, tvec, K, None)
        return to_out(q[:, 0])

    # top-down inset
    s = 2.4
    xmin, xmax, ymin, ymax = -20.0, 100.0, -40.0, 230.0
    Wi, Hi = int((xmax - xmin) * s), int((ymax - ymin) * s)
    Hw2i = K @ np.column_stack((R[:, 0], R[:, 1], tvec[:, 0]))
    Mimg2ins = np.array([[s, 0, -xmin * s], [0, -s, ymax * s], [0, 0, 1.0]]) @ np.linalg.inv(Hw2i)

    def ins(px, py):
        return (int(round((px - xmin) * s)), int(round((ymax - py) * s)))

    ix = 28 if a.inset == 'left' else OW - Wi - 28
    iy = 300

    f_title, f_sub, f_lbl = font(FONT_B, 46), font(FONT, 27), font(FONT, 24)
    f_big, f_unit, f_mono, f_small = font(FONT_B, 54), font(FONT, 24), font(MONO, 22), font(FONT, 21)

    t_start = max(0.0, m.move_start_s - a.pre_s)
    t_end = min(nfr / fps, m.move_end_s + a.post_s)
    n_out = int((t_end - t_start) * OFPS)
    n_card = int(a.card_s * OFPS)
    wr = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*'mp4v'), OFPS, (OW, OH))

    src_idx, src_main, src_top = -1, None, None

    def grab(i):
        nonlocal src_idx, src_main, src_top
        if i < src_idx:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            src_idx = i - 1
        fr = None
        while src_idx < i:
            ok, fr = cap.read()
            if not ok:
                return
            src_idx += 1
        if fr is None:
            return
        und = cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR)
        src_main = cv2.resize(cv2.rotate(und, cv2.ROTATE_90_COUNTERCLOCKWISE), (OW, OH), interpolation=cv2.INTER_AREA)
        src_top = cv2.warpPerspective(und, Mimg2ins, (Wi, Hi), flags=cv2.INTER_AREA)

    trail_t = t[(t >= t_start)]
    last = None
    for k in range(n_out + n_card):
        card = k >= n_out
        tt = t_start + min(k, n_out - 1) / OFPS
        if not card:
            grab(min(nfr - 1, int(round(tt * fps))))
            img = src_main.copy()
            top = src_top.copy()
            px, py, ph = pose_at(tt)
            fw = np.array([np.cos(np.radians(ph)), np.sin(np.radians(ph))])
            side = np.array([fw[1], -fw[0]])
            tr = [pose_at(q)[:2] for q in trail_t[trail_t <= tt]] + [(px, py)]
            # main: runway rows (subtle), straight reference, path, footprint, heading
            ov = img.copy()
            for r_ in range(7):
                q = pj([(-10, r_ * 40, 0), (90, r_ * 40, 0)]).astype(int)
                cv2.line(ov, tuple(q[0]), tuple(q[1]), (0, 170, 255), 2, cv2.LINE_AA)
            img = cv2.addWeighted(ov, 0.45, img, 0.55, 0)
            q = pj([(x0, y0, 0), (x0 + 240 * np.cos(np.radians(h0)), y0 + 240 * np.sin(np.radians(h0)), 0)]).astype(int)
            for j in range(0, 24, 2):                                 # dashed straight reference
                p1 = q[0] + (q[1] - q[0]) * j / 24
                p2 = q[0] + (q[1] - q[0]) * (j + 1) / 24
                cv2.line(img, tuple(p1.astype(int)), tuple(p2.astype(int)), REF_COL, 3, cv2.LINE_AA)
            if len(tr) > 1:
                cv2.polylines(img, [pj([(p[0], p[1], 0) for p in tr]).astype(np.int32)], False, PATH_COL, 5, cv2.LINE_AA)
            cs = [np.array([px, py]) + s1 * (Lcm / 2) * fw + s2 * (Wcm / 2) * side for s1, s2 in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            cv2.polylines(img, [pj([(c[0], c[1], 0) for c in cs]).astype(np.int32)], True, BODY_COL, 3, cv2.LINE_AA)
            a0, a1 = pj([(px, py, 0), (px + 28 * fw[0], py + 28 * fw[1], 0)]).astype(int)
            cv2.arrowedLine(img, tuple(a0), tuple(a1), HEAD_COL, 4, cv2.LINE_AA, tipLength=0.3)
            # inset: grid, reference, path, footprint
            for xx in np.arange(-20, 101, 10.0):
                cv2.line(top, ins(xx, ymin), ins(xx, ymax), (200, 170, 60), 1, cv2.LINE_AA)
            for yy in np.arange(-40, 231, 10.0):
                row = abs(yy % 40) < 1e-6
                cv2.line(top, ins(xmin, yy), ins(xmax, yy), (0, 150, 255) if row else (200, 170, 60), 2 if row else 1, cv2.LINE_AA)
            cv2.line(top, ins(x0, y0), ins(x0 + 240 * np.cos(np.radians(h0)), y0 + 240 * np.sin(np.radians(h0))), REF_COL, 1, cv2.LINE_AA)
            if len(tr) > 1:
                cv2.polylines(top, [np.array([ins(p[0], p[1]) for p in tr], np.int32)], False, PATH_COL, 3, cv2.LINE_AA)
            cv2.polylines(top, [np.array([ins(c[0], c[1]) for c in cs], np.int32)], True, BODY_COL, 2, cv2.LINE_AA)
            cv2.arrowedLine(top, ins(px, py), ins(px + 25 * fw[0], py + 25 * fw[1]), HEAD_COL, 2, cv2.LINE_AA, tipLength=0.3)
            img[iy:iy + Hi, ix:ix + Wi] = top
            cv2.rectangle(img, (ix - 2, iy - 2), (ix + Wi + 1, iy + Hi + 1), (255, 255, 255), 2)
            live = (tt, py - y0, px - x0, ph - h0)
            last = (img.copy(), live)
        else:
            img = last[0].copy()
            live = last[1]

        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')
        lay = Image.new('RGBA', pil.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(lay)
        if card:                                    # dim first: drawing on the RGBA layer replaces, not blends
            fade = min(1.0, (k - n_out) / (0.4 * OFPS))
            dr.rectangle((0, 0, OW, OH), fill=(0, 0, 0, int(120 * fade)))
        # header
        panel(dr, (20, 20, OW - 20, 262), 170)
        dr.text((48, 36), 'BLEGS quadruped - straight walk', font=f_title, fill=(255, 255, 255))
        dr.text((48, 100), '  |  '.join(cond[:3]) if cond else a.run, font=f_sub, fill=(120, 200, 255))
        dr.text((48, 140), '  |  '.join(cond[3:]) + '  |  run %s' % a.run, font=f_sub, fill=(220, 220, 220))
        dr.text((48, 186), 'ArUco 6x6 tags, lens-corrected  |  camera pose from %d floor tags (%.1f px)' % (nfl, ferr),
                font=f_small, fill=(170, 170, 170))
        dr.text((48, 216), 'robot tags ray-cast to their height  |  source 4K 25 fps -> 1080x1920 60p',
                font=f_small, fill=(170, 170, 170))
        dr.text((ix, iy + Hi + 8), 'top-down warp (floor homography)', font=f_small, fill=(255, 255, 255),
                stroke_width=2, stroke_fill=(0, 0, 0))
        if not card:
            # live numbers
            y_p = OH - 330
            panel(dr, (20, y_p, OW - 20, OH - 20), 170)
            cols = [('time', '%.1f' % (live[0] - t_start), 's'), ('forward', '%.0f' % live[1], 'cm'),
                    ('lateral', '%+.1f' % live[2], 'cm'), ('heading', '%+.1f' % live[3], 'deg')]
            cw = (OW - 40) / 4
            for j, (lab, val, unit) in enumerate(cols):
                cx = 20 + cw * j + 30
                dr.text((cx, y_p + 26), lab, font=f_lbl, fill=(170, 170, 170))
                dr.text((cx, y_p + 58), val, font=f_big, fill=(255, 255, 255))
                dr.text((cx, y_p + 128), unit, font=f_unit, fill=(170, 170, 170))
            # legend
            ly = y_p + 190
            for j, (col, txt) in enumerate(((PATH_COL, 'measured path'), (REF_COL, 'straight from start'),
                                           (BODY_COL, 'body footprint'), (HEAD_COL, 'heading'))):
                lx = 50 + j * 255
                dr.line((lx, ly + 16, lx + 40, ly + 16), fill=col[::-1] + (255,), width=6)
                dr.text((lx + 50, ly), txt, font=f_small, fill=(230, 230, 230))
            dr.text((50, ly + 50), 'lateral + = right, heading + = turned left (counter-clockwise)', font=f_small, fill=(150, 150, 150))
        else:
            y_c = 640
            panel(dr, (60, y_c, OW - 60, y_c + 790), int(225 * fade))
            al = int(255 * fade)
            dr.text((100, y_c + 40), 'Result - %s' % a.run, font=f_title, fill=(255, 255, 255, al))
            rows = [('distance walked', '%.0f cm' % m.D_cm), ('lateral shift', '%+.1f cm' % m.d_cm),
                    ('drift per metre', '%+.1f cm/m' % m.delta_cm_per_m), ('heading change', '%+.1f deg' % m.dphi_deg),
                    ('speed', '%.1f cm/s' % m.speed_cm_s)]
            for j, (lab, val) in enumerate(rows):
                yy = y_c + 140 + j * 74
                dr.text((100, yy), lab, font=f_sub, fill=(190, 190, 190, al))
                dr.text((620, yy - 8), val, font=f_big if j == 2 else font(FONT_B, 40), fill=(255, 255, 255, al))
            if len(other):
                yy = y_c + 540
                dr.line((100, yy, OW - 100, yy), fill=(90, 90, 90, al), width=2)
                same = met[met.index.str.startswith(a.run.split('-')[0])]
                dr.text((100, yy + 30), 'Same day, %d pairs:' % len(other), font=f_sub, fill=(190, 190, 190, al))
                dr.text((100, yy + 80), 'ML on   mean drift %+.1f cm/m, heading %+.1f deg' % (same.delta_cm_per_m.mean(), same.dphi_deg.mean()),
                        font=f_sub, fill=(120, 200, 255, al))
                dr.text((100, yy + 126), 'ML off  mean drift %+.1f cm/m, heading %+.1f deg' % (other.delta_cm_per_m.mean(), other.dphi_deg.mean()),
                        font=f_sub, fill=(255, 170, 120, al))
                dr.text((100, yy + 190), 'lateral + = right, heading + = turned left', font=f_small, fill=(150, 150, 150, al))
        frame = cv2.cvtColor(np.array(Image.alpha_composite(pil, lay).convert('RGB')), cv2.COLOR_RGB2BGR)
        wr.write(frame)
        if k in (int(n_out * 0.6), n_out + n_card - 1):
            cv2.imwrite(os.path.splitext(a.out)[0] + ('_still.jpg' if not card else '_card.jpg'), frame)
    wr.release()
    print('wrote %s | %d frames (%.1f s) at %d fps' % (a.out, n_out + n_card, (n_out + n_card) / OFPS, OFPS))


if __name__ == '__main__':
    main()
