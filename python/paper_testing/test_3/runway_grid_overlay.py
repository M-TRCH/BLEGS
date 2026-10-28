"""Export a runway video with the world grid drawn on top, and report how well the
nominal tag layout agrees with what the camera sees.

For every frame: (optionally) remove the lens distortion with a camera_calibration_v2.py
file, detect the runway tags (IDs 4..., 2 columns x N rows, 80 cm x 40 cm pitch), fit the
plane homography world->image to the tag CENTRES, and draw the 10 cm grid, the tag rows,
the tag outlines and the fit residual. The residual (nominal position minus where the
homography puts each tag, in mm on the floor) is the honest check of calibration + layout:
if the lens correction helps, it is smaller with --calib than without.

    python runway_grid_overlay.py --video D:\\THESIS\\Walk-Test\\Grid-14\\Runway-Demo.MP4 \\
        --calib output/params/calib_20mm_APSC_v2.npz --out output/video/runway_demo_grid.mp4
"""
import argparse
import os

import cv2
import cv2.aruco as aruco
import numpy as np

COL_X = {0: 0.0, 1: 80.0}
ROW_PITCH = 40.0
BAR = 124                      # height (px) of the black text bar above the picture


def world(tag_id):
    k = tag_id - 4
    return (COL_X[k % 2], (k // 2) * ROW_PITCH)


def tag_centres(det, gray, ids_wanted):
    c, ids, _ = det.detectMarkers(gray)
    out = {}
    if ids is not None:
        for i, cc in zip(ids.ravel(), c):
            if int(i) in ids_wanted:
                out[int(i)] = cc[0]
    return out, c, ids


def fit(centres):
    ids = sorted(centres)
    W = np.array([world(i) for i in ids], np.float64)
    P = np.array([centres[i].mean(0) for i in ids], np.float64)
    H, _ = cv2.findHomography(W, P, 0)                     # world (cm) -> image (px)
    Hi = np.linalg.inv(H)
    back = cv2.perspectiveTransform(P[:, None, :], Hi)[:, 0]
    err_mm = np.linalg.norm(back - W, axis=1) * 10.0
    return H, err_mm


def project(H, pts):
    return cv2.perspectiveTransform(np.array(pts, np.float64)[:, None, :], H)[:, 0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True)
    ap.add_argument('--calib', default=None, help='camera_calibration_v2.py .npz; without it the raw image is used')
    ap.add_argument('--out', required=True)
    ap.add_argument('--rows', type=int, default=7)
    ap.add_argument('--width', type=int, default=1920, help='output width (height keeps the aspect ratio)')
    ap.add_argument('--no-video', action='store_true', help='only print the residual statistics')
    a = ap.parse_args()

    ids_wanted = set(range(4, 4 + 2 * a.rows))
    cap = cv2.VideoCapture(a.video)
    w, h = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(5)
    maps = None
    if a.calib:
        z = np.load(a.calib)
        K, d = z['camera_matrix'], z['dist_coeffs']
        if tuple(z['image_size']) != (w, h):
            raise SystemExit('calibration is for %s but the video is %dx%d' % (tuple(z['image_size']), w, h))
        maps = cv2.initUndistortRectifyMap(K, d, None, K, (w, h), cv2.CV_16SC2)
    det = aruco.ArucoDetector(aruco.getPredefinedDictionary(aruco.DICT_6X6_250), aruco.DetectorParameters())
    ow = a.width
    oh = int(round(h * ow / w))
    writer = None
    if not a.no_video:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        writer = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (ow, oh + BAR))

    ymax = (a.rows - 1) * ROW_PITCH
    errs, miss, n = [], 0, 0
    th = max(2, w // 1200)
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        n += 1
        img = cv2.remap(fr, maps[0], maps[1], cv2.INTER_LINEAR) if maps else fr
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cen, corners, ids = tag_centres(det, gray, ids_wanted)
        if len(cen) < 4:
            miss += 1
            continue
        H, e = fit(cen)
        errs.append(e)
        if writer is None:
            continue
        # world grid: 10 cm lines over the tag area, dim extension 30 cm beyond it
        ext = 30.0
        for xx in np.arange(-ext, 80 + ext + 1, 10.0):
            inside = 0 <= xx <= 80
            p = project(H, [(xx, -ext), (xx, ymax + ext)]).astype(int)
            cv2.line(img, tuple(p[0]), tuple(p[1]), (255, 200, 0) if inside else (120, 100, 40), th if inside else max(1, th // 2), cv2.LINE_AA)
        for yy in np.arange(-ext, ymax + ext + 1, 10.0):
            inside = 0 <= yy <= ymax
            on_row = abs(yy % ROW_PITCH) < 1e-6
            p = project(H, [(-ext, yy), (80 + ext, yy)]).astype(int)
            col = (0, 140, 255) if (inside and on_row) else ((255, 200, 0) if inside else (120, 100, 40))
            cv2.line(img, tuple(p[0]), tuple(p[1]), col, th * (2 if (inside and on_row) else 1) if inside else max(1, th // 2), cv2.LINE_AA)
        for r in range(a.rows):
            q = project(H, [(-ext, r * ROW_PITCH)])[0].astype(int)
            cv2.putText(img, 'y=%d' % (r * ROW_PITCH), (int(q[0]) - 20, int(q[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, w / 2200, (0, 140, 255), th, cv2.LINE_AA)
        if ids is not None:
            aruco.drawDetectedMarkers(img, corners, ids, (0, 255, 0))
        for i, cc in cen.items():
            c0 = tuple(cc.mean(0).astype(int))
            cv2.circle(img, c0, th * 3, (0, 0, 255), -1, cv2.LINE_AA)
        txt = ['%s | frame %d  t=%.2fs' % ('undistorted (calib v2)' if maps else 'raw image', n - 1, (n - 1) / fps),
               '%d/%d tags | homography residual on tag centres: mean %.1f mm, max %.1f mm' % (len(cen), len(ids_wanted), e.mean(), e.max()),
               'grid: 10 cm lines; orange = tag rows; dim = 30 cm beyond the tags (extrapolated)']
        small = cv2.resize(img, (ow, oh), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((oh + BAR, ow, 3), np.uint8)             # text goes on a black bar above the picture
        canvas[BAR:] = small
        for k, t in enumerate(txt):
            cv2.putText(canvas, t, (24, 34 + k * 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(canvas)
        if n == 150:
            cv2.imwrite(os.path.splitext(a.out)[0] + '_still.jpg', canvas)
    cap.release()
    if writer is not None:
        writer.release()
    E = np.concatenate(errs) if errs else np.array([np.nan])
    print('%s: %d frames, %d without enough tags' % ('undistorted' if maps else 'raw', n, miss))
    print('  homography residual over all tags and frames: mean %.2f mm  RMS %.2f mm  max %.2f mm' %
          (E.mean(), np.sqrt((E ** 2).mean()), E.max()))
    per = np.array([e for e in errs])
    if len(per):
        mean_tag = per.mean(0)
        print('  per-tag mean residual (mm), IDs 4..: ' + ' '.join('%.1f' % v for v in mean_tag))
    if writer is not None:
        print('wrote', a.out)


if __name__ == '__main__':
    main()
