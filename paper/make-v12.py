"""v12 = v11 with the AI-use declaration the author settled on (21 Nov 2026).

The declaration had been on hold, highlighted, since v6.  The author asked for
the research work (test code, analysis, plots) to lead and the manuscript
help to stay brief; the wording below still states every kind of help the
project record shows (git: all manuscript-draft commits and the English
abstract were done with Claude), so it remains a full disclosure as the
journal's checklist item 5 asks.  The highlight is removed.

usage: python paper/make-v12.py V11.docx OUT.docx
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

DECLARATION = (
    'ผู้นิพนธ์ใช้ Claude (Anthropic) เป็นเครื่องมือช่วยงานวิจัยด้านซอฟต์แวร์ ได้แก่ เขียนและแก้ไขโค้ดภาษา Python '
    'สำหรับควบคุมการเดินในการทดสอบ ปรับเทียบกล้องและประมวลผลภาพ วิเคราะห์ข้อมูลการวัดและทดสอบทางสถิติ '
    'และพล็อตกราฟ รูป และตาราง ในการเตรียมต้นฉบับ ใช้ช่วยเรียบเรียงจากเนื้อหาที่ผู้นิพนธ์กำหนด '
    'แปลบทคัดย่อเป็นภาษาอังกฤษ ตรวจคำ และจัดรูปแบบเอกสารและรายการอ้างอิงตามแม่แบบของวารสาร '
    'ผู้นิพนธ์ออกแบบวงจรและกลไก ประกอบหุ่นยนต์ เขียนเฟิร์มแวร์ควบคุมมอเตอร์ ทำการทดลอง '
    'และเก็บข้อมูลทั้งหมดด้วยตนเอง ตัวเลขทุกค่ามาจากการวัดจริง รูปทุกรูปวาดด้วยโค้ดจากข้อมูลที่วัดได้ '
    'ไม่ได้ใช้ AI สร้างภาพ ผู้นิพนธ์ตรวจสอบโค้ด ผลลัพธ์ และข้อความทั้งหมด และรับผิดชอบต่อเนื้อหาของบทความทุกส่วน')


def text(b):
    return ''.join(m.group(2) for m in WT_RE.finditer(b))


hits = [k for k, b in enumerate(blocks) if text(b[2]).startswith('ผู้นิพนธ์ใช้ Claude (Anthropic)')]
if len(hits) != 1:
    sys.exit('AI declaration: %d matches' % len(hits))
k = hits[0]
heading = text(blocks[k - 1][2])
if 'คำประกาศการใช้ AI' not in heading:
    sys.exit('the paragraph before is %r, not the AI heading' % heading)

# the whole text goes into the first text run; the other runs are emptied (formatting kept)
b = blocks[k][2]
ts = list(WT_RE.finditer(b))
out, last = [], 0
for n, m in enumerate(ts):
    out += [b[last:m.start()], m.group(1), DECLARATION if n == 0 else '', m.group(3)]
    last = m.end()
out.append(b[last:])
b = ''.join(out).replace('<w:highlight w:val="yellow"/>', '')
blocks[k][2] = b

out, last = [], 0
for s, e, blk in blocks:
    out += [doc[last:s], blk]
    last = e
out.append(doc[last:])
new = ''.join(out)
if '<w:highlight ' in new:
    sys.exit('a highlight is left in the document')
parts['word/document.xml'] = new.encode('utf8')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for i in infos:
        z.writestr(i, parts[i.filename])
print('wrote', dst)
