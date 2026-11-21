"""v9 = v8 with the spacing and layout fixes from the 21 Nov 2026 check.

The author reviewed v8 and asked for a detailed spacing/format check, then
approved every finding (groups A and B).  Nothing here rewords the text: the
changes are spaces, one misspelling, fonts, blank lines and one style.

Group A - errors
  * double space "ทแยงมุม  คือ"; word split "การถดถอย พหุนาม"; "และ สร้าง"
  * misspelling "ที่ละคู่" -> "ทีละคู่"
  * "[-90,90]" gets the space after the comma that "[-210, -140]" has
  * extra space after the indent of the English abstract
  * the paragraph after eq. (6): delta was Calibri and D upright Sarabun; both
    become inline maths like every other variable, and the paragraph gets
    the Body Text style and em-space indent of its neighbours
  * blank lines: one line before every heading and after every figure/table
    (removed: 2.2.3 mid-section, above 3, above 3.3, above 3.4 - the one
    above 3 was left over from cutting 2.3.3 in v8; added: after figures 1-2
    before 2.2.3, and between table 3 and figures 4-5, where the figure was
    covering the table's bottom rule)
  * trailing spaces in three paragraphs; the empty paragraph that carries
    the section break before 1. บทนำ is no longer a Heading 2
Group B - author's choice, all accepted
  * Thai keywords separated by commas (template rule, as in the English)
  * table captions Thai Distribute + 3 pt above the table, as the template
  * Royal Institute spacing: no space before "และ" joining two words
    ("งานสำรวจและขนส่ง", "ขาและโครงสร้าง"), "เครื่องหมายอ้างอิงชนิด ArUco",
    and a space after "จากงานวิจัยที่ผ่านมา"

With --tracked the same changes are written as tracked revisions (author
"Claude (proposal)") into a copy of v8 instead.  Word's own Compare gets lost
around the blank lines next to tables and shows whole sections deleted and
re-typed; this marks only what changed.  The table-caption style change is
not tracked (it lives in styles.xml).

usage: python paper/make-v9.py V8.docx OUT.docx [--tracked]
"""
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
TRACK = '--tracked' in sys.argv[3:]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')
styles = parts['word/styles.xml'].decode('utf8')

BLOCK_RE = re.compile(r'<w:tbl>.*?</w:tbl>|<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*[^/])?>.*?</w:p>', re.S)
WT_RE = re.compile(r'(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)')
RUN_RE = re.compile(r'<w:r(?:\s[^>]*)?>(?:(?!<w:r[\s>]).)*?</w:r>', re.S)   # runs with no run inside
EM = ' '
_rev = [90000]


def rev():
    _rev[0] += 1
    return 'w:id="%d" w:author="Claude (proposal)" w:date="2026-11-21T00:00:00Z"' % _rev[0]


def text(b):
    return ''.join(re.findall(r'<(?:w|m):t(?:\s[^>]*)?>([^<]*)</(?:w|m):t>', b))


blocks = [[m.start(), m.end(), m.group(0)] for m in BLOCK_RE.finditer(doc)]


def find(cond, what):
    hits = [k for k, b in enumerate(blocks) if cond(text(b[2]).lstrip(EM + ' '))]
    if len(hits) != 1:
        sys.exit('%s: %d matches' % (what, len(hits)))
    return hits[0]


def starts(prefix):
    return find(lambda t: t.startswith(prefix), prefix)


def is_blank(k):
    b = blocks[k][2]
    return b.startswith('<w:p') and not text(b) and '<w:drawing' not in b and '<w:sectPr' not in b


def comb(c):
    """Thai marks that sit on the preceding consonant."""
    return c in 'ั' or 'ิ' <= c <= 'ฺ' or '็' <= c <= '๎'


def wt(tag, t):
    sp = ' xml:space="preserve"' if t != t.strip() else ''
    return '<w:%s%s>%s</w:%s>' % (tag, sp, t, tag)


