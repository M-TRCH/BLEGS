# Render the Markdown drafts to a formatted PDF for on-screen review.
# Run from anywhere:  powershell -File paper/preview.ps1
#
# This is the PREVIEW path (pandoc -> XeLaTeX -> PDF).  It needs no Word, so
# you can write and cut in Markdown and watch the page count all day.  It is
# NOT the submission path: the journal requires .docx, so the file you actually
# send still comes from build.ps1 and gets finished in Word.
#
# The two disagree slightly on length - Word pads OMML equations and applies
# widow/orphan control - so treat this PDF as the picture and build.ps1's .docx
# as the authority on "are we under 9 pages yet".
#
# Format rules live in journal/templates/preview-header.tex, all traceable to
# journal/FORMAT_GUIDE.md.
param([switch]$Anonymous)   # -Anonymous: drop the author block (double-blind copy)
$ErrorActionPreference = "Stop"
$paperDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Resolve pandoc: PATH first, then common install locations --------------
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

# --- Resolve xelatex (MiKTeX here; TeX Live works too) ----------------------
$xelatex = $null
$cmd = Get-Command xelatex -ErrorAction SilentlyContinue
if ($cmd) { $xelatex = $cmd.Source }
if (-not $xelatex) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\xelatex.exe",
        "$env:ProgramFiles\MiKTeX\miktex\bin\x64\xelatex.exe"
    )
    $candidates += (Get-ChildItem "C:\texlive\*\bin\*\xelatex.exe" -ErrorAction SilentlyContinue |
                    ForEach-Object { $_.FullName })
    foreach ($c in $candidates) { if (Test-Path $c) { $xelatex = $c; break } }
}
if (-not $xelatex) {
    Write-Error "xelatex not found. Install MiKTeX: winget install --id MiKTeX.MiKTeX"
}

$header = Join-Path $paperDir "journal\templates\preview-header.tex"
if (-not (Test-Path $header)) { Write-Error "preview-header.tex not found at $header" }
# Placeholder ("mock") spans/divs are coloured rather than dropped - see mock.lua.
$mockFilter = Join-Path $paperDir "journal\templates\mock.lua"
$journalFilter = Join-Path $paperDir "journal\templates\journal.lua"
$anonFilter = Join-Path $paperDir "journal\templates\anonymize.lua"
$anonMeta = if ($Anonymous) { "anonymous=true" } else { "anonymous=false" }

$names = @(
    "00_frontmatter.md", "01_introduction.md", "02_methods.md",
    "03_results.md", "04_discussion.md",
    "06_references.md"
)
$drafts = $names | ForEach-Object { Join-Path $paperDir "manuscript\drafts\$_" }
$out    = Join-Path $paperDir "manuscript\preview.pdf"
$work   = Join-Path $paperDir ".preview"

# Figures are referenced by bare filename; they live here (same as build.ps1).
# Built into a variable first - PowerShell splits --flag=(expr) into two args.
$resourcePath = (Join-Path $paperDir "figures\export") + ";" + (Join-Path $paperDir "tables\export")

# Same warning build.ps1 gives: pandoc drops raw HTML, so unresolved figure and
# value placeholders vanish from the output without a trace.
$marks = Select-String -Path $drafts -Pattern "<mark>" -SimpleMatch
if ($marks) {
    Write-Warning ("{0} <mark> placeholders still present - they will NOT appear in the PDF:" -f $marks.Count)
    $marks | Group-Object Path | ForEach-Object { Write-Warning ("  {0}: {1}" -f (Split-Path -Leaf $_.Name), $_.Count) }
}

# --- Staged copies of the drafts -------------------------------------------
# The drafts indent paragraphs with the HTML entity &emsp; (U+2003), which
# TH Sarabun New has no glyph for.  Strip it here and let \parindent in
# preview-header.tex do the indenting.  The drafts themselves are not touched.
$stage = Join-Path $work "drafts"
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$staged = @()
foreach ($n in $names) {
    $src = Join-Path $paperDir "manuscript\drafts\$n"
    $dst = Join-Path $stage $n
    $text = [System.IO.File]::ReadAllText($src)
    [System.IO.File]::WriteAllText($dst, $text.Replace("&emsp;", ""), $utf8NoBom)
    $staged += $dst
}

