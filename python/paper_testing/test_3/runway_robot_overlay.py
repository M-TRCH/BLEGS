"""Robot + runway overlay from a lens-corrected video, with the robot placed in 3D.

What it does
  1. removes the lens distortion (camera_calibration_v2.py file) and detects every ArUco tag
     (detections are cached next to the output, so a re-run with other settings takes seconds)
  2. solves the camera pose from the runway floor tags (IDs 4..17, 2 columns x 7 rows, 80 x 40 cm,
     median over the clip so a robot passing over a tag does not matter)
  3. puts each robot tag (IDs 0-3) on its own plane z = tag height by intersecting the camera ray
     with that plane - this replaces the height/parallax approximation of the old script
  4. reports the tag-to-tag distances in mm (a check against a tape measure) and draws the
     floor grid, the tags, the robot centre, heading and footprint on every frame

Local robot frame, as in apriltag_runway_tilt_check.py: x = right, y = forward, IDs 0/1 at the rear
(left/right), 2/3 at the front. World: origin at floor tag 4, +x toward tag 5, +y along the runway,
heading 90 deg = along +y.

    python runway_robot_overlay.py --video D:\\THESIS\\Walk-Test\\Grid-14\\Runway-wRobot-Demo.MP4 \\
        --calib output/params/calib_20mm_APSC_v2.npz --out output/video/runway_robot_grid.mp4 \\
        --z-rear-cm 26.0 --z-front-cm 27.5 --across-mm 140 --along-mm 373
"""
import argparse
import os
import pickle
import time

import cv2
import cv2.aruco as aruco
import numpy as np

COL_X = {0: 0.0, 1: 80.0}
ROW_PITCH = 40.0
BAR = 124
ROBOT_IDS = (0, 1, 2, 3)


def floor_world(i):
    k = i - 4
    return (COL_X[k % 2], ROW_PITCH * (k // 2), 0.0)


def detect_all(video, K, d, cache):
    cap = cv2.VideoCapture(video)
    w, h, fps, nfr = int(cap.get(3)), int(cap.get(4)), cap.get(5), int(cap.get(7))
    if os.path.exists(cache):
        old = pickle.load(open(cache, 'rb'))
        if len(old['frames']) == nfr and np.allclose(old['K'], K):
            print('using cached detections', cache)
            return old['frames'], (w, h), fps
    maps = cv2.initUndistortRectifyMap(K, d, None, K, (w, h), cv2.CV_16SC2)
    det = aruco.ArucoDetector(aruco.getPredefinedDictionary(aruco.DICT_6X6_250), aruco.DetectorParameters())
    frames, t0 = [], time.time()
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR), cv2.COLOR_BGR2GRAY)
        c, ids, _ = det.detectMarkers(g)
        frames.append({int(i): cc[0].copy() for i, cc in zip(ids.ravel(), c)} if ids is not None else {})
        if len(frames) % 100 == 0:
            print('  detected %d/%d frames (%.0f s)' % (len(frames), nfr, time.time() - t0), flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(cache)), exist_ok=True)
    pickle.dump(dict(frames=frames, K=K, d=d, size=(w, h), fps=fps), open(cache, 'wb'))
    return frames, (w, h), fps


