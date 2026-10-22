"""Lens calibration from a chessboard video, for the section-2.3.2 walking videos.

Successor to test_2/camera_calibration.py. What changed and why:
  * paths and board geometry come from the command line (one run per lens x mode)
  * corners are found with the sector-based detector (findChessboardCornersSB), which
    still finds the board where the classic detector gives up
  * frames where the board is moving are dropped (the A7R II is a rolling-shutter
    camera, so a moving board is a bent board), as are near-duplicate poses
  * a share of the good frames is held out; the calibration never sees them and their
    reprojection error is the honest accuracy figure
  * the .npz stores image size, RMS, hold-out RMS and the setup, so a 4K file cannot be
    mistaken for a 1080p one
  * a coverage picture shows which parts of the frame the board actually visited

Usage (one video = one lens, one recording mode, one focus setting):
    python camera_calibration_v2.py --video D:\\THESIS\\Camera-Calibration\\20mm_FF.MP4 \\
        --out output/params/calib_20mm_FF.npz --square-mm 55

Needs numpy + opencv-python + matplotlib.
"""
import argparse
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TERM = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True)
    ap.add_argument('--out', default=None, help='.npz to write (default: output/params/<video name>.npz)')
    ap.add_argument('--board', default='9x6', help='INNER corners, columns x rows (10x7 squares = 9x6)')
    ap.add_argument('--square-mm', type=float, default=31.25, help='printed square size; only sets the unit of the extrinsics')
    ap.add_argument('--step', type=int, default=5, help='look at every Nth frame (25 fps video: 5 = 5 per second)')
    ap.add_argument('--still-px', type=float, default=1.0,
                    help='keep a frame only if its corners moved less than this (mean px) against both neighbouring samples')
    ap.add_argument('--min-move-px', type=float, default=15.0,
                    help='skip a frame whose corners are within this mean distance of one already kept (near-duplicate pose)')
    ap.add_argument('--holdout', type=float, default=0.25, help='share of kept frames held out for validation')
    ap.add_argument('--fix-k3', action='store_true', help='freeze k3 at 0 (use when the frame edges are poorly covered)')
    ap.add_argument('--max-frames', type=int, default=80, help='stop collecting after this many kept frames')
    return ap.parse_args()


def find_corners(gray, board):
    ok, c = cv2.findChessboardCornersSB(gray, board, cv2.CALIB_CB_ACCURACY | cv2.CALIB_CB_NORMALIZE_IMAGE)
    return c[:, 0, :].astype(np.float32) if ok else None


def collect(video, board, step, still_px, min_move_px, max_frames):
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        sys.exit('cannot open ' + video)
    w, h = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(5)
    n_total = int(cap.get(7))
    samples = []                      # (frame_index, corners or None)
    idx = 0
    t0 = time.time()
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if idx % step == 0:
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            samples.append((idx, find_corners(g, board)))
        idx += 1
    cap.release()
    n_det = sum(c is not None for _, c in samples)
    print('%s  %dx%d  %.2f fps  %d frames  | looked at %d, board found in %d  (%.0f s)'
          % (os.path.basename(video), w, h, fps, n_total, len(samples), n_det, time.time() - t0))

    def shift(a, b):
        return float(np.linalg.norm(a - b, axis=1).mean())

    kept = []
    n_moving = n_dupe = 0
    for i, (fi, c) in enumerate(samples):
        if c is None:
            continue
        nbrs = [samples[j][1] for j in (i - 1, i + 1) if 0 <= j < len(samples) and samples[j][1] is not None]
        if not nbrs or max(shift(c, n) for n in nbrs) > still_px:
            n_moving += 1
            continue
        if any(shift(c, k[1]) < min_move_px for k in kept):
            n_dupe += 1
            continue
        kept.append((fi, c))
        if len(kept) >= max_frames:
            break
    print('kept %d poses  (dropped: %d moving, %d near-duplicate, %d without board)'
          % (len(kept), n_moving, n_dupe, len(samples) - n_det))
    return (w, h), fps, kept


def reproject_rms(obj, img, K, dist, rvec, tvec):
    p, _ = cv2.projectPoints(obj, rvec, tvec, K, dist)
    return float(np.sqrt(np.mean(np.sum((p[:, 0, :] - img) ** 2, axis=1))))


