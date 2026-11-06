<!-- Real data.  Flat, foam and gravel: 14-22 Oct 2026, L = 2.4 m.  Ramp: 6 Nov 2026, L = 1.2 m along the slope,
     angle set to +-0.5 deg, ML compensation off (log ml_on = 0), 0 kg leg-levelling table for both payloads.
     Source: python/paper_testing/test_3/output/data/capability_runs.csv, made by evaluate_capability_runs.py
     from output/log/run_sheet.csv + the robot and PZEM logs (energy = integral of V*I over the run).
     Rows of the run sheet that are not table conditions (12 Oct lift-back, shakedown, extra 6th flat run) are left out.
     Failed runs have no speed, k or CoT.  Ramp 15 deg was not run at 3 kg because 10 deg already failed.
     Ramp 10 deg, 3 kg: reached 0.5, 0.5, 0.5, 0.3, 0.3 m.  Ramp 15 deg, 0 kg: about 0.2 m on every run. -->

| Surface | Payload | Success | Speed (cm/s) | $\bar{k}$ | CoT |
|---|---|---|---|---|---|
| Flat | none | 5/5 | 7.4 | 0.10 | 5.8 |
| Flat | 3 kg | 5/5 | 6.1 | 0.14 | 8.2 |
| Ramp 5° | none | 5/5 | 6.3 | 0.22 | 7.7 |
| Ramp 5° | 3 kg | 5/5 | 4.0 | 0.29 | 13.2 |
| Ramp 10° | none | 5/5 | 4.0 | 0.17 | 15.0 |
| Ramp 10° | 3 kg | 0/5 | – | – | – |
| Ramp 15° | none | 0/5 | – | – | – |
| Foam | none | 5/5 | 4.5 | 0.23 | 11.2 |
| Foam | 3 kg | 5/5 | 3.4 | 0.11 | 15.7 |
| Gravel | none | 5/5 | 5.8 | 0.15 | 8.5 |
| Gravel | 3 kg | 5/5 | 4.5 | 0.11 | 12.0 |
