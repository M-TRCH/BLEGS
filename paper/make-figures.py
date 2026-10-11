"""Draw the manuscript figures into figures/export/fig1..5.jpg.

Every figure is 7.5 cm wide (one journal column), English-labelled, and reads in
black and white.  Nothing here is hand-placed data: the schematics are drawn from
the geometry constants in the control code, and the plots come straight from the
measurement files.

    fig1  test-rig schematics (single-leg vision rig; walking runway)  - drawn
    fig2  five-bar linkage at the home pose                            - from L_AC, L_CE, spacing
    fig3  trot phasing and the Bezier foot path                        - from walk_test.py mode 7
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
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Arc

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.join(HERE, 'figures', 'export')
COL_CM = 7.5
DPI = 300
WALK_DIR = r'D:\THESIS\walk_test'
FIG4_TRACKS = os.path.join(HERE, 'figures', 'src', 'fig4_tracks.npz')

# linkage geometry, identical to python/paper_testing/test_3/walk_test.py
L_AC, L_CE, SPACING = 105.0, 145.0, 85.0
HOME = (0.0, -220.0)
# gait of walk_test.py mode 7, the one the 2.3.2 runs used: TRAJECTORY_STEPS = 30 points
# per cycle at 50 Hz, SMOOTH_TROT_STANCE_RATIO = 0.75, GAIT_LIFT_HEIGHT = 40 (the Bezier
# control points sit at 1.25 x lift, so the apex is 0.75 x 1.25 x 40 = 37.5 mm), and the
# half-amplitude actually walked is min(NAV_V_MAX x cycle time, GAIT_STEP_FORWARD)
# = min(70 mm/s x 0.6 s, 35 mm) = 35 mm
STEPS, STANCE_RATIO, LIFT = 30, 0.75, 40.0
STEP = min(70.0 * STEPS / 50.0, 35.0)
# single-leg rig (2.2.1): the vision reference tags id0/id1 sit on the two motor axes
# (REF_WORLD in test_2/vision_based_trajectory_eval.py), id4 rides on the foot, the camera
# looks at the leg plane from 1.2 m with its axis normal to that plane
CAMERA_M, LENS_MM, FPS = 1.2, 25, 60
# runway (2.3.1): 8 floor tags in 4 rows on an 80 x 120 cm grid, 4 back tags on a
# 19.9 x 46.6 cm frame 31 cm above the floor, camera behind the robot 1.8 m high
GRID_W, GRID_L, TAG_FRAME = 80.0, 120.0, (19.9, 46.6)

# MATLAB look: Helvetica/Arial everywhere (maths included), a box of thin black axes
# with the ticks pointing inwards on all four sides, no grid, black on white.
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 8,
    'mathtext.fontset': 'custom', 'mathtext.rm': 'Arial', 'mathtext.it': 'Arial:italic',
    'mathtext.bf': 'Arial:bold',
    'axes.linewidth': 0.5, 'axes.edgecolor': 'black', 'axes.labelcolor': 'black',
    'xtick.direction': 'in', 'ytick.direction': 'in', 'xtick.top': True, 'ytick.right': True,
    'xtick.major.width': 0.5, 'ytick.major.width': 0.5, 'xtick.major.size': 3, 'ytick.major.size': 3,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7, 'axes.labelsize': 8,
    'axes.grid': False, 'lines.linewidth': 1.0, 'legend.frameon': False,
})


def new_fig(height_cm):
    return plt.figure(figsize=(COL_CM / 2.54, height_cm / 2.54))


def save(fig, name, svg=False):
    """Always the .jpg the manuscript and the journal use; with svg=True also an
    editable .svg (text kept as text) next to it."""
    os.makedirs(EXPORT, exist_ok=True)
    out = os.path.join(EXPORT, name + '.jpg')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', pad_inches=0.03,
                facecolor='white')
    if svg:
        with plt.rc_context({'svg.fonttype': 'none'}):
            fig.savefig(os.path.join(EXPORT, name + '.svg'), bbox_inches='tight',
                        pad_inches=0.03, facecolor='white')
    plt.close(fig)
    print('%-5s -> %s%s' % (name, out, ' (+ .svg)' if svg else ''))


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


def _linkage_points():
    pa, pb, pe = np.array([-SPACING / 2, 0.0]), np.array([SPACING / 2, 0.0]), np.array(HOME)
    return pa, pb, _elbow(pa, pe, outward=True), _elbow(pb, pe, outward=False), pe


# ---------------------------------------------------------------- fig1 ----
def fig1():
    """(a) the single-leg rig as the camera sees it, plus a top view of where the
    camera stands; (b) the walking runway from above, robot walking to the right."""
    INK, MID, LIGHT = 'black', '#808080', '#e6e6e6'
    fig = new_fig(10.0)
    gs = fig.add_gridspec(2, 2, width_ratios=[0.56, 0.44], height_ratios=[1.12, 1.0],
                          hspace=0.12, wspace=0.0, left=0.01, right=0.99, top=0.99, bottom=0.01)
    lab = dict(fontsize=7, color=INK)
    onl = dict(ha='center', va='center_baseline', bbox=dict(fc='white', ec='none', pad=1.0))   # text sitting on a line

    def tagbox(ax, x, y, s, z=6):
        ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, fc='white', ec=INK, lw=0.5, zorder=z))

    def camera(ax, x_lens, y, w):
        """One camera glyph for both panels: body w x 0.78w with the lens tip at (x_lens, y), looking +x."""
        ax.add_patch(Rectangle((x_lens - 0.3 * w - w, y - 0.39 * w), w, 0.78 * w, fc=LIGHT, ec=INK, lw=0.5))
        ax.add_patch(Rectangle((x_lens - 0.3 * w, y - 0.2 * w), 0.3 * w, 0.4 * w, fc=LIGHT, ec=INK, lw=0.5))

    # (a) left: the leg as the camera sees it, in real mm; the payload hangs from the foot
    ax = fig.add_subplot(gs[0, 0]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-125, 125); ax.set_ylim(-308, 52)
    pa, pb, c, d, pe = _linkage_points()
    ax.add_patch(Rectangle((-68, -14), 136, 32, fc=LIGHT, ec=INK, lw=0.5))        # motor block
    for p, q in ((pa, c), (c, pe), (pb, d), (d, pe)):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=INK, lw=1.2, solid_capstyle='round', zorder=3)
    for p in (pa, pb, c, d, pe):                                # id0, id1 on the motor axes,
        tagbox(ax, p[0], p[1], 20)                              # id2, id3 on the elbows, id4 on the foot
    ax.text(pa[0], 22, 'id0', ha='center', va='bottom', **lab)
    ax.text(pb[0], 22, 'id1', ha='center', va='bottom', **lab)
    ax.text(c[0] - 15, c[1], 'id2', ha='right', va='center', **lab)
    ax.text(d[0] + 15, d[1], 'id3', ha='left', va='center', **lab)
    ax.text(pe[0] + 15, pe[1], 'id4', va='center', **lab)
    ax.plot([0, 0], [pe[1] - 10, -256], color=INK, lw=0.5)                        # cord
    ax.add_patch(Rectangle((-18, -284), 36, 28, fc=LIGHT, ec=INK, lw=0.5))
    ax.text(24, -270, '0-3 kg', va='center', **lab)
    ax.annotate('', xy=(96, -300), xytext=(96, -250),
                arrowprops=dict(arrowstyle='-|>', lw=0.7, color=MID))             # gravity
    ax.text(102, -275, 'g', va='center', fontsize=7, color=MID, style='italic')
    ax.text(-122, 50, '(a)', fontsize=9, fontweight='bold', va='top', color=INK)

    # (a) right: the camera stands 1.2 m in front of that plane, axis normal to it
    ax = fig.add_subplot(gs[0, 1]); ax.axis('off'); ax.set_aspect('equal')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    camera(ax, 0.305, 0.55, 0.16)
    ax.plot([0.305, 0.82], [0.55, 0.55], color=INK, lw=0.5, ls='--')               # sight line, lens to plane
    ax.plot([0.82, 0.82], [0.30, 0.80], color=INK, lw=2.0)                         # leg plane, edge-on
    ax.text((0.305 + 0.82) / 2, 0.55, '%.1f m' % CAMERA_M, **lab, **onl)
    ax.text(0.18, 0.64, 'camera', ha='center', va='bottom', **lab)

    # (b) the runway from above, robot walking to the right, camera behind it
    ax = fig.add_subplot(gs[1, :]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-58, 148); ax.set_ylim(-30, 94)
    ax.add_patch(Rectangle((0, 0), GRID_L, GRID_W, fc='none', ec=INK, lw=0.5, ls=':'))
    # runway ids (apriltag_runway_tilt_check.py): left side 4/6/8/10, right side 5/7/9/11,
    # rows every 40 cm from the camera end; drawn with the walk direction to the right,
    # so the robot's left side is the top edge
    for row, x in enumerate((0, 40, 80, 120)):
        for y, tid in ((GRID_W, 4 + 2 * row), (0, 5 + 2 * row)):
            tagbox(ax, x, y, 7)
            ax.text(x, y + (7 if y else -7), str(tid), ha='center', va='bottom' if y else 'top',
                    fontsize=7, color=INK)
    ax.text(GRID_L / 2, -17, '%.0f x %.0f cm' % (GRID_L, GRID_W), ha='center', va='top', **lab)
    rx, ry = 34, GRID_W / 2                                 # robot body
    ax.add_patch(Rectangle((rx - 26, ry - 12), 52, 24, fc=LIGHT, ec=INK, lw=0.5))
    hx, hy = TAG_FRAME[1] / 2, TAG_FRAME[0] / 2
    # back tags: 0/1 rear, 2/3 front; 0/2 on the robot's left (top edge here)
    for tid, (ddx, ddy) in enumerate(((-hx, hy), (-hx, -hy), (hx, hy), (hx, -hy))):
        tagbox(ax, rx + ddx, ry + ddy, 5.5)
        ax.text(rx + ddx + (6 if ddx > 0 else -6), ry + ddy, str(tid), ha='left' if ddx > 0 else 'right',
                va='center', fontsize=7, color=INK)
    ax.text(rx, ry - 15, '%.1f x %.1f cm' % (TAG_FRAME[1], TAG_FRAME[0]), ha='center', va='top',
            fontsize=7, color=MID)
    ax.annotate('', xy=(rx + 48, ry), xytext=(rx + 30, ry),
                arrowprops=dict(arrowstyle='-|>', lw=1.0, color=INK, mutation_scale=7))
    camera(ax, -39, ry, 9)
    ax.plot([-39, -3.5], [ry, ry], color=INK, lw=0.5, ls='--')                     # camera to the first tag row
    ax.text((-39 - 3.5) / 2, ry, '1.8 m', **lab, **onl)
    ax.text(-45, ry + 6, 'camera', ha='center', va='bottom', **lab)
    ax.text(-56, 94, '(b)', fontsize=9, fontweight='bold', va='top', color=INK)
    save(fig, 'fig1', svg=True)


# ---------------------------------------------------------------- fig2 ----
def fig2():
    pa, pb, c, d, pe = _linkage_points()
    fig = new_fig(6.5); ax = fig.add_subplot(111); ax.set_aspect('equal')
    for p, q in ((pa, c), (c, pe), (pb, d), (d, pe)):
        ax.plot([p[0], q[0]], [p[1], q[1]], color='k', lw=1.6)
    # +x reference through both motor axes, extended past them so each angle has a datum
    ax.plot([pa[0] - 40, pb[0] + 40], [0, 0], color='0.4', lw=0.8, ls='--')
    for p in (pa, pb, c, d):
        ax.add_patch(Circle(p, 4, fc='w', ec='k', lw=0.8, zorder=5))
    ax.add_patch(Circle(pe, 4, fc='k', ec='k', zorder=5))
    lab = dict(fontsize=8)
    ax.text(pa[0] - 6, pa[1] + 9, r'$P_A$', ha='right', **lab)
    ax.text(pb[0] + 6, pb[1] + 9, r'$P_B$', ha='left', **lab)
    ax.text(c[0] - 8, c[1], r'$C$', ha='right', va='center', **lab)
    ax.text(d[0] + 8, d[1], r'$D$', ha='left', va='center', **lab)
    ax.text(pe[0], pe[1] - 14, r'$P_E$ (0, $-$220)', ha='center', fontsize=8)
    ax.text((pa[0] + c[0]) / 2 - 14, (pa[1] + c[1]) / 2, r'$L_{AC}$', ha='right', fontsize=7)
    ax.text((pb[0] + d[0]) / 2 + 14, (pb[1] + d[1]) / 2, r'$L_{BD}$', ha='left', fontsize=7)
    ax.text((c[0] + pe[0]) / 2 - 12, (c[1] + pe[1]) / 2, r'$L_{CE}$', ha='right', fontsize=7)
    ax.text((d[0] + pe[0]) / 2 + 12, (d[1] + pe[1]) / 2, r'$L_{DE}$', ha='left', fontsize=7)
    ax.text(0, 8, '%.0f mm' % SPACING, ha='center', fontsize=7)
    # joint angles measured from +x at each motor, as in equation (3)
    for p, q, name, sgn in ((pa, c, r'$\theta_A$', 1), (pb, d, r'$\theta_B$', -1)):
        ang = np.degrees(np.arctan2(q[1] - p[1], q[0] - p[0]))
        R_ARC = 24.0                                               # same radius for both arcs
        ax.add_patch(Arc(p, 2 * R_ARC, 2 * R_ARC, theta1=min(0, ang), theta2=max(0, ang),
                         color='0.3', lw=0.6, zorder=4))
        mid = np.radians(ang / 2)                                  # label on the arc's bisector
        ax.text(p[0] + 38 * np.cos(mid), p[1] + 38 * np.sin(mid), name, ha='center', va='center', fontsize=8)
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
    ax.set_xlim(-150, 150); ax.set_ylim(-250, 30)
    save(fig, 'fig2', svg=True)


# ---------------------------------------------------------------- fig3 ----
def _bezier(t, p0, p1, p2, p3):
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def foot_path():
    """Same construction as walk_test.generate_bezier_trajectory (lift_ratio 0.4,
    land_ratio 0.6): stance sweeps +STEP -> -STEP on the ground, the swing returns.
    Returns the commanded stance points, the commanded swing points and the
    continuous swing curve they are sampled from."""
    n_st = int(STEPS * STANCE_RATIO); n_sw = STEPS - n_st
    sx, ex, hy = STEP, -STEP, HOME[1]
    stance = [(sx + (ex - sx) * i / (n_st - 1), hy) for i in range(n_st)]
    p0, p3 = np.array([ex, hy]), np.array([sx, hy])
    p1 = np.array([ex + (sx - ex) * 0.4 * 0.5, hy + LIFT * 1.25])
    p2 = np.array([ex + (sx - ex) * (1 - (1 - 0.6) * 0.5), hy + LIFT * 1.25])
    swing = [tuple(_bezier(i / (n_sw - 1), p0, p1, p2, p3)) for i in range(n_sw)]
    curve = [tuple(_bezier(t, p0, p1, p2, p3)) for t in np.linspace(0, 1, 200)]
    return np.array(stance), np.array(swing), np.array(curve)


def fig3():
    fig = new_fig(6.5)
    gs = fig.add_gridspec(2, 1, height_ratios=[0.72, 1.0], hspace=0.55)
    # (a) trot phasing over two cycles: black = stance.  Diagonal pairs share a
    # phase (FR+RL at 0, FL+RR at 0.5), as get_gait_phase_offset() in walk_test.py
    ax = fig.add_subplot(gs[0])
    legs = [('FR', 0.0), ('FL', 0.5), ('RR', 0.5), ('RL', 0.0)]
    for i, (name, off) in enumerate(legs):
        y = len(legs) - 1 - i
        for s0 in (off - 1, off, off + 1):
            ax.add_patch(Rectangle((s0, y - 0.3), STANCE_RATIO, 0.6, fc='k', ec='k', lw=0.5))
            ax.add_patch(Rectangle((s0 + STANCE_RATIO, y - 0.3), 1 - STANCE_RATIO, 0.6,
                                   fc='w', ec='k', lw=0.5))
        ax.text(-0.05, y, name, ha='right', va='center', fontsize=7)
    ax.set_xlim(0, 2); ax.set_ylim(-0.6, len(legs) + 0.7)
    ax.set_yticks([]); ax.set_xticks([0, 0.5, 1, 1.5, 2])
    ax.set_xlabel('gait cycle', labelpad=1)
    ax.add_patch(Rectangle((0.02, 4.0), 0.12, 0.3, fc='k', ec='k', lw=0.5, clip_on=False))
    ax.text(0.18, 4.15, 'stance', va='center', fontsize=7)
    ax.add_patch(Rectangle((1.25, 4.0), 0.12, 0.3, fc='w', ec='k', lw=0.5, clip_on=False))
    ax.text(1.41, 4.15, 'swing', va='center', fontsize=7)
    ax.tick_params(axis='x', top=False)                       # the legend sits on the top edge
    ax.text(-0.16, 1.0, '(a)', fontsize=9, fontweight='bold', transform=ax.transAxes)

    # (b) the foot path in the leg frame: the foot pushes back along the ground
    # during stance, so the body advances the other way.  Dashed = the Bezier curve,
    # dots = the points the controller actually commands (30 per cycle)
    ax = fig.add_subplot(gs[1]); ax.set_aspect('equal')
    st, sw, curve = foot_path()
    apex = float(curve[:, 1].max()); lift = apex - HOME[1]
    ax.plot(st[:, 0], st[:, 1], 'k-', lw=1.4); ax.plot(curve[:, 0], curve[:, 1], 'k--', lw=1.0)
    ax.plot(st[:, 0], st[:, 1], 'k.', ms=3); ax.plot(sw[:, 0], sw[:, 1], 'k.', ms=3)
    ax.annotate('', xy=(-STEP + 3, HOME[1] - 7), xytext=(STEP - 3, HOME[1] - 7),
                arrowprops=dict(arrowstyle='-|>', lw=0.6, color='k', mutation_scale=7))
    ax.text(0, HOME[1] - 11, 'stance', ha='center', va='top', fontsize=7)
    ax.text(0, apex + 3, 'swing', ha='center', va='bottom', fontsize=7)
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
    ax.set_xlim(-STEP - 40, STEP + 40); ax.set_ylim(HOME[1] - 24, apex + 20)
    ax.text(-0.3, 1.0, '(b)', fontsize=9, fontweight='bold', transform=ax.transAxes)
    save(fig, 'fig3', svg=True)


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
    ax.legend(loc='lower left', frameon=False)
    ax.grid(True, lw=0.3, alpha=0.5)
    save(fig, 'fig5')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--tracks' in sys.argv:
        FIG4_TRACKS = sys.argv[sys.argv.index('--tracks') + 1]
    todo = args or ['fig1', 'fig2', 'fig3', 'fig4', 'fig5']
    for name in todo:
        globals()[name]() if name != 'fig4' else fig4(FIG4_TRACKS)
