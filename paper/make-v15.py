"""v15 = v14 revised for the editor's preliminary check of article 88_272060 (25 Nov 2026).

The editor asked for four things:
  1. author name, affiliation, phone and e-mail in the file   -> v15 is the named
     version (the anonymised copy is no longer made)
  2. figure 1 panels (a)-(b) as (ก)-(ข), in the figure and the text
     -> figures 1 and 3 are redrawn by make-figures.py with Thai labels (figure 3
        had (a)/(b) too); the text and the caption of figure 1 follow
  3. every table header and row label in Thai   -> cell text replaced below
     (numbers untouched; tables/src/*.md and tables/export/*.jpg say the same),
     table 2's unit moves to its caption like table 3's
  4. "revise it in the attached template"   -> the template is the same 2569 file
     v6-v14 took their page set-up and headers from, but their paragraphs used the
     build's own styles (Title, Body Text, heading 2...).  Every paragraph now uses
     the template's styles - ชื่อเรื่อง (a), ปกติ 14 (14), ปกติ 12 (12),
     Heading 14 Bold, สมการ (1), อ้างอิง [x] - with the direct formatting that keeps
     the measured v10 layout (0.75 cm indent, one blank line above headings,
     equations at the paragraph indent).  The first two pages follow the template's
     sequence of blank ปกติ 12 lines between the blocks.  Styles nothing uses any
     more are removed.

usage: python paper/make-v15.py V14.docx TEMPLATE.docx FIGURES_DIR OUT.docx OLD_FIGURES_DIR [--styles-only]
--styles-only stops after the restyling (no text, table or figure change): Word Compare
of that file against v15 shows only the editor's text changes, because Compare cannot
pair paragraphs across the restyled first pages.
"""
import re
import sys
import zipfile

import pymupdf

src, tpl_path, fig_dir, dst = sys.argv[1:5]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')
styles = parts['word/styles.xml'].decode('utf8')
tpl_styles = zipfile.ZipFile(tpl_path).read('word/styles.xml').decode('utf8')

INNER_P = re.compile(r'<w:p(?:\s[^>]*[^/])?>(?:(?!<w:p[\s>/]).)*?</w:p>|<w:p(?:\s[^>]*)?/>', re.S)
WT_RE = re.compile(r'(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)')
FONT_DIR = 'C:/Users/mteer/AppData/Local/Microsoft/Windows/Fonts/'
F_REG = pymupdf.Font(fontfile=FONT_DIR + 'THSarabunNew.ttf')
F_BOLD = pymupdf.Font(fontfile=FONT_DIR + 'THSarabunNew Bold.ttf')


def text(x):
    return ''.join(m.group(2) for m in WT_RE.finditer(x))


def style(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"/>', p)
    return m.group(1) if m else None


# ------------------------------------------------------------------ 1. template styles
def style_xml(s, sid):
    m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % re.escape(sid), s, re.S)
    return m.group(0) if m else None


for sid in ('a', '14', 'Heading14Bold', '1', 'x', '12'):
    x = style_xml(tpl_styles, sid)
    x = re.sub(r'<w:rsid[^>]*/>|<w:link w:val="[^"]*"/>|<w:uiPriority[^>]*/>', '', x)
    old = style_xml(styles, sid)
    if old:
        styles = styles.replace(old, x)
    else:
        styles = styles.replace('</w:styles>', x + '</w:styles>')

# ------------------------------------------------------------------ 2. pPr helpers
ORDER = ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl', 'numPr',
         'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens', 'kinsoku', 'wordWrap',
         'overflowPunct', 'topLinePunct', 'autoSpaceDE', 'autoSpaceDN', 'bidi', 'adjustRightInd', 'snapToGrid',
         'spacing', 'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection',
         'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr', 'sectPr', 'pPrChange']
CHILD = re.compile(r'<w:(\w+)(?:\s[^>]*)?/>|<w:(\w+)(?:\s[^>]*)?>.*?</w:\2>', re.S)