def edit(k, old, new=''):
    """Replace `old` with `new` in block k's text, across run boundaries."""
    b = blocks[k][2]
    full = ''.join(m.group(2) for m in WT_RE.finditer(b))
    at = full.find(old)
    if at < 0 or full.find(old, at + 1) >= 0:
        sys.exit('edit: %r found %d times in block %d' % (old, full.count(old), k))
    if not TRACK:
        end = at + len(old)
        ts = list(WT_RE.finditer(b))
        out, last, pos = [], 0, 0
        for m in ts:
            t = m.group(2)
            s, e = pos, pos + len(t)
            pos = e
            nt = t[:max(0, min(len(t), at - s))] + (new if s <= at < e else '') + t[max(0, min(len(t), end - s)):]
            open_tag = m.group(1)
            if nt != nt.strip() and 'xml:space' not in open_tag:
                open_tag = '<w:t xml:space="preserve">'
            out += [b[last:m.start()], open_tag, nt, m.group(3)]
            last = m.end()
        out.append(b[last:])
        blocks[k][2] = ''.join(out)
        return
    # tracked: delete/insert only the part that differs, never splitting a Thai cluster
    p = 0
    while p < min(len(old), len(new)) and old[p] == new[p]:
        p += 1
    s = 0
    while s < min(len(old), len(new)) - p and old[-1 - s] == new[-1 - s]:
        s += 1
    while p > 0 and ((p < len(old) and comb(old[p])) or (p < len(new) and comb(new[p]))):
        p -= 1
    while s > 0 and comb(old[len(old) - s]):
        s -= 1
    d0, d1, ins = at + p, at + len(old) - s, new[p:len(new) - s]
    out, last, pos, placed = [], 0, 0, False
    for m in RUN_RE.finditer(b):
        r = m.group(0)
        ts = list(WT_RE.finditer(r))
        if not ts:
            continue
        rs, re_ = pos, pos + sum(len(x.group(2)) for x in ts)
        pos = re_
        touches = (rs < d1 and re_ > d0) or (not placed and rs <= d0 < re_) or (not placed and d0 == re_ and d0 == d1 and False)
        if not touches:
            continue
        rpr = re.search(r'<w:rPr>.*?</w:rPr>', r, re.S)
        rpr = rpr.group(0) if rpr else ''
        if len(ts) != 1 or re.sub(r'^<w:r[^>]*>', '', r).replace(rpr, '', 1).replace(ts[0].group(0), '') != '</w:r>':
            sys.exit('edit: run in block %d holds more than text: %s' % (k, r[:120]))
        t = ts[0].group(2)
        a, z = max(0, d0 - rs), min(len(t), d1 - rs)
        pieces = []
        if t[:a]:
            pieces.append('<w:r>%s%s</w:r>' % (rpr, wt('t', t[:a])))
        if z > a:
            pieces.append('<w:del %s><w:r>%s%s</w:r></w:del>' % (rev(), rpr, wt('delText', t[a:z])))
        if not placed and rs <= d0 <= re_ and ins:
            pieces.append('<w:ins %s><w:r>%s%s</w:r></w:ins>' % (rev(), rpr, wt('t', ins)))
            placed = True
        if t[z:]:
            pieces.append('<w:r>%s%s</w:r>' % (rpr, wt('t', t[z:])))
        out += [b[last:m.start()], ''.join(pieces)]
        last = m.end()
    if ins and not placed:
        sys.exit('edit: nowhere to insert %r in block %d' % (ins, k))
    out.append(b[last:])
    blocks[k][2] = ''.join(out)


def sub_xml(k, old, new):
    b = blocks[k][2]
    if b.count(old) != 1:
        sys.exit('sub_xml: %d matches in block %d for %r' % (b.count(old), k, old[:80]))
    blocks[k][2] = b.replace(old, new)


def set_ppr(k, old_inner, new_inner):
    """Change a paragraph's pPr content (pStyle/ind/jc), tracked as a pPrChange."""
    if not TRACK:
        return sub_xml(k, '<w:pPr>%s</w:pPr>' % old_inner, '<w:pPr>%s</w:pPr>' % new_inner if new_inner else '')
    sub_xml(k, '<w:pPr>%s</w:pPr>' % old_inner,
            '<w:pPr>%s<w:pPrChange %s><w:pPr>%s</w:pPr></w:pPrChange></w:pPr>' % (new_inner, rev(), old_inner))


def math_run(t, italic=True):
    return ('<m:r><m:rPr><m:nor/></m:rPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
            'w:cs="Times New Roman"/>%s<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>%s</m:r>'
            % ('<w:i/><w:iCs/>' if italic else '', wt('m:t', t).replace('<w:m:t', '<m:t').replace('</w:m:t>', '</m:t>')))


def ins_math(r):
    return '<w:ins %s>%s</w:ins>' % (rev(), r) if TRACK else r


def swap_run(k, old_run, new_xml):
    """Replace a whole run by new XML (tracked: the old run is deleted)."""
    if not TRACK:
        return sub_xml(k, old_run, new_xml)
    m = re.match(r'(<w:r[^>]*>)(<w:rPr>.*?</w:rPr>)?<w:t( xml:space="preserve")?>([^<]*)</w:t></w:r>$', old_run)
    gone = '<w:del %s><w:r>%s%s</w:r></w:del>' % (rev(), m.group(2) or '', wt('delText', m.group(4)))
    sub_xml(k, old_run, gone + new_xml)


drop, after = set(), {}

