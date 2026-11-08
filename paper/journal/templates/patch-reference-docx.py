"""Bring reference.docx in line with the journal's own template (run once; idempotent).

Usage:  python journal/templates/patch-reference-docx.py

pandoc takes styles, page setup and the header from reference.docx, so every
journal rule that lives in a style is fixed here, once, instead of in Word by hand.
Checked against kmutnb-article-template.docx and five published TCI-1 papers
(8 Nov 2026):

  body text   Thai Distribute ("การกระจายแบบไทย"), as the guide's text requires.
  header      the template's odd/even page header (journal logo, journal name,
              page number on the outer edge) copied verbatim, fonts Sarabun ->
              TH Sarabun New; evenAndOddHeaders on; header distance 1.25 cm.
  captions    "Table Caption" / "Image Caption" are regular weight - journal.lua
              bolds only the label ("ตารางที่ N" / "รูปที่ N"), as the template does;
              keepLines so a caption never breaks across columns.
  equation    starts at the paragraph indent (0.5 cm), number flush right at the
              7.5 cm column edge - "ทุกสมการจัดตรงกับย่อหน้า".
  table       native tables: single borders all round, TH Sarabun New 12 pt,
              header row bold, cells centred vertically; rows keep together.
  reference   hanging indent 0.75 cm with a tab after "[n]" (IEEE list layout).
  author      one blank line between the title and the author line.
  figure      image paragraphs centred and kept with their caption.
"""
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, 'reference.docx')
TPL = os.path.join(HERE, 'kmutnb-article-template.docx')


def sub1(pattern, repl, text, flags=re.S):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        sys.exit('pattern not found: ' + pattern[:80])
    return new


def style_block(styles, sid):
    m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, styles, re.S)
    if not m:
        sys.exit('style not found: ' + sid)
    return m


def replace_style(styles, sid, new_xml):
    m = style_block(styles, sid)
    return styles[:m.start()] + new_xml + styles[m.end():]