def set_ppr(p, new_style, add=None, drop=()):
    """Give paragraph p style new_style and the direct properties in `add` (tag -> xml);
    properties already set directly win over `add` unless their tag is in `drop`."""
    m = re.search(r'<w:pPr>(.*?)</w:pPr>', p, re.S)
    kids = {}
    if m:
        for c in CHILD.finditer(m.group(1)):
            kids[c.group(1) or c.group(2)] = c.group(0)
    for t in drop:
        kids.pop(t, None)
    kids.pop('pStyle', None)
    if new_style:
        kids['pStyle'] = '<w:pStyle w:val="%s"/>' % new_style
    for t, x in (add or {}).items():
        kids.setdefault(t, x)
    unknown = set(kids) - set(ORDER)
    if unknown:
        sys.exit('unknown pPr children %s' % unknown)
    ppr = ''.join(kids[t] for t in ORDER if t in kids)
    ppr = '<w:pPr>%s</w:pPr>' % ppr if ppr else ''
    if p.endswith('/>'):
        return p[:-2] + '>' + ppr + '</w:p>'
    if m:
        return p[:m.start()] + ppr + p[m.end():]
    head = re.match(r'<w:p(?:\s[^>]*)?>', p).group(0)
    return head + ppr + p[len(head):]


KEEP = {'keepNext': '<w:keepNext/>', 'keepLines': '<w:keepLines/>'}
HEAD_SPACE = '<w:spacing w:before="373"/>'      # one blank line, as in v10
EMPTY12 = '<w:p><w:pPr><w:pStyle w:val="12"/></w:pPr></w:p>'
EMPTY = '<w:p/>'
remapped = {}


def remap(p):
    st = style(p)
    t = text(p).strip()
    new = None
    if st == 'Title':
        new = set_ppr(p, 'a', drop=('spacing', 'contextualSpacing')) + EMPTY
    elif st == 'Author':
        new = set_ppr(p, '14', drop=('spacing',))
    elif st == 'Affiliation':
        new = set_ppr(p, '12') + EMPTY12
    elif st == 'Corresponding':
        new = set_ppr(p, '12', drop=('spacing',)) + (EMPTY12 if t.startswith('©') else '')
    elif st in ('Heading2', 'Heading3'):
        if t in ('บทคัดย่อ', 'Abstract'):
            add = dict(KEEP)                    # the blank ปกติ 12 line above does the spacing
        else:
            add = dict(KEEP, spacing=HEAD_SPACE, outlineLvl='<w:outlineLvl w:val="%d"/>' % (1 if st == 'Heading2' else 2))
        new = set_ppr(p, 'Heading14Bold', add, drop=() if t not in ('บทคัดย่อ', 'Abstract') else ('spacing',))
    elif st == 'Heading4':
        new = set_ppr(p, '14', dict(KEEP, ind='<w:ind w:firstLine="426"/>', outlineLvl='<w:outlineLvl w:val="3"/>'))
    elif st in ('FirstParagraph', 'BodyText'):
        new = set_ppr(p, '14')
    elif st == 'Equation':
        new = set_ppr(p, '1', {'tabs': '<w:tabs><w:tab w:val="clear" w:pos="3969"/><w:tab w:val="right" w:pos="8618"/></w:tabs>',
                               'ind': '<w:ind w:firstLine="426"/>', 'jc': '<w:jc w:val="left"/>'})
    elif st == 'Reference':
        new = set_ppr(p, 'x', {'jc': '<w:jc w:val="left"/>'})
    elif st == 'ImageCaption':
        new = set_ppr(p, '14', {'keepLines': '<w:keepLines/>', 'jc': '<w:jc w:val="center"/>'})
    elif st == 'TableCaption':
        new = set_ppr(p, '14', dict(KEEP, spacing='<w:spacing w:after="60"/>'))
    elif st == 'CaptionedFigure':
        new = set_ppr(p, '14', {'keepNext': '<w:keepNext/>', 'jc': '<w:jc w:val="center"/>'})
    elif st == 'Compact':
        new = set_ppr(p, '12')
    elif st is None and not t and '<w:sectPr' not in p and '<w:br' not in p and '<w:drawing' not in p:
        new = None                              # plain blank line: decided by its neighbours below
    if new is not None:
        remapped[st] = remapped.get(st, 0) + 1
        return new
    return p


