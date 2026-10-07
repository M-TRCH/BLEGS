"""Render every tables/src/*.md pipe table to tables/export/*.jpg.

The journal wants each table as a separate .jpg alongside the manuscript, and the
manuscript embeds the same .jpg (`![](tableN.jpg){width=7.5cm}`) so that a table
cannot drift out of sync with its picture.  Markdown stays the source of truth;
this script is the only thing that writes tables/export/.

    python render-tables.py            # all tables
    python render-tables.py table2     # just one

Inline math in the source (`$D$`, `$\\varphi_{end}$`) is passed through to
matplotlib mathtext, so it renders the same way it does in the manuscript.
Comments (`<!-- ... -->`) are for the author and are stripped.
"""
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# DejaVu Sans has no Thai glyphs, and table1 still carries Thai placeholders.
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Leelawadee UI',
                                          'Tahoma', 'Arial']

_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_DIR, 'tables', 'src')
EXPORT = os.path.join(_DIR, 'tables', 'export')

HEADER_BG = '#E8E8E8'
GRID = '#B4B4B4'
FONT_PT = 13
ROW_PT = 34            # row height in points
PAD_PT = 18            # horizontal padding per cell
CHAR_PT = 7.6          # approximate advance width per character at FONT_PT
BOLD_K = 1.10          # the header row is bold, so it runs wider


def parse(path):
    text = re.sub(r'<!--.*?-->', '', open(path, encoding='utf-8').read(), flags=re.S)
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
            continue                       # the |---|---| separator
        rows.append(cells)
    if not rows:
        raise ValueError('no pipe table found in %s' % path)
    width = max(len(r) for r in rows)
    return [r + [''] * (width - len(r)) for r in rows]


def _visual_len(cell):
    """Length as drawn: math markers and TeX braces take no width."""
    return len(re.sub(r'[${}\\]|_(?=\w)', '', cell))


def render(name):
    rows = parse(os.path.join(SRC, name + '.md'))
    header, body = rows[0], rows[1:]
    ncol = len(header)

    widths_pt = [
        max([_visual_len(header[c]) * BOLD_K]
            + [_visual_len(r[c]) for r in body]) * CHAR_PT + PAD_PT * 2
        for c in range(ncol)
    ]
    total_pt = sum(widths_pt)
    fig_w = total_pt / 72.0
    fig_h = (len(rows) * ROW_PT) / 72.0

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')
    tbl = ax.table(cellText=body, colLabels=header, loc='center',
                   cellLoc='center',
                   colWidths=[w / total_pt for w in widths_pt])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(FONT_PT)

    for (row, _col), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_linewidth(0.8)
        cell.set_height(1.0 / len(rows))
        if row == 0:
            cell.set_facecolor(HEADER_BG)
            cell.set_text_props(fontweight='bold')
        else:
            cell.set_facecolor('white')

    # A source file carrying the line `<!-- MOCK -->` holds placeholder numbers:
    # stamp the picture so it can never be mistaken for a measurement.
    src_text = open(os.path.join(SRC, name + '.md'), encoding='utf-8').read()
    if re.search(r'<!--\s*MOCK\s*-->', src_text):
        ax.text(0.5, 0.5, 'MOCK DATA', transform=ax.transAxes, ha='center',
                va='center', fontsize=44, fontweight='bold', color='#BE1E1E',
                alpha=0.28, rotation=22, zorder=10)

    out = os.path.join(EXPORT, name + '.jpg')
    os.makedirs(EXPORT, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches='tight', pad_inches=0.02,
                facecolor='white')
    plt.close(fig)
    print('%-10s %d x %d  ->  %s' % (name, len(rows) - 1, ncol, out))


def main():
    wanted = sys.argv[1:]
    if not wanted:
        wanted = sorted(os.path.splitext(f)[0] for f in os.listdir(SRC)
                        if f.endswith('.md'))
    for name in wanted:
        render(name)


if __name__ == '__main__':
    main()