# --- group A: text ----------------------------------------------------------------
edit(starts('หุ่นยนต์มี 4 ขา มอเตอร์รวม 8 ตัว'), 'เดินแบบทแยงมุม  คือ', 'เดินแบบทแยงมุม คือ')
k = starts('ตารางที่ 3 เทียบแบบจำลองทั้ง 5')
edit(k, 'ผู้วิจัยจึงใช้การถดถอย พหุนาม', 'ผู้วิจัยจึงใช้การถดถอยพหุนาม')
edit(k, 'ในการทดลองเดินทั้งหมด ', 'ในการทดลองเดินทั้งหมด')
edit(starts('กลไกน้ำหนักเบาย่อมให้ความแข็งเกร็งน้อยลง'), 'ดังกล่าว และ สร้าง', 'ดังกล่าว และสร้าง')
edit(starts('ก่อนเก็บข้อมูล ผู้วิจัยวัดความสูงทั้งสี่มุม'), 'คงที่ภายในแต่ละคู่ ', 'คงที่ภายในแต่ละคู่')
edit(starts('แรงเฉลี่ยจากการวัด 5 ครั้ง'), 'ใช้แรงดันไฟฟ้า 12 โวลต์ ', 'ใช้แรงดันไฟฟ้า 12 โวลต์')
edit(starts('Lightweight robot legs'), EM + ' Lightweight robot legs', EM + 'Lightweight robot legs')

# [-90,90] -> [-90, 90]: a normal-text space after the comma (Word drops plain spaces in maths)
k = starts('ข้อมูลฝึกสอนเก็บแบบสถิต')
comma = ('<m:t>90</m:t></m:r><m:r><m:rPr><m:sty m:val="p"/></m:rPr><w:rPr><w:rFonts w:ascii="Cambria Math" '
         'w:hAnsi="Cambria Math"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><m:t>,</m:t></m:r>')
sub_xml(k, comma, comma + ins_math(math_run(' ', italic=False)))

# the paragraph after eq. (6)
k = starts('แต่ละรอบเดินได้ระยะไม่เท่ากัน')
edit(k, 'ที่ละคู่', 'ทีละคู่')
edit(k, 'แต่ละรอบเดินได้ระยะไม่เท่ากัน', EM + 'แต่ละรอบเดินได้ระยะไม่เท่ากัน')
set_ppr(k, '<w:ind w:firstLine="280"/><w:jc w:val="thaiDistribute"/>', '<w:pStyle w:val="BodyText"/>')
swap_run(k, '<w:r w:rsidRPr="007107E4"><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
            '</w:rPr><w:t>δ</w:t></w:r>', '<m:oMath>%s</m:oMath>' % ins_math(math_run('δ')))
swap_run(k, '<w:r w:rsidRPr="007107E4"><w:t xml:space="preserve">D </w:t></w:r>',
         '<m:oMath>%s</m:oMath>' % ins_math(math_run('D'))
         + ('<w:ins %s><w:r><w:t xml:space="preserve"> </w:t></w:r></w:ins>' % rev() if TRACK
            else '<w:r><w:t xml:space="preserve"> </w:t></w:r>'))
blank7 = k + 1                                    # the empty paragraph above eq. (7) carried the same overrides
assert is_blank(blank7)
set_ppr(blank7, '<w:ind w:firstLine="280"/><w:jc w:val="thaiDistribute"/>', '')

# --- group A: blank lines -----------------------------------------------------------
k = starts('ผู้วิจัยเปรียบเทียบแบบจำลอง 5 ประเภท')       # 2.2.3, stray blank between its paragraphs
assert is_blank(k + 1) and text(blocks[k + 2][2]).lstrip(EM).startswith('แบบจำลองไม่ได้ถูกวัดผล')
drop.add(k + 1)
for head in ('3. ผลการทดลองและอภิปรายผลการทดลอง', '3.3 ผลของการชดเชยต่อการเดินจริง', '3.4 อภิปรายผล'):
    h = starts(head)
    assert is_blank(h - 1) and not is_blank(h - 2), head
    drop.add(h - 1)                                   # the heading's own 14 pt above is the one line


def figure_table(caption):
    hits = [k for k, b in enumerate(blocks) if b[2].startswith('<w:tbl>') and caption in text(b[2])]
    if len(hits) != 1:
        sys.exit('%s: %d figure tables' % (caption, len(hits)))
    return hits[0]


fig12 = figure_table('รูปที่ 1 (a)')
assert text(blocks[fig12 + 1][2]).startswith('2.2.3')
after[fig12] = True
fig45 = figure_table('รูปที่ 4 วิถีวงกลม')
assert blocks[fig45 - 1][2].startswith('<w:tbl>') and 'POLY3' in text(blocks[fig45 - 1][2])
after[fig45 - 1] = True