def main():
    src = zipfile.ZipFile(REF)
    tpl = zipfile.ZipFile(TPL)
    parts = {i.filename: src.read(i.filename) for i in src.infolist()}
    order = [i.filename for i in src.infolist()]

    styles = parts['word/styles.xml'].decode('utf8')
    if 'w:styleId="Reference"' in styles:
        if 'thaiDistribute' in style_block(styles, 'BodyText').group(0):
            print('reference.docx already patched - nothing to do')
            return
        styles = thai_distribute(styles)
        parts['word/styles.xml'] = styles.encode('utf8')
        write(src, parts, order)
        return
    styles = thai_distribute(styles)

    # ---- styles -------------------------------------------------------------
    styles = replace_style(styles, 'TableCaption',
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="TableCaption">'
        '<w:name w:val="Table Caption"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:keepLines/><w:jc w:val="left"/></w:pPr>'
        '<w:rPr><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>')
    styles = replace_style(styles, 'ImageCaption',
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="ImageCaption">'
        '<w:name w:val="Image Caption"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:keepLines/><w:jc w:val="center"/></w:pPr>'
        '<w:rPr><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>')
    styles = replace_style(styles, 'Equation',
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Equation">'
        '<w:name w:val="Equation"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:tabs><w:tab w:val="right" w:pos="4252"/></w:tabs>'
        '<w:ind w:firstLine="280"/><w:jc w:val="left"/></w:pPr><w:rPr/></w:style>')
    styles = replace_style(styles, 'CaptionedFigure',
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="CaptionedFigure">'
        '<w:name w:val="Captioned Figure"/><w:basedOn w:val="Figure"/>'
        '<w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr></w:style>')
    styles = replace_style(styles, 'Table',
        '<w:style w:type="table" w:default="1" w:styleId="Table">'
        '<w:name w:val="Table"/><w:basedOn w:val="TableNormal"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr>'
        '<w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
        '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="57" w:type="dxa"/>'
        '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar>'
        '</w:tblPr>'
        '<w:trPr><w:cantSplit/></w:trPr>'
        '<w:tcPr><w:vAlign w:val="center"/></w:tcPr>'
        '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:bCs/></w:rPr></w:tblStylePr>'
        '</w:style>')
    # Author: one blank line (14 pt) between the title and the author line
    m = style_block(styles, 'Author')
    author = m.group(0).replace('<w:keepNext />', '<w:keepNext /><w:spacing w:before="280" />', 1)
    if author == m.group(0):
        sys.exit('Author style: keepNext not found')
    styles = styles[:m.start()] + author + styles[m.end():]
    # Compact = table-cell paragraphs (the drafts have no lists any more):
    # keep each row with the next so a table moves to the next column whole
    m = style_block(styles, 'Compact')
    compact = m.group(0).replace('<w:pPr>', '<w:pPr><w:keepNext />', 1)
    styles = styles[:m.start()] + compact + styles[m.end():]
    # new: Reference (IEEE list, hanging indent)
    styles = styles.replace('</w:styles>',
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Reference">'
        '<w:name w:val="Reference"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:tabs><w:tab w:val="left" w:pos="425"/></w:tabs>'
        '<w:ind w:left="425" w:hanging="425"/><w:jc w:val="both"/></w:pPr>'
        '<w:rPr/></w:style></w:styles>')
    parts['word/styles.xml'] = styles.encode('utf8')

    # ---- header (from the journal template) --------------------------------
    rels = parts['word/_rels/document.xml.rels'].decode('utf8')
    ctypes = parts['[Content_Types].xml'].decode('utf8')
    media_map = {}
    for n in ('1', '2'):
        h = tpl.read('word/header%s.xml' % n).decode('utf8')
        h = h.replace('w:ascii="Sarabun"', 'w:ascii="TH Sarabun New"') \
             .replace('w:cs="Sarabun"', 'w:cs="TH Sarabun New"') \
             .replace('w:eastAsia="Sarabun"', 'w:eastAsia="TH Sarabun New"') \
             .replace('w:hAnsi="Sarabun"', 'w:hAnsi="TH Sarabun New"')
        hr = tpl.read('word/_rels/header%s.xml.rels' % n).decode('utf8')
        for tgt in re.findall(r'Target="media/([^"]+)"', hr):
            new = 'hdr_' + tgt
            media_map[tgt] = new
            hr = hr.replace('Target="media/%s"' % tgt, 'Target="media/%s"' % new)
        parts['word/header%s.xml' % n] = h.encode('utf8')
        parts['word/_rels/header%s.xml.rels' % n] = hr.encode('utf8')
        order += ['word/header%s.xml' % n, 'word/_rels/header%s.xml.rels' % n]
        rels = rels.replace('</Relationships>',
            '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/header" Id="rIdHdr%s" Target="header%s.xml" /></Relationships>' % (n, n))
        ctypes = ctypes.replace('</Types>',
            '<Override PartName="/word/header%s.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/></Types>' % n)
    for old, new in media_map.items():
        parts['word/media/' + new] = tpl.read('word/media/' + old)
        order.append('word/media/' + new)
    if 'Extension="png"' not in ctypes:
        ctypes = ctypes.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>')
    parts['word/_rels/document.xml.rels'] = rels.encode('utf8')
    parts['[Content_Types].xml'] = ctypes.encode('utf8')

    doc = parts['word/document.xml'].decode('utf8')
    doc = sub1(r'(<w:sectPr>)', r'\1<w:headerReference w:type="default" r:id="rIdHdr1"/>'
                                 r'<w:headerReference w:type="even" r:id="rIdHdr2"/>', doc)
    doc = sub1(r'w:header="720"', 'w:header="709"', doc)
    parts['word/document.xml'] = doc.encode('utf8')

    st = parts['word/settings.xml'].decode('utf8')
    st = sub1(r'(<w:defaultTabStop [^>]*/>)', r'\1\n  <w:evenAndOddHeaders />', st)
    parts['word/settings.xml'] = st.encode('utf8')

    write(src, parts, order)


def thai_distribute(styles):
    """Body text: Thai Distribute, as the guide requires.  With plain 'both'
    Word can only stretch the spaces, so a Thai line that has none stays ragged
    and lines with one or two spaces open wide gaps; Thai Distribute spreads
    the slack between characters instead (checked on the rendered PDF, 8 Nov)."""
    m = style_block(styles, 'BodyText')
    new = re.sub(r'<w:jc w:val="both" ?/>', '<w:jc w:val="thaiDistribute"/>', m.group(0))
    return styles[:m.start()] + new + styles[m.end():]


def write(src, parts, order):
    fd, tmp = tempfile.mkstemp(suffix='.docx', dir=HERE)
    os.close(fd)
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as out:
        for name in order:
            out.writestr(name, parts[name])
    src.close()
    shutil.move(tmp, REF)
    print('patched', REF)


if __name__ == '__main__':
    main()
