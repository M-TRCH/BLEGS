"""Print-ready chessboard for lens calibration (camera_calibration_v2.py).

Vector PDF at true size: the page is the paper size, every square is exactly --square-mm.
Default: A3 landscape, 10 x 7 squares = 9 x 6 INNER corners (the --board 9x6 default of
camera_calibration_v2.py), 32 mm squares, at least one square of white border all round.

    python make_chessboard_pdf.py                      # A3, 32 mm
    python make_chessboard_pdf.py --square-mm 33 --out board.pdf

PRINT AT 100 % ("actual size", never "fit to page"), then check the 100 mm bar with a ruler.
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PAPER_MM = {'A4': (297.0, 210.0), 'A3': (420.0, 297.0), 'A2': (594.0, 420.0)}   # landscape


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--paper', choices=sorted(PAPER_MM), default='A3')
    ap.add_argument('--squares', default='10x7', help='squares across x down (inner corners = each minus 1)')
    ap.add_argument('--square-mm', type=float, default=32.0)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    W, H = PAPER_MM[a.paper]
    nx, ny = (int(v) for v in a.squares.lower().split('x'))
    s = a.square_mm
    bw, bh = nx * s, ny * s
    if bw + 2 * s > W + 1e-6 or bh + 2 * s > H + 1e-6:
        raise SystemExit('board %.0f x %.0f mm does not fit %s with a one-square border (largest square that fits: %.1f mm)'
                         % (bw, bh, a.paper, min(W / (nx + 2), H / (ny + 2))))
    x0, y0 = (W - bw) / 2.0, (H - bh) / 2.0

    fig = plt.figure(figsize=(W / 25.4, H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis('off')
    for j in range(ny):
        for i in range(nx):
            if (i + j) % 2 == 0:                   # black square in the top-left corner
                ax.add_patch(Rectangle((x0 + i * s, y0 + j * s), s, s, facecolor='black', edgecolor='none', lw=0))

    # scale check bar and label, outside the border zone of the board
    by = y0 + bh + s * 0.55
    ax.plot([x0, x0 + 100], [by, by], color='black', lw=1.2, solid_capstyle='butt')
    for xx in (x0, x0 + 100):
        ax.plot([xx, xx], [by - 2, by + 2], color='black', lw=1.0)
    ax.text(x0 + 104, by, '100 mm - measure this bar after printing',
            fontsize=8, va='center', ha='left', family='DejaVu Sans')
    ax.text(x0 + bw, by, '%s  %dx%d squares  %d x %d inner corners  %.2f mm  PRINT AT 100%%' %
            (a.paper, nx, ny, nx - 1, ny - 1, s), fontsize=8, va='center', ha='right', family='DejaVu Sans')

    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'paper', 'field',
                                'chessboard_%s_%dx%d_%gmm.pdf' % (a.paper, nx - 1, ny - 1, s))
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, format='pdf')
    print('wrote', out)
    print('page %.0f x %.0f mm | board %.0f x %.0f mm | border %.1f mm left/right, %.1f mm top/bottom' %
          (W, H, bw, bh, x0, y0))


if __name__ == '__main__':
    main()
