# Paper — การพัฒนาต้นแบบหุ่นยนต์สี่ขารูปแบบสององศาอิสระภายใต้แรงบิดต่อน้ำหนักที่เหมาะสม

ต้นฉบับบทความวิจัยสำหรับ **The Journal of KMUTNB** (วารสารวิชาการพระจอมเกล้าพระนครเหนือ, TCI Tier 1)
ส่วนนี้เป็นชั้น "เปเปอร์" ของ monorepo BLEGS — โค้ดที่ผลิตข้อมูลทั้งหมดอยู่ใน [`../python/`](../python/)
และเฟิร์มแวร์อยู่ใน [`../firmware/`](../firmware/) จึงไม่มีสำเนาโค้ดในโฟลเดอร์นี้อีกต่อไป

## งานวิจัยโดยย่อ

หุ่นยนต์สี่ขา BLEGS (Bio-inspired LEGged System) ขาละสององศาอิสระด้วยกลไก Separated Five-Bar Linkage
ขับด้วยมอเตอร์ BLDC (FOC/SVPWM) + เอนโคดเดอร์สัมบูรณ์ AS5047P อัตราทด 8:1 — ใช้แนวทางเชิงข้อมูล
(วัดตำแหน่งจริงด้วย ArUco vision) สร้างแบบจำลองชดเชยความคลาดเคลื่อนเชิงกล เพื่อให้ได้ความแม่นยำสูง
โดยไม่ต้องเพิ่มเซนเซอร์หรือชิ้นส่วนกลไก

การทดลอง 3 ชุด: (1) แรงบิดต่อน้ำหนัก (2) ความแม่นยำปลายขา + แบบจำลองชดเชย ML
(3) การเดินทั้งตัว — เทียบเปิด/ปิดการชดเชย และหาขีดจำกัดบนพื้นผิวจริง

## โครงสร้าง

```
paper/
├── manuscript/
│   ├── drafts/            ต้นฉบับฉบับวารสาร (ย่อให้เข้าเพดาน 9 หน้า) — build อ่านจากที่นี่
│   ├── drafts-full/       ฉบับเต็มสำหรับวิทยานิพนธ์ — ไม่เข้ากระบวนการ build
│   └── submission/        ไฟล์ .docx ที่ส่งจริง + SUBMISSION_CHECKLIST.md
├── figures/  src/ export/  ต้นฉบับรูปที่แก้ได้ / .jpg สำหรับส่ง (วารสารบังคับ)
├── tables/   src/ export/  ตารางก็ต้องส่งเป็น .jpg เช่นกัน
├── data/     real/ vision/ ข้อมูลที่ใช้สร้างรูปและตาราง
├── references/            ไฟล์อ้างอิง / .bib / PDF ที่อ้างถึง
├── journal/               ข้อกำหนดวารสาร เทมเพลต และ reference.docx ของ pandoc
├── build.ps1              แปลง drafts → manuscript.docx (ไฟล์ที่ส่งจริง)
├── preview.ps1            แปลง drafts → preview.pdf ผ่าน XeLaTeX (เร็ว ไม่ต้องมี Word)
└── preview-word.ps1       แปลง drafts → preview-word.pdf ผ่าน Word — Thai Distribute
                           ของจริง สองคอลัมน์จริง จำนวนหน้าตัวนี้คือตัวตัดสิน
```

## วิธีทำงาน

1. เขียน/แก้ต้นฉบับใน `manuscript/drafts/` (ธรรมเนียมการเขียนดู [`CLAUDE.md`](CLAUDE.md))
   — **มีสองฉบับ**: `drafts/` คือฉบับวารสารที่ถูกย่อให้เข้าเพดาน 9 หน้า ส่วน `drafts-full/`
   คือฉบับเต็มระดับวิทยานิพนธ์ที่เก็บไว้อ้างอิง ไม่มีสคริปต์ไหนอ่าน `drafts-full/`
2. รูปและตาราง: ไฟล์ต้นฉบับไว้ `*/src/` — ส่งออก .jpg ไว้ `*/export/`
3. ดูหน้าตาและความยาวระหว่างเขียน: `powershell -File paper/preview.ps1` → `manuscript/preview.pdf`
   (XeLaTeX — เร็ว ไม่ต้องมี Word แต่การตัดบรรทัดไทยเป็นค่าประมาณ) หรือ
   `powershell -File paper/preview-word.ps1` → `manuscript/preview-word.pdf`
   (ผ่าน Word จริง — Thai Distribute ถูกต้อง **จำนวนหน้าจากตัวนี้คือตัวตัดสิน**)
4. แปลงเป็น .docx สำหรับเก็บงานส่งจริง: `powershell -File paper/build.ps1` (ดู [`journal/README.md`](journal/README.md))
5. เก็บงานขั้นสุดท้ายใน Word ตาม [`manuscript/submission/SUBMISSION_CHECKLIST.md`](manuscript/submission/SUBMISSION_CHECKLIST.md) แล้วส่งผ่าน ThaiJO

## สถานะและแผน

ดู [`action-plan.md`](action-plan.md) — สรุป: บทที่ 2 (วิธีการ) เขียนครบแล้ว 26 สมการ,
บทอื่นยังไม่เริ่ม, การทดลอง 2.3.3 ออกแบบแล้วรอทดสอบจริง