# work block by block at the top level so the blank line after each abstract can be found
BLOCK_RE = re.compile(r'<w:tbl>.*?</w:tbl>|<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*[^/])?>.*?</w:p>', re.S)
blocks = [m.group(0) for m in BLOCK_RE.finditer(doc)]
spans = [m.span() for m in BLOCK_RE.finditer(doc)]
out_blocks = []
for k, b in enumerate(blocks):
    prev_t = text(blocks[k - 1]).strip() if k else ''
    if b.startswith('<w:tbl>'):
        out_blocks.append(INNER_P.sub(lambda m: remap(m.group(0)), b))
        continue
    if not text(b).strip() and style(b) is None and '<w:sectPr' not in b and '<w:br' not in b \
            and style(blocks[k - 1]) == 'FirstParagraph' and (prev_t.startswith('ขาหุ่นยนต์') or prev_t.startswith('Lightweight')):
        out_blocks.append(EMPTY12)              # the blank line under each abstract, as in the template
        remapped['abstract blank'] = remapped.get('abstract blank', 0) + 1
        continue
    if '<w:txbxContent>' in b:                  # the keyword paragraphs carry the citation boxes
        head_end = b.index('</w:pPr>') + len('</w:pPr>') if b.find('</w:pPr>') < b.find('<w:r>') else re.match(r'<w:p(?:\s[^>]*)?>', b).end()
        out_blocks.append(remap(b[:head_end] + '</w:p>')[:-len('</w:p>')] + b[head_end:])
        continue
    out_blocks.append(remap(b))

out, last = [], 0
for (s, e), b in zip(spans, out_blocks):
    out += [doc[last:s], b]
    last = e
out.append(doc[last:])
doc = ''.join(out)

STYLES_ONLY = '--styles-only' in sys.argv

# ------------------------------------------------------------------ 3. (a)/(b) -> (ก)/(ข)
def edit_in_paragraphs(old, new, expect):
    if STYLES_ONLY:
        return
    n = [0]

    def fix(m):
        p = m.group(0)
        ts = list(WT_RE.finditer(p))
        full = ''.join(t.group(2) for t in ts)
        if old not in full:
            return p
        at = full.find(old)
        if full.find(old, at + 1) >= 0:
            sys.exit('twice in one paragraph: %r' % old)
        n[0] += 1
        end = at + len(old)
        o, last, pos = [], 0, 0
        for t in ts:
            s0, e0 = pos, pos + len(t.group(2))
            pos = e0
            tx = t.group(2)
            nt = tx[:max(0, min(len(tx), at - s0))] + (new if s0 <= at < e0 else '') + tx[max(0, min(len(tx), end - s0)):]
            tag = t.group(1)
            if nt != nt.strip() and 'xml:space' not in tag:
                tag = '<w:t xml:space="preserve">'
            o += [p[last:t.start()], tag, nt, t.group(3)]
            last = t.end()
        o.append(p[last:])
        return ''.join(o)

    global doc
    doc = INNER_P.sub(fix, doc)
    if n[0] != expect:
        sys.exit('%r: %d paragraphs, expected %d' % (old, n[0], expect))


edit_in_paragraphs('ดังรูปที่ 1 (a)', 'ดังรูปที่ 1 (ก)', 1)
edit_in_paragraphs('ดังรูปที่ 1 (b)', 'ดังรูปที่ 1 (ข)', 1)
edit_in_paragraphs(' (a) การติดตั้งกล้อง', ' (ก) การติดตั้งกล้อง', 1)
edit_in_paragraphs(' (b) การจัดวางเครื่องหมาย', ' (ข) การจัดวางเครื่องหมาย', 1)
edit_in_paragraphs('กับวิถีปลายขาที่วัดได้', 'กับวิถีปลายขาที่วัดได้ (มิลลิเมตร)', 1)     # table 2 caption

