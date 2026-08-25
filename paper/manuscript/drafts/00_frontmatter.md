# ส่วนนำของบทความ (Front Matter)

<!-- หน้า 1: ภาษาไทย | หน้า 2: ภาษาอังกฤษ ตามโครงสร้างบังคับของวารสาร

     ค่าที่ยังไม่มีเขียนเป็น [รอผล: ...] แบบข้อความธรรมดา ไม่ใช่ <mark> โดยตั้งใจ
     เพราะ pandoc ตัด <mark> ทิ้งเงียบ ๆ ทำให้วัดจำนวนหน้าไม่ตรงความจริง
     ก่อนส่งต้องไม่เหลือ [รอผล: ...] สักอัน -->

## ชื่อเรื่อง (ภาษาไทย)

การชดเชยความคลาดเคลื่อนเชิงกลด้วยแนวทางเชิงข้อมูลสำหรับหุ่นยนต์สี่ขาน้ำหนักเบาที่มีอัตราส่วนแรงบิดต่อน้ำหนักสูง

## Title (English)

Data-Driven Compensation of Mechanical Deflection in a Lightweight Quadruped Robot with a High Torque-to-Weight Ratio

## ผู้นิพนธ์ / Authors

<mark>[รอกำหนด: ชื่อ-นามสกุล ไทยและอังกฤษ, สังกัด, ที่อยู่หน่วยงาน, อีเมลและโทรศัพท์ของ Corresponding Author]</mark>

## บทคัดย่อ (ภาษาไทย)

&emsp;การออกแบบโครงสร้างขาหุ่นยนต์ให้มีน้ำหนักเบาช่วยเพิ่มอัตราส่วนแรงบิดต่อน้ำหนัก แต่แลกมาด้วยการเสียรูปเชิงกลของชิ้นส่วนภายใต้ภาระโหลด ทำให้ตำแหน่งปลายขาที่เกิดขึ้นจริงเบี่ยงเบนจากค่าที่คำนวณด้วยจลนศาสตร์ย้อนกลับ การแก้ไขด้วยการเพิ่มความแข็งเกร็งของโครงสร้างหรือการติดตั้งเซนเซอร์วัดตำแหน่งเพิ่มเติมย่อมทำให้มวลรวมสูงขึ้นและลดทอนข้อได้เปรียบที่ออกแบบไว้แต่แรก บทความนี้จึงเสนอการชดเชยความคลาดเคลื่อนดังกล่าวด้วยซอฟต์แวร์และข้อมูล โดยไม่เพิ่มมวลหรือเซนเซอร์ให้กับระบบ ต้นแบบที่ใช้ศึกษาเป็นหุ่นยนต์สี่ขา ขาละสององศาอิสระด้วยกลไกห้าชิ้นส่วนแบบแยกส่วน ขับเคลื่อนด้วยมอเตอร์กระแสตรงไร้แปรงถ่านร่วมกับเอนโคดเดอร์สัมบูรณ์และชุดเฟืองทดอัตราส่วน 8:1 ให้อัตราส่วนแรงบิดต่อมวลเท่ากับ [รอผล: อัตราส่วนแรงบิดต่อมวล] นิวตันเมตรต่อกิโลกรัม การสร้างแบบจำลองเริ่มจากตรวจวัดตำแหน่งปลายขาที่แท้จริงด้วยระบบประมวลผลภาพและเครื่องหมายอ้างอิงที่จุดกริด 152 จุด ภายใต้ภาระโหลด 4 ระดับ รวม 608 ตัวอย่าง แล้วฝึกแบบจำลองการเรียนรู้ของเครื่อง 5 ประเภทให้พยากรณ์ความคลาดเคลื่อนจากมุมสั่งการและกระแสมอเตอร์ การประเมินผลใช้การเคลื่อนที่ต่อเนื่องตามวิถีวงกลมซึ่งเป็นเงื่อนไขที่ต่างจากชุดฝึก ผลการทดลองแสดงว่าความคลาดเคลื่อนที่เกิดขึ้นมีลักษณะเป็นการเลื่อนตำแหน่งของวิถีทั้งเส้นมากกว่าการผิดรูปของวิถี กล่าวคือรัศมีที่ปลายขาลากได้คงที่ที่ 29.65 ± 0.19 มิลลิเมตร ทุกระดับภาระโหลด ขณะที่จุดศูนย์กลางเลื่อนต่ำลงตามภาระโหลดอย่างเป็นระบบถึง 11.66 มิลลิเมตร โดยไม่เป็นสัดส่วนตรงกับภาระโหลด และการเปิดใช้แบบจำลองชดเชยดึงจุดศูนย์กลางกลับได้ 9.82 มิลลิเมตรที่ภาระโหลดสูงสุด เมื่อนำไปใช้กับการเดินจริงของหุ่นยนต์ทั้งตัว อัตราการเบี่ยงเบนต่อระยะทางลดลงจาก 43.25 เหลือ 8.73 เซนติเมตรต่อเมตร ที่ภาระโหลด 3 กิโลกรัม และจาก 9.31 เหลือ 1.03 เซนติเมตรต่อเมตร ในสภาวะไม่มีโหลด

**คำสำคัญ:** กลไกห้าชิ้นส่วน การเรียนรู้ของเครื่อง เครื่องหมายอ้างอิงเชิงภาพ ภาระโหลด

## Abstract (English)

&emsp;Designing a robot leg for low mass raises its torque-to-weight ratio, but the same lightness lets the structure deflect under load, so the foot settles away from the position inverse kinematics predicts. Stiffening the structure or adding sensors adds mass, eroding the very advantage sought. This paper instead compensates that error in software from measured data, adding neither mass nor sensors. The prototype is a quadruped with two degrees of freedom per leg through a separated five-bar linkage, driven by brushless DC motors with absolute encoders through an 8:1 reduction, giving a torque-to-mass ratio of [pending] N·m/kg. True foot positions were measured by a calibrated vision system with fiducial markers over a 152-point grid under four payload levels, yielding 608 samples, and five machine-learning models were trained to predict positional error from commanded joint angles and motor currents. Evaluation used continuous circular motion, a condition absent from training. The error proved to be dominated by translation of the whole path rather than distortion of its shape: the traced radius held at 29.65 ± 0.19 mm across every payload, while the path centre sagged by up to 11.66 mm as load increased, and not in proportion to it. Compensation recovered 9.82 mm of that offset at the heaviest payload. Applied to whole-robot walking, lateral deviation per metre travelled fell from 43.25 to 8.73 cm/m under a 3 kg payload, and from 9.31 to 1.03 cm/m unloaded.

**Keywords:** five-bar linkage, machine learning, fiducial marker, payload
