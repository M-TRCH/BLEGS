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
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle

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
    fig = new_fig(11.0)
    gs = fig.add_gridspec(2, 2, width_ratios=[0.54, 0.46], height_ratios=[1.12, 1.0],
                          hspace=0.15, wspace=0.02)

    # (a) left: the leg plane as the camera sees it, in real mm.  The leg hangs from
    # the motor block, which is clamped to the stand; the payload hangs from the foot.
    ax = fig.add_subplot(gs[0, 0]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-125, 125); ax.set_ylim(-312, 50)
    pa, pb, c, d, pe = _linkage_points()
    ax.add_patch(Rectangle((-32, 38), 64, 8, fc='0.3', ec='none'))            # stand
    ax.plot([0, 0], [18, 38], color='0.3', lw=3)                              # clamp
    ax.annotate('', xy=(104, -95), xytext=(104, -45),
                arrowprops=dict(arrowstyle='-|>', lw=0.6, color='0.4'))       # gravity
    ax.text(110, -70, 'g', va='center', fontsize=6, color='0.4', style='italic')
    ax.add_patch(Rectangle((-70, -16), 140, 34, fc='0.85', ec='k', lw=0.6))   # motor block
    for p, q in ((pa, c), (c, pe), (pb, d), (d, pe)):
        ax.plot([p[0], q[0]], [p[1], q[1]], color='k', lw=1.6, zorder=3)
    for p in (c, d):
        ax.add_patch(Circle(p, 4, fc='w', ec='k', lw=0.6, zorder=5))
    tag = 22
    for p in (pa, pb, pe):                                                    # id0, id1, id4
        ax.add_patch(Rectangle((p[0] - tag / 2, p[1] - tag / 2), tag, tag,
                               fc='w', ec='k', lw=0.6, zorder=6))
    ax.text(pa[0], 23, 'id0', ha='center', va='bottom', fontsize=6)
    ax.text(pb[0], 23, 'id1', ha='center', va='bottom', fontsize=6)
    ax.text(pe[0] + 16, pe[1], 'id4 (foot)', va='center', fontsize=6)
    ax.plot([0, 0], [pe[1] - tag / 2, -258], color='k', lw=0.6)              # payload cord
    ax.add_patch(Rectangle((-20, -286), 40, 28, fc='0.55', ec='k', lw=0.6))
    ax.text(0, -292, 'payload 0-3 kg', ha='center', va='top', fontsize=6)
    ax.text(-122, 48, '(a)', fontsize=8, fontweight='bold', va='top')

    # (a) right: top view - the camera axis is normal to the leg plane
    ax = fig.add_subplot(gs[0, 1]); ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.5, 0.98, 'top view (not to scale)', ha='center', va='top', fontsize=6)
    ax.add_patch(Rectangle((0.06, 0.48), 0.17, 0.13, fc='0.2', ec='none'))     # camera body
    ax.add_patch(Rectangle((0.23, 0.515), 0.05, 0.06, fc='0.2', ec='none'))    # lens
    ax.annotate('', xy=(0.80, 0.545), xytext=(0.28, 0.545),
                arrowprops=dict(arrowstyle='-|>', lw=0.6, color='0.4', linestyle='--'))
    ax.plot([0.83, 0.83], [0.25, 0.85], color='k', lw=2.2)                     # leg plane, edge-on
    ax.text(0.87, 0.545, 'leg\nplane', va='center', fontsize=6)
    ax.annotate('', xy=(0.28, 0.36), xytext=(0.83, 0.36),
                arrowprops=dict(arrowstyle='<->', lw=0.6))
    ax.text(0.555, 0.31, '%.1f m' % CAMERA_M, ha='center', va='top', fontsize=6)
    ax.text(0.03, 0.66, 'camera\n%d mm lens, %d fps' % (LENS_MM, FPS), va='bottom', fontsize=6)

    # (b) the runway from above, robot walking to the right, camera behind it
    ax = fig.add_subplot(gs[1, :]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-52, 150); ax.set_ylim(-30, 96)
    ax.add_patch(Rectangle((0, 0), GRID_L, GRID_W, fc='none', ec='0.6', lw=0.6, ls=':'))
    for x in (0, 40, 80, 120):                              # 4 rows of floor tags
        for y in (0, GRID_W):
            ax.add_patch(Rectangle((x - 4, y - 4), 8, 8, fc='w', ec='k', lw=0.6))
    ax.text(GRID_L / 2, GRID_W + 8, '8 floor tags on an %.0f x %.0f cm grid' % (GRID_W, GRID_L),
            ha='center', va='bottom', fontsize=6)
    rx, ry = 34, GRID_W / 2                                 # robot body, 52 x 24 cm
    ax.add_patch(FancyBboxPatch((rx - 26, ry - 12), 52, 24, boxstyle='round,pad=1',
                                fc='0.88', ec='k', lw=0.6))
    hx, hy = TAG_FRAME[1] / 2, TAG_FRAME[0] / 2
    for ddx, ddy in ((-hx, -hy), (hx, -hy), (-hx, hy), (hx, hy)):
        ax.add_patch(Rectangle((rx + ddx - 3, ry + ddy - 3), 6, 6, fc='w', ec='k', lw=0.6))
    ax.annotate('', xy=(rx + 46, ry), xytext=(rx + 29, ry),
                arrowprops=dict(arrowstyle='-|>', lw=0.8, color='k'))
    ax.text(rx + 37, ry + 4, 'walk', ha='center', va='bottom', fontsize=6)
    ax.plot([rx + hx, rx + hx], [ry - hy - 3, -9], color='0.5', lw=0.5)       # leader
    ax.text(GRID_L / 2, -11, '4 back tags on a %.1f x %.1f cm frame\n31 cm above the floor'
            % TAG_FRAME, ha='center', va='top', fontsize=6)
    ax.add_patch(Rectangle((-29, ry - 3.5), 8, 7, fc='0.2', ec='none'))       # camera
    ax.annotate('', xy=(-6, ry), xytext=(-21, ry),
                arrowprops=dict(arrowstyle='-|>', lw=0.6, color='0.4', linestyle='--'))
    ax.text(-25, ry + 7, 'camera\n1.8 m high', ha='center', va='bottom', fontsize=6)
    ax.text(-40, 100, '(b)', fontsize=8, fontweight='bold', va='top')
    save(fig, 'fig1')


