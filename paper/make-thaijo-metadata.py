"""ThaiJO_Metadata.txt - the text to paste into the ThaiJO forms, taken from a finished .docx.

Every field (titles, abstracts, keywords, references) is read from the
manuscript itself, so the form cannot drift from the file that is uploaded.
Re-run it on every revised version.

usage: python paper/make-thaijo-metadata.py MANUSCRIPT.docx OUT.txt PAGES
"""
import re
import sys
import zipfile

src, dst, pages = sys.argv[1], sys.argv[2], sys.argv[3]
doc = zipfile.ZipFile(src).read('word/document.xml').decode('utf8')
doc = re.sub(r'<mc:Fallback>.*?</mc:Fallback>', '', doc, flags=re.S)
doc = re.sub(r'<w:txbxContent>.*?</w:txbxContent>', '', doc, flags=re.S)   # the citation boxes nest paragraphs
BLOCK_RE = re.compile(r'<w:tbl>.*?</w:tbl>|<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*[^/])?>.*?</w:p>', re.S)


def text(b):
    b = re.sub(r'<w:txbxContent>.*?</w:txbxContent>', '', b, flags=re.S)
    out = []
    for m in re.finditer(r'<(w|m):t(?:\s[^>]*)?>([^<]*)</(?:w|m):t>|<w:tab/>', b):
        out.append(' ' if m.group(0) == '<w:tab/>' else m.group(2))
    s = ''.join(out).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\s+', ' ', s).strip()


def style(b):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', b)
    return m.group(1) if m else ''


P = [(style(b), text(b)) for b in BLOCK_RE.findall(doc) if b.startswith('<w:p')]
titles = [t for s, t in P if s == 'Title']
assert len(titles) == 2, titles
i_th = next(i for i, (s, t) in enumerate(P) if t == 'บทคัดย่อ')
i_en = next(i for i, (s, t) in enumerate(P) if t == 'Abstract')
abs_th = P[i_th + 1][1]
abs_en = P[i_en + 1][1]
kw_th = next(t for s, t in P if t.startswith('คำสำคัญ:')).split(':', 1)[1]
kw_en = next(t for s, t in P if t.startswith('Keywords:')).split(':', 1)[1]
kw_th = [k.strip() for k in kw_th.split(',')]
kw_en = [k.strip() for k in kw_en.split(',')]
refs = [t for s, t in P if s == 'Reference']
assert refs and all(re.match(r'\[\d+\] ', r) for r in refs), refs[:2]
n_words_en = len(abs_en.split())

RULE = '=' * 78
out = []
w = out.append
w('ข้อมูลสำหรับคัดลอกลงแบบฟอร์ม ThaiJO')
w('ดึงจากต้นฉบับ %s โดย paper/make-thaijo-metadata.py - ถ้าแก้ต้นฉบับอีก ให้รันใหม่' % src.replace('\\', '/').split('/')[-1])
w('กรอกทั้งช่องภาษาไทยและภาษาอังกฤษ ให้สัญลักษณ์ลูกโลกเป็นสีเขียว')
w('')
w(RULE); w('STEP 1: START'); w(RULE)
w('- ภาษา: ไทย · Section/Categories ถ้ามีให้เลือก')
w('- อ่าน Section Policy และ Submission Requirements ก่อนติ๊กทุกข้อ (จุดเดียวที่บอกเงื่อนไขเฉพาะวารสาร)')
w('- Comments for the Editor: คัดลอกจากหัวข้อท้ายไฟล์นี้ (ไม่บังคับ แต่แนะนำให้ใส่)')
w('- ยอมรับลิขสิทธิ์และนโยบายความเป็นส่วนตัว: ผู้นิพนธ์อ่านและกดเอง')
w('')
w(RULE); w('STEP 2: UPLOAD SUBMISSION - ลากไฟล์ลงพร้อมกันได้ แล้วเลือกประเภททีละไฟล์'); w(RULE)
w('BLEGS_Manuscript_Anonymous.docx   -> Article Text   (ฉบับปิดชื่อ: วารสารประเมินแบบ double-blind)')
w('BLEGS_Manuscript_Anonymous.pdf    -> Article Text   (รายการตรวจสอบข้อ 3 ขอทั้ง Word และ PDF)')
w('Figure1.jpg ... Figure5.jpg       -> Other')
w('Table1.jpg ... Table4.jpg         -> Other')
w('BLEGS_Manuscript.docx / .pdf      -> เก็บไว้ ใช้แทนฉบับปิดชื่อเฉพาะเมื่อ Step 1 สั่งให้ส่งฉบับมีชื่อ')
w('')
w(RULE); w('STEP 3: ENTER METADATA - Prefix และ Subtitle เว้นว่าง'); w(RULE)
w(''); w('TITLE (ไทย)'); w(titles[0])
w(''); w('TITLE (English)'); w(titles[1])
w(''); w('ABSTRACT (ไทย) - 1 ย่อหน้า'); w(abs_th)
w(''); w('ABSTRACT (English) - 1 ย่อหน้า, %d words' % n_words_en); w(abs_en)
w('')
w(RULE)
w('CONTRIBUTORS - ระบบใส่ชื่อผู้ส่งไว้แล้ว: กด ▸ หน้าชื่อ → Edit แล้วเติมให้ครบทั้งไทย/อังกฤษ')
w('ติ๊ก "Principal contact for editorial correspondence" และ "Include this contributor in browse lists"')
w(RULE)
w('Given name (EN): Teerachot          Family name (EN): Mueangchamnong')
w('ชื่อ (ไทย): ธีรโชติ                     นามสกุล (ไทย): เมืองจำนงค์')
w('Email: m.teerachot@outlook.com')
w('Country: Thailand')
w('Affiliation (EN): Department of Mechanical Engineering Technology, College of Industrial Technology, '
  'King Mongkut’s University of Technology North Bangkok')
