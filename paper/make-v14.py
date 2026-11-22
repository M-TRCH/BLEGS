"""v14 = v13 with one number corrected in section 3.2.

The full check of v12 (21 Nov 2026) recomputed every number from the raw
data.  One was off: "ทุกแบบลดความคลาดเคลื่อนได้ร้อยละ 53 ถึง 55".  From
python/paper_testing/test_2/output/data/dynamic_eval.csv the five models cut
the mean residual error by 54.8 (POLY3), 54.3 (MLP), 54.1 (RF), 53.3 (POLY4)
and 52.3 % (SVR), so the range is 52 to 55.  The author approved the fix on
22 Nov 2026.  Nothing else changes.

usage: python paper/make-v14.py V13.docx OUT.docx
"""
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
infos = zin.infolist()
parts = {i.filename: zin.read(i.filename) for i in infos}
doc = parts['word/document.xml'].decode('utf8')

OLD = 'ลดความคลาดเคลื่อนได้ร้อยละ 53 ถึง 55'
NEW = 'ลดความคลาดเคลื่อนได้ร้อยละ 52 ถึง 55'
INNER_P = re.compile(r'<w:p(?:\s[^>]*)?>(?:(?!<w:p[\s>]).)*?</w:p>', re.S)
WT_RE = re.compile(r'(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)')
count = [0]


def fix(m):
    p = m.group(0)
    ts = list(WT_RE.finditer(p))
    full = ''.join(t.group(2) for t in ts)
    at = full.find(OLD)
    if at < 0:
        return p
    count[0] += 1
    end = at + len(OLD)
    out, last, pos = [], 0, 0
    for t in ts:
        s, e = pos, pos + len(t.group(2))
        pos = e
        txt = t.group(2)
        nt = txt[:max(0, min(len(txt), at - s))] + (NEW if s <= at < e else '') + txt[max(0, min(len(txt), end - s)):]
        tag = t.group(1)
        if nt != nt.strip() and 'xml:space' not in tag:
            tag = '<w:t xml:space="preserve">'
        out += [p[last:t.start()], tag, nt, t.group(3)]
        last = t.end()
    out.append(p[last:])
    return ''.join(out)


new = INNER_P.sub(fix, doc)
if count[0] != 1:
    sys.exit('expected the phrase once, found %d' % count[0])
parts['word/document.xml'] = new.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('fixed 53 -> 52; wrote', dst)
