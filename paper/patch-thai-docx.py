"""Make a pandoc-produced .docx break Thai lines correctly in Word.

Usage:  python patch-thai-docx.py <file.docx>          (patches in place)

Why this exists (verified by A/B on 2026-08-23, this machine, Office 2024 +
Thai proofing pack): Word only engages its Thai dictionary word-breaker for a
document that carries what native Word documents always carry -

  document.xml   <w:cs/> + <w:lang w:bidi="th-TH"/> on every Thai run
  settings.xml   <w:applyBreakingRules/> and a <w:compat> block whose
                 compatibilityMode is 15

pandoc emits none of these (and strips them from reference.docx), so its
output opens in compatibility mode 12 with untagged runs, and Word then wraps
Thai at spaces only, hard-breaking mid-word at the margin.  No single item is
enough: runs-only and settings-only variants both stayed broken; the full set
fixed it.  The minimal subset was not isolated - this applies exactly what
native Word writes.

It also sets equations to 10 pt and (since 8 Nov 2026, when tables became
native Word tables) fixes every table to one 7.5 cm journal column, and adds
the running footer the published papers carry (rule + authors, "title." in
italic) - the journal's template has no footer part, so pandoc gets none.

Stdlib only, so the plain PATH python works.
"""
import html
import io
import re
import sys
import zipfile

THAI = re.compile('[฀-๿]')
CS_LANG = '<w:cs/><w:lang w:bidi="th-TH"/>'
COMPAT = (
    '<w:compat>'
    '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
    '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="differentiateMultirowTableHeaders" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="useWord2013TrackBottomHyphenation" w:uri="http://schemas.microsoft.com/office/word" w:val="0"/>'
    '</w:compat>'
)


def patch_document(xml: str) -> str:
    tagged = [0]

    def tag_run(m):
        run = m.group(0)
        if not THAI.search(run) or '<w:cs/>' in run:
            return run
        tagged[0] += 1
        if '<w:rPr>' in run:
            return run.replace('<w:rPr>', '<w:rPr>' + CS_LANG, 1)
        return re.sub(r'(<w:r(?: [^>]*)?>)', r'\1<w:rPr>' + CS_LANG + '</w:rPr>',
                      run, count=1)

    out = re.sub(r'<w:r(?: [^>]*)?>.*?</w:r>', tag_run, xml, flags=re.S)
    print(f'  document.xml: {tagged[0]} Thai runs tagged cs + th-TH')

    out = times_math(out)
    out = size_tables(out)
    return out


# The guide: variables and symbols in Times New Roman 10 pt (the published
# papers comply: Times New Roman italic 10 in text and equations, no Cambria
# Math anywhere).  Word only lets a maths font (Cambria Math) render OMML runs
# in maths style, so a run that should look like Times is switched to "normal
# text" (m:nor) with Times New Roman and its italic/bold set by hand from the
# run's maths style.  Runs that hold only operators, brackets and punctuation
# stay maths-style: Word spaces binary operators only for those, and its glyphs
# for them match Times closely.  Checked on the rendered PDF, 8 Nov 2026.
MATH_OPS = set('=+-−×,.;:()[]|∈∫⊤&      ')
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
SZ10 = '<w:sz w:val="20"/><w:szCs w:val="20"/>'


