# Build the submission .docx from the Markdown drafts with pandoc.
# Run from anywhere:  powershell -File paper/build.ps1
#
# What pandoc does NOT handle (finish in Word afterwards — see
# manuscript/submission/SUBMISSION_CHECKLIST.md):
#   - equation numbers flushed to the column's right edge
#   - the two-column body layout (front matter stays single-column,
#     so columns are applied per-section in Word, not in reference.docx)
#   - table captions above tables / figure captions below figures
param([switch]$Anonymous)   # -Anonymous: drop the author block (double-blind copy)
$ErrorActionPreference = "Stop"
$paperDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Resolve pandoc: PATH first, then common install locations
$pandoc = $null
$cmd = Get-Command pandoc -ErrorAction SilentlyContinue
if ($cmd) { $pandoc = $cmd.Source }
if (-not $pandoc) {
    $candidates = @(
        "$env:LOCALAPPDATA\Pandoc\pandoc.exe",
        "$env:ProgramFiles\Pandoc\pandoc.exe",
        "$env:USERPROFILE\miniconda3\Library\bin\pandoc.exe",
        "$env:USERPROFILE\miniconda3\Scripts\pandoc.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $pandoc = $c; break } }
}
if (-not $pandoc) {
    Write-Error "pandoc not found. Install with: winget install --id JohnMacFarlane.Pandoc"
}

$reference = Join-Path $paperDir "journal\templates\reference.docx"
if (-not (Test-Path $reference)) {
    Write-Error "reference.docx not found at $reference (see paper/journal/README.md)"
}

$drafts = @(
    "00_frontmatter.md", "01_introduction.md", "02_methods.md",
    "03_results.md", "04_discussion.md",
    "06_references.md"
) | ForEach-Object { Join-Path $paperDir "manuscript\drafts\$_" }

$out = Join-Path $paperDir "manuscript\submission\manuscript.docx"

# Build the resource path into a variable first.  Written inline as
# --resource-path=(Join-Path ...), PowerShell splits it into TWO arguments -
# an empty --resource-path= plus a bare path that pandoc then treats as an
# input file and fails on ("withBinaryFile: permission denied").
$resourcePath = (Join-Path $paperDir "figures\export") + ";" + (Join-Path $paperDir "tables\export")

# Warn about <mark> placeholders: pandoc drops raw HTML silently in docx
# output, so unresolved figure/value placeholders would vanish without trace.
$marks = Select-String -Path $drafts -Pattern "<mark>" -SimpleMatch
if ($marks) {
    Write-Warning ("{0} <mark> placeholders still present - they will NOT appear in the .docx:" -f $marks.Count)
    $marks | Group-Object Path | ForEach-Object { Write-Warning ("  {0}: {1}" -f (Split-Path -Leaf $_.Name), $_.Count) }
}

$mockFilter = Join-Path $paperDir "journal\templates\mock.lua"
$journalFilter = Join-Path $paperDir "journal\templates\journal.lua"
$anonFilter = Join-Path $paperDir "journal\templates\anonymize.lua"
$anonMeta = if ($Anonymous) { "anonymous=true" } else { "anonymous=false" }
& $pandoc @drafts `
    --reference-doc=$reference `
    --lua-filter=$journalFilter `
    --lua-filter=$mockFilter `
    --lua-filter=$anonFilter -M $anonMeta `
    --resource-path=$resourcePath `
    -o $out
if ($LASTEXITCODE -ne 0) { Write-Error "pandoc failed ($LASTEXITCODE)" }

# Without this, Word wraps the Thai text at spaces only and hard-breaks
# mid-word at the margin (see the header of patch-thai-docx.py): the patch
# adds the run tags and settings flags that native Word documents carry, so
# the submission lays out correctly on any Word with Thai proofing installed.
& python (Join-Path $paperDir "patch-thai-docx.py") $out
if ($LASTEXITCODE -ne 0) { Write-Error "patch-thai-docx failed ($LASTEXITCODE)" }
Write-Host "Wrote $out"
