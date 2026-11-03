<!-- 3 Nov 2026 re-shoot: 5 ML-on/ML-off pairs per payload, open-loop straight walk.
     Source: python/paper_testing/test_3/output/data/walk_video_metrics_261103_{0kg,3kg}.csv
     (walk_video_metrics.py).  Mean +/- SD over 5 runs; delta and phi_end are taken as absolute
     values because the drift direction differs between payloads; d_60 is the lateral shift
     at 60 cm along the runway, a distance every run reached.  Paired t-test p values in 3.3. -->

| Metric | No-load off | No-load on | 3 kg off | 3 kg on |
|---|---|---|---|---|
| Runs | 5 | 5 | 5 | 5 |
| $D$ (m) | 1.98 ± 0.05 | 1.94 ± 0.03 | 0.82 ± 0.18 | 1.07 ± 0.03 |
| $\vert\delta\vert$ (cm/m) | 23.7 ± 3.9 | 7.9 ± 3.2 | 29.4 ± 3.1 | 15.1 ± 3.0 |
| $\vert\varphi_{end}\vert$ (deg) | 24.0 ± 5.0 | 5.3 ± 3.3 | 24.1 ± 1.9 | 10.3 ± 3.5 |
| $\vert d_{60}\vert$ (cm) | 9.0 ± 1.0 | 7.5 ± 1.2 | 13.4 ± 3.7 | 5.0 ± 1.3 |
| Speed (cm/s) | 13.8 ± 0.3 | 13.4 ± 1.0 | 8.9 ± 0.3 | 7.7 ± 0.4 |