def _math_run(m):
    run = m.group(0)
    mr = re.search(r'<m:rPr>(.*?)</m:rPr>', run, re.S)
    mrp = mr.group(1) if mr else ''
    text = ''.join(re.findall(r'<m:t(?: [^>]*)?>([^<]*)</m:t>', run))
    body = re.sub(r'<m:rPr>.*?</m:rPr>|<w:rPr>.*?</w:rPr>', '', run, flags=re.S)
    if text and all(c in MATH_OPS for c in text.replace('&amp;', '&')):
        rpr = '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>' + SZ10 + '</w:rPr>'
        return body.replace('<m:r>', '<m:r>' + (mr.group(0) if mr else '') + rpr, 1)
    sty = re.search(r'm:sty m:val="(\w+)"', mrp)
    sty = sty.group(1) if sty else ('p' if '<m:nor/>' in mrp else 'i')
    bold = '<w:b/><w:bCs/>' if 'b' in sty else ''
    if sty not in ('i', 'bi'):
        return _tnr_run(text, bold, False)
    # maths style sets letters italic but digits upright on its own; normal
    # text does neither, so split the run: letters italic, the rest upright
    return ''.join(_tnr_run(seg, bold, bool(re.match("[%s]" % _LETTERS, seg)))
                   for seg in re.findall(r'[%s]+|[^%s]+' % (_LETTERS, _LETTERS),
                                         html.unescape(text)))


_LETTERS = 'A-Za-zΑ-Ωα-ωϑϕϵ'


def _tnr_run(text: str, bold: str, italic: bool) -> str:
    esc = html.escape(html.unescape(text), quote=False)
    return ('<m:r><m:rPr><m:nor/></m:rPr><w:rPr>' + TNR + bold
            + ('<w:i/><w:iCs/>' if italic else '') + SZ10
            + '</w:rPr><m:t xml:space="preserve">' + esc + '</m:t></m:r>')


def _unwrap_delims(xml: str) -> str:
    """A delimiter pair with an explicit | or [ is drawn in the style of the
    run next to it, so beside a Times italic run it comes out slanted.  Neither
    pair in the paper has to stretch (one-line contents: a subscript, a 1x3
    row vector), so write them as plain upright Times characters.  The big
    parentheses of eq. 3 start with an upright "(" run and are left alone."""
    def unwrap(m):
        beg, end, inner = m.group(1), m.group(2), m.group(3)
        if beg not in '|[' or re.search(r'<m:(?:d|f|eqArr|rad|nary)>', inner) \
                or inner.count('<m:mr>') > 1:
            return m.group(0)
        ch = lambda c: _tnr_run(c, '', False)
        return ch(beg) + inner + ch(end)
    pat = (r'<m:d><m:dPr>(?:(?!</m:dPr>).)*?<m:begChr m:val="([^"]*)"\s*/>'
           r'(?:(?!</m:dPr>).)*?<m:endChr m:val="([^"]*)"\s*/>'
           r'(?:(?!</m:dPr>).)*?</m:dPr><m:e>((?:(?!<m:d>).)*?)</m:e></m:d>')
    return re.sub(pat, unwrap, xml, flags=re.S)


def times_math(xml: str) -> str:
    out = _unwrap_delims(xml)
    out, n = re.subn(r'<m:r>.*?</m:r>', _math_run, out, flags=re.S)
    print(f'  document.xml: {n} maths runs set to Times New Roman 10 pt '
          '(operators stay Cambria Math for spacing)')
    return out


COLUMN_TW = 4252   # one journal column, 7.5 cm, in twips
CELL_PAD_TW = 175  # left + right cell margin (2 x 57) and the slack Word keeps

# Advance widths in twips at 12 pt, measured from THSarabunNew.ttf / Bold.ttf
# with Pillow (8 Nov 2026) for ' '..'~' then U+2212 U+00B1 U+00B0 U+2013
# U+2014 U+00D7 U+00B7.  OMML characters (Cambria Math 10 pt) average 106.
_GLYPHS = ''.join(chr(c) for c in range(32, 127)) + '−±°–—×·'
_W_REG = [52, 35, 50, 97, 87, 140, 102, 29, 46, 46, 68, 99, 39, 52, 39, 65, 87, 87, 87, 87, 87, 87,
          87, 87, 87, 87, 39, 39, 99, 99, 99, 68, 129, 96, 91, 97, 103, 84, 84, 102, 106, 35, 63, 90,
          85, 132, 106, 117, 91, 117, 91, 84, 91, 112, 94, 141, 100, 88, 102, 47, 63, 47, 99, 84, 49,
          83, 96, 79, 96, 90, 49, 75, 94, 34, 37, 76, 48, 144, 94, 96, 96, 96, 52, 68, 57, 94, 82,
          122, 76, 81, 77, 50, 37, 50, 100, 99, 99, 51, 86, 173, 99, 39]
