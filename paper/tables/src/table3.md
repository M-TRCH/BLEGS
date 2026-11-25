<!-- 25 Nov 2026: the editor of The Journal of KMUTNB asked for every table header and row label in Thai
     (preliminary check of article 88_272060); units follow the body text (Thai unit names). -->
<!-- Cross-condition model comparison.  Every value from
     ../../python/paper_testing/test_2/output/data/dynamic_eval.csv
     (dynamic_model_evaluation.py) - do not hand-edit, re-run the script.

     This is deliberately NOT the table in output/models/training_summary.txt.
     That one is in-sample (train_compensation_model.py fits and predicts on
     the same 608 rows) and ranks Random Forest first at 0.40 mm / R2 0.97,
     which is overfitting, not accuracy.  What is tabulated here is the error
     still left at the foot while each model runs inside the control loop, on
     continuous circular motion the models never saw during training.

     The finding is that the five models are indistinguishable: 0.30 mm
     separates best from worst, against the 6.64 mm each of them removes. -->

| แบบจำลอง | ไม่มีโหลด | 1 กิโลกรัม | 2 กิโลกรัม | 3 กิโลกรัม | เฉลี่ย |
|---|---|---|---|---|---|
| ไม่ชดเชย | 8.70 | 11.92 | 13.32 | 14.54 | 12.12 |
| พหุนามอันดับ 3 | 3.63 | 5.17 | 6.06 | 7.03 | 5.47 |
| โครงข่ายประสาทเทียม | 3.27 | 5.94 | 6.06 | 6.88 | 5.54 |
| ป่าสุ่ม | 3.57 | 5.55 | 5.96 | 7.14 | 5.56 |
| พหุนามอันดับ 4 | 3.56 | 5.95 | 5.90 | 7.21 | 5.66 |
| เวกเตอร์สนับสนุน | 3.78 | 5.78 | 5.78 | 7.78 | 5.78 |
