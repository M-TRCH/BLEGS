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
- Figure/table placeholders: `<mark>[แทรก รูปที่ N: caption]</mark>`; undecided values: `<mark>[รอกำหนด...]</mark>`. **pandoc silently drops `<mark>` (raw HTML) in docx output** — `build.ps1` warns about remaining ones.
- Captions must not use the word "แสดง" (journal rule).

**Chapter 2 is methods**: it defines procedures and metrics but must not report measured values or conclusions. Defer numbers with "รายงานในบทผลการทดลอง" / "นำเสนอในบทถัดไป" as §2.2.1 and §2.3.2 already do. Equipment specs (marker sizes, camera resolution) are fine in methods; results are not.

## Journal rules that shape the work

Full set: `journal/FORMAT_GUIDE.md` and the official docs in `journal/instructions/`. The ones that bite:

- **≤ 9 A4 pages total** on paper, two columns, TH Sarabun New — but the author has confirmed up to **12** is acceptable. As of 2026-08-26 the Word build measures **12**, i.e. the ceiling, with §3.4 still unwritten. Anything added from here needs something else cut.
- **Every figure AND table must also be submitted as a separate .jpg** → `figures/export/`, `tables/export/`. Tables are authored as pipe-tables in `tables/src/*.md` and rendered by **`render-tables.py`** (the only writer of `tables/export/`); the manuscript embeds the same .jpg, so a table can never drift from its picture. Tables are English-only — Thai text renders as empty boxes in DejaVu Sans.
- Abstract ≤ 250 words, stand-alone, no citations; keywords must not repeat title words; conclusion 1–2 paragraphs, must not restate the abstract.
- References: IEEE, English only, Thai sources get `(in Thai)`; every entry cited in text.
- Double-blind review by 3 external reviewers — an anonymized copy may be needed.

## Build pipeline

Two paths over the same drafts:

- **`build.ps1`** → `manuscript/submission/manuscript.docx` — the submission. pandoc with `journal/templates/reference.docx`. What pandoc cannot do (finish in Word): equation numbers flush right, per-section column layout, caption placement. reference.docx rules — incl. the Thai-font trap (`w:cs`/`w:szCs`) — are in `journal/README.md`.
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
`ar-SA` (pandoc default) -> `th-TH`, and body justification matches the journal template's
plain `both` instead of `thaiDistribute`.

The two disagree by ~2 pages (Word pads OMML equations and applies widow/orphan control). Use the PDF for the picture, the .docx for the verdict on page count.

Both drop `<mark>` placeholders silently — each script warns about how many remain.

Watch the heading syntax: an ATX heading with **no blank line above it** is not parsed as a heading, and the whole section title silently disappears into the previous paragraph in both outputs (this bit §2.2.2 in `02_methods.md`). Levels must stay consistent too — §2.1/§2.2/§2.3 are siblings and all belong at `###`.

## Measurement facts for §2.3 (verified from the four walk videos)

- Runway frame: X = 0–80 cm across (centreline 40), Y = 0–120 cm along; heading 90° = along +Y. Analysis: `../python/paper_testing/test_3/apriltag_runway_tilt_check.py` (writes `<video>_pose.csv`; videos on `D:\THESIS\walk_test\`).
- Robot back tags: **19.9 × 46.6 cm** tape-measured (`ROBOT_TAG_LOCAL_POINTS_CM`).
- **Parallax**: runway markers lie on the floor, robot tags ride ~31 cm above it → homography magnifies distances by m ≈ 1.21–1.22 (consistent across all four videos; camera ≈ 1.8 m). Divide distances by m; angles unaffected. §2.3.1 eq. (16)–(17). Raising runway markers to tag height removes the effect for future recordings.
- Robot walks ~2 m but the grid covers 120 cm → about half of each track is extrapolated (tag-rectangle self-check shows the mapping holds; report the proportion).
- §2.3.2 has **one recorded run per condition** — the weakest evidence in the paper, and limitation 1 in chapter 4. §2.1 is the mean of 5 gauge trials (individual readings were never written down, so no SD). §2.2.4's "5 repeats" means **5 consecutive laps inside one continuous clip**, not 5 separate trials — verified 2026-08-26 by unwrapping the tracked angle: all 24 clips contain 5.00 ± 0.03 laps.

## Known text-vs-code gaps (details + file:line in `action-plan.md`)

Still open:

1. **The §2.3.3 experiment itself** — §3.4 is empty and the paper promises a capability matrix. This is the only thing still blocking submission on the data side.
2. Physical runway has a duplicate ID-6 tag standing in for ID 7 (`--duplicate-id6-mode`).
3. §2.3.3's remaining `<mark>`: test distance $L$, ramp-angle steps, and the compliant/rough surface specs. $L$ is constrained by the power tether — see action-plan item 3.1.ข.

Closed (kept here because the reasoning is easy to re-break):

- §2.2 circle geometry — r = 30 mm and centre (0, −170), both proved from the video by unconstrained circle fitting, not assumed. Text, `calibration_coverage_check.py`, and `vision_based_trajectory_eval.py` all agree now.
- §2.2.2 counts are 152 points / 608 samples (`workspace_grid.csv` is a 19 × 8 grid at 10 mm pitch).
- §2.2.1 undistortion — the static grid capture really did run without it (the calibration filename was stale; both paths are fixed now, but the source video is gone so it cannot be re-processed). Measured from the calibration parameters over the real grid, the omission is worth 0.38 mm mean / 0.54 mm max, of which all but **0.12 mm RMS** is a common-mode shift that cancels in every difference the paper reports. Stated as a bounded limitation in §2.2.1 — do not "fix" it by re-training.
- §2.2.3 validation — `output/models/training_summary.txt` is in-sample and must never be presented as model accuracy. The real cross-condition numbers come from `../python/paper_testing/test_2/dynamic_model_evaluation.py` → `output/data/dynamic_eval.csv`, which measures the error still left at the foot with each model running in the loop across all 24 clips. The five models sit within 0.30 mm of each other, so POLY4 is deployed for engineering reasons, not accuracy.