# ------------------------------------------------------------------ 4. tables in Thai
L2 = ['รายการ', 'ไม่มีโหลด', '1 กิโลกรัม', '2 กิโลกรัม', '3 กิโลกรัม']
CELLS = [
    {'Quantity': 'รายการ', 'Value': 'ค่า',
     '{M}, mean of 5 trials (N)': 'แรงสูงสุด {M} เฉลี่ย 5 ครั้ง (นิวตัน)',
     'Moment arm {M} (m)': 'แขนโมเมนต์ {M} (เมตร)',
     '{M} (N·m)': 'แรงบิดสูงสุด {M} (นิวตันเมตร)',
     'Robot mass {M} (kg)': 'มวลหุ่นยนต์ {M} (กิโลกรัม)',
     'Torque-to-mass ratio (N·m/kg)': 'อัตราส่วนแรงบิดต่อมวล (นิวตันเมตรต่อกิโลกรัม)'},
    {'Quantity': 'รายการ', 'No-load': 'ไม่มีโหลด', '1 kg': '1 กิโลกรัม', '2 kg': '2 กิโลกรัม', '3 kg': '3 กิโลกรัม',
     'Radius, comp. off (mm)': 'รัศมี ปิดการชดเชย',
     'Radius, POLY4 (mm)': 'รัศมี ชดเชยด้วยพหุนามอันดับ 4',
     'Centre {M}, comp. off (mm)': 'จุดศูนย์กลางแกน {M} ปิดการชดเชย',
     'Centre {M}, POLY4 (mm)': 'จุดศูนย์กลางแกน {M} ชดเชยด้วยพหุนามอันดับ 4',
     'Centre offset, comp. off (mm)': 'ระยะเยื้องจุดศูนย์กลาง ปิดการชดเชย',
     'Centre offset, POLY4 (mm)': 'ระยะเยื้องจุดศูนย์กลาง ชดเชยด้วยพหุนามอันดับ 4',
     'Fit RMS, comp. off (mm)': 'ค่า RMS ของการสวมวงกลม ปิดการชดเชย',
     'Fit RMS, POLY4 (mm)': 'ค่า RMS ของการสวมวงกลม ชดเชยด้วยพหุนามอันดับ 4'},
    {'Model': 'แบบจำลอง', 'No-load': 'ไม่มีโหลด', '1 kg': '1 กิโลกรัม', '2 kg': '2 กิโลกรัม', '3 kg': '3 กิโลกรัม',
     'Mean': 'เฉลี่ย', 'None': 'ไม่ชดเชย', 'POLY3': 'พหุนามอันดับ 3', 'MLP': 'โครงข่ายประสาทเทียม (MLP)',
     'RF': 'ป่าสุ่ม (RF)', 'POLY4': 'พหุนามอันดับ 4', 'SVR': 'เวกเตอร์สนับสนุน (SVR)'},
    # header cells break after the payload, so Word does not split "ปิดการ|ชดเชย"
    {'Metric': 'ตัวชี้วัด', 'No-load off': 'ไม่มีโหลด\nปิดการชดเชย', 'No-load on': 'ไม่มีโหลด\nเปิดการชดเชย',
     '3 kg off': '3 กิโลกรัม\nปิดการชดเชย', '3 kg on': '3 กิโลกรัม\nเปิดการชดเชย', 'Runs': 'จำนวนรอบ',
     '{M} (m)': 'ระยะที่เดินได้ {M} (เมตร)', '{M} (cm/m)': 'อัตราการเบี่ยง {M} (เซนติเมตรต่อเมตร)',
     '{M} (deg)': 'มุมเบี่ยง {M} (องศา)', '{M} (cm)': 'ระยะเบี่ยงด้านข้าง {M} (เซนติเมตร)',
     'Speed (cm/s)': 'ความเร็ว (เซนติเมตรต่อวินาที)'},
]
MATH = re.compile(r'<m:oMath>.*?</m:oMath>', re.S)