_W_BOLD = [54, 40, 70, 111, 88, 165, 117, 41, 59, 59, 82, 100, 41, 54, 41, 66, 91, 91, 91, 91, 91, 91,
           91, 91, 91, 91, 41, 41, 100, 100, 100, 69, 137, 108, 95, 104, 110, 86, 86, 109, 113, 39, 68,
           99, 86, 138, 113, 124, 94, 124, 95, 88, 101, 116, 101, 147, 102, 95, 108, 56, 64, 56, 100,
           90, 50, 88, 104, 83, 104, 94, 61, 80, 102, 39, 41, 82, 51, 153, 102, 99, 103, 103, 59, 71,
           62, 100, 86, 115, 84, 87, 86, 61, 42, 61, 101, 100, 106, 66, 80, 166, 100, 41]
_REG = dict(zip(_GLYPHS, _W_REG))
_BOLD = dict(zip(_GLYPHS, _W_BOLD))


def _cell_tokens(cell: str, bold: bool):
    """(width, is_space) per character of one table cell."""
    table = _BOLD if bold else _REG
    out = []
    for m in re.finditer(r'<(w|m):t(?: [^>]*)?>([^<]*)</(?:w|m):t>', cell):
        for ch in m.group(2):
            w = 106.0 if m.group(1) == 'm' else float(table.get(ch, 100))
            out.append((w, ch == ' ' and m.group(1) == 'w'))
    return out


def size_tables(xml: str) -> str:
    """Native tables (journal.lua) come out of pandoc 'auto' wide with equal
    grid columns that add up to more than a column.  Fix each one to exactly
    one column (7.5 cm): every column gets the width of its longest cell text;
    if that is too wide in total, the first (label) column - the only one whose
    text is words that can wrap - gives up the difference, never below its
    longest word.  If the numeric columns still do not fit, the table is set
    in 11 pt (the guide allows smaller table text if it stays legible) and
    sized again; spare width is shared out in proportion."""
    count = [0]

    def fix(m):
        t = m.group(0)
        ncol = len(re.findall(r'<w:gridCol ', t))
        if ncol == 0:
            return t
        full = [0.0] * ncol     # widest cell text per column
        word = [0.0] * ncol     # widest unbreakable word per column
        for r, row in enumerate(re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S)):
            for j, cell in enumerate(re.findall(r'<w:tc>.*?</w:tc>', row, re.S)[:ncol]):
                toks = _cell_tokens(cell, bold=(r == 0))   # header row is bold
                run = longest = 0.0
                for w, sp in toks + [(0.0, True)]:
                    if sp:
                        longest = max(longest, run)
                        run = 0.0
                    else:
                        run += w
                word[j] = max(word[j], longest)
                # a header may wrap between its words; body cells should not
                full[j] = max(full[j], longest if r == 0 else sum(w for w, _ in toks))
        scale = 1.0
        if word[0] + sum(full[1:]) + ncol * CELL_PAD_TW > COLUMN_TW:
            scale = 11.0 / 12.0      # the numbers do not fit at 12 pt
        elif COLUMN_TW - sum(full[1:]) - (ncol - 1) * CELL_PAD_TW < 0.55 * (full[0] + CELL_PAD_TW):
            scale = 11.0 / 12.0      # they fit, but the labels would wrap to 3+ lines
        want = [scale * f + CELL_PAD_TW for f in full]
        excess = sum(want) - COLUMN_TW
        if excess > 0:
            give = min(excess, want[0] - (scale * word[0] + CELL_PAD_TW))
            want[0] -= give
            excess -= give
            if excess > 0:   # still too wide: shrink every column alike
                total = sum(want)
                want = [w - excess * w / total for w in want]
        widths = [int(COLUMN_TW * w / sum(want)) for w in want]
        widths[-1] += COLUMN_TW - sum(widths)
        if scale < 1.0:
            sz = '<w:sz w:val="22"/><w:szCs w:val="22"/>'
            t = re.sub(r'(<w:r>)(?!<w:rPr>)', r'\1<w:rPr>' + sz + '</w:rPr>', t)
            t = re.sub(r'(<w:r><w:rPr>)(?!' + re.escape(sz) + ')', r'\1' + sz, t)
        t = re.sub(r'<w:tblW [^>]*/>',
                   f'<w:tblW w:type="dxa" w:w="{COLUMN_TW}"/><w:tblLayout w:type="fixed"/>', t, count=1)
        t = re.sub(r'<w:tblGrid>.*?</w:tblGrid>',
                   '<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>',
                   t, count=1, flags=re.S)

        def fix_row(rm):
            k = [0]

            def tcw(_):
                w = widths[min(k[0], ncol - 1)]
                k[0] += 1
                return f'<w:tcPr><w:tcW w:w="{w}" w:type="dxa"/></w:tcPr>'
            return re.sub(r'<w:tcPr ?/>', tcw, rm.group(0))
        t = re.sub(r'<w:tr[ >].*?</w:tr>', fix_row, t, flags=re.S)
        count[0] += 1
        return t

    out = re.sub(r'<w:tbl>.*?</w:tbl>', fix, xml, flags=re.S)
    if count[0]:
        print(f'  document.xml: {count[0]} tables fixed to one column (7.5 cm)')
    return out


