# Drone Metashape Local

โปรแกรม Windows แบบ one-click สำหรับสร้าง Orthomosaic จากโฟลเดอร์ภาพโดรนด้วย Agisoft Metashape ผ่าน Python API หน้าเว็บและ backend ทำงานเฉพาะที่ `127.0.0.1`; ภาพไม่ถูกส่งขึ้น cloud และผู้ใช้ทั่วไปไม่ต้องใช้ Codex

> สถานะปัจจุบัน: automated และ mock-mode validation ผ่านแล้ว การทำงานกับ Metashape/License/GeoTIFF จริงยังต้องตรวจใน Phase 5 ก่อนใช้กับ production

## เริ่มใช้งานครั้งแรก

1. ติดตั้ง Python 3.11–3.13 และ Agisoft Metashape ที่มี license ใช้งานได้
2. ดับเบิลคลิก `start.bat`
3. ครั้งแรกโปรแกรมจะสร้าง `.venv` และติดตั้ง dependency หากยังไม่มี
4. หากหา Metashape ไม่พบ โปรแกรมจะให้เลือก `metashape.exe`
5. Browser เปิดหลัง backend พร้อมใช้งานแล้วเท่านั้น

การเปิดครั้งต่อไปไม่ติดตั้ง dependency ซ้ำ เว้นแต่ `requirements.txt` เปลี่ยนหรือ dependency หาย

## ขั้นตอนใช้งานปกติ

1. กด **เลือกโฟลเดอร์ภาพ**
2. ตรวจรหัสแปลง จำนวนภาพ CRS โฟลเดอร์ผลลัพธ์ และ preset
3. เลือกวิธีจัดการหากมีผลลัพธ์เดิม
4. กด **เริ่มสร้าง Orthomosaic**
5. ติดตาม Align → Depth Maps → DEM → Orthomosaic → Export จาก timeline
6. เมื่อสำเร็จ กดเปิดโฟลเดอร์ผลลัพธ์

ผลลัพธ์หลักคือ Metashape project (`.psx`), Orthomosaic GeoTIFF (`.tif`), optional PDF report, persisted job state และ processing log งานที่ล้มเหลวจะมี diagnostic package

## โหมดทดสอบ

รัน `start.bat --mock-metashape` เพื่อทดสอบ UI/state/retry/failure โดยไม่เรียก Metashape หน้าเว็บจะแสดงป้ายชัดเจนและไฟล์จำลองใช้แทนผลผลิตจริงไม่ได้

ดูรายละเอียดที่ [การติดตั้ง](docs/installation.md), [workflow](docs/workflow.md) และ [การแก้ปัญหา](docs/troubleshooting.md)
