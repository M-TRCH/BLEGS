"""Build v6: the author's finished v5 moved onto the journal's template of 1 Oct 2026 (2569).

usage: python paper/make-v6.py V5.docx TEMPLATE.docx OUT.docx

v5 (the author's Word master, proofread by hand on 17 Nov 2026) is only read.
TEMPLATE is the journal's "Thai ver. template ใหม่ เริ่มใช้ 1 ต.ค. 2569.docx"
(Google Drive folder linked from the journal's Submissions page).

What changes, and nothing else (the text the author wrote is kept verbatim):
  page      18.7 x 26.0 cm, one column, margins 3.05/2.0/1.8/1.2 cm + 0.5 cm
            gutter, mirrored - the template's own section settings
  header    the template's odd/even journal header (crest, page number)
  page 1-2  "บทความวิจัย" / "Research Article" label, DOI and dates line,
            copyright line, citation box at the foot of each page (the
            template's own text boxes), department placeholder in the
            affiliation; the English page and the introduction each start a page
  sections  "3. ผลการทดลองและอภิปรายผลการทดลอง" with the discussion as 3.5,
            "4. สรุปผลการทดลอง" for the closing paragraph
  end       the four declarations the template now asks for, as drafts
  refs      the 19 references rewritten in APA (numbers in the text unchanged)
Yellow highlight = text the author still has to supply or confirm.
"""
import re
import sys
import zipfile

V5, TPL, OUT = sys.argv[1:4]

src = zipfile.ZipFile(V5)
parts = {i.filename: src.read(i.filename) for i in src.infolist()}
order = [i.filename for i in src.infolist()]
tpl = zipfile.ZipFile(TPL)
tdoc = tpl.read('word/document.xml').decode('utf8')

doc = parts['word/document.xml'].decode('utf8')

# text width of the template's body section: 10603 - 1021 - 680 - 284 twips
TEXT_W = 8618
PARA_RE = re.compile(r'<w:p(?:\s[^>]*)?/>|<w:p(?:\s[^>]*[^/])?>.*?</w:p>', re.S)


def ptext(p):
    return ''.join(re.findall(r'<(?:w|m):t(?: [^>]*)?>([^<]*)</(?:w|m):t>', p))


def find_para(cond, what):
    hits = [m for m in PARA_RE.finditer(doc) if cond(m.group(0))]
    if len(hits) != 1:
        sys.exit('%s: %d paragraphs match' % (what, len(hits)))
    return hits[0]


def by_text(start, style=None):
    def cond(p):
        if not ptext(p).lstrip('  ').startswith(start):
            return False
        return style is None or ('<w:pStyle w:val="%s"/>' % style) in p
    return cond


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def run(text, italic=False, hl=False, cs=None, extra=''):
    if cs is None:
        cs = bool(re.search('[฀-๿]', text))
    rpr = ('<w:i/><w:iCs/>' if italic else '') + extra + \
          ('<w:highlight w:val="yellow"/>' if hl else '') + ('<w:cs/>' if cs else '')
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (
        '<w:rPr>%s</w:rPr>' % rpr if rpr else '', esc(text))


def para(style, runs, ppr_extra=''):
    return '<w:p><w:pPr><w:pStyle w:val="%s"/>%s</w:pPr>%s</w:p>' % (style, ppr_extra, ''.join(runs))


def replace_span(m, new):
    global doc
    doc = doc[:m.start()] + new + doc[m.end():]


def insert_before(m, new):
    global doc
    doc = doc[:m.start()] + new + doc[m.start():]


def insert_after(m, new):
    global doc
    doc = doc[:m.end()] + new + doc[m.end():]


def bookmarks(p):
    return ''.join(re.findall(r'<w:bookmark(?:Start|End)\b[^>]*/>', p))


# ---- page setup: every section takes the template's body-section values ----
def fix_sect(m):
    s = m.group(0)
    s = re.sub(r'<w:pgSz [^>]*/>', '<w:pgSz w:w="10603" w:h="14742" w:code="263"/>', s)
    s = re.sub(r'<w:pgMar [^>]*/>', '<w:pgMar w:top="1729" w:right="680" w:bottom="1134" '
               'w:left="1021" w:header="1134" w:footer="1021" w:gutter="284"/>', s)
    s = re.sub(r'<w:cols [^>]*/>', '<w:cols w:space="567"/>', s)
    s = s.replace('<w:type w:val="continuous"/>', '')   # the introduction starts a page
    return s


