"""Draft figures for section 2.3.3 from output/data/capability_runs.csv (written by
evaluate_capability_runs.py). Flat + gravel only so far; rerun after more surfaces.

(a) cost of transport per condition, every run as a dot, mean as a bar
(b) bus power vs walking speed, one dot per run - power is set by load, speed by surface

Writes output/figures/capability_draft.png (+ .svg). Needs only numpy + matplotlib.
"""
import csv
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'output', 'data', 'capability_runs.csv')
OUT = os.path.join(HERE, 'output', 'figures')

SURFACES = [('Flat (reference)', 'Flat', '#2a78d6'), ('Rough (gravel)', 'Gravel', '#eb6834')]
LOADS = [(0.0, 'no load', 'o', True), (3.0, '3 kg', 's', False)]   # 3 kg = hollow marker

rows = [r for r in csv.DictReader(open(SRC, encoding='utf-8'))
        if r['surface'] in {s for s, _, _ in SURFACES} and r['success'] == '1']

plt.rcParams.update({'font.family': 'Arial', 'font.size': 8, 'axes.linewidth': 0.8,
                     'xtick.direction': 'in', 'ytick.direction': 'in'})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={'width_ratios': [1, 1.15]})
rng = np.random.default_rng(1)

# (a) CoT per condition
x = 0
ticks, labels = [], []
for surf, sname, col in SURFACES:
    for load, lname, mk, filled in LOADS:
        c = [float(r['cot']) for r in rows if r['surface'] == surf and float(r['payload_kg']) == load]
        if not c:
            continue
        ax1.bar(x, np.mean(c), width=0.62, color=col, alpha=0.18, edgecolor='none')
        ax1.hlines(np.mean(c), x - 0.31, x + 0.31, color=col, lw=2)
        ax1.scatter(x + rng.uniform(-0.14, 0.14, len(c)), c, s=22, marker=mk,
                    facecolor=col if filled else 'white', edgecolor=col, lw=1.2, zorder=3)
        ax1.text(x, max(c) + 0.35, '%.1f' % np.mean(c), ha='center', va='bottom', fontsize=8)
        ticks.append(x); labels.append('%s\n%s (n=%d)' % (sname, lname, len(c)))
        x += 1
    x += 0.4
ax1.set_xticks(ticks); ax1.set_xticklabels(labels, fontsize=7)
ax1.set_ylabel('Cost of transport (-)')
ax1.set_ylim(0, 17)
ax1.set_title('(a)', loc='left', fontsize=9, fontweight='bold')

# (b) bus power vs speed
for surf, sname, col in SURFACES:
    for load, lname, mk, filled in LOADS:
        rr = [r for r in rows if r['surface'] == surf and float(r['payload_kg']) == load]
        if not rr:
            continue
        v = np.array([float(r['speed_cm_s']) for r in rr])
        p = np.array([float(r['v_bus_V']) * float(r['i_bus_A']) for r in rr])
        ax2.scatter(v, p, s=26, marker=mk, facecolor=col if filled else 'white', edgecolor=col,
                    lw=1.2, zorder=3, label='%s, %s' % (sname, lname))
ax2.set_xlabel('Walking speed (cm/s)')
ax2.set_ylabel('Bus power (W)')
ax2.set_xlim(3, 9); ax2.set_ylim(0, 50)
ax2.legend(frameon=False, fontsize=7, loc='lower right', ncol=1, handletextpad=0.3)
ax2.set_title('(b)', loc='left', fontsize=9, fontweight='bold')

fig.tight_layout()
os.makedirs(OUT, exist_ok=True)
for ext in ('png', 'svg'):
    fig.savefig(os.path.join(OUT, 'capability_draft.' + ext), dpi=200)
print('wrote', os.path.join(OUT, 'capability_draft.png'), '-', len(rows), 'runs')
