<!-- Transposed like table4, for the same reason: the four payload levels read
     across, the quantities down the side, so it stays at 5 columns and fits a
     7.5 cm journal column.

     Every value comes from ../../python/paper_testing/test_2/output/data/
     dynamic_eval.csv, written by dynamic_model_evaluation.py over all 24
     circle clips.  Do not hand-edit numbers here - re-run that script.

     The point of the table is the offset/shape split: radius and fit RMS
     (shape) barely move, while the centre offset grows with payload and is
     what compensation pulls back. -->

| Quantity | No-load | 1 kg | 2 kg | 3 kg |
|---|---|---|---|---|
| Radius, comp. off (mm) | 29.58 | 30.03 | 29.84 | 29.33 |
| Radius, POLY4 (mm) | 29.68 | 30.25 | 30.33 | 29.77 |
| Centre $y$, comp. off (mm) | −179.00 | −185.93 | −188.28 | −190.64 |
| Centre $y$, POLY4 (mm) | −173.86 | −178.28 | −178.39 | −180.87 |
| Centre offset, comp. off (mm) | 11.51 | 17.24 | 19.52 | 21.79 |
| Centre offset, POLY4 (mm) | 4.45 | 8.38 | 8.58 | 11.00 |
| Fit RMS, comp. off (mm) | 1.29 | 0.91 | 1.35 | 1.81 |
| Fit RMS, POLY4 (mm) | 1.69 | 1.70 | 1.25 | 1.46 |
