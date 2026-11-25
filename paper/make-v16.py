"""v16 = the author's reviewed copy of v15 (the highlighted one) plus the table changes they approved.

On 25 Nov 2026 the author reviewed `compare/BLEGS_KMUTNB_2026-11-25_v15_highlighted.docx`
in Word and edited it themself (wording in 2.1, 2.2.1, 2.2.3, 2.2.4, 3.4, the CRediT and
AI statements, figure 2's caption, table 3's model names).  That file is now the master;
this script only adds what the author asked for on top of it:

  * tables 1 and 4: a symbol column ("สัญลักษณ์") between the label and the values;
    the label keeps "name (unit)", the symbol moves to its own cell (table 1's last row
    gets tau_max/W, as in equation (2); rows with no symbol get "–"), and table 1's
    "เฉลี่ย 5 ครั้ง" goes - the caption already says the values are means of 5
  * table 2: "ค่า RMS ของการสวมวงกลม" -> "ค่ารากกำลังสองเฉลี่ยของการสวมวงกลม", as the author
    already wrote in 2.2.4
  * column widths of tables 1, 2 and 4 re-fitted to the new text

It writes two files: OUT_HIGHLIGHTED keeps the author's yellow marks (the editor's
requests) and marks this round's changes in cyan; OUT is the same with every highlight
removed (the file to send).

usage: python paper/make-v16.py AUTHOR_V15_HIGHLIGHTED.docx OUT.docx OUT_HIGHLIGHTED.docx
"""
import re
import sys
import zipfile

import pymupdf

src, dst, dst_hl = sys.argv[1:4]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')

INNER_P = re.compile(r'<w:p(?:\s[^>]*[^/])?>(?:(?!<w:p[\s>/]).)*?</w:p>', re.S)
WT = re.compile(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>')
MATH = re.compile(r'<m:oMath>.*?</m:oMath>', re.S)
CYAN = '<w:highlight w:val="cyan"/>'
FONT_DIR = 'C:/Users/mteer/AppData/Local/Microsoft/Windows/Fonts/'
F_REG = pymupdf.Font(fontfile=FONT_DIR + 'THSarabunNew.ttf')
F_BOLD = pymupdf.Font(fontfile=FONT_DIR + 'THSarabunNew Bold.ttf')
SLASH = ('<m:r><m:rPr><m:sty m:val="p"/></m:rPr><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>'
         '<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><m:t>/</m:t></m:r>')


def text(x):
    return ''.join(WT.findall(x))


def cell_rpr(p, highlight=True):
    """rPr for new Thai text in a cell: the cell's first text run's rPr, Thai-flagged, cyan."""
    m = re.search(r'<w:r(?:\s[^>]*)?>(<w:rPr>.*?</w:rPr>)?(?:<w:[a-zA-Z]+[^>]*/>)*<w:t', p, re.S)
    rpr = m.group(1) if m and m.group(1) else '<w:rPr></w:rPr>'
    rpr = re.sub(r'<w:highlight w:val="\w+"/>', '', rpr)
    if '<w:cs/>' not in rpr:
        rpr = rpr.replace('<w:lang', '<w:cs/><w:lang', 1) if '<w:lang' in rpr else rpr.replace('</w:rPr>', '<w:cs/></w:rPr>')
    if highlight:   # w:highlight sits before w:u/w:vertAlign/w:cs/w:lang in rPr order
        for anchor in ('<w:u ', '<w:vertAlign', '<w:rtl', '<w:cs/>', '<w:lang', '</w:rPr>'):
            if anchor in rpr:
                rpr = rpr.replace(anchor, CYAN + anchor, 1)
                break
    return rpr


def math_hl(x):
    """Cyan on every maths run (the w:rPr inside each m:r)."""
    x = re.sub(r'<w:highlight w:val="\w+"/>', '', x)
    return re.sub(r'(<m:r>(?:<m:rPr>.*?</m:rPr>)?<w:rPr>)', r'\1' + CYAN, x, flags=re.S)


def run(rpr, t):
    sp = ' xml:space="preserve"' if t != t.strip() else ''
    return '<w:r>%s<w:t%s>%s</w:t></w:r>' % (rpr, sp, t)


def p_head(p):
    return re.match(r'<w:p(?:\s[^>]*)?>(<w:pPr>.*?</w:pPr>)?', p, re.S).group(0)


def set_jc(head, jc):
    if '<w:jc ' in head:
        return re.sub(r'<w:jc w:val="\w+"/>', '<w:jc w:val="%s"/>' % jc, head)
    return head.replace('</w:pPr>', '<w:jc w:val="%s"/></w:pPr>' % jc) if '<w:pPr>' in head else head + ''


def width_pt(x, bold):
    w = 0.0
    for m in re.finditer(r'<m:oMath>.*?</m:oMath>|<w:t(?:\s[^>]*)?>([^<]*)</w:t>', x, re.S):
        if m.group(0).startswith('<m:oMath'):
            w += 5.2 * len(''.join(re.findall(r'<m:t[^>]*>([^<]*)</m:t>', m.group(0)))) + 3
        else:
            w += (F_BOLD if bold else F_REG).text_length(m.group(1), fontsize=12)
    return w


def width_lines_pt(x, bold):
    lines = x.split('<w:br/>')
    return max(width_pt(l, bold) for l in lines)


def refit(t, label):
    rows = re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S)
    grid = [int(x) for x in re.findall(r'<w:gridCol w:w="(\d+)"/>', t)]
    total = sum(grid)
    cells = [re.findall(r'<w:tc>.*?</w:tc>', r, re.S) for r in rows]
    ncol = len(cells[0])
    assert all(len(c) == ncol for c in cells), label
    pad = 2 * 57 + 60
    need = []
    for c in range(ncol):
        body = max(width_pt(cells[r][c], False) for r in range(1, len(rows))) * 20 + pad
        head = width_lines_pt(cells[0][c], True) * 20 + pad
        need.append((body, head))
    want = [max(b, h) for b, h in need]
    if sum(want) > total:
        want = [max(b, h / 2 + pad / 2) for b, h in need]
    if sum(want) > total:
        sys.exit('%s does not fit: %s' % (label, want))
    extra = total - sum(want)
    new = [int(w + extra * w / sum(want)) for w in want]
    new[-1] += total - sum(new)
    t = re.sub(r'<w:tblGrid>.*?</w:tblGrid>', '<w:tblGrid>%s</w:tblGrid>' % ''.join('<w:gridCol w:w="%d"/>' % g for g in new), t, flags=re.S)
    out = []
    for r in re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S):
        it = iter(new)
        out.append(re.sub(r'<w:tcW w:w="\d+" w:type="dxa"/>', lambda _: '<w:tcW w:w="%d" w:type="dxa"/>' % next(it), r))
    for a, b in zip(re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S), out):
        t = t.replace(a, b, 1)
    print('%s: columns %s -> %s' % (label, grid, new))
    return t