w('สังกัด (ไทย): ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล วิทยาลัยเทคโนโลยีอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ')
w("Contributor's role: Author   (ไม่ใส่ยศหรือตำแหน่งในช่องชื่อ)")
w('ORCID: ใส่ถ้ามี (ไม่บังคับ)')
w('')
w(RULE); w('KEYWORDS - พิมพ์ทีละคำแล้วกด Enter'); w(RULE)
w('ไทย:'); out.extend(kw_th)
w(''); w('English:'); out.extend(kw_en)
w('')
w(RULE); w('SUPPORTING AGENCIES - เว้นว่าง (ไม่มีทุน)'); w(RULE)
w('')
w(RULE); w('REFERENCES - วางทั้งก้อน แต่ละรายการหนึ่งบรรทัด (%d รายการ, APA ตามแม่แบบ 2569)' % len(refs)); w(RULE)
out.extend(refs)
w('')
w(RULE); w('COMMENTS FOR THE EDITOR - ร่าง ตรวจและแก้ก่อนใช้'); w(RULE)
w('เรียน บรรณาธิการวารสารวิชาการพระจอมเกล้าพระนครเหนือ')
w('')
w('ผู้นิพนธ์ขอส่งบทความวิจัยเรื่อง "%s" (%s) เพื่อพิจารณาตีพิมพ์ในวารสาร '
  'บทความนี้เสนอการชดเชยความคลาดเคลื่อนของขาหุ่นยนต์สี่ขาน้ำหนักเบาด้วยแบบจำลองเชิงข้อมูล '
  'โดยไม่เพิ่มมวลหรือเซนเซอร์ และประเมินผลทั้งระดับขาเดี่ยวและการเดินจริง' % (titles[0], titles[1]))
w('')
w('บทความนี้ยังไม่เคยตีพิมพ์และไม่อยู่ระหว่างการพิจารณาของวารสารอื่น [ตรวจว่าเป็นจริง] '
  'ต้นฉบับจัดตามแม่แบบภาษาไทยของวารสารที่มีผลตั้งแต่ 1 ตุลาคม 2569 แนบทั้งไฟล์ Word และ PDF ฉบับปิดชื่อผู้นิพนธ์ '
  'พร้อมไฟล์ .jpg ของรูป 5 รูปและตาราง 4 ตาราง ต้นฉบับมีความยาว %s หน้า ซึ่งเกินกว่าที่แม่แบบแนะนำไว้ 12 หน้า '
  'หากต้องปรับความยาวหรือรูปแบบ ผู้นิพนธ์ยินดีแก้ไขตามคำแนะนำ' % pages)
w('')
w('[ย่อหน้านี้ใส่หรือไม่ก็ได้ - แนะนำให้ใส่] ผู้นิพนธ์ขอแจ้งว่าบทความนี้ใช้ AI เกินขอบเขตการขัดเกลาภาษาตามรายการตรวจสอบข้อ 5 '
  'รายละเอียดอยู่ในหัวข้อคำประกาศการใช้ AI เครื่องมือ AI และซอฟต์แวร์ท้ายบทความ ข้อมูลและผลการทดลองทั้งหมดมาจากการวัดจริง '
  'และผู้นิพนธ์ได้ตรวจสอบทุกส่วนแล้ว หากขอบเขตนี้ไม่สอดคล้องกับนโยบายของวารสาร ผู้นิพนธ์ขอรับคำแนะนำก่อนเข้าสู่กระบวนการพิจารณา')
w('')
w('ขอแสดงความนับถือ')
w('ธีรโชติ เมืองจำนงค์')

with open(dst, 'w', encoding='utf-8-sig', newline='\r\n') as f:
    f.write('\n'.join(out) + '\n')
print('wrote %s: %d references, keywords %d/%d, English abstract %d words' % (dst, len(refs), len(kw_th), len(kw_en), n_words_en))
