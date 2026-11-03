"""Path chart for the §2.3 infographic: body-centre paths of the 3 Nov 2026 runs (figures/src/fig5_tracks.npz),
ML on (blue) vs off (orange), one panel per payload.  Writes paths.svg next to this file.

    python make_paths_svg.py
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
z = np.load(os.path.join(HERE, '..', 'figures', 'src', 'fig5_tracks.npz'))
ON, OFF, INK2, GRID = '#2a78d6', '#eb6834', '#52514e', '#e4e3df'

plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 8, 'axes.edgecolor': INK2, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False,
                     'svg.fonttype': 'none'})
fig, axes = plt.subplots(1, 2, figsize=(3.5, 3.3), sharey=True)
for ax, (load, title) in zip(axes, (('0kg', 'No load'), ('3kg', '3 kg'))):
    for key in sorted(k for k in z.files if k.startswith(load)):
        p = z[key]
        c = ON if '_ML' in key else OFF
        k = np.ones(5) / 5
        x = np.convolve(np.pad(p[:, 0], 2, mode='edge'), k, 'valid')     # light smoothing of the gait sway
        y = np.convolve(np.pad(p[:, 1], 2, mode='edge'), k, 'valid')
        ax.plot(x, y, color=c, lw=1.4, alpha=0.9, solid_capstyle='round')
        ax.plot(x[-1], y[-1], 'o', ms=4, color=c, mec='white', mew=1.2)
    ax.axvline(0, color=INK2, lw=0.8, ls=(0, (2, 2)))
    ax.set_xlim(-60, 35); ax.set_ylim(-5, 212)
    ax.set_xticks([-50, -25, 0, 25])
    ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.set_title(title, fontsize=9, color='#0b0b0b', loc='left', pad=4)
    ax.set_xlabel('lateral (cm)')
    ax.tick_params(length=0)
axes[0].set_ylabel('distance along runway (cm)')
fig.tight_layout(pad=0.3, w_pad=0.6)
fig.savefig(os.path.join(HERE, 'paths.svg'), transparent=True)
print('wrote paths.svg')
