"""Make a pandoc-produced .docx break Thai lines correctly in Word.

Usage:  python patch-thai-docx.py <file.docx>          (patches in place)

Why this exists (verified by A/B on 2026-08-23, this machine, Office 2024 +
Thai proofing pack): Word only engages its Thai dictionary word-breaker for a
document that carries what native Word documents always carry -

  document.xml   <w:cs/> + <w:lang w:bidi="th-TH"/> on every Thai run
  settings.xml   <w:applyBreakingRules/> and a <w:compat> block whose
                 compatibilityMode is 15

pandoc emits none of these (and strips them from reference.docx), so its
output opens in compatibility mode 12 with untagged runs, and Word then wraps
Thai at spaces only, hard-breaking mid-word at the margin.  No single item is
enough: runs-only and settings-only variants both stayed broken; the full set
fixed it.  The minimal subset was not isolated - this applies exactly what
native Word writes.

Stdlib only, so the plain PATH python works.
"""
import io
import re
import sys
import zipfile

THAI = re.compile('[฀-๿]')
CS_LANG = '<w:cs/><w:lang w:bidi="th-TH"/>'
COMPAT = (
    '<w:compat>'
    '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
    '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="differentiateMultirowTableHeaders" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="useWord2013TrackBottomHyphenation" w:uri="http://schemas.microsoft.com/office/word" w:val="0"/>'
    '</w:compat>'
)


def patch_document(xml: str) -> str:
    tagged = [0]

    def tag_run(m):
        run = m.group(0)
        if not THAI.search(run) or '<w:cs/>' in run:
            return run
        tagged[0] += 1
        if '<w:rPr>' in run:
            return run.replace('<w:rPr>', '<w:rPr>' + CS_LANG, 1)
        return re.sub(r'(<w:r(?: [^>]*)?>)', r'\1<w:rPr>' + CS_LANG + '</w:rPr>',
                      run, count=1)

    out = re.sub(r'<w:r(?: [^>]*)?>.*?</w:r>', tag_run, xml, flags=re.S)
    print(f'  document.xml: {tagged[0]} Thai runs tagged cs + th-TH')
    return out


def patch_settings(xml: str) -> str:
    out = re.sub(r'<w:compat>.*?</w:compat>', '', xml, flags=re.S)
    flags = ('<w:applyBreakingRules/>' if 'applyBreakingRules' not in out else '') + COMPAT
    # schema order: both belong before w:rsids / w:themeFontLang
    for anchor in ('<w:rsids>', '<w:themeFontLang', '</w:settings>'):
        i = out.find(anchor)
        if i != -1:
            out = out[:i] + flags + out[i:]
            break
    print('  settings.xml: applyBreakingRules + compatibilityMode 15')
    return out


def main(path: str) -> None:
    zin = zipfile.ZipFile(path)
    items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    zin.close()

    buf = io.BytesIO()
    zout = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)
    for info, data in items:
        if info.filename == 'word/document.xml':
            data = patch_document(data.decode('utf-8')).encode('utf-8')
        elif info.filename == 'word/settings.xml':
            data = patch_settings(data.decode('utf-8')).encode('utf-8')
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zout.writestr(zi, data)
    zout.close()

    # sanity: both parts must still parse before we overwrite the original
    import xml.etree.ElementTree as ET
    check = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    ET.fromstring(check.read('word/document.xml'))
    ET.fromstring(check.read('word/settings.xml'))

    with open(path, 'wb') as f:
        f.write(buf.getvalue())
    print(f'  patched: {path}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: python patch-thai-docx.py <file.docx>')
    main(sys.argv[1])