# --- Markdown -> standalone LaTeX ------------------------------------------
# Page setup per FORMAT_GUIDE.md s.2 (margins) and s.3 (TH Sarabun New 14 pt).
# There is no 14 pt article class, so the base is 12 pt scaled by 14/12
# = 1.16667.  Note the guide is internally inconsistent here: 2.5 cm side
# margins leave 16 cm of text, which splits into 7.75 cm columns rather than
# the 7.5 cm the same guide asks for.  The journal's own .docx template uses
# left 3.0 / right 2.5 cm, which gives exactly 7.5 + 0.5 + 7.5.  This script
# follows the guide; change $sideMargin to 3cm/2.5cm to follow the template.
$tex = Join-Path $work "preview.tex"
& $pandoc @staged `
    --standalone `
    --to=latex `
    -H $header `
    --lua-filter=$journalFilter `
    --lua-filter=$mockFilter `
    --lua-filter=$anonFilter -M $anonMeta `
    -V documentclass=article `
    -V classoption=twocolumn `
    -V classoption=12pt `
    -V geometry:a4paper `
    -V geometry:top=3cm `
    -V geometry:bottom=3cm `
    -V geometry:left=2.5cm `
    -V geometry:right=2.5cm `
    -V mainfont="TH Sarabun New" `
    -V mainfontoptions="Scale=1.16667" `
    --resource-path=$resourcePath `
    -o $tex
if ($LASTEXITCODE -ne 0) { Write-Error "pandoc failed ($LASTEXITCODE)" }

# --- LaTeX -> PDF ----------------------------------------------------------
# pandoc's --resource-path only governs pandoc's own lookups; it writes bare
# \includegraphics{fig1.jpg} and xelatex then resolves that itself.  Copy the
# figures next to the .tex so xelatex finds them without a machine-specific
# \graphicspath.
foreach ($dir in ($resourcePath -split ';')) {
    if (Test-Path $dir) {
        Get-ChildItem -Path $dir -Include *.jpg, *.jpeg, *.png, *.pdf -File -Recurse |
            ForEach-Object { Copy-Item $_.FullName -Destination $work -Force }
    }
}

# Compiled here rather than through --pdf-engine so the .log survives; it is
# where the page count comes from, and where to look when a build breaks.
$xeArgs = @("-interaction=nonstopmode", "-halt-on-error", "-output-directory=$work")
if ($xelatex -match "MiKTeX") { $xeArgs += "--enable-installer" }
$xeArgs += $tex

# Twice, so any forward references settle.
foreach ($pass in 1, 2) {
    $null = & $xelatex @xeArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error ("xelatex failed on pass {0} ({1}). See {2}" -f $pass, $LASTEXITCODE, (Join-Path $work "preview.log"))
    }
}

$pdf = Join-Path $work "preview.pdf"
if (-not (Test-Path $pdf)) { Write-Error "xelatex produced no PDF; see $work\preview.log" }
Copy-Item $pdf $out -Force

# --- Report ----------------------------------------------------------------
$pages = "?"
$log = Join-Path $work "preview.log"
if (Test-Path $log) {
    # TeX hard-wraps the log at 79 columns, so "Output written on <long path>
    # (N pages)." is split across lines - unwrap before matching.
    $flat = [System.IO.File]::ReadAllText($log) -replace "\r?\n", ""
    $m = [regex]::Match($flat, "Output written on .*?\((\d+) pages")
    if ($m.Success) { $pages = $m.Groups[1].Value }
}
Write-Host ("Wrote {0}" -f $out)
Write-Host ("Pages: {0}  (journal limit: 9)" -f $pages)
if ($pages -ne "?" -and [int]$pages -gt 9) {
    Write-Warning ("Over the 9-page limit by {0}. Check build.ps1's .docx for the authoritative count." -f ([int]$pages - 9))
}
