"""Anonymized copy of a finished manuscript .docx (the source file is only read).

Drops the Author / Affiliation / Corresponding paragraphs (Thai and English),
removes the author name from the running footers (title kept, as the -Anonymous
build does), and blanks the author fields in the document properties.
Fails loudly if anything identifying is left.

usage: python paper/anonymize-docx.py SRC.docx DST.docx
(used 19 Nov 2026 for the ThaiJO upload; run it again on every revised file -
the review is double-blind and revisions must stay anonymous)
"""
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
NAMES = ['ธีรโชติ', 'เมืองจำนงค์', 'Teerachot', 'Mueangchamnong',
         'm.teerachot', 'outlook.com', '4556 0911', 'วิทยาลัยเทคโนโลยีอุตสาหกรรม',
         'College of Industrial Technology',
         # the department, filled in since v8 (21 Nov 2026)
         'เทคโนโลยีวิศวกรรมเครื่องกล', 'Mechanical Engineering Technology']

zin = zipfile.ZipFile(src)
parts = {i.filename: zin.read(i.filename) for i in zin.infolist()}
infos = zin.infolist()

doc = parts['word/document.xml'].decode('utf8')
n_drop = 0


def drop(m):
    """Author and affiliation lines, and the corresponding-author line with the
    phone and e-mail.  Since v6 the Corresponding style also carries the
    template's received/accepted dates and copyright line - those stay."""
    global n_drop
    p = m.group(0)
    st = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    text = ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', p))
    if st and (st.group(1) in ('Author', 'Affiliation')
               or st.group(1) == 'Corresponding' and ('@' in text or 'โทรศัพท์' in text or 'Tel.' in text)):
        n_drop += 1
        return ''
    return p


# only plain paragraphs: a text box (v6's citation boxes) nests paragraphs inside one
doc = re.sub(r'<w:p\b[^>]*>(?:(?!</w:p>|<w:txbxContent>).)*</w:p>', drop, doc, flags=re.S)
if n_drop != 6:
    sys.exit('expected 6 author paragraphs, dropped %d' % n_drop)
# v6 on: the name also appears in the citation boxes and the CRediT statement
doc = doc.replace('ธีรโชติ เมืองจำนงค์ เป็น', 'ธีรโชติ เมืองจำนงค์เป็น')   # CRediT: no stray space once the name goes
doc, n_th = re.subn(r'ธีรโชติ เมืองจำนงค์', 'ผู้นิพนธ์', doc)
doc, n_en = re.subn(r'Mueangchamnong, T\.', 'Author, A.', doc)
parts['word/document.xml'] = doc.encode('utf8')

n_ftr = 0
for name in list(parts):
    if re.match(r'word/footer\d+\.xml$', name):
        x = parts[name].decode('utf8')
        new = re.sub(r'(<w:t[^>]*>)ธีรโชติ เมืองจำนงค์, ', r'\1', x)
        if new != x:
            n_ftr += 1
        parts[name] = new.encode('utf8')
if n_ftr != 2:
    sys.exit('expected 2 footers with the author name, changed %d' % n_ftr)

core = parts['docProps/core.xml'].decode('utf8')
core = re.sub(r'<dc:creator>[^<]*</dc:creator>', '<dc:creator></dc:creator>', core)
core = re.sub(r'<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>',
              '<cp:lastModifiedBy></cp:lastModifiedBy>', core)
parts['docProps/core.xml'] = core.encode('utf8')
if 'docProps/custom.xml' in parts:
    parts['docProps/custom.xml'] = parts['docProps/custom.xml'].replace(
        b'name="anonymous"><vt:lpwstr>False', b'name="anonymous"><vt:lpwstr>True')

left = []
for name, data in parts.items():
    if name.endswith('.xml') or name.endswith('.rels'):
        text = data.decode('utf8', 'ignore')
        left += ['%s: %s' % (name, k) for k in NAMES if k in text]
if left:
    sys.exit('identifying text left:\n  ' + '\n  '.join(left))

with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as out:
    for i in infos:
        out.writestr(i, parts[i.filename])
print('wrote', dst, '- dropped', n_drop, 'paragraphs, cleaned', n_ftr, 'footers,',
      'replaced the name %d (Thai) + %d (English) times in the body' % (n_th, n_en))
