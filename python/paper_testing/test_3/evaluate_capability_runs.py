"""Turn the section-2.3.3 field runs into the capability matrix (paper table 5).

Inputs
------
1. A run sheet the operator fills in, one row per run (default
   output/log/run_sheet.csv - pre-filled with the 2.3.3 matrix, rows whose
   log_file is blank are skipped; run_sheet.example.csv shows filled rows):

       log_file, surface, payload_kg, run, ramp_deg, success, distance_m, note

   log_file   name of the robot log walk_test.py wrote for that run; a file that
              holds several runs walked back to back (>= 15 s without a drive
              command between them) is addressed as  name.csv#2  for its 2nd run
   surface    flat | ramp | compliant | rough   (free text is fine, it is grouped as-is)
   payload_kg 0 or 3
   ramp_deg   blank except for ramp runs
   success    1 = met every criterion in 2.3.3, 0 = did not
   distance_m tape-measured along the surface

2. The robot logs (50 Hz, with v_cmd_mm_s and turn_k_cmd) - give the walking
   time and the steering-effort index k-bar.
3. PZEM logs from pzem_logger.py in the same directory - give V(t) and I(t).
   Runs are matched to meter samples by wall-clock time: the robot log's start
   is the timestamp in its file name, so the two clocks must be the same PC.

Outputs
-------
    output/data/capability_runs.csv     one row per run with every metric
    printed matrix                      per surface x payload, plus the critical ramp angle
    --write-table                       also rewrite paper/tables/src/table5.md

CoT = E / (m g d) with E = integral of V*I over the walking window, m = robot
mass + payload, d the tape-measured distance.

    python evaluate_capability_runs.py                       # dry run, prints only
    python evaluate_capability_runs.py --write-table
    python evaluate_capability_runs.py --sheet output/log/run_sheet.example.csv --simulate-pzem
    python evaluate_capability_runs.py --list-logs       # every robot log with its start time, to fill the sheet
"""
import argparse
import csv
import glob
import os
import time
from collections import OrderedDict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(HERE, 'output', 'log')
DATA_DIR = os.path.join(HERE, 'output', 'data')
TABLE5 = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'paper', 'tables', 'src', 'table5.md'))

ROBOT_MASS_KG = 5.597          # weighed by the author, 26 Aug 2026
G = 9.80665
RATE_HZ = 50.0
SIM_V, SIM_I = 12.5, 1.6       # used only with --simulate-pzem, and flagged everywhere


def log_start_epoch(log_file: str) -> float:
    """walk_test.py names logs movement_<dist>mm_YYYYmmdd_HHMMSS.csv (local time)."""
    stem = os.path.splitext(os.path.basename(log_file))[0]
    stamp = '_'.join(stem.split('_')[-2:])
    return time.mktime(time.strptime(stamp, '%Y%m%d_%H%M%S'))


def load_pzem(pzem_dir: str) -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(os.path.join(pzem_dir, 'pzem_*.csv'))):
        d = pd.read_csv(f)
        d['file'] = os.path.basename(f)
        frames.append(d)
    if not frames:
        return pd.DataFrame(columns=['t_unix', 'v_V', 'i_A', 'p_W', 'file'])
    return pd.concat(frames, ignore_index=True).sort_values('t_unix')


SPLIT_GAP_S = 10.0   # no drive command for this long = the robot was carried back to the start
                     # (12 Oct: carry-backs took 14-24 s, steering pauses inside a run <= 7 s)