def patch_settings(xml: str) -> str:
    out = re.sub(r'<w:compat>.*?</w:compat>', '', xml, flags=re.S)
    flags = ('<w:applyBreakingRules/>' if 'applyBreakingRules' not in out else '') + COMPAT
    # schema order: both belong before w:rsids / w:themeFontLang
    for anchor in ('<w:rsids>', '<w:themeFontLang', '</w:settings>'):
        i = out.find(anchor)
        if i != -1:
            out = out[:i] + flags + out[i:]
            break
    print('  settings.xml: applyBreakingRules + compatibilityMode 15')
    return out


W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
FOOTER_REL = R_NS + '/footer'
FOOTER_CT = 'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml'


def _para_text(xml: str, style: str) -> str:
    """Text of the first paragraph in `style`, superscripts (the * marks) dropped."""
    m = re.search(r'<w:p\b(?:(?!</w:p>).)*?<w:pStyle w:val="%s"\s*/>.*?</w:p>' % style, xml, re.S)
    if not m:
        return ''
    runs = [r for r in re.findall(r'<w:r\b.*?</w:r>', m.group(0), re.S)
            if '<w:vertAlign w:val="superscript"' not in r]
    text = ''.join(''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', r)) for r in runs)
    return re.sub(r'\s+', ' ', text).strip()


def footer_text(doc_xml: str) -> str:
    """The running footer of the published papers: <authors>, "<title>."  -
    'A และ B' for two authors, 'A และคณะ' for three or more.  The -Anonymous
    build has no Author paragraph, so the footer is then the title alone."""
    title = _para_text(doc_xml, 'Title')
    authors = [a.strip() for a in re.split(r',| และ ', _para_text(doc_xml, 'Author')) if a.strip()]
    if len(authors) > 2:
        who = authors[0] + ' และคณะ'
    else:
        who = ' และ '.join(authors)
    quoted = '“%s.”' % title.rstrip('.')
    return (who + ', ' + quoted) if who else quoted


def footer_part(text: str) -> bytes:
    """Rule across the text width, then the line in 12 pt italic, flush left -
    as on pages 3+ of every published TCI-1 paper checked (8 Nov 2026)."""
    esc = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    rpr = ('<w:rPr><w:rFonts w:ascii="TH Sarabun New" w:hAnsi="TH Sarabun New" '
           'w:eastAsia="TH Sarabun New" w:cs="TH Sarabun New"/><w:i/><w:iCs/>'
           '<w:sz w:val="24"/><w:szCs w:val="24"/>' + CS_LANG + '</w:rPr>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:ftr xmlns:w="%s" xmlns:r="%s"><w:p><w:pPr>'
            '<w:pBdr><w:top w:val="single" w:sz="6" w:space="4" w:color="000000"/></w:pBdr>'
            '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '<w:ind w:left="0" w:right="0" w:firstLine="0"/><w:jc w:val="left"/>%s</w:pPr>'
            '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p></w:ftr>'
            % (W_NS, R_NS, rpr, rpr, esc)).encode('utf-8')


def add_footer(parts: dict) -> None:
    """The journal's template has no footer; the published papers all have one
    (typeset by the journal).  Same text on odd and even pages, because the
    reference doc turns evenAndOddHeaders on and an even page with no footer
    part of its own would be blank.  Footer distance 1.25 cm, as the template."""
    doc = parts['word/document.xml'].decode('utf-8')
    if 'w:footerReference' in doc:
        return
    text = footer_text(doc)
    for n in ('1', '2'):
        parts['word/footer%s.xml' % n] = footer_part(text)
    rels = parts['word/_rels/document.xml.rels'].decode('utf-8')
    for n in ('1', '2'):
        rels = rels.replace('</Relationships>', '<Relationship Type="%s" Id="rIdFtr%s" '
                            'Target="footer%s.xml"/></Relationships>' % (FOOTER_REL, n, n))
    parts['word/_rels/document.xml.rels'] = rels.encode('utf-8')
    ct = parts['[Content_Types].xml'].decode('utf-8')
    for n in ('1', '2'):
        ct = ct.replace('</Types>', '<Override PartName="/word/footer%s.xml" '
                        'ContentType="%s"/></Types>' % (n, FOOTER_CT))
    parts['[Content_Types].xml'] = ct.encode('utf-8')
    # the body's final sectPr: header refs come first, footer refs right after them
    i = doc.rfind('<w:sectPr')
    j = doc.index('>', i) + 1
    hdrs = re.match(r'(?:<w:headerReference [^>]*/>)*', doc[j:]).end()
    refs = ('<w:footerReference w:type="default" r:id="rIdFtr1"/>'
            '<w:footerReference w:type="even" r:id="rIdFtr2"/>')
    doc = doc[:j + hdrs] + refs + doc[j + hdrs:]
    doc = doc[:i] + re.sub(r'w:footer="\d+"', 'w:footer="709"', doc[i:], count=1)
    parts['word/document.xml'] = doc.encode('utf-8')
    print('  footer (odd + even):', text)


def main(path: str) -> None:
    zin = zipfile.ZipFile(path)
    infos = zin.infolist()
    parts = {i.filename: zin.read(i.filename) for i in infos}
    zin.close()

    parts['word/document.xml'] = patch_document(parts['word/document.xml'].decode('utf-8')).encode('utf-8')
    parts['word/settings.xml'] = patch_settings(parts['word/settings.xml'].decode('utf-8')).encode('utf-8')
    add_footer(parts)

    buf = io.BytesIO()
    zout = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)
    names = [i.filename for i in infos]
    for info in infos:
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zout.writestr(zi, parts[info.filename])
    for name in parts:
        if name not in names:
            zout.writestr(name, parts[name])
    zout.close()

    # sanity: both parts must still parse before we overwrite the original
    import xml.etree.ElementTree as ET
    check = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    for part in ('document', 'settings', 'footer1', 'footer2'):
        ET.fromstring(check.read('word/%s.xml' % part))

    with open(path, 'wb') as f:
        f.write(buf.getvalue())
    print(f'  patched: {path}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: python patch-thai-docx.py <file.docx>')
    main(sys.argv[1])