# --- group A: invisible -------------------------------------------------------------
sect = [k for k, b in enumerate(blocks) if '<w:sectPr' in b[2] and '<w:pStyle w:val="Heading2"/>' in b[2]]
assert len(sect) == 1 and not text(blocks[sect[0]][2])
if TRACK:
    b = blocks[sect[0]][2]
    rest = re.search(r'<w:pPr><w:pStyle w:val="Heading2"/>(.*?</w:sectPr>)</w:pPr>', b, re.S).group(1)
    sub_xml(sect[0], '<w:pPr><w:pStyle w:val="Heading2"/>' + rest + '</w:pPr>',
            '<w:pPr>%s<w:pPrChange %s><w:pPr><w:pStyle w:val="Heading2"/></w:pPr></w:pPrChange></w:pPr>' % (rest, rev()))
else:
    sub_xml(sect[0], '<w:pStyle w:val="Heading2"/>', '')

# --- group B --------------------------------------------------------------------------
k = find(lambda t: t.startswith('คำสำคัญ:'), 'Thai keywords')
edit(k, 'กลไกห้าชิ้นส่วน การ', 'กลไกห้าชิ้นส่วน, การ')
edit(k, 'ของเครื่อง เครื่องหมาย', 'ของเครื่อง, เครื่องหมาย')
edit(k, 'เชิงภาพ ภาระโหลด', 'เชิงภาพ, ภาระโหลด')
edit(starts('หุ่นยนต์สี่ขาได้รับความสนใจ'), 'ในงานสำรวจ และขนส่ง', 'ในงานสำรวจและขนส่ง')
edit(starts('วิธีที่นิยมในการเพิ่มอัตราส่วนนี้'), 'ลดมวลของขา และโครงสร้าง', 'ลดมวลของขาและโครงสร้าง')
edit(starts('ตำแหน่งจริงของปลายขาวัดด้วยกล้อง'), 'เครื่องหมายอ้างอิง ชนิด ArUco', 'เครื่องหมายอ้างอิงชนิด ArUco')
edit(starts('จากงานวิจัยที่ผ่านมา'), 'จากงานวิจัยที่ผ่านมาการแก้ปัญหานี้', 'จากงานวิจัยที่ผ่านมา การแก้ปัญหานี้')
old_cap = ('w:styleId="TableCaption"><w:name w:val="Table Caption"/><w:basedOn w:val="Normal"/>'
           '<w:qFormat/><w:pPr><w:keepNext/><w:keepLines/></w:pPr>')
if styles.count(old_cap) != 1:
    sys.exit('TableCaption style not as expected')
styles = styles.replace(old_cap, old_cap.replace(
    '<w:keepLines/></w:pPr>', '<w:keepLines/><w:spacing w:after="60"/><w:jc w:val="thaiDistribute"/></w:pPr>'))


# --- write ----------------------------------------------------------------------------
def dropped(b):
    """A blank paragraph removed: gone, or (tracked) its paragraph mark deleted."""
    if not TRACK:
        return ''
    mark = '<w:rPr><w:del %s/></w:rPr>' % rev()
    if b.endswith('/>'):
        return b[:-2] + '><w:pPr>%s</w:pPr></w:p>' % mark
    if '<w:pPr>' in b:
        assert '<w:rPr>' not in b and '<w:sectPr' not in b and '<w:pPrChange' not in b
        return b.replace('</w:pPr>', mark + '</w:pPr>', 1)
    return re.sub(r'^(<w:p[^>]*>)', r'\1<w:pPr>%s</w:pPr>' % mark.replace('\\', '\\\\'), b)


out, last = [], 0
for k, (s, e, b) in enumerate(blocks):
    out += [doc[last:s], dropped(b) if k in drop else b]
    if k in after:
        out.append('<w:p><w:pPr><w:rPr><w:ins %s/></w:rPr></w:pPr></w:p>' % rev() if TRACK else '<w:p/>')
    last = e
out.append(doc[last:])
new = ''.join(out)

if not TRACK:
    body = re.sub(r'<mc:Fallback>.*?</mc:Fallback>', '', new, flags=re.S)
    t = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', body))
    for bad in ('ทแยงมุม  ', 'การถดถอย พหุนาม', 'และ สร้าง', 'ที่ละคู่', EM + ' '):
        if bad in t:
            sys.exit('still there: %r' % bad)
    if 'w:ascii="Calibri"' in body:
        sys.exit('still there: Calibri')
print('%s: dropped %d blank paragraphs, added %d%s'
      % ('tracked' if TRACK else 'clean', len(drop), len(after), ', %d revisions' % (_rev[0] - 90000) if TRACK else ''))
parts['word/document.xml'] = new.encode('utf8')
parts['word/styles.xml'] = styles.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('wrote', dst)