def split_log(path: str):
    """A log may hold several runs walked back to back (walk, carry back, walk again).
    Returns (name, segments): the robot log name and a list of (t_first, t_last)
    walking windows separated by >= SPLIT_GAP_S without any drive command."""
    d = pd.read_csv(path)
    tick = d.groupby('time').agg(v=('v_cmd_mm_s', 'first'), k=('turn_k_cmd', 'first'))
    t = tick.index.to_numpy()
    moving = ((tick.v.abs() > 1.0) | (tick.k.abs() > 0.05)).to_numpy()
    tm = t[moving]
    if len(tm) == 0:
        raise ValueError('no walking ticks in %s' % os.path.basename(path))
    cuts = np.where(np.diff(tm) >= SPLIT_GAP_S)[0]
    bounds = [0] + list(cuts + 1) + [len(tm)]
    return [(float(tm[a]), float(tm[b - 1])) for a, b in zip(bounds[:-1], bounds[1:])]


def analyse_log(path: str, segment: int = 0):
    """segment = 1-based run inside the file (0 = treat the whole file as one run)."""
    d = pd.read_csv(path)
    tick = d.groupby('time').agg(v=('v_cmd_mm_s', 'first'), k=('turn_k_cmd', 'first'))
    t = tick.index.to_numpy()
    moving = (tick.v.abs() > 1.0) | (tick.k.abs() > 0.05)
    if not moving.any():
        raise ValueError('no walking ticks in %s' % os.path.basename(path))
    if segment:
        segs = split_log(path)
        if segment > len(segs):
            raise ValueError('%s has only %d run(s), #%d asked' % (os.path.basename(path), len(segs), segment))
        a, b = segs[segment - 1]
        moving &= (tick.index >= a) & (tick.index <= b)
    tm = t[moving.to_numpy()]
    dt = np.diff(t)
    return dict(
        ticks=len(t), rate_hz=len(t) / t[-1] if t[-1] else float('nan'),
        dropped=int((dt > 0.030).sum()),
        t_first=float(tm[0]), t_last=float(tm[-1]),
        t_move=float(moving.sum() / RATE_HZ),
        k_bar=float(tick.k[moving].abs().mean()),
        sum_i_motor_A=float((d.groupby('time')[['current_A_mA', 'current_B_mA']]
                             .sum().sum(axis=1) / 1000.0)[moving.to_numpy()].mean()),
    )


def parse_log_ref(ref: str):
    """'movement_x.csv' -> (file, 0); 'movement_x.csv#3' -> (file, 3) = third run in it."""
    ref = ref.strip()
    if '#' in ref:
        f, n = ref.rsplit('#', 1)
        return f.strip(), int(n)
    return ref, 0


def energy_from_pzem(pz: pd.DataFrame, t0: float, t1: float):
    """Trapezoidal integral of V*I over [t0, t1]; returns (E_J, V_mean, I_mean, n)."""
    w = pz[(pz.t_unix >= t0 - 1.0) & (pz.t_unix <= t1 + 1.0)]
    if len(w) < 2:
        return None
    tt = w.t_unix.to_numpy(float)
    p = (w.v_V * w.i_A).to_numpy(float)
    # clip the sample times to the window so idle seconds either side are not counted
    tt_c = np.clip(tt, t0, t1)
    trapezoid = getattr(np, 'trapezoid', None) or np.trapz      # numpy 2 renamed it
    e = float(trapezoid(p, tt_c))
    return e, float(w.v_V.mean()), float(w.i_A.mean()), int(len(w))


