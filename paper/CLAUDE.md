# CLAUDE.md — paper/

Paper-layer guidance. Repo-wide architecture, build commands, and robot facts live in the **root [`CLAUDE.md`](../CLAUDE.md)** — read that first. This file only covers what is specific to the manuscript.

## What this is

The manuscript for a TCI Tier 1 journal paper (The Journal of KMUTNB) about the BLEGS quadruped and its data-driven leg-error compensation. **Two versions live side by side**: `manuscript/drafts/` is the journal version, cut to fit the hard 9-page limit, and is what `build.ps1` / `preview.ps1` read; `manuscript/drafts-full/` keeps the uncut thesis-scale text for reference and is read by nothing. Edits go to `drafts/` unless you are deliberately updating the thesis copy. Everything here is writing and submission material; the code that produced the data is `../python/paper_testing/` (test_2 = single-leg + ML models, test_3 = whole-robot walking) — **there is no code copy under paper/ by design**, so never "fix" analysis scripts here.

## Writing conventions (match the existing text exactly)

The manuscript is Thai academic prose; English in parentheses on first use of a technical term. Patterns used consistently in `manuscript/drafts/02_methods.md`:

- Paragraphs open with `&emsp;`.
- Headings use decimal numbering (`### 2.3.1`, `#### 2.3.3.1` where a 4th level was unavoidable).
- Display equations are `$$...$$`, introduced by `ตามสมการที่ (N)`; variables defined after in a `โดยที่:` bullet list.
- **Equation numbers are sequential and maintained by hand** — inserting or deleting one renumbers every later one plus its cross-references. Grep `สมการที่ (` and fix all; the references live in `02_methods.md` and `03_results.md`. The journal version carries **9 equations**, all displayed in `02_methods.md` (the thesis copy in `drafts-full/` still has 26).
- **Placeholder content is marked `[...]{.mock}` (inline) or `::: mock` (block), never `<mark>`.** `journal/templates/mock.lua` renders it red in the PDF and bold with a ⟦จำลอง⟧ prefix in .docx, so nothing is silently dropped; `grep -n mock manuscript/drafts/*.md` lists what still has to be replaced. A table whose source carries `<!-- MOCK -->` gets a MOCK DATA watermark from `render-tables.py`. (`<mark>` was the old convention: pandoc drops raw HTML, so it vanished from both outputs.)
- Captions must not use the word "แสดง" (journal rule).

**Chapter 2 is methods**: it defines procedures and metrics but must not report measured values or conclusions. Defer numbers with "รายงานในบทผลการทดลอง" / "นำเสนอในบทถัดไป" as §2.2.1 and §2.3.2 already do. Equipment specs (marker sizes, camera resolution) are fine in methods; results are not.

## Journal rules that shape the work

Full set: `journal/FORMAT_GUIDE.md` and the official docs in `journal/instructions/`. The ones that bite:

