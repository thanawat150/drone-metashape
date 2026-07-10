# การติดตั้งบน Windows

## สิ่งที่ต้องมี

- Windows 10/11 64-bit
- Python 3.11, 3.12 หรือ 3.13 โดยให้คำสั่ง `py -3` หรือ `python` ใช้งานได้
- Agisoft Metashape และ license ที่ถูกต้องสำหรับงานจริง
- พื้นที่ว่างเพียงพอสำหรับ project, depth maps, DEM และ GeoTIFF

## First launch

ดับเบิลคลิก `start.bat` จากโฟลเดอร์โปรแกรม ตัว launcher จะหา Python, สร้าง `.venv` เมื่อยังไม่มี, และติดตั้ง `requirements.txt` เมื่อ fingerprint เปลี่ยนหรือ import dependency ไม่สำเร็จ จากนั้นจึงเปิด backend ที่ `127.0.0.1` รอ `/api/health` และเปิด browser

Metashape executable ถูกค้นตามลำดับ: ค่าใน `config.local.json`, ตำแหน่งติดตั้ง Windows ที่พบบ่อย, แล้ว native file picker ค่าเลือกที่ผ่าน validation จะเก็บใน `config.local.json` ซึ่ง Git ignore ไว้

ใช้ `start.bat --mock-metashape` เพื่อทดสอบโดยไม่ต้องมี Metashape ใช้ `start.bat --no-browser` เมื่อไม่ต้องการให้ launcher เปิด browser

## Local configuration

`config.example.json` เป็นค่าอ้างอิง ส่วน `config.local.json` เป็นค่าของเครื่องและไม่ควร commit Server ต้องใช้ `127.0.0.1`; อย่าใส่ Telegram token หรือ secret ในไฟล์นี้

## Path ภาษาไทย

job/state/config อ่านเขียน UTF-8 และการเรียก subprocess ใช้ argument list ไม่ต่อ command string ชุดทดสอบครอบคลุม path ภาษาไทย แต่การรองรับจริงตลอด Metashape API/GeoTIFF ต้องยืนยันใน Phase 5

Antivirus อาจตรวจ `.venv` หรือ local server ครั้งแรก อนุญาตเฉพาะ private local use และไม่เปลี่ยน host เป็น LAN address