doc, n = re.subn(r'<w:sectPr\b[^>]*>.*?</w:sectPr>', fix_sect, doc, flags=re.S)
if n != 2:
    sys.exit('expected 2 sections, found %d' % n)

# ---- front pages ----------------------------------------------------------
def label(text):
    return ('<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="1" w:color="000000"/>'
            '<w:left w:val="single" w:sz="4" w:space="4" w:color="000000"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="1" w:color="000000"/>'
            '<w:right w:val="single" w:sz="4" w:space="4" w:color="000000"/></w:pBdr>'
            '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/><w:spacing w:before="0" w:after="120"/>'
            '<w:ind w:left="0" w:right="%d"/><w:jc w:val="center"/></w:pPr>%s</w:p>'
            % (TEXT_W - 1531, run(text, extra='<w:sz w:val="26"/><w:szCs w:val="26"/>')))


m = find_para(lambda p: '<w:pStyle w:val="Title"/>' in p and 'การชดเชย' in ptext(p), 'Thai title')
title_th = ptext(m.group(0)).strip()
insert_before(m, label('บทความวิจัย'))
m = find_para(lambda p: '<w:pStyle w:val="Title"/>' in p and 'Data-Driven' in ptext(p), 'English title')
title_en = ptext(m.group(0)).strip()
insert_before(m, label('Research Article'))

DOI = '        DOI: 10.14416/j.kmutnb.2026.xx.xxx'
COPY = '© 2026 King Mongkut’s University of Technology North Bangkok. All Rights Reserved.'
for start, dates in (
        ('* ผู้นิพนธ์ประสานงาน', 'รับเมื่อ xx เดือน xxxx แก้ไขเมื่อ xx เดือน xxxx ตอบรับเมื่อ xx เดือน xxxx '
                                 'เผยแพร่ออนไลน์ xx เดือน xxxx'),
        ('* Corresponding Author', 'Received xx Month xxxx; Revised xx Month xxxx; Accepted xx Month xxxx; '
                                   'Published online: xx Month xxxx')):
    m = find_para(by_text(start, 'Corresponding'), start)
    p = m.group(0)
    p = p[:-len('</w:p>')] + run(DOI, cs=False) + '</w:p>'
    p = p.replace('<w:pStyle w:val="Corresponding"/>', '<w:pStyle w:val="Corresponding"/><w:spacing w:before="140"/>', 1)
    tight = '<w:spacing w:before="0"/>'
    replace_span(m, p + para('Corresponding', [run(dates)], tight) + para('Corresponding', [run(COPY, cs=False)], tight))

for start, dept in (('วิทยาลัยเทคโนโลยีอุตสาหกรรม', 'ภาควิชา……………… '),
                    ('College of Industrial Technology', 'Department of ………………, ')):
    m = find_para(by_text(start, 'Affiliation'), start)
    p = m.group(0)
    i = p.index('</w:pPr>') + len('</w:pPr>')
    replace_span(m, p[:i] + run(dept, hl=True) + p[i:])

# citation boxes: the template's own text boxes, refilled
acs = re.findall(r'<mc:AlternateContent>.*?</mc:AlternateContent>', tdoc, re.S)
box_th = next(x for x in acs if 'การอ้างอิงบทความ' in x)
box_en = next(x for x in acs if 'Please cite' in x)
BOX_RPR = ('<w:rFonts w:eastAsia="Times New Roman"/><w:color w:val="000000"/>'
           '<w:sz w:val="24"/><w:szCs w:val="24"/>')


def box_para(segs):
    runs = ''.join(run(t, italic=i, extra=BOX_RPR) for t, i in segs)
    return ('<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="425"/></w:tabs><w:overflowPunct/>'
            '<w:spacing w:line="216" w:lineRule="auto"/><w:jc w:val="both"/>'
            '<w:textAlignment w:val="center"/></w:pPr>%s</w:p>' % runs)


def refill(box, segs, docpr):
    body = box_para(segs)
    box = re.sub(r'<w:txbxContent>.*?</w:txbxContent>', lambda _: '<w:txbxContent>%s</w:txbxContent>' % body,
                 box, flags=re.S)
    box = re.sub(r'<wp:docPr id="\d+"', '<wp:docPr id="%d"' % docpr, box)
    box = box.replace('<a:noAutofit/>', '<a:spAutoFit/>')
    box = box.replace('<wp:wrapNone/>', '<wp:wrapTopAndBottom/>')   # text never runs under the box
    return '<w:r><w:rPr><w:noProof/></w:rPr>%s</w:r>' % box


