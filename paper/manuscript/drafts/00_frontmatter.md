<!-- หน้า 1: ภาษาไทย | หน้า 2: ภาษาอังกฤษ ตามโครงสร้างบังคับของวารสาร (FORMAT_GUIDE.md ข้อ 4)
     หัวข้อ ## แรกของแต่ละหน้าคือชื่อเรื่องเอง ไม่มีป้ายกำกับ "ชื่อเรื่อง/ผู้นิพนธ์" เพราะ
     บทความจริงไม่มีป้ายเหล่านั้น — Word ตอนเก็บงานแค่เปลี่ยนสไตล์ชื่อเรื่องเป็น 18 pt

     บล็อกผู้นิพนธ์อยู่ใน ::: author ... ::: เพื่อให้ build -Anonymous ตัดออกได้ทั้งก้อน
     (double-blind review) — journal/templates/anonymize.lua

     ค่าที่ยังไม่ยืนยันเขียนเป็น [...]{.mock} (สีแดงใน PDF) ก่อนส่งต้องไม่เหลือสักจุด
     ตรวจด้วย: grep -n mock manuscript/drafts/*.md

     บทคัดย่อ: ≤ 250 คำ ตามที่ Word นับ (ไทยใช้ตัวตัดคำของ Word) · 1 ย่อหน้า · ห้ามอ้างอิง
     คำสำคัญ 3–5 คำ ห้ามซ้ำคำในชื่อเรื่อง — สคริปต์ตรวจแล้ว 8 ต.ค. 2026 -->

## การชดเชยความคลาดเคลื่อนเชิงกลด้วยแนวทางเชิงข้อมูลสำหรับหุ่นยนต์สี่ขาน้ำหนักเบาที่มีอัตราส่วนแรงบิดต่อน้ำหนักสูง

::: author
ธีรโชติ เมืองจำนงค์

[ภาควิชา/คณะ — รอยืนยัน]{.mock} มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ · ผู้นิพนธ์ประสานงาน: m.teerachot@outlook.com
:::

## บทคัดย่อ

&emsp;การออกแบบขาหุ่นยนต์ให้มีน้ำหนักเบาช่วยเพิ่มอัตราส่วนแรงบิดต่อน้ำหนัก แต่ทำให้โครงสร้างเสียรูปภายใต้ภาระโหลดจนตำแหน่งปลายขาจริงเบี่ยงจากค่าที่คำนวณด้วยจลนศาสตร์ย้อนกลับ การแก้ด้วยการเพิ่มความแข็งเกร็งหรือเซนเซอร์ย่อมเพิ่มมวลกลับคืน บทความนี้จึงชดเชยความคลาดเคลื่อนด้วยซอฟต์แวร์จากข้อมูลที่วัดจริง โดยไม่เพิ่มมวลหรือเซนเซอร์ ต้นแบบเป็นหุ่นยนต์สี่ขาขาละสององศาอิสระแบบกลไกห้าชิ้นส่วน มีอัตราส่วนแรงบิดต่อมวล 1.81 นิวตันเมตรต่อกิโลกรัม ตำแหน่งปลายขาจริงวัดด้วยระบบวิทัศน์และเครื่องหมายอ้างอิงบนกริด 152 จุด ภายใต้ภาระโหลด 4 ระดับ รวม 608 ตัวอย่าง แล้วฝึกแบบจำลองการเรียนรู้ของเครื่อง 5 ประเภทให้พยากรณ์ความคลาดเคลื่อนจากมุมสั่งการและกระแสมอเตอร์ และประเมินด้วยการเคลื่อนที่ตามวิถีวงกลมซึ่งไม่อยู่ในชุดฝึก ผลพบว่าความคลาดเคลื่อนเป็นการเลื่อนตำแหน่งของวิถีทั้งเส้นมากกว่าการผิดรูป รัศมีที่ลากได้คงที่ที่ 29.91 ± 0.39 มิลลิเมตร ขณะที่จุดศูนย์กลางย้อยลงถึง 11.65 มิลลิเมตรอย่างไม่เป็นสัดส่วนกับโหลด การชดเชยดึงกลับได้ 9.78 มิลลิเมตร และแบบจำลองทั้งห้าให้ผลต่างกันเพียง 0.30 มิลลิเมตร เมื่อใช้กับการเดินจริง อัตราการเบี่ยงเบนต่อระยะทางลดจาก 43.25 เหลือ 8.73 เซนติเมตรต่อเมตรที่ภาระโหลด 3 กิโลกรัม และจาก 9.31 เหลือ 1.03 ในสภาวะไม่มีโหลด

**คำสำคัญ:** กลไกห้าชิ้นส่วน การเรียนรู้ของเครื่อง เครื่องหมายอ้างอิงเชิงภาพ ภาระโหลด

## Data-Driven Compensation of Mechanical Deflection in a Lightweight Quadruped Robot with a High Torque-to-Weight Ratio

::: author
[Teerachot Muangchamnong]{.mock}

[Department/Faculty — to confirm]{.mock}, King Mongkut's University of Technology North Bangkok · Corresponding author: m.teerachot@outlook.com
:::

## Abstract

&emsp;Designing a robot leg for low mass raises its torque-to-weight ratio, but the same lightness lets the structure deflect under load, so the foot settles away from the position inverse kinematics predicts. Stiffening it or adding sensors adds mass, eroding the advantage sought. This paper instead compensates that error in software from measured data, adding neither mass nor sensors. The prototype is a quadruped with two degrees of freedom per leg through a separated five-bar linkage, driven by brushless DC motors with absolute encoders and an 8:1 reduction, giving 1.81 N·m/kg. A calibrated vision system with fiducial markers measured true foot positions over a 152-point grid under four payload levels, yielding 608 samples, and five machine-learning models were trained to predict positional error from commanded joint angles and motor currents. Evaluation used continuous circular motion, a condition absent from training. The error proved to be dominated by translation of the whole path rather than distortion of its shape: the traced radius held at 29.91 ± 0.39 mm across every payload, while the path centre sagged by up to 11.65 mm as load increased, and not in proportion to it. Compensation recovered 9.78 mm of that offset at the heaviest payload, and all five models landed within 0.30 mm of one another, so the deployed model was chosen on engineering grounds. Applied to whole-robot walking, lateral deviation per metre travelled fell from 43.25 to 8.73 cm/m under a 3 kg payload, and from 9.31 to 1.03 cm/m unloaded.

**Keywords:** five-bar linkage, machine learning, fiducial marker, payload
