<!-- 25 Nov 2026: the editor of The Journal of KMUTNB asked for every table header and row label in Thai
     (preliminary check of article 88_272060); units follow the body text (Thai unit names). -->
<!-- 3 Nov 2026 re-shoot: 5 ML-on/ML-off pairs per payload, open-loop straight walk.
     Source: python/paper_testing/test_3/output/data/walk_video_metrics_261103_{0kg,3kg}.csv
     (walk_video_metrics.py).  Mean +/- SD over 5 runs; delta and phi_end are taken as absolute
     values because the drift direction differs between payloads; d_60 is the lateral shift
     at 60 cm along the runway, a distance every run reached.  Paired t-test p values in 3.3. -->

| ตัวชี้วัด | สัญลักษณ์ | ไม่มีโหลด ปิดการชดเชย | ไม่มีโหลด เปิดการชดเชย | 3 กิโลกรัม ปิดการชดเชย | 3 กิโลกรัม เปิดการชดเชย |
|---|---|---|---|---|---|
| จำนวนรอบ | – | 5 | 5 | 5 | 5 |
| ระยะที่เดินได้ (เมตร) | $D$ | 1.98 ± 0.05 | 1.94 ± 0.03 | 0.82 ± 0.18 | 1.07 ± 0.03 |
| อัตราการเบี่ยง (เซนติเมตรต่อเมตร) | $\vert\delta\vert$ | 23.7 ± 3.9 | 7.9 ± 3.2 | 29.4 ± 3.1 | 15.1 ± 3.0 |
| มุมเบี่ยง (องศา) | $\vert\varphi_{end}\vert$ | 24.0 ± 5.0 | 5.3 ± 3.3 | 24.1 ± 1.9 | 10.3 ± 3.5 |
| ระยะเบี่ยงด้านข้าง (เซนติเมตร) | $\vert d_{60}\vert$ | 9.0 ± 1.0 | 7.5 ± 1.2 | 13.4 ± 3.7 | 5.0 ± 1.3 |
| ความเร็ว (เซนติเมตรต่อวินาที) | – | 13.8 ± 0.3 | 13.4 ± 1.0 | 8.9 ± 0.3 | 7.7 ± 0.4 |