cite_th = [('การอ้างอิงบทความ: ธีรโชติ เมืองจำนงค์. (25xx). %s. ' % title_th, False),
           ('วารสารวิชาการพระจอมเกล้าพระนครเหนือ', True),
           (', 3x(x), หน้า 1–xx, เลขที่บทความ 2xx-xxxxxx. http://dx.doi.org/10.14416/j.kmutnb.20xx.xx.xxx', False)]
cite_en = [('Please cite this article as: Mueangchamnong, T. (20xx). %s. ' % title_en, False),
           ('The Journal of KMUTNB', True),
           (', 3x(x), 1–xx, Art. no. 2xx-xxxxxx. http://dx.doi.org/10.14416/j.kmutnb.20xx.xx.xxx (in Thai)', False)]
for start, box, segs, pid in (('คำสำคัญ:', box_th, cite_th, 9101), ('Keywords:', box_en, cite_en, 9102)):
    m = find_para(by_text(start), start)
    p = m.group(0)
    replace_span(m, p[:-len('</w:p>')] + refill(box, segs, pid) + '</w:p>')

# ---- sections 3 and 4 -------------------------------------------------------
m = find_para(lambda p: ptext(p).strip() == '3. ผลการทดลอง', 'section 3 heading')
replace_span(m, para('Heading2', [bookmarks(m.group(0)), run('3. ผลการทดลองและอภิปรายผลการทดลอง')]))
m = find_para(lambda p: ptext(p).strip() == '4. อภิปรายผลและสรุป', 'discussion heading')
replace_span(m, para('Heading3', [bookmarks(m.group(0)), run('3.5 อภิปรายผล')]))
m = find_para(by_text('โดยสรุป'), 'conclusion')
insert_before(m, para('Heading2', [run('4. สรุปผลการทดลอง')]))
concl = m  # positions shifted; look it up again below

# v5 still carries two versions of the surface-test paragraph - flag the older one
m = find_para(lambda p: 'ผลชุดนี้จึงเป็นขีดความสามารถพื้นฐาน' in ptext(p), 'older duplicate paragraph')
p = re.sub(r'<w:rPr>', '<w:rPr><w:highlight w:val="yellow"/>', m.group(0))
p = re.sub(r'<w:r>(?!<w:rPr>)', '<w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr>', p)
replace_span(m, p)

# ---- declarations (drafts for the author) -----------------------------------
EM = ' '
decl = [
    ('คำประกาศเรื่องผลประโยชน์ทับซ้อน',
     [run(EM + 'ผู้นิพนธ์ไม่มีประเด็นเรื่องผลประโยชน์ทับซ้อนกับเนื้อหาของบทความนี้')]),
    ('คำประกาศการมีส่วนร่วมของผู้ประพันธ์',
     [run(EM + 'ธีรโชติ เมืองจำนงค์ ออกแบบและวางกรอบงานวิจัย สร้างหุ่นยนต์ต้นแบบ ทำการทดลอง '
               'วิเคราะห์ข้อมูล และเขียนบทความ', hl=True)]),
    ('คำประกาศการใช้ AI เครื่องมือ AI และซอฟต์แวร์',
     [run(EM + 'ผู้นิพนธ์ใช้ Claude (Anthropic) ช่วยเรียบเรียงและขัดเกลาภาษาของต้นฉบับ แปลบทคัดย่อเป็นภาษาอังกฤษ '
               'เขียนโปรแกรมสำหรับวิเคราะห์ข้อมูลและสร้างรูป และจัดรูปแบบเอกสาร ผู้นิพนธ์ตรวจสอบผลและเนื้อหาทั้งหมด '
               'และรับผิดชอบต่อความถูกต้องของบทความ', hl=True)]),
    ('คำประกาศเรื่องจริยธรรม',
     [run(EM + 'งานวิจัยนี้ไม่มีกิจกรรมที่เกี่ยวข้องกับมนุษย์หรือสัตว์ทดลองที่ต้องขออนุมัติจากคณะกรรมการพิจารณาจริยธรรม')]),
]
m = find_para(lambda p: ptext(p).strip() == 'เอกสารอ้างอิง' and 'Heading2' in p, 'references heading')
insert_before(m, ''.join(para('Heading2', [run(h)]) + para('BodyText', body) for h, body in decl))

