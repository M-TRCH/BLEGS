# Render the drafts to PDF *through Word*, in the journal's two-column layout.
# Run from anywhere:  powershell -File paper/preview-word.ps1
#
# Why this exists alongside preview.ps1 (pandoc -> XeLaTeX): Thai justification.
# Thai has no inter-word spaces, so justified Thai must be distributed between
# characters.  Word does that via Thai Distribute (set on Body Text in
# reference.docx); XeTeX cannot, so the LaTeX preview only approximates the
# printed line breaks.  This PDF comes from the same engine that lays out the
# submitted file, so its page count is the authoritative one.
#
# HISTORY - read before "improving" this script.  This text is a verbatim copy
# of the one variant that completed reliably (3/3, ~5 s end to end) after an
# evening in which every rewritten variant hung inside Word (8/8, always at the
# PDF export step, with pagination itself instant).  Ruled out one by one:
# zombie WINWORD instances, OneDrive sync, wide tables, image sizes, column
# widths, word-count statistics, output piping, stale work-dir locks, and the
# script's own location.  The surviving correlation was the script text itself:
# additions as innocuous as a Get-Process pre-flight and a Select-String block
# preceded every hang.  Two rules are load-bearing for certain: use SaveAs2
# (17), never ExportAsFixedFormat, and let Word work in local temp.  Beyond
# that: change as little as possible, and test any change immediately.
# THAI LINE BREAKING - two prerequisites, both in place since 2026-08-23:
# (1) the machine needs Office Thai proofing (the free Thai Language Accessory
# Pack - installed here); (2) the docx itself must carry the run tags and
# settings flags native Word documents have, which pandoc omits - added by
# patch-thai-docx.py in the pipeline below.  Missing either one makes Word
# wrap Thai at spaces only and hard-break mid-word at the margin.
$ErrorActionPreference = "Stop"
function Step($m) { Write-Output ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $m) }

$paperDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$work = Join-Path $env:TEMP ("blegs-word-{0:yyyyMMdd-HHmmss}" -f (Get-Date))
New-Item -ItemType Directory -Force -Path $work | Out-Null

$names = @("00_frontmatter.md","01_introduction.md","02_methods.md","03_results.md",
           "04_discussion.md","06_references.md")
$enc = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("$work\_marker.md", "BODYSTARTMARKER`n", $enc)
$inputs = @()
foreach ($n in $names) {
    # two-column body starts at "1. บทนำ" (journal FORMAT_GUIDE section 4); pages 1-2 stay single-column
    if ($n -eq "01_introduction.md") { $inputs += "$work\_marker.md" }
    $inputs += (Join-Path $paperDir "manuscript\drafts\$n")
}
$resourcePath = (Join-Path $paperDir "figures\export") + ";" + (Join-Path $paperDir "tables\export")

Step "pandoc..."
& pandoc @inputs --reference-doc="$paperDir\journal\templates\reference.docx" `
    --lua-filter="$paperDir\journal\templates\mock.lua" `
    --lua-filter="$paperDir\journal\templates\anonymize.lua" -M anonymous=false `
    --resource-path=$resourcePath -o "$work\preview.docx"
if ($LASTEXITCODE -ne 0) { throw "pandoc failed" }

Step "patch Thai line breaking..."
& python "$paperDir\patch-thai-docx.py" "$work\preview.docx"
if ($LASTEXITCODE -ne 0) { throw "patch-thai-docx failed" }

$CM = 28.3464567
Step "New Word (clean state)"
$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
$doc = $word.Documents.Open("$work\preview.docx", $false, $false)
Step ("opened; paragraphs={0} shapes={1}" -f $doc.Paragraphs.Count, $doc.InlineShapes.Count)
try {
    $rng = $doc.Content; $f = $rng.Find
    $f.Text = "BODYSTARTMARKER"; $f.Forward = $true; $f.MatchCase = $true
    if (-not $f.Execute()) { throw "marker not found" }
    $pr = $rng.Paragraphs.Item(1).Range
    $start = $pr.Start
    $pr.Delete() | Out-Null
    $doc.Range($start, $start).InsertBreak(3) | Out-Null
    Step ("section break in; sections={0}" -f $doc.Sections.Count)

    foreach ($s in $doc.Sections) {
        $ps = $s.PageSetup
        $ps.TopMargin = 3.0*$CM; $ps.BottomMargin = 3.0*$CM
        $ps.LeftMargin = 2.5*$CM; $ps.RightMargin = 2.5*$CM
    }
    Step "margins set"

    $tc = $doc.Sections.Item($doc.Sections.Count).PageSetup.TextColumns
    $tc.SetCount(2); $tc.EvenlySpaced = $true; $tc.Spacing = 0.5*$CM
    Step "columns set"

    Step "paginate (ComputeStatistics)..."
    $pages = $doc.ComputeStatistics(2)
    Step ("pages={0}" -f $pages)

    Step "SaveAs2 -> PDF..."
    $doc.SaveAs2("$work\preview.pdf", 17)
    Step "PDF saved"

    Step "SaveAs2 -> laid-out docx..."
    $doc.SaveAs2("$work\laid-out.docx", 12)
    Step "docx saved"
} finally {
    try { $doc.Close(0) } catch {}
    try { $word.Quit() } catch {}
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}

Copy-Item "$work\preview.pdf" (Join-Path $paperDir "manuscript\preview-word.pdf") -Force
# the Word source of that PDF - two-column layout already applied; use it as
# the starting point for hand-finishing (equations flush right, captions, ...)
Copy-Item "$work\laid-out.docx" (Join-Path $paperDir "manuscript\preview-word.docx") -Force
Step ("done; PDF {0} KB, {1} pages (journal limit: 9)" -f ([math]::Round((Get-Item "$work\preview.pdf").Length/1KB)), $pages)
Step "Word source of the PDF: manuscript\preview-word.docx"
