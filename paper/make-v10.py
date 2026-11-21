"""v10 = v9 with the paragraph indent and heading space of the 2569 template.

Measured on 21 Nov 2026 against the journal's own template (PDF from Word):
  * paragraphs open with a tab to a 0.75 cm stop (426 twips); v5-v9 opened
    them with an em space, 0.49 cm - the old template and the published
    two-column papers.  Equations and level-3 headings ("2.2.1") start at
    the paragraph indent ("ทุกสมการจัดตรงกับย่อหน้า"), so they move with it.
  * a heading sits one full blank line below the text above it (37.3 pt
    line to line); v5-v9 used 14 pt of space above (32.6 pt).  The same
    shortfall left equations (4) and (7), which a heading follows, without
    the full blank line under them that the template asks for.
The author asked for both to follow the template.  No text changes: every
paragraph's opening em space becomes a tab, and three styles change.  One
layout fix keeps it at 14 pages: the last row of each data table is no longer
kept with the next paragraph (see free_last_row).

usage: python paper/make-v10.py V9.docx OUT.docx
"""
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')
styles = parts['word/styles.xml'].decode('utf8')

BLOCK_RE = re.compile(r'<w:tbl>.*?</w:tbl>|<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*[^/])?>.*?</w:p>', re.S)
EM = ' '
INDENT = 426                 # twips = 0.75 cm, the template's tab stop in its body style "ปกติ 14"
HEAD_SPACE = 373             # twips = 18.65 pt, one blank line of 14 pt TH Sarabun New in the template


def style_of(b):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', b)
    return m.group(1) if m else None


# --- every em-space indent becomes a tab -------------------------------------------
n = 0
out, last = [], 0
for m in BLOCK_RE.finditer(doc):
    b = m.group(0)
    if not b.startswith('<w:tbl>'):
        t0 = re.search(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', b)
        if t0 and t0.group(1).startswith(EM):
            if style_of(b) not in ('BodyText', 'FirstParagraph'):
                sys.exit('em-space paragraph in style %s' % style_of(b))
            s, e = t0.span()
            first = t0.group(0).replace('>' + EM, '>', 1)
            first = re.sub(r'<w:t(?:\s[^>]*)?></w:t>$', '', first)     # the run held only the em space
            b = b[:s] + '<w:tab/>' + first + b[e:]
            n += 1
    out += [doc[last:m.start()], b]
    last = m.end()
out.append(doc[last:])
new = ''.join(out)
if EM in re.sub(r'<mc:Fallback>.*?</mc:Fallback>', '', new, flags=re.S):
    sys.exit('an em space is left')


# --- a data table's last row is not kept with what follows -----------------------------
# Every cell paragraph inherits keep-with-next (styles Compact and Table), so each table
# dragged the paragraphs after it along: with the deeper indent, table 1 plus heading 3.2
# plus its first lines no longer fitted on page 8, the table jumped and the paper ran to
# 15 pages.  Rows still stay together; only the last one may end a page.
def free_last_row(m):
    t = m.group(0)
    if '<w:tblStyle w:val="Table"/>' not in t:
        return t                                      # figure tables keep their own settings
    rows = list(re.finditer(r'<w:tr[ >].*?</w:tr>', t, re.S))
    r = rows[-1]
    last = r.group(0).replace('<w:pStyle w:val="Compact"/>', '<w:pStyle w:val="Compact"/><w:keepNext w:val="0"/>')
    if last == r.group(0):
        sys.exit('table without Compact cells')
    free_last_row.n += 1
    return t[:r.start()] + last + t[r.end():]


free_last_row.n = 0
new = re.sub(r'<w:tbl>.*?</w:tbl>', free_last_row, new, flags=re.S)


# --- styles ---------------------------------------------------------------------------
def restyle(sid, old, repl):
    global styles
    m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, styles, re.S)
    if not m or m.group(0).count(old) != 1:
        sys.exit('style %s: %r not found once' % (sid, old))
    styles = styles[:m.start()] + m.group(0).replace(old, repl) + styles[m.end():]


restyle('BodyText', '<w:pPr><w:jc w:val="thaiDistribute"/></w:pPr>',
        '<w:pPr><w:tabs><w:tab w:val="left" w:pos="%d"/></w:tabs><w:jc w:val="thaiDistribute"/></w:pPr>' % INDENT)
for sid in ('Heading4', 'Equation'):
    restyle(sid, '<w:ind w:firstLine="280"/>', '<w:ind w:firstLine="%d"/>' % INDENT)
for sid in ('Heading1', 'Heading2', 'Heading3'):
    restyle(sid, '<w:spacing w:before="280"/>', '<w:spacing w:before="%d"/>' % HEAD_SPACE)

print('%d em-space indents -> tab at %d twips; headings %d twips above; %d tables free their last row'
      % (n, INDENT, HEAD_SPACE, free_last_row.n))
parts['word/document.xml'] = new.encode('utf8')
parts['word/styles.xml'] = styles.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('wrote', dst)