def list_logs(log_dir: str, pzem_dir: str):
    """Print every robot log with its wall-clock start, so the operator can match
    the runs written on the sheet to file names after the session."""
    pz = load_pzem(pzem_dir)
    print('%-36s %-19s %7s %6s %6s %4s' % ('log_file', 'start', 'move_s', 'k_bar', 'Hz', 'pzem'))
    for f in sorted(glob.glob(os.path.join(log_dir, 'movement_*.csv'))):
        start = log_start_epoch(f)
        clock = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
        try:
            segs = split_log(f)
        except ValueError:
            print('%-36s %-19s (no walking ticks)' % (os.path.basename(f), clock)); continue
        except KeyError:
            print('%-36s %-19s (old log without v_cmd_mm_s/turn_k_cmd)' % (os.path.basename(f), clock)); continue
        # one line per run inside the file; a single-run file keeps its plain name
        for n in range(1, len(segs) + 1):
            m = analyse_log(f, n if len(segs) > 1 else 0)
            t0, t1 = start + m['t_first'], start + m['t_last']
            covered = int(((pz.t_unix >= t0 - 1.0) & (pz.t_unix <= t1 + 1.0)).sum()) if len(pz) else 0
            name = os.path.basename(f) + ('#%d' % n if len(segs) > 1 else '')
            print('%-36s %-19s %7.1f %6.3f %6.1f %4s' % (
                name, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0)), m['t_move'], m['k_bar'],
                m['rate_hz'], 'yes' if covered >= 2 else 'no'))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--sheet', default=os.path.join(LOG_DIR, 'run_sheet.csv'))
    ap.add_argument('--log-dir', default=LOG_DIR)
    ap.add_argument('--pzem-dir', default=LOG_DIR)
    ap.add_argument('--write-table', action='store_true', help='rewrite paper/tables/src/table5.md')
    ap.add_argument('--simulate-pzem', action='store_true',
                    help='no meter data: assume %.1f V x %.1f A (output is flagged SIMULATED)' % (SIM_V, SIM_I))
    ap.add_argument('--list-logs', action='store_true',
                    help='print every robot log in --log-dir with its start time and exit (to fill the sheet)')
    args = ap.parse_args()
    if args.list_logs:
        list_logs(args.log_dir, args.pzem_dir); return

    sheet = pd.read_csv(args.sheet, dtype=str, keep_default_na=False)
    pz = load_pzem(args.pzem_dir)
    rows = []
    simulated_any = False
    for _, r in sheet.iterrows():
        if not r['log_file'].strip():
            continue
        fname, seg = parse_log_ref(r['log_file'])
        path = os.path.join(args.log_dir, fname)
        if not os.path.exists(path):
            print('  !! missing log %s - row skipped' % r['log_file']); continue
        try:
            m = analyse_log(path, seg)
        except (ValueError, KeyError) as exc:
            print('  !! %s - row skipped (nothing to measure)' % exc); continue
        start = log_start_epoch(path)
        t0, t1 = start + m['t_first'], start + m['t_last']
        em = energy_from_pzem(pz, t0, t1)
        if em is None:
            if not args.simulate_pzem:
                print('  !! no PZEM samples cover %s (%s) - CoT left blank'
                      % (r['log_file'], time.strftime('%H:%M:%S', time.localtime(t0))))
                e_j = v_mean = i_mean = float('nan'); n_pz = 0; src = 'none'
            else:
                e_j, v_mean, i_mean, n_pz = SIM_V * SIM_I * m['t_move'], SIM_V, SIM_I, 0
                src = 'SIMULATED'; simulated_any = True
        else:
            e_j, v_mean, i_mean, n_pz = em; src = 'pzem'
        payload = float(r['payload_kg'] or 0)
        dist = float(r['distance_m']) if r['distance_m'].strip() else float('nan')
        cot = e_j / ((ROBOT_MASS_KG + payload) * G * dist) if dist > 0 else float('nan')
        rows.append(OrderedDict(
            log_file=r['log_file'], surface=r['surface'].strip(), payload_kg=payload,
            run=r['run'], ramp_deg=r['ramp_deg'].strip(), success=int(r['success'] or 0),
            distance_m=dist, t_move_s=round(m['t_move'], 2),
            # energy is integrated over the whole span from first to last motion, pauses
            # included; speed uses only the ticks the robot was actually commanded to move
            t_window_s=round(m['t_last'] - m['t_first'], 2),
            speed_cm_s=round(100 * dist / m['t_move'], 2) if dist > 0 else float('nan'),
            k_bar=round(m['k_bar'], 3), sum_i_motor_A=round(m['sum_i_motor_A'], 2),
            v_bus_V=round(v_mean, 2) if v_mean == v_mean else '', i_bus_A=round(i_mean, 3) if i_mean == i_mean else '',
            e_J=round(e_j, 1) if e_j == e_j else '', cot=round(cot, 2) if cot == cot else '',
            energy_source=src, pzem_samples=n_pz,
            log_rate_hz=round(m['rate_hz'], 1), dropped_ticks=m['dropped'], note=r['note'],
        ))

    if not rows:
        print('no runs'); return
    runs = pd.DataFrame(rows)
    os.makedirs(DATA_DIR, exist_ok=True)
    out = os.path.join(DATA_DIR, 'capability_runs.csv')
    runs.to_csv(out, index=False)
    print('\nper-run metrics -> %s' % out)
    print(runs[['log_file', 'surface', 'payload_kg', 'run', 'success', 'distance_m', 't_move_s',
                'speed_cm_s', 'k_bar', 'i_bus_A', 'cot', 'energy_source']].to_string(index=False))

    # ---- matrix -------------------------------------------------------------
    def label(s, rd):
        return '%s, %s°' % (s, rd) if rd else s
    runs['cond'] = [label(s, rd) for s, rd in zip(runs.surface, runs.ramp_deg)]
    runs['cot_num'] = pd.to_numeric(runs.cot, errors='coerce')
    agg = runs.groupby(['cond', 'payload_kg'], sort=False).agg(
        n=('success', 'size'), ok=('success', 'sum'),
        speed=('speed_cm_s', 'mean'), k_bar=('k_bar', 'mean'), cot=('cot_num', 'mean')).reset_index()
    print('\n=== capability matrix%s ===' % (' (ENERGY SIMULATED)' if simulated_any else ''))
    print('%-22s %-8s %8s %12s %7s %6s' % ('surface', 'payload', 'success', 'speed cm/s', 'k_bar', 'CoT'))
    for _, a in agg.iterrows():
        print('%-22s %-8s %8s %12.1f %7.2f %6s' % (
            a.cond, 'none' if a.payload_kg == 0 else '%g kg' % a.payload_kg,
            '%d/%d' % (a.ok, a.n), a.speed, a.k_bar, '%.1f' % a.cot if a.cot == a.cot else '-'))

    ramp = runs[runs.ramp_deg != '']
    if len(ramp):
        print('\ncritical ramp angle (highest angle with every run successful):')
        for payload, g in ramp.groupby('payload_kg'):
            ok = g.groupby('ramp_deg').success.agg(['sum', 'size'])
            full = [float(a) for a, s in ok.iterrows() if s['sum'] == s['size']]
            print('  payload %g kg: %s' % (payload, ('%g°' % max(full)) if full else 'none passed'))

    # ---- table 5 ------------------------------------------------------------
    if args.write_table:
        lines = []
        if simulated_any:
            lines.append('<!-- MOCK -->')
            lines.append('<!-- Energy column is SIMULATED (no PZEM data) - re-run without --simulate-pzem. -->')
        lines.append('<!-- Generated by python/paper_testing/test_3/evaluate_capability_runs.py from')
        lines.append('     output/log/run_sheet.csv + the robot and PZEM logs.  Do not hand-edit. -->')
        lines.append('')
        lines.append('| Surface | Payload | Success | Speed (cm/s) | $\\bar{k}$ | CoT |')
        lines.append('|---|---|---|---|---|---|')
        for _, a in agg.iterrows():
            lines.append('| %s | %s | %d/%d | %.1f | %.2f | %s |' % (
                a.cond, 'none' if a.payload_kg == 0 else '%g kg' % a.payload_kg, a.ok, a.n,
                a.speed, a.k_bar, '%.1f' % a.cot if a.cot == a.cot else '–'))
        with open(TABLE5, 'w', encoding='utf-8', newline='') as fh:
            fh.write('\n'.join(lines) + '\n')
        print('\nwrote %s%s' % (TABLE5, '  (still marked MOCK)' if simulated_any else ''))


if __name__ == '__main__':
    main()