def thai_rpr(p):
    m = re.search(r'<w:r(?:\s[^>]*)?>(<w:rPr>.*?</w:rPr>)?<w:t', p, re.S)
    rpr = m.group(1) if m and m.group(1) else '<w:rPr></w:rPr>'
    if '<w:cs/>' not in rpr:
        rpr = rpr.replace('<w:lang', '<w:cs/><w:lang', 1) if '<w:lang' in rpr else rpr.replace('</w:rPr>', '<w:cs/></w:rPr>')
    return rpr


def run(rpr, t):
    out = []
    for j, line in enumerate(t.split('\n')):
        sp = ' xml:space="preserve"' if line != line.strip() else ''
        out.append(('<w:br/>' if j else '') + '<w:t%s>%s</w:t>' % (sp, line))
    return '<w:r>%s%s</w:r>' % (rpr, ''.join(out))


def cell_key(p):
    segs = []
    for m in re.finditer(r'<m:oMath>.*?</m:oMath>|<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p, re.S):
        segs.append('{M}' if m.group(0).startswith('<m:oMath') else m.group(1))
    return ''.join(segs)


def width_pt(cell_p, bold):
    w = 0.0
    for m in re.finditer(r'<m:oMath>.*?</m:oMath>|<w:t(?:\s[^>]*)?>([^<]*)</w:t>', cell_p, re.S):
        if m.group(0).startswith('<m:oMath'):
            w += 5.2 * len(''.join(re.findall(r'<m:t[^>]*>([^<]*)</m:t>', m.group(0)))) + 3
        else:
            w += (F_BOLD if bold else F_REG).text_length(m.group(1), fontsize=12)
    return w


def width_lines_pt(cell_p, bold):
    """Widest line of a cell whose text has explicit <w:br/> breaks."""
    lines = re.split(r'<w:br/>', cell_p)
    return max(width_pt(x if x.startswith('<w:p') else '<w:p>' + x, bold) for x in lines) if len(lines) > 1 else width_pt(cell_p, bold)


tables_done = [0]


def fix_table(m):
    t = m.group(0)
    if '<w:tblStyle w:val="Table"/>' not in t:
        return t
    i = tables_done[0]
    tables_done[0] += 1
    mapping = CELLS[i]
    used = set()

    def fix_cell_p(pm):
        p = pm.group(0)
        key = cell_key(p)
        if key not in mapping:
            if re.fullmatch(r'[−\d.± ]*', key):
                return p
            sys.exit('table %d: no Thai for %r' % (i + 1, key))
        used.add(key)
        maths = MATH.findall(p)
        rpr = thai_rpr(p)
        pieces = mapping[key].split('{M}')
        if len(pieces) - 1 != len(maths):
            sys.exit('table %d %r: math count' % (i + 1, key))
        body = ''
        for j, piece in enumerate(pieces):
            if piece:
                body += run(rpr, piece)
            if j < len(maths):
                body += maths[j]
        head = re.match(r'<w:p(?:\s[^>]*)?>(<w:pPr>.*?</w:pPr>)?', p, re.S).group(0)
        return head + body + '</w:p>'

    t = INNER_P.sub(fix_cell_p, t)
    missing = set(mapping) - used
    if missing:
        sys.exit('table %d: unused %s' % (i + 1, missing))
    # column widths from the Thai text (12 pt TH Sarabun New), total kept at the text width
    rows = re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S)
    grid = [int(x) for x in re.findall(r'<w:gridCol w:w="(\d+)"/>', t)]
    ncol, total = len(grid), sum(grid)
    cells = [re.findall(r'<w:tc>.*?</w:tc>', r, re.S) for r in rows]
    assert all(len(c) == ncol for c in cells)
    pad = 2 * 57 + 60
    need = []
    for c in range(ncol):
        body = max(width_pt(cells[r][c], False) for r in range(1, len(rows))) * 20 + pad
        head = width_lines_pt(cells[0][c], True) * 20 + pad
        need.append((body, head))
    want = [max(b, h) for b, h in need]
    if sum(want) > total:                        # let the header cells wrap onto two lines
        want = [max(b, h / 2 + pad / 2) for b, h in need]
    if sum(want) > total:
        sys.exit('table %d does not fit: %s' % (i + 1, want))
    extra = total - sum(want)
    new_grid = [int(w + extra * w / sum(want)) for w in want]
    new_grid[-1] += total - sum(new_grid)
    t = re.sub(r'<w:tblGrid>.*?</w:tblGrid>',
               '<w:tblGrid>%s</w:tblGrid>' % ''.join('<w:gridCol w:w="%d"/>' % g for g in new_grid), t, flags=re.S)
    out_rows = []
    for r in re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S):
        cs = iter(new_grid)
        out_rows.append(re.sub(r'<w:tcW w:w="\d+" w:type="dxa"/>', lambda _: '<w:tcW w:w="%d" w:type="dxa"/>' % next(cs), r))
    for old_r, new_r in zip(re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S), out_rows):
        t = t.replace(old_r, new_r, 1)
    print('table %d: columns %s -> %s twips' % (i + 1, grid, new_grid))
    return t


