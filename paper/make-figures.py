"""Draw the manuscript figures into figures/export/fig1..5.jpg.

Every figure is 7.5 cm wide (one journal column), English-labelled, and reads in
black and white.  Nothing here is hand-placed data: the schematics are drawn from
the geometry constants in the control code, and the plots come straight from the
measurement files.

    fig1  test-rig schematics (single-leg vision rig; walking runway)  - drawn
    fig2  five-bar linkage at the home pose                            - from L_AC, L_CE, spacing
    fig3  trot phasing and the Bezier foot path                        - from walk_test.py constants
    fig4  measured foot circles, compensation off vs on                - from the circle clips
    fig5  walking paths of the four conditions                         - from walk_test/*_pose.csv

    python make-figures.py            # all
    python make-figures.py fig2 fig3  # some

fig4 needs the tracked points of four clips; pass --tracks <npz> if they are not
in the default location (see FIG4_TRACKS below).
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.join(HERE, 'figures', 'export')
COL_CM = 7.5
DPI = 300
WALK_DIR = r'D:\THESIS\walk_test'
FIG4_TRACKS = os.path.join(HERE, 'figures', 'src', 'fig4_tracks.npz')

# linkage geometry, identical to python/paper_testing/test_3/walk_test.py
L_AC, L_CE, SPACING = 105.0, 145.0, 85.0
HOME = (0.0, -220.0)
# gait, identical to walk_test.py mode 7
STEPS, STANCE_RATIO, LIFT, STEP = 30, 0.75, 40.0, 25.0

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.linewidth': 0.6,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    'axes.labelsize': 8, 'lines.linewidth': 1.0,
})


def new_fig(height_cm):
    return plt.figure(figsize=(COL_CM / 2.54, height_cm / 2.54))


def save(fig, name):
    os.makedirs(EXPORT, exist_ok=True)
    out = os.path.join(EXPORT, name + '.jpg')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', pad_inches=0.03,
                facecolor='white')
    plt.close(fig)
    print('%-5s -> %s' % (name, out))


# ---------------------------------------------------------------- fig1 ----
def fig1():
    """Two schematics: (a) the single-leg vision rig, (b) the walking runway."""
    fig = new_fig(11.0)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.15], hspace=0.28)

    # (a) side view of the leg rig: camera above, leg hanging from the stand
    ax = fig.add_subplot(gs[0]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-1.6, 2.1); ax.set_ylim(-2.3, 1.55)
    # stand + leg
    ax.add_patch(Rectangle((-1.1, -2.2), 2.2, 0.12, fc='0.3', ec='none'))
    ax.add_patch(Rectangle((-1.05, -2.1), 0.1, 2.1, fc='0.3', ec='none'))
    ax.add_patch(Rectangle((-1.05, -0.05), 0.75, 0.1, fc='0.3', ec='none'))
    bx, by = -0.3, 0.0                                   # motor block
    ax.add_patch(Rectangle((bx - 0.35, by - 0.18), 0.7, 0.3, fc='0.75', ec='k', lw=0.6))
    for dx, lab in ((-0.22, 'id0'), (0.22, 'id1')):
        ax.add_patch(Rectangle((bx + dx - 0.07, by - 0.07), 0.14, 0.14, fc='w', ec='k', lw=0.6))
        ax.text(bx + dx, by + 0.2, lab, ha='center', fontsize=6)
    # links to the foot
    cx, cy = bx - 0.45, by - 0.65
    dx_, dy_ = bx + 0.45, by - 0.65
    ex, ey = bx, by - 1.45
    for (x0, y0, x1, y1) in ((bx - 0.22, by, cx, cy), (bx + 0.22, by, dx_, dy_),
                             (cx, cy, ex, ey), (dx_, dy_, ex, ey)):
        ax.plot([x0, x1], [y0, y1], color='k', lw=1.4)
    for x, y in ((cx, cy), (dx_, dy_), (bx - 0.22, by), (bx + 0.22, by)):
        ax.add_patch(Circle((x, y), 0.05, fc='w', ec='k', lw=0.6))
    ax.add_patch(Rectangle((ex - 0.08, ey - 0.08), 0.16, 0.16, fc='w', ec='k', lw=0.6))
    ax.text(ex + 0.14, ey - 0.02, 'id4 (foot)', fontsize=6, va='center')
    # payload hanging from the foot
    ax.plot([ex, ex], [ey - 0.08, ey - 0.42], color='k', lw=0.6)
    ax.add_patch(Rectangle((ex - 0.16, ey - 0.62), 0.32, 0.2, fc='0.55', ec='k', lw=0.6))
    ax.text(ex + 0.24, ey - 0.5, 'payload 0-3 kg', fontsize=6, va='center')
    # camera above, looking down
    ax.add_patch(FancyBboxPatch((bx - 0.22, 1.1), 0.44, 0.25, boxstyle='round,pad=0.02',
                                fc='0.2', ec='none'))
    ax.add_patch(Rectangle((bx - 0.08, 0.98), 0.16, 0.12, fc='0.2', ec='none'))
    ax.plot([bx - 0.08, bx - 1.0], [0.98, -1.75], color='0.5', lw=0.5, ls='--')
    ax.plot([bx + 0.08, bx + 1.0], [0.98, -1.75], color='0.5', lw=0.5, ls='--')
    ax.annotate('', xy=(1.25, 0.98), xytext=(1.25, -1.6),
                arrowprops=dict(arrowstyle='<->', lw=0.6))
    ax.text(1.32, -0.3, '1.2 m', fontsize=6, rotation=90, va='center')
    ax.text(bx + 0.3, 1.22, 'camera, 25 mm lens\n60 fps', fontsize=6, va='center')
    ax.text(-1.55, 1.4, '(a)', fontsize=8, fontweight='bold')

    # (b) top view of the runway
    ax = fig.add_subplot(gs[1]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-25, 132); ax.set_ylim(-42, 142)
    ax.add_patch(Rectangle((0, 0), 80, 120, fc='none', ec='0.5', lw=0.6, ls=':'))
    for y in (0, 40, 80, 120):                              # 4 rows of floor tags
        for x in (0, 80):
            ax.add_patch(Rectangle((x - 4, y - 4), 8, 8, fc='w', ec='k', lw=0.6))
    ax.text(40, 127, 'floor tags, grid 80 x 120 cm', ha='center', fontsize=6)
    ax.annotate('', xy=(0, -12), xytext=(80, -12), arrowprops=dict(arrowstyle='<->', lw=0.6))
    ax.text(40, -19, '80 cm', ha='center', fontsize=6)
    ax.annotate('', xy=(120, 0), xytext=(120, 120), arrowprops=dict(arrowstyle='<->', lw=0.6))
    ax.text(125, 60, '120 cm', rotation=90, va='center', fontsize=6)
    # robot body with 4 back tags, 19.9 x 46.6 cm
    rx, ry = 40, 30
    ax.add_patch(FancyBboxPatch((rx - 12, ry - 26), 24, 52, boxstyle='round,pad=1',
                                fc='0.88', ec='k', lw=0.6))
    for ddx, ddy in ((-9.95, -23.3), (9.95, -23.3), (-9.95, 23.3), (9.95, 23.3)):
        ax.add_patch(Rectangle((rx + ddx - 3, ry + ddy - 3), 6, 6, fc='w', ec='k', lw=0.6))
    ax.annotate('', xy=(rx, ry + 36), xytext=(rx, ry + 26),
                arrowprops=dict(arrowstyle='-|>', lw=0.8))
    ax.text(rx + 3, ry + 32, 'walk', fontsize=6)
    ax.text(rx + 46, ry + 22, 'robot tags\n19.9 x 46.6 cm\n31 cm high', fontsize=6, va='center')
    # camera behind, looking along +Y
    ax.add_patch(Rectangle((rx - 5, -36), 10, 6, fc='0.2', ec='none'))
    ax.plot([rx - 5, -20], [-30, 125], color='0.5', lw=0.5, ls='--')
    ax.plot([rx + 5, 100], [-30, 125], color='0.5', lw=0.5, ls='--')
    ax.text(rx + 7, -33, 'camera, 1.8 m high', fontsize=6, va='center')
    ax.text(-24, 136, '(b)', fontsize=8, fontweight='bold')
    save(fig, 'fig1')


# ---------------------------------------------------------------- fig2 ----
def _elbow(p_motor, p_foot, outward):
    """Circle-circle intersection, picking the elbow on the given side."""
    p_motor, p_foot = np.asarray(p_motor, float), np.asarray(p_foot, float)
    d = np.linalg.norm(p_foot - p_motor)
    a = (L_AC ** 2 - L_CE ** 2 + d ** 2) / (2 * d)
    h = np.sqrt(max(L_AC ** 2 - a ** 2, 0.0))
    mid = p_motor + a * (p_foot - p_motor) / d
    perp = np.array([-(p_foot - p_motor)[1], (p_foot - p_motor)[0]]) / d
    c1, c2 = mid + h * perp, mid - h * perp
    return c1 if (c1[0] < mid[0]) == outward else c2


def fig2():
    pa, pb = np.array([-SPACING / 2, 0.0]), np.array([SPACING / 2, 0.0])
    pe = np.array(HOME)
    c = _elbow(pa, pe, outward=True)
    d = _elbow(pb, pe, outward=False)
    fig = new_fig(6.5); ax = fig.add_subplot(111); ax.set_aspect('equal')
    for p, q in ((pa, c), (c, pe), (pb, d), (d, pe)):
        ax.plot([p[0], q[0]], [p[1], q[1]], color='k', lw=1.6)
    ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color='0.4', lw=1.0, ls='--')
    for p in (pa, pb, c, d):
        ax.add_patch(Circle(p, 4, fc='w', ec='k', lw=0.8, zorder=5))
    ax.add_patch(Circle(pe, 4, fc='k', ec='k', zorder=5))
    lab = dict(fontsize=8)
    ax.text(pa[0] - 6, pa[1] + 9, r'$P_A$', ha='right', **lab)
    ax.text(pb[0] + 6, pb[1] + 9, r'$P_B$', ha='left', **lab)
    ax.text(c[0] - 8, c[1], r'$C$', ha='right', va='center', **lab)
    ax.text(d[0] + 8, d[1], r'$D$', ha='left', va='center', **lab)
    ax.text(pe[0], pe[1] - 14, r'$P_E$ (foot)', ha='center', **lab)
    ax.text((pa[0] + c[0]) / 2 - 14, (pa[1] + c[1]) / 2, r'$L_{AC}$', ha='right', fontsize=7)
    ax.text((pb[0] + d[0]) / 2 + 14, (pb[1] + d[1]) / 2, r'$L_{BD}$', ha='left', fontsize=7)
    ax.text((c[0] + pe[0]) / 2 - 12, (c[1] + pe[1]) / 2, r'$L_{CE}$', ha='right', fontsize=7)
    ax.text((d[0] + pe[0]) / 2 + 12, (d[1] + pe[1]) / 2, r'$L_{DE}$', ha='left', fontsize=7)
    ax.text(0, 8, '85 mm', ha='center', fontsize=7)
    # joint angles measured from +x at each motor
    for p, q, name, sgn in ((pa, c, r'$\theta_A$', 1), (pb, d, r'$\theta_B$', -1)):
        ang = np.degrees(np.arctan2(q[1] - p[1], q[0] - p[0]))
        th = np.linspace(0, ang, 30) if sgn > 0 else np.linspace(ang, 0, 30)
        th = np.radians(np.linspace(min(0, ang), max(0, ang), 30))
        ax.plot(p[0] + 22 * np.cos(th), p[1] + 22 * np.sin(th), color='0.3', lw=0.6)
        ax.text(p[0] + sgn * 30, p[1] - 22, name, ha='center', fontsize=8)
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
    ax.set_xlim(-150, 150); ax.set_ylim(-250, 30)
    ax.grid(True, lw=0.3, alpha=0.5)
    ax.text(-145, -243, 'home pose (0, -220) mm', fontsize=6)
    save(fig, 'fig2')


# ---------------------------------------------------------------- fig3 ----
def _bezier(t, p0, p1, p2, p3):
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def foot_path():
    """Same construction as walk_test.generate_bezier_trajectory."""
    n_st = int(STEPS * STANCE_RATIO); n_sw = STEPS - n_st
    sx, ex, hy = STEP, -STEP, HOME[1]
    stance = [(sx + (ex - sx) * i / (n_st - 1), hy) for i in range(n_st)]
    p0, p3 = np.array([ex, hy]), np.array([sx, hy])
    p1 = np.array([ex + (sx - ex) * 0.4 * 0.5, hy + LIFT * 1.25])
    p2 = np.array([ex + (sx - ex) * (1 - 0.4 * 0.5), hy + LIFT * 1.25])
    swing = [tuple(_bezier(i / (n_sw - 1), p0, p1, p2, p3)) for i in range(n_sw)]
    return np.array(stance), np.array(swing)


def fig3():
    fig = new_fig(6.5)
    gs = fig.add_gridspec(2, 1, height_ratios=[0.8, 1.0], hspace=0.65)
    # (a) trot phasing over two cycles: black = stance
    ax = fig.add_subplot(gs[0])
    legs = [('FR', 0.0), ('FL', 0.5), ('RR', 0.5), ('RL', 0.0)]
    for i, (name, off) in enumerate(legs):
        y = len(legs) - 1 - i
        for cyc in range(2):
            s0 = cyc + off
            ax.add_patch(Rectangle((s0, y - 0.3), STANCE_RATIO, 0.6, fc='k', ec='none'))
            ax.add_patch(Rectangle((s0 + STANCE_RATIO, y - 0.3), 1 - STANCE_RATIO, 0.6,
                                   fc='w', ec='k', lw=0.5))
            if off:  # wrap the part that falls before 0
                ax.add_patch(Rectangle((s0 - 1, y - 0.3), STANCE_RATIO, 0.6, fc='k', ec='none'))
                ax.add_patch(Rectangle((s0 - 1 + STANCE_RATIO, y - 0.3), 1 - STANCE_RATIO, 0.6,
                                       fc='w', ec='k', lw=0.5))
        ax.text(-0.05, y, name, ha='right', va='center', fontsize=7)
    ax.set_xlim(0, 2); ax.set_ylim(-0.6, len(legs) + 0.7)
    ax.set_yticks([]); ax.set_xticks([0, 0.5, 1, 1.5, 2])
    ax.set_xlabel('gait cycle', labelpad=1)
    ax.add_patch(Rectangle((0.02, 4.0), 0.12, 0.3, fc='k', clip_on=False))
    ax.text(0.18, 4.15, 'stance, 75% of cycle', va='center', fontsize=6)
    ax.add_patch(Rectangle((1.25, 4.0), 0.12, 0.3, fc='w', ec='k', lw=0.5, clip_on=False))
    ax.text(1.41, 4.15, 'swing', va='center', fontsize=6)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.text(-0.3, 4.15, '(a)', fontsize=8, fontweight='bold')
    # (b) the foot path in the leg frame
    ax = fig.add_subplot(gs[1]); ax.set_aspect('equal')
    st, sw = foot_path()
    ax.plot(st[:, 0], st[:, 1], 'k-', lw=1.4)
    ax.plot(sw[:, 0], sw[:, 1], 'k--', lw=1.0)
    ax.text(0, HOME[1] + 4, 'stance', ha='center', fontsize=6)
    ax.text(0, HOME[1] + LIFT + 6, 'swing', ha='center', fontsize=6)
    ax.plot(st[:, 0], st[:, 1], 'k.', ms=3); ax.plot(sw[:, 0], sw[:, 1], 'k.', ms=3)
    ax.annotate('', xy=(-STEP, HOME[1] - 7), xytext=(STEP, HOME[1] - 7),
                arrowprops=dict(arrowstyle='-|>', lw=0.7, color='0.3'))
    ax.text(0, HOME[1] - 16, 'body moves this way', ha='center', fontsize=6, color='0.3')
    ax.text(STEP + 4, HOME[1] + LIFT / 2, '%.0f mm\nlift' % LIFT, fontsize=6, va='center', ha='left')
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
    ax.set_xlim(-45, 50); ax.set_ylim(HOME[1] - 24, HOME[1] + LIFT + 24)
    ax.grid(True, lw=0.3, alpha=0.5)
    ax.text(-56, HOME[1] + LIFT + 20, '(b)', fontsize=8, fontweight='bold')
    save(fig, 'fig3')


# ---------------------------------------------------------------- fig4 ----
def fig4(tracks=FIG4_TRACKS):
    if not os.path.exists(tracks):
        print('fig4: no tracks at', tracks, '- skipped'); return
    z = np.load(tracks)
    panels = [('no_load', 'No-load'), ('3kg', '3 kg payload')]
    fig = new_fig(5.0)
    axes = fig.subplots(1, 2, sharey=True)
    th = np.linspace(0, 2 * np.pi, 200)
    for ax, (load, title) in zip(axes, panels):
        ax.set_aspect('equal')
        ax.plot(30 * np.cos(th), -170 + 30 * np.sin(th), color='0.55', lw=0.8, ls='--',
                label='commanded')
        off = z[load + '__original']; on = z[load + '__model_poly4']
        ax.plot(off[:, 0], off[:, 1], '.', color='0.6', ms=1.2, label='compensation off')
        ax.plot(on[:, 0], on[:, 1], '.', color='k', ms=1.2, label='POLY4 on')
        ax.set_title(title, fontsize=8, pad=3)
        ax.set_xlabel('x (mm)'); ax.set_xlim(-48, 48); ax.set_ylim(-232, -128)
        ax.grid(True, lw=0.3, alpha=0.5)
    axes[0].set_ylabel('y (mm)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06),
               markerscale=5, handlelength=1.6)
    save(fig, 'fig4')


# ---------------------------------------------------------------- fig5 ----
def fig5():
    import csv
    runs = [('walk_pose.csv', 'No-load, off', '0.6', '--'),
            ('walk_ml_pose.csv', 'No-load, on', 'k', '-'),
            ('walk_3kg_pose.csv', '3 kg, off', '0.6', ':'),
            ('walk_ml_3kg_pose.csv', '3 kg, on', 'k', '-.')]
    fig = new_fig(6.0); ax = fig.add_subplot(111)
    for fn, lab, col, ls in runs:
        path = os.path.join(WALK_DIR, fn)
        if not os.path.exists(path):
            print('fig5: missing', path); continue
        rows = [r for r in csv.DictReader(open(path, encoding='utf-8')) if r['is_held'] == '0']
        m = float(rows[0]['scale_est'])
        x = np.array([float(r['x_cm']) for r in rows]) / m
        y = np.array([float(r['y_cm']) for r in rows]) / m
        ax.plot(x - x[0], y - y[0], color=col, ls=ls, lw=1.2, label=lab)
    ax.axvline(0, color='0.75', lw=0.6)
    ax.set_xlabel('lateral deviation from start (cm), + = right')
    ax.set_ylabel('distance along the runway (cm)')
    ax.set_xlim(-60, 25); ax.set_ylim(-5, 175)
    ax.legend(loc='upper left', frameon=False)
    ax.grid(True, lw=0.3, alpha=0.5)
    save(fig, 'fig5')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--tracks' in sys.argv:
        FIG4_TRACKS = sys.argv[sys.argv.index('--tracks') + 1]
    todo = args or ['fig1', 'fig2', 'fig3', 'fig4', 'fig5']
    for name in todo:
        globals()[name]() if name != 'fig4' else fig4(FIG4_TRACKS)