# ---- references in APA -------------------------------------------------------
I = True
APA = {
    1: [('Biswal, P., & Mohanty, P. K. (2021). Development of quadruped walking robots: A review. ', 0),
        ('Ain Shams Engineering Journal, 12', I), ('(2), 2017–2031. https://doi.org/10.1016/j.asej.2020.11.005', 0)],
    2: [('Lee, J., Hwangbo, J., Wellhausen, L., Koltun, V., & Hutter, M. (2020). Learning quadrupedal locomotion '
         'over challenging terrain. ', 0), ('Science Robotics, 5', I),
        ('(47), Article eabc5986. https://doi.org/10.1126/scirobotics.abc5986', 0)],
    3: [('Seok, S., Wang, A., Chuah, M. Y., Hyun, D. J., Lee, J., Otten, D. M., Lang, J. H., & Kim, S. (2015). '
         'Design principles for energy-efficient legged locomotion and implementation on the MIT Cheetah robot. ', 0),
        ('IEEE/ASME Transactions on Mechatronics, 20', I),
        ('(3), 1117–1129. https://doi.org/10.1109/TMECH.2014.2339013', 0)],
    4: [('Kenneally, G., De, A., & Koditschek, D. E. (2016). Design principles for a family of direct-drive legged '
         'robots. ', 0), ('IEEE Robotics and Automation Letters, 1', I),
        ('(2), 900–907. https://doi.org/10.1109/LRA.2016.2528294', 0)],
    5: [('Tsai, L.-W. (1999). ', 0), ('Robot analysis: The mechanics of serial and parallel manipulators', I),
        ('. Wiley.', 0)],
    6: [('Ananthanarayanan, A., Azadi, M., & Kim, S. (2012). Towards a bio-inspired leg design for high-speed '
         'running. ', 0), ('Bioinspiration & Biomimetics, 7', I),
        ('(4), Article 046005. https://doi.org/10.1088/1748-3182/7/4/046005', 0)],
    7: [('Valsecchi, G., Grandia, R., & Hutter, M. (2020). Quadrupedal locomotion on uneven terrain with sensorized '
         'feet. ', 0), ('IEEE Robotics and Automation Letters, 5', I),
        ('(2), 1548–1555. https://doi.org/10.1109/LRA.2020.2969160', 0)],
    8: [('Nguyen, H. N., Zhou, J., & Kang, H. J. (2015). A calibration method for enhancing robot accuracy through '
         'integration of an extended Kalman filter algorithm and an artificial neural network. ', 0),
        ('Neurocomputing, 151', I), (', 996–1005. https://doi.org/10.1016/j.neucom.2014.03.085', 0)],
    9: [('ams-OSRAM AG. (2021). ', 0),
        ('AS5047P: 14-bit on-axis magnetic rotary position sensor with 12-bit decimal and binary incremental '
         'pulse count', I), (' (Datasheet v2-00).', 0)],
    10: [('Pillay, P., & Krishnan, R. (1989). Modeling, simulation, and analysis of permanent-magnet motor drives. '
          'I. The permanent-magnet synchronous motor drive. ', 0),
         ('IEEE Transactions on Industry Applications, 25', I),
         ('(2), 265–273. https://doi.org/10.1109/28.25541', 0)],
    11: [('Garrido-Jurado, S., Muñoz-Salinas, R., Madrid-Cuevas, F. J., & Marín-Jiménez, M. J. (2014). Automatic '
          'generation and detection of highly reliable fiducial markers under occlusion. ', 0),
         ('Pattern Recognition, 47', I), ('(6), 2280–2292. https://doi.org/10.1016/j.patcog.2014.01.005', 0)],
    12: [('Zhang, Z. (2000). A flexible new technique for camera calibration. ', 0),
         ('IEEE Transactions on Pattern Analysis and Machine Intelligence, 22', I),
         ('(11), 1330–1334. https://doi.org/10.1109/34.888718', 0)],
    13: [('Hyun, D. J., Seok, S., Lee, J., & Kim, S. (2014). High speed trot-running: Implementation of a '
          'hierarchical controller using proprioceptive impedance control on the MIT Cheetah. ', 0),
         ('The International Journal of Robotics Research, 33', I),
         ('(11), 1417–1445. https://doi.org/10.1177/0278364914532150', 0)],
    14: [('Raibert, M. H. (1986). ', 0), ('Legged robots that balance', I), ('. MIT Press.', 0)],
    15: [('Tucker, V. A. (1975). The energetic cost of moving about. ', 0), ('American Scientist, 63', I),
         ('(4), 413–419.', 0)],
    16: [('Hutter, M., Gehring, C., Jud, D., Lauber, A., Bellicoso, C. D., Tsounis, V., Hwangbo, J., Bodie, K., '
          'Fankhauser, P., Bloesch, M., Diethelm, R., Bachmann, S., Melzer, A., & Hoepflinger, M. (2016). ANYmal – '
          'A highly mobile and dynamic quadrupedal robot. In ', 0),
         ('2016 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)', I),
         (' (pp. 38–44). IEEE. https://doi.org/10.1109/IROS.2016.7758092', 0)],
    17: [('Katz, B., Di Carlo, J., & Kim, S. (2019). Mini Cheetah: A platform for pushing the limits of dynamic '
          'quadruped control. In ', 0), ('2019 International Conference on Robotics and Automation (ICRA)', I),
         (' (pp. 6295–6301). IEEE. https://doi.org/10.1109/ICRA.2019.8793865', 0)],
    18: [('Grimminger, F., Meduri, A., Khadiv, M., Viereck, J., Wüthrich, M., Naveau, M., Berenz, V., Heim, S., '
          'Widmaier, F., Flayols, T., Fiene, J., Badri-Spröwitz, A., & Righetti, L. (2020). An open '
          'torque-controlled modular robot architecture for legged locomotion research. ', 0),
         ('IEEE Robotics and Automation Letters, 5', I),
         ('(2), 3650–3657. https://doi.org/10.1109/LRA.2020.2976639', 0)],
    19: [('Unitree Robotics. (n.d.). ', 0), ('Go2 quadruped robot — specifications', I),
         ('. Retrieved October 9, 2026, from https://www.unitree.com/go2', 0)],
}
for n, segs in APA.items():
    m = find_para(lambda p, n=n: '<w:pStyle w:val="Reference"/>' in p and ptext(p).startswith('[%d]' % n), 'ref %d' % n)
    old = ptext(m.group(0))
    head = '<w:p><w:pPr><w:pStyle w:val="Reference"/></w:pPr><w:r><w:t>[%d]</w:t></w:r><w:r><w:tab/></w:r>' % n
    replace_span(m, head + ''.join(run(t, italic=bool(i), cs=False) for t, i in segs) + '</w:p>')

