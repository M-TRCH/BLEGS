"""v8 = v6 without the physical-capability experiment.

The author reviewed the v7 cut proposal on 21 Nov 2026 and rejected it: no v5
paragraph is to be condensed (typo fixes only), and every table and figure that
helps the reader stays.  Instead, drop the last experiment - walking on real
surfaces under manual control - as a whole:

  * methods 2.3.3 with its two equations (turning command, cost of transport)
  * results 3.4 with table 5, and the two discussion paragraphs on it
  * the fourth limitation (and the 12 V sentence that closed it)
  * the last sentence of the Thai and the English abstract
  * Raibert (1986) and Tucker (1975), cited only there; later refs renumbered

Every other paragraph is v6's (= v5's text) word for word.  Also filled in:
the department (author, 21 Nov 2026), the CRediT statement (author-approved
wording), and the section number missing from 2.2.3 ("ตามหัวข้อ 2.2.4").  The AI
declaration is left as in v6, still highlighted - on hold.

Edits work on the text of a paragraph across its runs, so run formatting
(fonts, italics, the Arial combining macron) is kept.

usage: python paper/make-v8.py V6.docx OUT.docx
"""
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')

BLOCK_RE = re.compile(r'<w:tbl>.*?</w:tbl>|<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*[^/])?>.*?</w:p>', re.S)
WT_RE = re.compile(r'(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)')


def text(b):
    return ''.join(re.findall(r'<(?:w|m):t(?:\s[^>]*)?>([^<]*)</(?:w|m):t>', b))


blocks = [[m.start(), m.end(), m.group(0)] for m in BLOCK_RE.finditer(doc)]


def find(cond, what):
    hits = [k for k, b in enumerate(blocks) if cond(text(b[2]).lstrip('  '))]
    if len(hits) != 1:
        sys.exit('%s: %d matches' % (what, len(hits)))
    return hits[0]


def starts(prefix):
    return find(lambda t: t.startswith(prefix), prefix)


def style(k):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', blocks[k][2])
    return m.group(1) if m else None


def edit(k, old, new=''):
    """Replace `old` with `new` in block k's text, across run boundaries."""
    b = blocks[k][2]
    ts = list(WT_RE.finditer(b))
    full = ''.join(m.group(2) for m in ts)
    at = full.find(old)
    if at < 0 or full.find(old, at + 1) >= 0:
        sys.exit('edit: %r found %d times in block %d' % (old, full.count(old), k))
    end = at + len(old)
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


def unhighlight(k):
    blocks[k][2] = blocks[k][2].replace('<w:highlight w:val="yellow"/>', '')


drop = set()


def drop_range(first, stop):
    """Drop blocks first .. stop-1."""
    drop.update(range(first, stop))


# --- the experiment itself ------------------------------------------------------
m0 = starts('2.3.3 การหาขีดจำกัดทางกายภาพ')
m1 = starts('3. ผลการทดลองและอภิปรายผลการทดลอง')
assert style(m0) == 'Heading4' and style(m1) == 'Heading2'
drop_range(m0, m1)                                   # heading, 5 paragraphs, eq. (8), eq. (9)
r0 = starts('3.4 ขีดจำกัดทางกายภาพ')
r1 = starts('3.5 อภิปรายผล')
assert style(r0) == 'Heading3' and style(r1) == 'Heading3'
drop_range(r0, r1)                                   # heading, text, table 5 and caption, empty paragraph
n_tbl = sum(1 for k in range(r0, r1) if blocks[k][2].startswith('<w:tbl>'))
assert n_tbl == 1, n_tbl
surf = [k for k, b in enumerate(blocks) if text(b[2]).lstrip('  ').startswith('บนพื้นผิวจริง')]
assert len(surf) == 2, surf                          # v5 carries this paragraph twice
drop.update(surf)
drop.add(starts('[14]Raibert'))
drop.add(starts('[15]Tucker'))

