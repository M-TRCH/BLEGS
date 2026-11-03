"""One walking run, shown two ways: (1) the lens-corrected video with the runway grid, the tags and the robot
pose drawn on it, and (2) the floor warped to a top-down map (bird's-eye) with the same pose and the path.
Both use the cached detections of walk_video_metrics.py, so no detection is repeated.

  overlay : 10 cm grid (orange = tag rows), tag outlines (yellow = robot tags 0-3), tag rectangle dropped to
            the floor (cyan), heading (magenta), path so far (red)
  top-down: the floor plane rectified with the camera pose (4 px per cm), grid every 10 cm, floor tags appear as
            squares on their grid points when the geometry is right; robot tag positions are the ray-plane
            intersections at the tag height (their x, y are true horizontal positions)

    python walk_run_demo.py --video D:\\THESIS\\Walk-Test\\261030-0-kg\\ML-1.MP4 --calib output/params/calib_20mm_APSC_v2.npz ^
        --det output/video/cache_metrics_0kg/ML-1_det.pkl --metrics output/data/walk_video_metrics_261030_0kg.csv ^
        --run ML-1 --out output/video/demo_ML-1
"""
import argparse
import csv
import os
import pickle

import cv2
import numpy as np

import walk_video_metrics as wvm

ROW_PITCH = 40.0
BAR = 70


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True)
    ap.add_argument('--calib', required=True)
    ap.add_argument('--det', required=True, help='<run>_det.pkl written by walk_video_metrics.py')
    ap.add_argument('--out', required=True, help='prefix: writes <out>_overlay.mp4 and <out>_topdown.mp4')
    ap.add_argument('--metrics', default=None)
    ap.add_argument('--run', default=None, help='row of --metrics to print on the last frames')
    ap.add_argument('--z-rear-cm', type=float, default=26.0)
    ap.add_argument('--z-front-cm', type=float, default=27.5)
    ap.add_argument('--along-mm', type=float, default=373.0)
    ap.add_argument('--across-mm', type=float, default=140.0)
    ap.add_argument('--width', type=int, default=1280)
    a = ap.parse_args()

    z = np.load(a.calib)
    K, d = z['camera_matrix'], z['dist_coeffs']
    det = pickle.load(open(a.det, 'rb'))
    frames, step, fps = det['frames'], det['step'], det['fps']
    R, C, err, nfl = wvm.camera_pose(frames, K)
    Ki = np.linalg.inv(K)
    rvec, _ = cv2.Rodrigues(R)
    tvec = (-R @ C).reshape(3, 1)
    Lcm, Wcm = a.along_mm / 10.0, a.across_mm / 10.0

    def plane(uv, zc):
        ray = R.T @ (Ki @ np.array([uv[0], uv[1], 1.0]))
        return C + (zc - C[2]) / ray[2] * ray

    def pj(p3):
        q, _ = cv2.projectPoints(np.array(p3, np.float64).reshape(-1, 3), rvec, tvec, K, None)
        return q[:, 0]

    # floor-plane homography image -> top-down canvas
    s = 4.0
    xmin, xmax, ymin, ymax = -35.0, 115.0, -65.0, 255.0
    Wc, Hc = int((xmax - xmin) * s), int((ymax - ymin) * s)
    Hw2i = K @ np.column_stack((R[:, 0], R[:, 1], tvec[:, 0]))
    Mcv = np.array([[s, 0, -xmin * s], [0, -s, ymax * s], [0, 0, 1.0]])
    Mimg2canvas = Mcv @ np.linalg.inv(Hw2i)

    def to_canvas(x, y):
        return (int(round((x - xmin) * s)), int(round((ymax - y) * s)))

    label = ''
    if a.metrics and a.run:
        for r in csv.DictReader(open(a.metrics, encoding='utf-8')):
            if r['run'] == a.run:
                label = ('%s | distance %s cm | lateral shift %s cm (delta %s cm/m) | heading change %+.1f deg | speed %s cm/s' %
                         (a.run, r['D_cm'], r['d_cm'], r['delta_cm_per_m'], float(r['dphi_deg']), r['speed_cm_s']))

    cap = cv2.VideoCapture(a.video)
    w, h = int(cap.get(3)), int(cap.get(4))
    maps = cv2.initUndistortRectifyMap(K, d, None, K, (w, h), cv2.CV_16SC2)
    ow = a.width
    oh = int(round(h * ow / w))
    out_fps = fps / step
    wr_o = cv2.VideoWriter(a.out + '_overlay.mp4', cv2.VideoWriter_fourcc(*'mp4v'), out_fps, (ow, oh + BAR))
    wr_t = cv2.VideoWriter(a.out + '_topdown.mp4', cv2.VideoWriter_fourcc(*'mp4v'), out_fps, (Wc, Hc + BAR))
    th = max(2, w // 1200)
    trail = []
    idx = 0
    n_done = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if idx % step:
            idx += 1
            continue
        f = frames.get(idx, {})
        img = cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR)
        # ---- robot pose for this frame
        pts = {i: plane(f[i].mean(0), a.z_rear_cm if i < 2 else a.z_front_cm) for i in wvm.ROBOT_IDS if i in f}
        pose = None
        if len(pts) >= 2:
            xy = {i: p[:2] for i, p in pts.items()}
            if len(xy) == 4:
                fw = ((xy[2] - xy[0]) + (xy[3] - xy[1])) / 2
                fw /= np.linalg.norm(fw)
                ctr = np.mean(list(xy.values()), axis=0)
            elif 0 in xy and 1 in xy:
                u = xy[1] - xy[0]
                fw = np.array([-u[1], u[0]]) / np.linalg.norm(u)
                ctr = (xy[0] + xy[1]) / 2 + (Lcm / 2) * fw
            elif 2 in xy and 3 in xy:
                u = xy[3] - xy[2]
                fw = np.array([-u[1], u[0]]) / np.linalg.norm(u)
                ctr = (xy[2] + xy[3]) / 2 - (Lcm / 2) * fw
            else:
                fw = None
            if fw is not None:
                pose = (ctr, fw, np.degrees(np.arctan2(fw[1], fw[0])), len(xy))
                trail.append(ctr.copy())
        info = 'no robot pose (fewer than 2 tags)'
        if pose:
            info = 'robot centre x %.1f y %.1f cm | heading %.1f deg | %d/4 robot tags' % (pose[0][0], pose[0][1], pose[2], pose[3])
        t_txt = 't = %.2f s' % (idx / fps)

        # ---- 1. overlay on the camera image
        for xx in np.arange(-20, 100.1, 10.0):
            q = pj([(xx, -20, 0), (xx, 260, 0)]).astype(int)
            cv2.line(img, tuple(q[0]), tuple(q[1]), (255, 200, 0) if 0 <= xx <= 80 else (120, 100, 40), th if 0 <= xx <= 80 else 1, cv2.LINE_AA)
        for yy in np.arange(-20, 260.1, 10.0):
            row = abs(yy % ROW_PITCH) < 1e-6 and 0 <= yy <= 240
            q = pj([(-20, yy, 0), (100, yy, 0)]).astype(int)
            cv2.line(img, tuple(q[0]), tuple(q[1]), (0, 140, 255) if row else (255, 200, 0), th * 2 if row else th, cv2.LINE_AA)
        for i, c in f.items():
            col = (0, 255, 255) if i < 4 else (0, 255, 0)
            cv2.polylines(img, [c.astype(np.int32)], True, col, th * 2 if i < 4 else th, cv2.LINE_AA)
        if pose:
            ctr, fw = pose[0], pose[1]
            side = np.array([fw[1], -fw[0]])
            corners = [ctr + s1 * (Lcm / 2) * fw + s2 * (Wcm / 2) * side for s1, s2 in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            cv2.polylines(img, [pj([(c[0], c[1], 0.0) for c in corners]).astype(np.int32)], True, (255, 255, 0), th * 2, cv2.LINE_AA)
            if len(trail) > 1:
                cv2.polylines(img, [pj([(p[0], p[1], 0.0) for p in trail]).astype(np.int32)], False, (0, 0, 255), th, cv2.LINE_AA)
            a0, a1 = pj([(ctr[0], ctr[1], 0.0), (ctr[0] + 30 * fw[0], ctr[1] + 30 * fw[1], 0.0)]).astype(int)
            cv2.arrowedLine(img, tuple(a0), tuple(a1), (255, 0, 255), th * 2, cv2.LINE_AA, tipLength=0.25)
        small = cv2.resize(img, (ow, oh), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((oh + BAR, ow, 3), np.uint8)
        canvas[BAR:] = small
        for k, txt in enumerate(('overlay - camera image, lens corrected | ' + t_txt, info)):
            cv2.putText(canvas, txt, (14, 26 + k * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
        wr_o.write(canvas)

        # ---- 2. top-down map
        top = cv2.warpPerspective(cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR), Mimg2canvas, (Wc, Hc), flags=cv2.INTER_LINEAR)
        for xx in np.arange(-30, 111, 10.0):
            cv2.line(top, to_canvas(xx, ymin), to_canvas(xx, ymax), (255, 200, 0) if 0 <= xx <= 80 else (120, 100, 40), 1, cv2.LINE_AA)
        for yy in np.arange(-60, 251, 10.0):
            row = abs(yy % ROW_PITCH) < 1e-6 and 0 <= yy <= 240
            cv2.line(top, to_canvas(xmin, yy), to_canvas(xmax, yy), (0, 140, 255) if row else (255, 200, 0), 2 if row else 1, cv2.LINE_AA)
        for r_ in range(7):
            for cx in (0.0, 80.0):
                cv2.circle(top, to_canvas(cx, r_ * ROW_PITCH), 5, (0, 255, 0), -1, cv2.LINE_AA)       # nominal floor tag centres
        for r_ in range(7):
            cv2.putText(top, 'y=%d' % (r_ * 40), to_canvas(-33, r_ * 40 + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1, cv2.LINE_AA)
        if pose:
            ctr, fw = pose[0], pose[1]
            side = np.array([fw[1], -fw[0]])
            cs = [ctr + s1 * (Lcm / 2) * fw + s2 * (Wcm / 2) * side for s1, s2 in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            cv2.polylines(top, [np.array([to_canvas(c[0], c[1]) for c in cs], np.int32)], True, (255, 255, 0), 2, cv2.LINE_AA)
            if len(trail) > 1:
                cv2.polylines(top, [np.array([to_canvas(p[0], p[1]) for p in trail], np.int32)], False, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.arrowedLine(top, to_canvas(ctr[0], ctr[1]), to_canvas(ctr[0] + 30 * fw[0], ctr[1] + 30 * fw[1]), (255, 0, 255), 2, cv2.LINE_AA, tipLength=0.25)
            for i, p in pts.items():
                cv2.circle(top, to_canvas(p[0], p[1]), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.putText(top, str(i), (to_canvas(p[0], p[1])[0] + 8, to_canvas(p[0], p[1])[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)
        tcanvas = np.zeros((Hc + BAR, Wc, 3), np.uint8)
        tcanvas[BAR:] = top
        lines = ['top-down map (4 px per cm) | ' + t_txt, 'x %.1f y %.1f cm, %.1f deg' % (pose[0][0], pose[0][1], pose[2]) if pose else 'no pose']
        for k, txt in enumerate(lines):
            cv2.putText(tcanvas, txt, (10, 26 + k * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        if label and idx / fps > (max(frames) / fps) - 4.0:
            cv2.putText(tcanvas, a.run, (10, Hc + BAR - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        wr_t.write(tcanvas)
        if n_done == 140:
            cv2.imwrite(a.out + '_overlay_still.jpg', canvas)
            cv2.imwrite(a.out + '_topdown_still.jpg', tcanvas)
        n_done += 1
        idx += 1
    wr_o.release()
    wr_t.release()
    print('wrote', a.out + '_overlay.mp4', 'and', a.out + '_topdown.mp4', '|', n_done, 'frames at', out_fps, 'fps')
    if label:
        print(label)


if __name__ == '__main__':
    main()
