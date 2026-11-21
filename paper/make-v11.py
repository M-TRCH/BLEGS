"""v11 = v10 with two reference fixes from the 21 Nov 2026 reference check.

Every reference was checked against its publisher's record (Crossref for the
14 DOIs, the ISBN for Tsai, the maker's documents for the datasheet and the
Unitree page; notes in manuscript/submission/NEW_TEMPLATE_PLAN.md).  All 17
are real and published; two entries needed fixing, and the author approved
both:

  [8]  APA keeps the hyphen in initials of hyphenated given names
       (Hoai-Nhan, Hee-Jun): "Nguyen, H.-N." and "Kang, H.-J."
  [9]  the datasheet's full title ends "... for 28krpm high speed
       capability"; the maker's product page URL is added

Edits work on the text across runs, so the italics of the datasheet title
are kept.

usage: python paper/make-v11.py V10.docx OUT.docx
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
blocks = [[m.start(), m.end(), m.group(0)] for m in BLOCK_RE.finditer(doc)]


def text(b):
    return ''.join(m.group(2) for m in WT_RE.finditer(b))


def ref(n):
    hits = [k for k, b in enumerate(blocks) if '<w:pStyle w:val="Reference"/>' in b[2] and text(b[2]).startswith('[%d]' % n)]
    if len(hits) != 1:
        sys.exit('reference [%d]: %d matches' % (n, len(hits)))
    return hits[0]


def edit(k, old, new):
    """Replace `old` with `new` in block k's text; `new` goes into the run where `old` starts."""
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


k = ref(8)
edit(k, 'Nguyen, H. N.,', 'Nguyen, H.-N.,')
edit(k, 'Kang, H. J. (2015)', 'Kang, H.-J. (2015)')
k = ref(9)
edit(k, 'incremental pulse count', 'incremental pulse count for 28krpm high speed capability')   # inside the italic title
edit(k, '(Datasheet v2-00).', '(Datasheet v2-00). https://ams-osram.com/as5047p')

out, last = [], 0
for s, e, b in blocks:
    out += [doc[last:s], b]
    last = e
out.append(doc[last:])
parts['word/document.xml'] = ''.join(out).encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('wrote', dst)