# --- what refers to it ----------------------------------------------------------
edit(find(lambda t: t.startswith('ขาหุ่นยนต์ที่ออกแบบให้น้ำหนักเบา'), 'Thai abstract'),
     ' ส่วนการทดสอบแบบบังคับมือ หุ่นยนต์เดินบนพื้นราบ กรวด และโฟมผ่านทุกรอบของการทดลอง '
     'และขึ้นทางลาดได้ถึง 10 องศาเมื่อไม่มีโหลด และ 5 องศาที่โหลด 3 กิโลกรัม')
edit(find(lambda t: t.startswith('Lightweight robot legs'), 'English abstract'),
     ' Under manual remote control, the robot completed every trial on flat ground, gravel and foam, '
     'and climbed slopes of up to 10° without payload and 5° with 3 kg.')
lim = starts('งานวิจัยนี้มีข้อจำกัดสี่ประการ')
edit(lim, 'ข้อจำกัดสี่ประการ', 'ข้อจำกัดสามประการ')
t_lim = text(blocks[lim][2])
edit(lim, t_lim[t_lim.index(' ประการที่สี่'):])     # the fourth limitation to the end of the paragraph
edit(r1, '3.5 อภิปรายผล', '3.4 อภิปรายผล')

# references [16]-[19] become [14]-[17], in the text (section 3.1) and in the list
torque = starts('แรงเฉลี่ยจากการวัด 5 ครั้ง')
for old, new in (('[16]', '[14]'), ('[17]', '[15]'), ('[18]', '[16]'), ('[19]', '[17]')):
    edit(torque, old, new)
for old, new, who in (('[16]', '[14]', 'Hutter'), ('[17]', '[15]', 'Katz'),
                      ('[18]', '[16]', 'Grimminger'), ('[19]', '[17]', 'Unitree')):
    edit(starts(old + who), old, new)

# --- fixes and filled-in items ----------------------------------------------------
edit(starts('แบบจำลองไม่ได้ถูกวัดผลบนชุดฝึก'), 'ตามหัวข้อ ซึ่ง', 'ตามหัวข้อ 2.2.4 ซึ่ง')
k = starts('ภาควิชา……')
edit(k, 'ภาควิชา……………… ', 'ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล ')
unhighlight(k)
k = starts('Department of ……')
edit(k, 'Department of ………………, ', 'Department of Mechanical Engineering Technology, ')
unhighlight(k)
k = starts('ธีรโชติ เมืองจำนงค์ ออกแบบและวางกรอบงานวิจัย')
old = text(blocks[k][2]).lstrip('  ')
edit(k, old, 'ธีรโชติ เมืองจำนงค์ เป็นผู้ดำเนินงานวิจัยนี้เพียงผู้เดียว ได้แก่ วางแนวคิดและออกแบบวิธีการวิจัย '
             'ออกแบบวงจรขับมอเตอร์และกลไกขา ประกอบหุ่นยนต์ต้นแบบ พัฒนาเฟิร์มแวร์ควบคุมมอเตอร์และโปรแกรมควบคุมการเดิน '
             'ทำการทดลองและเก็บข้อมูลทั้งหมด วิเคราะห์และตรวจสอบผล และเขียนบทความ')
unhighlight(k)

# --- write --------------------------------------------------------------------------
out, last = [], 0
for k, (s, e, b) in enumerate(blocks):
    out += [doc[last:s], '' if k in drop else b]
    last = e
out.append(doc[last:])
new = ''.join(out)

t = re.sub(r'<[^>]+>', '', new)
for gone in ('ทางลาด', 'PZEM', 'ต้นทุนการขนส่ง', 'ตารางที่ 5', 'สมการที่ (8)', 'สมการที่ (9)',
             'Raibert', 'Tucker', '[18]', '[19]', 'ประการที่สี่', '……'):
    if gone in t:
        sys.exit('still in the text: ' + gone)
print('dropped %d blocks (%d tables); %d -> %d tables in the document'
      % (len(drop), n_tbl, doc.count('<w:tbl>'), new.count('<w:tbl>')))
parts['word/document.xml'] = new.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('wrote', dst)