# ---------------------------------------------------------------- fig2 ----
def fig2():
    pa, pb, c, d, pe = _linkage_points()
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
    ax.text(pe[0], pe[1] - 14, r'$P_E$ (foot), home pose (0, $-$220) mm', ha='center', fontsize=7)
    ax.text((pa[0] + c[0]) / 2 - 14, (pa[1] + c[1]) / 2, r'$L_{AC}$', ha='right', fontsize=7)
    ax.text((pb[0] + d[0]) / 2 + 14, (pb[1] + d[1]) / 2, r'$L_{BD}$', ha='left', fontsize=7)
    ax.text((c[0] + pe[0]) / 2 - 12, (c[1] + pe[1]) / 2, r'$L_{CE}$', ha='right', fontsize=7)
    ax.text((d[0] + pe[0]) / 2 + 12, (d[1] + pe[1]) / 2, r'$L_{DE}$', ha='left', fontsize=7)
    ax.text(0, 8, '%.0f mm' % SPACING, ha='center', fontsize=7)
    # joint angles measured from +x at each motor, as in equation (3)
    for p, q, name, sgn in ((pa, c, r'$\theta_A$', 1), (pb, d, r'$\theta_B$', -1)):
        ang = np.degrees(np.arctan2(q[1] - p[1], q[0] - p[0]))
        th = np.radians(np.linspace(min(0, ang), max(0, ang), 30))
        ax.plot(p[0] + 22 * np.cos(th), p[1] + 22 * np.sin(th), color='0.3', lw=0.6)
        ax.text(p[0] + sgn * 30, p[1] - 22, name, ha='center', fontsize=8)
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
    ax.set_xlim(-150, 150); ax.set_ylim(-250, 30)
    save(fig, 'fig2')


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
            ax.add_patch(Rectangle((s0, y - 0.3), STANCE_RATIO, 0.6, fc='k', ec='none'))
            ax.add_patch(Rectangle((s0 + STANCE_RATIO, y - 0.3), 1 - STANCE_RATIO, 0.6,
                                   fc='w', ec='k', lw=0.5))
        ax.text(-0.05, y, name, ha='right', va='center', fontsize=7)
    ax.set_xlim(0, 2); ax.set_ylim(-0.6, len(legs) + 0.7)
    ax.set_yticks([]); ax.set_xticks([0, 0.5, 1, 1.5, 2])
    ax.set_xlabel('gait cycle', labelpad=1)
    ax.add_patch(Rectangle((0.02, 4.0), 0.12, 0.3, fc='k', clip_on=False))
    ax.text(0.18, 4.15, 'stance, %.0f%% of the cycle' % (100 * STANCE_RATIO),
            va='center', fontsize=6)
    ax.add_patch(Rectangle((1.25, 4.0), 0.12, 0.3, fc='w', ec='k', lw=0.5, clip_on=False))
    ax.text(1.41, 4.15, 'swing', va='center', fontsize=6)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.text(-0.16, 1.0, '(a)', fontsize=8, fontweight='bold', transform=ax.transAxes)

    # (b) the foot path in the leg frame: the foot pushes back along the ground
    # during stance, so the body advances the other way.  Dashed = the Bezier curve,
    # dots = the points the controller actually commands (30 per cycle)
    ax = fig.add_subplot(gs[1]); ax.set_aspect('equal')
    st, sw, curve = foot_path()
    apex = float(curve[:, 1].max()); lift = apex - HOME[1]
    ax.plot(st[:, 0], st[:, 1], 'k-', lw=1.4); ax.plot(curve[:, 0], curve[:, 1], 'k--', lw=1.0)
    ax.plot(st[:, 0], st[:, 1], 'k.', ms=3); ax.plot(sw[:, 0], sw[:, 1], 'k.', ms=3)
    ax.annotate('', xy=(-STEP + 3, HOME[1] - 7), xytext=(STEP - 3, HOME[1] - 7),
                arrowprops=dict(arrowstyle='-|>', lw=0.7, color='k'))
    ax.text(0, HOME[1] - 11, 'stance: foot pushes back', ha='center', va='top', fontsize=6)
    ax.text(0, apex + 3, 'swing', ha='center', va='bottom', fontsize=6)
    ax.annotate('', xy=(-STEP - 12, apex + 10), xytext=(-STEP - 52, apex + 10),
                arrowprops=dict(arrowstyle='-|>', lw=0.8, color='0.4'))
    ax.text(-STEP - 32, apex + 14, 'body', ha='center', va='bottom', fontsize=6, color='0.4')
    ax.annotate('', xy=(STEP + 9, apex), xytext=(STEP + 9, HOME[1]),
                arrowprops=dict(arrowstyle='<->', lw=0.6, color='k'))
    ax.text(STEP + 13, (apex + HOME[1]) / 2, '%.1f mm' % lift, va='center', fontsize=6)
    ax.text(STEP + 40, apex + 24, '%d points\nper cycle' % STEPS, ha='right', va='top',
            fontsize=5.5, color='0.4')
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
    ax.set_xlim(-STEP - 56, STEP + 42); ax.set_ylim(HOME[1] - 26, apex + 26)
    ax.text(-0.3, 1.0, '(b)', fontsize=8, fontweight='bold', transform=ax.transAxes)
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