def camera_pose(frames, K):
    ids = [i for i in range(4, 18) if np.mean([i in f for f in frames]) > 0.3]
    W = np.array([floor_world(i) for i in ids], np.float64)
    P = np.array([np.median(np.array([f[i].mean(0) for f in frames if i in f]), 0) for i in ids], np.float64)
    ok, rv, tv = cv2.solvePnP(W, P, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
    R, _ = cv2.Rodrigues(rv)
    proj, _ = cv2.projectPoints(W, rv, tv, K, None)
    return rv, tv, R, (-R.T @ tv).ravel(), np.linalg.norm(proj[:, 0] - P, axis=1), ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True)
    ap.add_argument('--calib', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--z-rear-cm', type=float, default=27.0, help='height of tags 0,1 above the floor')
    ap.add_argument('--z-front-cm', type=float, default=27.0, help='height of tags 2,3 above the floor')
    ap.add_argument('--across-mm', type=float, default=140.0)
    ap.add_argument('--along-mm', type=float, default=373.0)
    ap.add_argument('--width', type=int, default=1920)
    ap.add_argument('--no-video', action='store_true')
    a = ap.parse_args()

    z = np.load(a.calib)
    K, d = z['camera_matrix'], z['dist_coeffs']
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    cache = os.path.splitext(a.out)[0] + '_det.pkl'
    frames, (w, h), fps = detect_all(a.video, K, d, cache)
    n = len(frames)
    rv, tv, R, C, res, ids = camera_pose(frames, K)
    Ki = np.linalg.inv(K)
    print('\ncamera from %d floor tags: x %.0f y %.0f height %.0f cm, %.0f deg below horizontal; reprojection mean %.2f px'
          % (len(ids), C[0], C[1], C[2], np.degrees(np.arcsin(-(R.T @ [0, 0, 1.0])[2])), res.mean()))
    print('floor tags never seen (damaged / hidden?):', [i for i in range(4, 18) if not any(i in f for f in frames)])

    def on_plane(uv, zc):
        ray = R.T @ (Ki @ np.array([uv[0], uv[1], 1.0]))
        return C + (zc - C[2]) / ray[2] * ray

    Lcm, Wcm = a.along_mm / 10.0, a.across_mm / 10.0
    poses = []                                     # per frame: (centre xy, heading deg, n tags) or None
    dist = []
    for f in frames:
        pts = {i: on_plane(f[i].mean(0), a.z_rear_cm if i < 2 else a.z_front_cm) for i in ROBOT_IDS if i in f}
        if len(pts) < 2:
            poses.append(None)
            continue
        if all(i in pts for i in ROBOT_IDS):
            dist.append([np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3]),
                         np.linalg.norm(pts[0] - pts[2]), np.linalg.norm(pts[1] - pts[3])])
            u = ((pts[1] - pts[0]) + (pts[3] - pts[2]))[:2] / 2
            fwd = ((pts[2] - pts[0]) + (pts[3] - pts[1]))[:2] / 2
            fwd /= np.linalg.norm(fwd)
            ctr = np.mean([pts[i][:2] for i in ROBOT_IDS], axis=0)
        else:
            if 0 in pts and 1 in pts:
                u = (pts[1] - pts[0])[:2]; mid = (pts[0] + pts[1])[:2] / 2; sgn = +1
            elif 2 in pts and 3 in pts:
                u = (pts[3] - pts[2])[:2]; mid = (pts[2] + pts[3])[:2] / 2; sgn = -1
            else:
                poses.append(None)
                continue
            fwd = np.array([-u[1], u[0]]) / np.linalg.norm(u)
            ctr = mid + sgn * (Lcm / 2) * fwd
        poses.append((ctr, float(np.degrees(np.arctan2(fwd[1], fwd[0]))), len(pts), np.array([-fwd[1], fwd[0]])))
    if dist:
        D = np.array(dist) * 10
        print('\ntag distances (mm) over %d frames with all 4 tags; tape measure: across %.0f, along %.0f' % (len(D), a.across_mm, a.along_mm))
        for nm, k, ref in (('0-1', 0, a.across_mm), ('2-3', 1, a.across_mm), ('0-2', 2, a.along_mm), ('1-3', 3, a.along_mm)):
            print('  %s  mean %.1f  sd %.1f   (%+.1f mm vs tape)' % (nm, D[:, k].mean(), D[:, k].std(), D[:, k].mean() - ref))
    seen = [p for p in poses if p]
    print('frames with a robot pose: %d/%d (4 tags: %d, 2-3 tags: %d)' %
          (len(seen), n, sum(1 for p in seen if p[2] == 4), sum(1 for p in seen if p[2] < 4)))
    if a.no_video:
        return

    ow = a.width
    oh = int(round(h * ow / w))
    writer = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (ow, oh + BAR))
    cap = cv2.VideoCapture(a.video)
    maps = cv2.initUndistortRectifyMap(K, d, None, K, (w, h), cv2.CV_16SC2)
    th = max(2, w // 1200)

    def pj(pts3):
        p, _ = cv2.projectPoints(np.array(pts3, np.float64).reshape(-1, 3), rv, tv, K, None)
        return p[:, 0]

    def line3(img, p, q, col, t):
        pp = pj([p, q]).astype(int)
        cv2.line(img, tuple(pp[0]), tuple(pp[1]), col, t, cv2.LINE_AA)

    for yy in np.arange(-30, 270.1, 10.0):
        pass
    trail = []
    for k in range(n):
        ok, fr = cap.read()
        if not ok:
            break
        img = cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR)
        for xx in np.arange(-20, 100.1, 10.0):
            line3(img, (xx, -20, 0), (xx, 260, 0), (255, 200, 0) if 0 <= xx <= 80 else (120, 100, 40), th if 0 <= xx <= 80 else 1)
        for yy in np.arange(-20, 260.1, 10.0):
            row = abs(yy % ROW_PITCH) < 1e-6 and 0 <= yy <= 240
            line3(img, (-20, yy, 0), (100, yy, 0), (0, 140, 255) if row else (255, 200, 0), th * 2 if row else th)
        for i, c in frames[k].items():
            col = (0, 255, 255) if i < 4 else (0, 255, 0)
            cv2.polylines(img, [c.astype(np.int32)], True, col, th * 2 if i < 4 else th, cv2.LINE_AA)
            cv2.putText(img, str(i), tuple((c.mean(0) + [-14, -26]).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, w / 2200, col, th, cv2.LINE_AA)
        p = poses[k]
        info = 'robot: no pose (fewer than 2 tags)'
        if p:
            ctr, hd, nt, left = p[0], p[1], p[2], p[3]
            fw = np.array([np.cos(np.radians(hd)), np.sin(np.radians(hd))])
            trail.append((ctr[0], ctr[1], 0.0))
            corners = [ctr + s1 * (Lcm / 2) * fw + s2 * (Wcm / 2) * np.array([fw[1], -fw[0]]) for s1, s2 in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            poly = pj([(c[0], c[1], 0.0) for c in corners]).astype(np.int32)
            cv2.polylines(img, [poly], True, (255, 255, 0), th * 2, cv2.LINE_AA)
            if len(trail) > 1:
                cv2.polylines(img, [pj(trail).astype(np.int32)], False, (0, 0, 255), th, cv2.LINE_AA)
            a0, a1 = pj([(ctr[0], ctr[1], 0.0), (ctr[0] + 30 * fw[0], ctr[1] + 30 * fw[1], 0.0)]).astype(int)
            cv2.arrowedLine(img, tuple(a0), tuple(a1), (255, 0, 255), th * 2, cv2.LINE_AA, tipLength=0.25)
            cv2.circle(img, tuple(a0), th * 4, (255, 0, 255), -1, cv2.LINE_AA)
            info = 'robot centre x %.1f y %.1f cm | heading %.1f deg (90 = along +y) | %d/4 robot tags%s' % (
                ctr[0], ctr[1], hd, nt, '' if nt == 4 else ' (pose from the visible pair)')
        txt = ['t=%.2fs frame %d | undistorted | tag plane z: rear %.1f / front %.1f cm' % (k / fps, k, a.z_rear_cm, a.z_front_cm), info,
               'grid 10 cm, orange = tag rows | cyan = tag rectangle on the floor | magenta = heading | red = path']
        canvas = np.zeros((oh + BAR, ow, 3), np.uint8)
        canvas[BAR:] = cv2.resize(img, (ow, oh), interpolation=cv2.INTER_AREA)
        for j, t in enumerate(txt):
            cv2.putText(canvas, t, (24, 34 + j * 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(canvas)
        if k == 60:
            cv2.imwrite(os.path.splitext(a.out)[0] + '_still.jpg', canvas)
    writer.release()
    print('wrote', a.out)


if __name__ == '__main__':
    main()