def add_symbol_column(t, label, drop=()):
    rows = re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S)
    new_rows = []
    for k, r in enumerate(rows):
        tcs = list(re.finditer(r'<w:tc>.*?</w:tc>', r, re.S))
        first, second = tcs[0].group(0), tcs[1].group(0)
        sp = INNER_P.search(second).group(0)                 # a value cell's paragraph: centred, right size
        lp = INNER_P.search(first).group(0)
        if k == 0:
            sym_p = p_head(sp) + run(cell_rpr(sp), 'สัญลักษณ์') + '</w:p>'
            new_first = first
        else:
            maths = MATH.findall(lp)
            label_text = re.sub(r'\s+', ' ', text(lp))
            for d in drop:
                label_text = label_text.replace(d, '')
            label_text = re.sub(r'\s+', ' ', label_text).strip()
            if label_text.startswith('อัตราส่วนแรงบิดต่อมวล') and not maths:
                tau = [m for m in MATH.findall(t) if 'τ' in m][0]
                w = [m for m in MATH.findall(t) if re.search(r'<m:t>W</m:t>', m)][0]
                inner = lambda m: m[len('<m:oMath>'):-len('</m:oMath>')]
                maths = ['<m:oMath>' + inner(tau) + SLASH + inner(w) + '</m:oMath>']
            sym = ''.join(math_hl(m) for m in maths) if maths else run(cell_rpr(sp), '–')
            sym_p = p_head(sp) + sym + '</w:p>'
            if label_text == re.sub(r'\s+', ' ', text(lp)).strip() and not MATH.search(lp):
                new_first = first                              # label unchanged (no symbol to move out)
            else:
                new_lp = p_head(lp) + run(cell_rpr(lp), label_text) + '</w:p>'
                new_first = first.replace(lp, new_lp, 1)
        sym_tc = second.replace(sp, sym_p, 1)
        r2 = r[:tcs[0].start()] + new_first + sym_tc + r[tcs[0].end():]
        new_rows.append(r2)
    for a, b in zip(rows, new_rows):
        t = t.replace(a, b, 1)
    # one more grid column (width is re-fitted below)
    t = re.sub(r'(<w:tblGrid><w:gridCol w:w="\d+"/>)', r'\1<w:gridCol w:w="1000"/>', t, count=1)
    return t


done = []


def fix_table(m):
    t = m.group(0)
    if '<w:tblStyle w:val="Table"/>' not in t:
        return t
    head = text(re.search(r'<w:tr[ >].*?</w:tr>', t, re.S).group(0))
    if head.startswith('รายการค่า'):                       # table 1
        t = add_symbol_column(t, 'table 1', drop=(' เฉลี่ย 5 ครั้ง',))
        done.append(1)
        return refit(t, 'table 1')
    if head.startswith('ตัวชี้วัด'):                       # table 4
        t = add_symbol_column(t, 'table 4')
        done.append(4)
        return refit(t, 'table 4')
    if 'ค่า RMS ของการสวมวงกลม' in text(t):                # table 2
        n = [0]

        def cell(pm):
            p = pm.group(0)
            tx = text(p)
            if 'ค่า RMS ของการสวมวงกลม' not in tx:
                return p
            n[0] += 1
            return p_head(p) + run(cell_rpr(p), tx.replace('ค่า RMS ของการสวมวงกลม', 'ค่ารากกำลังสองเฉลี่ยของการสวมวงกลม')) + '</w:p>'
        t = INNER_P.sub(cell, t)
        if n[0] != 2:
            sys.exit('table 2: %d RMS rows' % n[0])
        done.append(2)
        return refit(t, 'table 2')
    return t


doc = re.sub(r'<w:tbl>.*?</w:tbl>', fix_table, doc, flags=re.S)
if sorted(done) != [1, 2, 4]:
    sys.exit('tables done: %s' % done)
if 'RMS' in text(doc):
    sys.exit('RMS still in the text')


def write(path, xml):
    parts['word/document.xml'] = xml.encode('utf8')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for i in infos:
            z.writestr(i, parts[i.filename])
    print('wrote', path)


write(dst_hl, doc)
clean = re.sub(r'<w:highlight w:val="\w+"/>', '', doc)
write(dst, clean)
for name in list(parts):                                     # the footers carried yellow on the name
    if re.match(r'word/(header|footer)\d+\.xml$', name):
        parts[name] = re.sub(rb'<w:highlight w:val="\w+"/>', b'', parts[name])
write(dst, clean)
