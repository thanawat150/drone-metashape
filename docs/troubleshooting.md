# การแก้ปัญหา

- **ไม่พบ Python** — ติดตั้ง Python 3.11–3.13 และเลือกเพิ่ม Python/launcher ลง PATH
- **ติดตั้ง dependency ไม่สำเร็จ** — ตรวจ internet/proxy ครั้งแรก แล้วดู `logs/startup.log`; การเปิดปกติภายหลังไม่ต้องติดตั้งซ้ำ
- **Port ถูกใช้งาน** — หากเป็นแอปนี้ launcher จะใช้ server เดิม หากเป็นโปรแกรมอื่น ให้ปิดโปรแกรมนั้นหรือเปลี่ยน port ใน local config
- **ไม่พบ Metashape** — เลือก `metashape.exe` จริง ไม่ใช่ shortcut; ตรวจ installation และ edition
- **License unavailable** — เปิด Metashape และแก้ activation/license ก่อนลองใหม่
- **ไม่พบภาพ** — ภาพต้องอยู่ระดับบนสุดของโฟลเดอร์และใช้นามสกุล JPG/JPEG/TIF/TIFF/DNG
- **Alignment ต่ำ** — ตรวจ overlap, blur, GPS/reference และ dataset; ห้ามลด threshold โดยไม่มีเหตุผลด้านคุณภาพ
- **DEM ล้มเหลว** — ตรวจว่า profile ต้องการ depth maps หรือ tie points และดู failed stage/log
- **พื้นที่ไม่พอ** — ย้าย output ไป drive ที่มีพื้นที่ โดยเฉพาะ Standard/High Quality
- **พบ output เดิม** — เลือก version ใหม่เป็นทางปลอดภัย; overwrite ต้องยืนยัน Resume ยังปิดไว้ก่อน real validation
- **Permission/antivirus/firewall** — ให้สิทธิ์เขียน source/output และอนุญาต local `127.0.0.1`; ไม่ต้องเปิดรับจาก LAN
- **Path ภาษาไทยมีปัญหา** — เก็บ diagnostic package และระบุ path/Metashape version โดยไม่ย้ายไฟล์ production ทับของเดิม
- **เปิดหน้าเว็บไม่ได้** — ดู `logs/startup.log` และลอง `http://127.0.0.1:8765/api/health`

เมื่อ job ล้มเหลว กด **เปิด Diagnostics** แล้วให้ Codex อ่านโฟลเดอร์ `diagnostics/<job_id>` Codex ไม่ควร execute code หรืออ้าง real compatibility จาก mock output