- **≤ 9 A4 pages total** on paper (the newer guide says 8–10), two columns, TH Sarabun New — but the author has confirmed up to **12** is acceptable, and the five published TCI-1 examples run 10–14 pages. As of 2026-11-08 the Word build measures **12** with every section written, i.e. the ceiling. Anything added from here needs something else cut. **Figure/table position in the drafts is a layout decision**: figures 1–3 and tables 4–5 sit one paragraph after their first mention so that they land at the top of a column and text fills the gaps (journal rule: figures at the top of the page); moving them back costs about a column, i.e. page 13.
- **Every figure AND table must also be submitted as a separate .jpg** → `figures/export/`, `tables/export/`. Figures are drawn by **`make-figures.py`** (schematics from the geometry constants, plots from the measurement files; fig4 reads `figures/src/fig4_tracks.npz`), so regenerate rather than hand-edit. Since 8 Nov 2026 every word in a figure is TH Sarabun New 12 pt (the guide's size for figure detail text) and variables are Times New Roman 9 pt, matching the body maths; `save()` scales each canvas until the export is exactly 7.5 cm wide, so those are true printed sizes (it refuses to save a figure with something wider than the column, e.g. a legend). Figure heights drive pagination: the 12-page layout depends on fig4 sitting before table 2 and fig5 after the first paragraph that follows table 4 in `03_results.md`. Tables are authored as pipe-tables in `tables/src/*.md` and rendered by **`render-tables.py`** (the only writer of `tables/export/`, the separate .jpg the journal wants). Since 8 Nov 2026 the .docx carries **native Word tables** read from the same `tables/src/*.md` by `journal.lua` (the drafts still reference `tableN.jpg`; the filter swaps the image for the table), so the two cannot drift. Tables are English-only — Thai text renders as empty boxes in DejaVu Sans.
- Abstract ≤ 250 words, stand-alone, no citations; keywords must not repeat title words; conclusion 1–2 paragraphs, must not restate the abstract. **Count the Thai abstract with Word** (`Range.ComputeStatistics(0)` on `manuscript/preview-word.docx`), not with a regex — Word's Thai word breaker is what the editors use; it read 356 before the 8 Oct cut and 241 after. There is no acknowledgement section (no funding source) — the build scripts list six draft files.
- Double-blind copy: `build.ps1 -Anonymous` / `preview.ps1 -Anonymous` drop the `::: author` div in `00_frontmatter.md` via `journal/templates/anonymize.lua`. Keep every identifying line inside that div.
- References: IEEE, English only, Thai sources get `(in Thai)`; every entry cited in text.
- Double-blind review by 3 external reviewers — an anonymized copy may be needed.

## Build pipeline

Two paths over the same drafts:

- **`build.ps1`** → `manuscript/submission/manuscript.docx` — single-column, pre-layout. **The file actually handed over for submission is the two-column `preview-word.docx`, saved under a new name in `manuscript/submission/`** (8 Nov: `BLEGS_KMUTNB_2026-11-08_v5.docx`; the author receives the .docx on `OneDrive\Desktop`, no PDF). pandoc with `journal/templates/reference.docx`. `journal/templates/journal.lua` (first filter in all three scripts) numbers the equations (starting at the paragraph indent, number flush right), bolds only the caption label ("ตารางที่ N" / "รูปที่ N"), swaps table images for native tables, inserts the template's blank lines (one between consecutive equations, none when a heading follows), drops the space above a level-2 heading that follows a level-1 heading, gives references a hanging indent, puts a blank line above the keywords, and maps the front-matter divs to the Title/Author/Affiliation/Corresponding styles; `patch-thai-docx.py` sets maths in Times New Roman 10 pt as the guide asks (Word renders OMML in a maths font only, so letter/digit runs become "normal text" runs in Times New Roman with italic letters and upright digits set by hand; operator-only runs stay Cambria Math so Word keeps its operator spacing; the explicit `| |` and `[ ]` delimiters are written as plain characters because Word draws them in the slant of the adjacent run) and sizes every table to one 7.5 cm column from glyph widths measured off THSarabunNew.ttf (a table whose numbers would not fit, or whose labels would wrap to 3+ lines, is set in 11 pt — the guide allows smaller table text), and adds the running footer of the published papers (rule, then `author, “title.”` in 12 pt italic, odd and even pages; text taken from the Title/Author paragraphs, title only in the -Anonymous build) — the journal template itself has no footer. `journal/templates/patch-reference-docx.py` documents and reproduces every change to reference.docx (journal header with logo and odd/even page numbers copied from the official template, regular-weight caption styles, Equation/Reference/Table styles, Thai Distribute body text) — it rebuilds the committed file byte-for-byte from the 3 Nov version, so edit the script, not the .docx. Left for Word: final figure placement and page-by-page checks. Margins 3.5/3/3/2.5 cm per `journal/instructions/template-example.pdf`.
- **`preview.ps1`** → `manuscript/preview.pdf` — journal-formatted PDF for judging length and looks while writing. pandoc → XeLaTeX with `journal/templates/preview-header.tex`; **no Word needed**, so cutting can be done entirely in Markdown. Prints the page count against the 9-page limit.

**`preview-word.ps1` renders the true two-column layout through Word** (pandoc -> Word COM
-> SaveAs2 PDF, ~5 s) and its page count is the authoritative one, because Word is the only
engine here that justifies Thai correctly (Thai Distribute). The script's header carries the
full debugging history - the short version: it is a verbatim copy of the one variant that
ran reliably; every "improved" rewrite hung inside Word at the PDF-export step (pagination
itself always instant) even though the Word calls were semantically identical, and the cause
was never isolated beyond the script text itself. Two rules are certain: `SaveAs2(…, 17)`
works where `ExportAsFixedFormat` hangs, and Word gets a fresh dir under local `%TEMP%` per
run. Treat the script as sealed: change as little as possible and test immediately after any
edit. If a run is killed mid-way, stray WINWORD.EXE processes must be killed before the next
run.

**Thai line breaking in Word needs two things, and both are handled.** (1) Office Thai
proofing must be installed on the machine (the free Thai Language Accessory Pack; done here
2026-08-23 - without it even the journal's own template renders with space-only breaks).
(2) The .docx itself must carry what native Word documents always carry: `<w:cs/>` +
`<w:lang w:bidi="th-TH"/>` on Thai runs, plus `<w:applyBreakingRules/>` and a
compatibilityMode-15 `<w:compat>` block in settings.xml. pandoc emits none of these (its
output even opens in compatibility mode 12), and no single item is enough - the full set
was isolated by A/B on rendered PDFs. `patch-thai-docx.py` applies them and both `build.ps1`
and `preview-word.ps1` run it right after pandoc, so the submission .docx lays out correctly
on any Thai-capable Word. Related permanent fixes in reference.docx: complex-script language
`ar-SA` (pandoc default) -> `th-TH`, and body text in **Thai Distribute** (8 Nov 2026; it
was `both` to copy the template's XML, but with `both` Word can only stretch spaces, so a
Thai line without any stayed ragged and short lines opened wide gaps — the guide's text
asks for Thai Distribute and the published papers look like it). References stay `both`.

The two disagree by ~2 pages (Word pads OMML equations and applies widow/orphan control). Use the PDF for the picture, the .docx for the verdict on page count.

Both drop `<mark>` placeholders silently — each script warns about how many remain.

Watch the heading syntax: an ATX heading with **no blank line above it** is not parsed as a heading, and the whole section title silently disappears into the previous paragraph in both outputs (this bit §2.2.2 in `02_methods.md`). Levels must stay consistent too — §2.1/§2.2/§2.3 are siblings and all belong at `###`.

## Measurement facts for §2.3.2 (re-shot 3 Nov 2026; the August single-run data is retired)

- Data: 5 ML-on/ML-off pairs per payload (0 kg, 3 kg), videos `D:\THESIS\Walk-Test\261103-{0,3}-kg\ML-0N/WO-0N.MP4`, metrics `../python/paper_testing/test_3/output/data/walk_video_metrics_261103_{0kg,3kg}.csv` (written by `walk_video_metrics.py`), table 4 and `figures/src/fig5_tracks.npz` from those. Each clip matches its walk_test log by end time (within 3 s).
- Runway: 14 floor tags (IDs 4–17) in 2 columns × 7 rows, 80 × 40 cm pitch, 240 cm long; world origin at tag 4, +x toward tag 5, heading 90° = +y. Camera Sony 4K 25p APS-C 20 mm, `calib_20mm_APSC_v2.npz`, every frame undistorted; camera pose (≈1.47 m high) solved from the floor tags.
- Robot back tags: 140 × 373 mm frame; positions by **ray–plane intersection at tag height** (rear 26.0 cm, front 27.5 cm — the heights at which the four tag spacings match the tape within 0.5 mm), §2.3.1 eq. (5). No homography magnification any more.
- Gait for §2.3.2: walk_test r22/r23 (stroke 50 mm, lift 25 mm, 0.44 s cycle, stance 0.70); ML gain 1.0, EMA α 0.30, slew 1 mm/tick, clamp 12 mm, right legs mirrored. Steering trim was tuned by hand **with ML on**: +40 % (pairs 1–2) / +35 % (pairs 3–5) at 0 kg, +60 % at 3 kg — compare ML on/off within a payload only. The 3 kg set uses the 0 kg levelling table on purpose (all four corners sank equally). Every 3 kg ML-off run was stopped by hand before leaving the runway.
- §2.1 is the mean of 5 gauge trials (individual readings were never written down, so no SD). §2.2.4's "5 repeats" means **5 consecutive laps inside one continuous clip**, not 5 separate trials — verified 2026-08-26 by unwrapping the tracked angle: all 24 clips contain 5.00 ± 0.03 laps.

## Known text-vs-code gaps (details + file:line in `action-plan.md`)

Still open:

1. §2.3.3's one remaining mock: the gravel spec (size and thickness) — waiting on the author. (§3.4 and table 5 carry real data since 6–8 Nov.)
2. Physical runway has a duplicate ID-6 tag standing in for ID 7 (`--duplicate-id6-mode`).
3. The affiliation names no department (guide: ภาควิชา คณะ มหาวิทยาลัย จังหวัด) — ask the author before adding one.

Closed (kept here because the reasoning is easy to re-break):

- §2.2 circle geometry — r = 30 mm and centre (0, −170), both proved from the video by unconstrained circle fitting, not assumed. Text, `calibration_coverage_check.py`, and `vision_based_trajectory_eval.py` all agree now.
- §2.2.2 counts are 152 points / 608 samples (`workspace_grid.csv` is a 19 × 8 grid at 10 mm pitch).
- §2.2.1 undistortion — the static grid capture really did run without it (the calibration filename was stale; both paths are fixed now, but the source video is gone so it cannot be re-processed). Measured from the calibration parameters over the real grid, the omission is worth 0.38 mm mean / 0.54 mm max, of which all but **0.12 mm RMS** is a common-mode shift that cancels in every difference the paper reports. Stated as a bounded limitation in §2.2.1 — do not "fix" it by re-training.
- §2.2.3 validation — `output/models/training_summary.txt` is in-sample and must never be presented as model accuracy. The real cross-condition numbers come from `../python/paper_testing/test_2/dynamic_model_evaluation.py` → `output/data/dynamic_eval.csv`, which measures the error still left at the foot with each model running in the loop across all 24 clips. The five models sit within 0.30 mm of each other, so POLY4 is deployed for engineering reasons, not accuracy.
