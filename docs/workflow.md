# Workflow และการตรวจผล

ระบบใช้ stage คงที่: PREFLIGHT, CREATE_PROJECT, ADD_PHOTOS, ALIGN, DEPTH_MAPS, DEM, ORTHOMOSAIC, EXPORT, VALIDATE_OUTPUT, SAVE_PROJECT และ COMPLETE แต่ละ stage บันทึกสถานะ เวลา จำนวนภาพ warning/error ลง `state.json` แบบ atomic

PREFLIGHT ตรวจ job/profile, source images, output access และ conflict หลังเพิ่มภาพต้องได้ camera paths/count ตรงโฟลเดอร์ที่เลือก Alignment ต้องมี tie points; ค่าเริ่มต้นคือผ่านที่ 85%, warning ที่ 60–ต่ำกว่า 85%, และล้มเหลวต่ำกว่า 60% DEM/orthomosaic ต้องมี object จริง ส่วน export ต้องเป็นไฟล์ current-run ที่ขนาดมากกว่าศูนย์

Warning ดำเนินต่อได้โดยไม่ปลอมเป็น passed Fatal failure หยุด stage ถัดไป Retry อัตโนมัติได้ครั้งเดียวเฉพาะ error ที่จัดว่า retryable และใช้ profile เดิม การกดยกเลิกจะหยุดระหว่าง stage เพื่อไม่ kill ระหว่าง save/export

ผลลัพธ์เดิมมีตัวเลือก version ใหม่, overwrite หลังยืนยัน, หรือยกเลิก Resume ถูกแสดงเป็นแนวคิดแต่ยังไม่เปิดใช้งาน production จนกว่าจะตรวจ project evidence กับ Metashape รุ่นจริง

สถานะและประวัติคงอยู่หลัง restart งาน retry สร้าง job/output เวอร์ชันใหม่เพื่อรักษาหลักฐานเดิม