if not STYLES_ONLY:
    doc = re.sub(r'<w:tbl>.*?</w:tbl>', fix_table, doc, flags=re.S)
    if tables_done[0] != 4:
        sys.exit('expected 4 data tables, did %d' % tables_done[0])

# ------------------------------------------------------------------ 5. figures 1 and 3
rels = parts['word/_rels/document.xml.rels'].decode('utf8')
media = {t: zin.read('word/' + t) for t in re.findall(r'Target="(media/[^"]+)"', rels)}
old_dir = sys.argv[5] if len(sys.argv) > 5 else None
for n in (() if STYLES_ONLY else (1, 3)):
    new_bytes = open('%s/fig%d.jpg' % (fig_dir, n), 'rb').read()
    old_bytes = open('%s/fig%d.jpg' % (old_dir, n), 'rb').read() if old_dir else None
    hits = [name for name, data in media.items() if data == old_bytes]
    if len(hits) != 1:
        sys.exit('figure %d: %d embedded matches for the old image' % (n, len(hits)))
    a, b = pymupdf.Pixmap(old_bytes), pymupdf.Pixmap(new_bytes)
    if (a.width, a.height) != (b.width, b.height):
        sys.exit('figure %d changed size' % n)
    parts['word/' + hits[0]] = new_bytes
    print('figure %d -> %s' % (n, hits[0]))

# ------------------------------------------------------------------ 6. retire styles nothing uses
everything = doc + ''.join(v.decode('utf8', 'ignore') for k, v in parts.items()
                           if re.match(r'word/(header|footer|footnotes|endnotes)', k))
for sid in ('Author', 'Affiliation', 'Corresponding', 'FirstParagraph', 'CaptionedFigure', 'ImageCaption',
            'TableCaption', 'Equation', 'Reference', 'Compact', 'Figure'):
    if 'w:val="%s"' % sid in everything:
        sys.exit('style %s still used' % sid)
    x = style_xml(styles, sid)
    if x:
        styles = styles.replace(x, '')
for sid in ('Author', 'Affiliation', 'Corresponding', 'FirstParagraph', 'CaptionedFigure', 'ImageCaption',
            'TableCaption', 'Equation', 'Reference', 'Compact', 'Figure'):
    if 'w:val="%s"' % sid in styles:
        styles = re.sub(r'<w:(next|basedOn|link) w:val="%s"/>' % sid, '', styles)

left = sorted(set(re.findall(r'<w:pStyle w:val="([^"]+)"/>', doc)))
print('paragraph styles now used:', left)
print('remapped:', remapped)
if set(left) - {'a', '14', '12', 'Heading14Bold', '1', 'x'}:
    sys.exit('non-template paragraph style left: %s' % (set(left) - {'a', '14', '12', 'Heading14Bold', '1', 'x'}))

parts['word/document.xml'] = doc.encode('utf8')
parts['word/styles.xml'] = styles.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('wrote', dst)