# ---- tables: one 7.5 cm column -> the full text width, same proportions ------
def widen(m):
    t = m.group(0)
    w0 = int(re.search(r'<w:tblW w:w="(\d+)" w:type="dxa"/>', t).group(1))
    f = TEXT_W / w0
    t = re.sub(r'<w:tblW w:w="\d+" w:type="dxa"/>', '<w:tblW w:w="%d" w:type="dxa"/>' % TEXT_W, t)
    t = re.sub(r'(<w:(?:gridCol|tcW) w:w=")(\d+)"', lambda g: '%s%d"' % (g.group(1), round(int(g.group(2)) * f)), t)
    t = t.replace('<w:sz w:val="22"/>', '<w:sz w:val="24"/>').replace('<w:szCs w:val="22"/>', '<w:szCs w:val="24"/>')
    return t


doc, n = re.subn(r'<w:tbl>.*?</w:tbl>', widen, doc, flags=re.S)
if n != 5:
    sys.exit('expected 5 tables, found %d' % n)


# ---- figures: 7.5 cm wide in a 15.2 cm column -> two to a row ------------------
# Figures 1 and 2 are first cited in consecutive paragraphs of 2.2.1; figure 4 at
# the end of 3.2 and figure 5 at the start of 3.3, so that pair sits between the two.
def cut_figure(num):
    """Remove figure `num` (picture paragraph, caption, and the blank line the build
    put under the caption); return the picture and caption paragraphs."""
    global doc
    cap = find_para(lambda p: '<w:pStyle w:val="ImageCaption"/>' in p and ptext(p).startswith('รูปที่ %d ' % num),
                    'caption %d' % num)
    figs = [m for m in PARA_RE.finditer(doc, 0, cap.start()) if '<wp:inline' in m.group(0)]
    fig = figs[-1]
    after = PARA_RE.match(doc, cap.end())
    end = after.end() if after and not ptext(after.group(0)).strip() and '<w:drawing' not in after.group(0) else cap.end()
    fig_xml, cap_xml = fig.group(0), cap.group(0)
    between = doc[fig.end():cap.start()]
    if PARA_RE.sub('', between).strip() or ptext(between).strip() or '<w:drawing' in between:
        sys.exit('figure %d: something other than empty lines between picture and caption' % num)
    doc = doc[:fig.start()] + doc[end:]
    return fig.start(), fig_xml, cap_xml


