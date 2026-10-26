"""Print-ready ArUco (DICT_6X6_250) stickers for the section-2.3 vision setup.

Vector PDF at true size, A4 portrait, 6 stickers per page (2 x 3). IDs 0-3 are the robot's
back tags, 4-17 the runway grid (2 columns x 7 rows, 40 cm pitch; rows 4-7 are the
existing 2 x 4 grid, rows 8-... the proposed extension to 240 cm).

Each sticker = the marker (black border included) + a white quiet zone. The quiet zone is
part of the detector's requirement, so cut at the outer crop marks, NOT at the black border.
Small ticks on the middle of every side of the sticker mark the marker CENTRE lines: the
runway coordinates in apriltag_runway_tilt_check.py are marker centres.

    python make_aruco_stickers_pdf.py                       # IDs 0-17, 70 mm marker
    python make_aruco_stickers_pdf.py --marker-mm 90 --ids 0-3
PRINT AT 100 % ("actual size"); verify the 100 mm bar at the foot of each page.
"""
import argparse
import os

import cv2
import cv2.aruco as aruco
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PAGE_W, PAGE_H = 210.0, 297.0
RUNWAY_X = {0: 0.0, 1: 80.0}                          # left / right column (cm)


def parse_ids(txt):
    out = []
    for part in txt.split(','):
        if '-' in part:
            a, b = part.split('-')
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def describe(i):
    if i <= 3:
        pos = {0: (-9.95, -23.3), 1: (9.95, -23.3), 2: (-9.95, 23.3), 3: (9.95, 23.3)}[i]
        return 'ID %d  robot back tag (%.2f, %.2f) cm' % (i, pos[0], pos[1])
    row, col = (i - 4) // 2, (i - 4) % 2
    return 'ID %d  runway %s col, row %d  (x=%d, y=%d cm)' % (i, 'right' if col else 'left', row, RUNWAY_X[col], row * 40)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ids', default='0-17')
    ap.add_argument('--marker-mm', type=float, default=70.0, help='outer side of the black border')
    ap.add_argument('--margin-mm', type=float, default=8.0, help='white quiet zone around the marker')
    ap.add_argument('--out', default=None)
    ap.add_argument('--check-png', default=None, help='also write every page as <name>_pN.png (for a decode test)')
    a = ap.parse_args()

    ids = parse_ids(a.ids)
    m, q = a.marker_mm, a.margin_mm
    S = m + 2 * q                                     # sticker side
    gut, pm = 10.0, 8.0                               # gutter (holds the label), page margin
    cols = int((PAGE_W - 2 * pm + gut) // (S + gut))
    rows = int((PAGE_H - 2 * pm - 14 + gut) // (S + gut))         # 14 mm kept for the scale bar
    per = cols * rows
    if per < 1:
        raise SystemExit('sticker %.0f mm does not fit an A4 page' % S)
    ar = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    mod = m / 8.0                                     # 6 data + 2 border modules
    pages = [ids[k:k + per] for k in range(0, len(ids), per)]

    out = a.out or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
                                                'paper', 'field', 'aruco_stickers_id%d-%d_%gmm.pdf' % (ids[0], ids[-1], m)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(out) as pdf:
        for pi, page in enumerate(pages):
            fig = plt.figure(figsize=(PAGE_W / 25.4, PAGE_H / 25.4))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, PAGE_W); ax.set_ylim(PAGE_H, 0); ax.axis('off')
            x_start = (PAGE_W - (cols * S + (cols - 1) * gut)) / 2.0
            for k, mid in enumerate(page):
                r, c = divmod(k, cols)
                x0, y0 = x_start + c * (S + gut), pm + r * (S + gut)
                bits = aruco.generateImageMarker(ar, mid, 8, borderBits=1)        # 8 x 8, 255 = white
                for j in range(8):
                    for i in range(8):
                        if bits[j, i] == 0:
                            ax.add_patch(Rectangle((x0 + q + i * mod, y0 + q + j * mod), mod, mod,
                                                   facecolor='black', edgecolor='none', lw=0))
                # crop marks (outer corners of the sticker) and centre-line ticks
                for cx_, cy_ in [(x0, y0), (x0 + S, y0), (x0, y0 + S), (x0 + S, y0 + S)]:
                    dx = -1 if cx_ == x0 else 1
                    dy = -1 if cy_ == y0 else 1
                    ax.plot([cx_, cx_ + dx * 3], [cy_, cy_], color='0.4', lw=0.4)
                    ax.plot([cx_, cx_], [cy_, cy_ + dy * 3], color='0.4', lw=0.4)
                mx, my = x0 + S / 2, y0 + S / 2
                for (px, py, qx, qy) in [(mx, y0, mx, y0 + 2.2), (mx, y0 + S, mx, y0 + S - 2.2),
                                         (x0, my, x0 + 2.2, my), (x0 + S, my, x0 + S - 2.2, my)]:
                    ax.plot([px, qx], [py, qy], color='0.35', lw=0.5)
                ax.text(x0 + S / 2, y0 + S + 5.2, describe(mid), fontsize=6.3, ha='center', va='center', family='DejaVu Sans')
            by = PAGE_H - 12
            bx = (PAGE_W - 100) / 2
            ax.plot([bx, bx + 100], [by, by], color='black', lw=1.0, solid_capstyle='butt')
            for xx in (bx, bx + 100):
                ax.plot([xx, xx], [by - 1.8, by + 1.8], color='black', lw=0.8)
            ax.text(PAGE_W / 2, by + 5, 'ArUco DICT_6X6_250 | marker %g mm + %g mm white margin | PRINT AT 100%% - this bar must measure 100 mm | page %d/%d'
                    % (m, q, pi + 1, len(pages)), fontsize=6.3, ha='center', va='center', family='DejaVu Sans')
            if a.check_png:
                fig.savefig('%s_p%d.png' % (os.path.splitext(a.check_png)[0], pi + 1), dpi=300)
            pdf.savefig(fig)
            plt.close(fig)
    print('wrote', out)
    print('%d stickers, %d per page (%d x %d), %d page(s); sticker %.0f x %.0f mm, marker %g mm' %
          (len(ids), per, cols, rows, len(pages), S, S, m))


if __name__ == '__main__':
    main()