def coverage(size, kept, board, out_png):
    w, h = size
    pts = np.concatenate([c for _, c in kept])
    gx, gy = 4, 3
    H, _, _ = np.histogram2d(pts[:, 0], pts[:, 1], bins=[gx, gy], range=[[0, w], [0, h]])
    covered = (H > 0).sum()
    print('coverage: %d of %d regions (%dx%d grid) contain board corners' % (covered, gx * gy, gx, gy))
    print('  region counts (rows top->bottom):')
    for r in range(gy):
        print('   ', ' '.join('%5d' % H[c, r] for c in range(gx)))
    print('  corners reached x %.0f-%.0f of %d, y %.0f-%.0f of %d'
          % (pts[:, 0].min(), pts[:, 0].max(), w, pts[:, 1].min(), pts[:, 1].max(), h))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 7 * h / w))
        ax.scatter(pts[:, 0], pts[:, 1], s=1.5, c='#2a78d6')
        ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.set_aspect('equal')
        for gxx in np.linspace(0, w, gx + 1)[1:-1]:
            ax.axvline(gxx, color='0.8', lw=0.6)
        for gyy in np.linspace(0, h, gy + 1)[1:-1]:
            ax.axhline(gyy, color='0.8', lw=0.6)
        ax.set_title('board corners over %d poses' % len(kept), fontsize=9)
        fig.tight_layout(); fig.savefig(out_png, dpi=110); plt.close(fig)
        print('coverage picture:', out_png)
    except Exception as e:                      # picture is a convenience, never fatal
        print('no coverage picture (%s)' % e)
    return covered / float(gx * gy)


def main():
    a = parse_args()
    cols, rows = (int(x) for x in a.board.lower().split('x'))
    board = (cols, rows)
    out = a.out or os.path.join(HERE, 'output', 'params', os.path.splitext(os.path.basename(a.video))[0] + '.npz')
    os.makedirs(os.path.dirname(out), exist_ok=True)

    size, fps, kept = collect(a.video, board, a.step, a.still_px, a.min_move_px, a.max_frames)
    if len(kept) < 12:
        sys.exit('only %d usable poses - need 12+ (40-60 is the target). Move the board more, hold it still ~1 s per pose.' % len(kept))

    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= a.square_mm

    cover = coverage(size, kept, board, os.path.splitext(out)[0] + '_coverage.png')

    # deterministic hold-out: every k-th pose
    k = max(2, int(round(1.0 / a.holdout)))
    test_i = set(range(0, len(kept), k))
    train = [kept[i][1] for i in range(len(kept)) if i not in test_i]
    test = [kept[i][1] for i in range(len(kept)) if i in test_i]
    flags = cv2.CALIB_FIX_K3 if a.fix_k3 else 0

    def calibrate(img_list):
        rms, K, d, rv, tv = cv2.calibrateCamera([objp] * len(img_list), img_list, size, None, None, flags=flags)
        return rms, K, d, rv, tv

    rms_tr, K, d, _, _ = calibrate(train)
    errs = []
    for c in test:
        ok, rv, tv = cv2.solvePnP(objp, c, K, d, flags=cv2.SOLVEPNP_ITERATIVE)
        errs.append(reproject_rms(objp, c, K, d, rv, tv))
    rms_ho = float(np.mean(errs))

    rms_all, K, d, rv, tv = calibrate([c for _, c in kept])
    per = [reproject_rms(objp, kept[i][1], K, d, rv[i], tv[i]) for i in range(len(kept))]
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    hfov = np.degrees(2 * np.arctan(size[0] / (2 * fx)))
    vfov = np.degrees(2 * np.arctan(size[1] / (2 * fy)))

    print('\n=== result (%s) ===' % os.path.basename(a.video))
    print('poses used: %d  (train %d / hold-out %d)' % (len(kept), len(train), len(test)))
    print('RMS reprojection  all %.3f px | train %.3f px | HOLD-OUT %.3f px' % (rms_all, rms_tr, rms_ho))
    print('worst single pose %.3f px' % max(per))
    print('fx %.1f  fy %.1f  cx %.1f (centre %.1f)  cy %.1f (centre %.1f)' % (fx, fy, cx, size[0] / 2, cy, size[1] / 2))
    print('field of view  H %.1f deg  V %.1f deg' % (hfov, vfov))
    print('distortion k1 k2 p1 p2 k3 =', ' '.join('%.5f' % v for v in d.ravel()))

    warn = []
    if rms_ho > 0.5:
        warn.append('hold-out error above 0.5 px')
    if rms_ho > 1.5 * rms_tr + 0.05:
        warn.append('hold-out much worse than train: overfitting - more poses, or --fix-k3')
    if cover < 0.75:
        warn.append('board visited only %.0f%% of the frame regions - the edges are unconstrained' % (100 * cover))
    if abs(cx - size[0] / 2) > 0.05 * size[0] or abs(cy - size[1] / 2) > 0.05 * size[1]:
        warn.append('principal point far from the image centre')
    dd = d.ravel()
    if abs(dd[0]) > 0.6 or abs(dd[1]) > 1.5 or (len(dd) > 4 and abs(dd[4]) > 2.0):
        warn.append('distortion coefficients look implausible for a rectilinear prime lens - not constrained by the data')
    for wmsg in warn:
        print('WARNING:', wmsg)
    print('verdict:', 'OK' if not warn else 'USE WITH CARE / REDO')

    np.savez(out, camera_matrix=K, dist_coeffs=d, image_size=np.array(size), rms=rms_all, holdout_rms=rms_ho,
             n_poses=len(kept), board=np.array(board), square_mm=a.square_mm, fps=fps,
             source=os.path.basename(a.video), fix_k3=bool(a.fix_k3), created=time.strftime('%Y-%m-%d %H:%M:%S'))
    print('saved', out)


if __name__ == '__main__':
    main()