NOB = ''.join('<w:%s w:val="nil"/>' % s for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
HALF = TEXT_W // 2


def pair(a, b):
    def row(cells, valign):
        return ('<w:tr><w:trPr><w:cantSplit/></w:trPr>%s</w:tr>' % ''.join(
            '<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:vAlign w:val="%s"/></w:tcPr>%s</w:tc>'
            % (HALF, valign, c) for c in cells))
    return ('<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/>'
            '<w:tblBorders>%s</w:tblBorders><w:tblLayout w:type="fixed"/>'
            '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
            '<w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
            'w:noHBand="1" w:noVBand="1"/></w:tblPr><w:tblGrid><w:gridCol w:w="%d"/><w:gridCol w:w="%d"/>'
            '</w:tblGrid>%s%s</w:tbl>'
            % (TEXT_W, NOB, HALF, HALF, row((a[1], b[1]), 'bottom'), row((a[2], b[2]), 'top')))


f2 = cut_figure(2)
f1 = cut_figure(1)
doc = doc[:f1[0]] + pair(f1, f2) + doc[f1[0]:]
f5 = cut_figure(5)
f4 = cut_figure(4)
m = find_para(by_text('3.3 ', 'Heading3'), 'heading 3.3')
insert_before(m, pair(f4, f5) + '<w:p/>')

parts['word/document.xml'] = doc.encode('utf8')

# ---- styles: equation numbers flush with the new, wider text block ------------
styles = parts['word/styles.xml'].decode('utf8')
styles, n = re.subn(r'(<w:style [^>]*w:styleId="Equation".*?<w:tab w:val="right" w:pos=")4252(")',
                    r'\g<1>%d\2' % TEXT_W, styles, flags=re.S)
if n != 1:
    sys.exit('Equation style tab not found')
# the template's header paragraphs use two of its own styles; without them they
# fall back to 14 pt Normal and the journal line is cut off
tstyles = tpl.read('word/styles.xml').decode('utf8')
for sid in ('12', 'BasicParagraph'):
    if 'w:styleId="%s"' % sid not in styles:
        s = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, tstyles, re.S).group(0)
        s = re.sub(r'<w:link w:val="[^"]*"/>|<w:rsid w:val="[^"]*"/>', '', s)
        styles = styles.replace('</w:styles>', s + '</w:styles>')
# APA entries end in long DOIs; justified, those lines open wide gaps
styles, n = re.subn(r'(<w:style [^>]*w:styleId="Reference"(?:(?!</w:style>).)*?)<w:jc w:val="both"/>', r'\1<w:jc w:val="left"/>',
                    styles, flags=re.S)
if n != 1:
    sys.exit('Reference style alignment not found')
parts['word/styles.xml'] = styles.encode('utf8')

# ---- settings: mirrored margins, as in the template ---------------------------
st = parts['word/settings.xml'].decode('utf8')
if '<w:mirrorMargins/>' not in st:
    st = st.replace('<w:embedSystemFonts/>', '<w:embedSystemFonts/><w:mirrorMargins/>', 1)
    if '<w:mirrorMargins/>' not in st:
        sys.exit('settings: anchor for mirrorMargins not found')
parts['word/settings.xml'] = st.encode('utf8')

# ---- headers: the template's body-section pair (even = header4, odd = header5) --
ct = parts['[Content_Types].xml'].decode('utf8')
if 'Extension="jpeg"' not in ct:
    ct = ct.replace('<Default Extension="jpg"', '<Default Extension="jpeg" ContentType="image/jpeg"/>'
                    '<Default Extension="jpg"', 1)
parts['[Content_Types].xml'] = ct.encode('utf8')
for mine, theirs in (('header1', 'header4'), ('header2', 'header5')):
    parts['word/%s.xml' % mine] = tpl.read('word/%s.xml' % theirs)
    rels = tpl.read('word/_rels/%s.xml.rels' % theirs).decode('utf8')
    for tgt in sorted(set(re.findall(r'Target="media/([^"]+)"', rels))):
        new = 'tpl2569_' + tgt
        rels = rels.replace('Target="media/%s"' % tgt, 'Target="media/%s"' % new)
        if 'word/media/' + new not in parts:
            parts['word/media/' + new] = tpl.read('word/media/' + tgt)
            order.append('word/media/' + new)
    parts['word/_rels/%s.xml.rels' % mine] = rels.encode('utf8')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as out:
    for name in order:
        out.writestr(name, parts[name])
print('wrote', OUT)
