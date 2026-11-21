"""v13 = v12 with the English title matched word for word to the Thai one.

The Thai title stays as it was.  The English title had two words the Thai one
does not say: "Lightweight" (no "น้ำหนักเบา" in the Thai) and "Deflection",
which is also narrower than the paper's own finding - section 3.4 says the
error includes free play in the gears and joints, not deformation alone, and
the English abstract calls it "error" throughout.  Chosen by the author on
21 Nov 2026 (option 1):

    การชดเชยความคลาดเคลื่อนเชิงกลด้วยแนวทางเชิงข้อมูลสำหรับหุ่นยนต์สี่ขาที่อัตราส่วนแรงบิดต่อน้ำหนักสูง
    Data-Driven Compensation of Mechanical Error for a Quadruped Robot with a High Torque-to-Weight Ratio

The English title appears three times in document.xml: the title paragraph,
and the "Please cite this article as" text box (its DrawingML copy and the
VML fallback copy Word keeps for old readers).  All three change; the Thai
title, the running footer and the Thai citation box do not.

usage: python paper/make-v13.py V12.docx OUT.docx
"""
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')

OLD = 'Mechanical Deflection in a Lightweight Quadruped Robot'
NEW = 'Mechanical Error for a Quadruped Robot'
INNER_P = re.compile(r'<w:p(?:\s[^>]*)?>(?:(?!<w:p[\s>]).)*?</w:p>', re.S)   # paragraphs with no paragraph inside
WT_RE = re.compile(r'(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)')


def replace_across_runs(p):
    ts = list(WT_RE.finditer(p))
    full = ''.join(m.group(2) for m in ts)
    at = full.find(OLD)
    if at < 0:
        return p, 0
    if full.find(OLD, at + 1) >= 0:
        sys.exit('title found twice in one paragraph')
    end = at + len(OLD)
    out, last, pos = [], 0, 0
    for m in ts:
        t = m.group(2)
        s, e = pos, pos + len(t)
        pos = e
        nt = t[:max(0, min(len(t), at - s))] + (NEW if s <= at < e else '') + t[max(0, min(len(t), end - s)):]
        open_tag = m.group(1)
        if nt != nt.strip() and 'xml:space' not in open_tag:
            open_tag = '<w:t xml:space="preserve">'
        out += [p[last:m.start()], open_tag, nt, m.group(3)]
        last = m.end()
    out.append(p[last:])
    return ''.join(out), 1


count = [0]


def fix(m):
    p, n = replace_across_runs(m.group(0))
    count[0] += n
    return p


new = INNER_P.sub(fix, doc)
if count[0] != 3:
    sys.exit('expected the English title 3 times (title + citation box x2), found %d' % count[0])
if OLD in ''.join(m.group(2) for m in WT_RE.finditer(new)):
    sys.exit('old title still in the text')
parts['word/document.xml'] = new.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('English title replaced in %d places; wrote %s' % (count[0], dst))
