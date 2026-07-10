# Codex maintenance

Codex ไม่ใช่ runtime dependency ผู้ใช้ปกติใช้ `start.bat` และหน้าเว็บเท่านั้น ใช้ Codex เมื่อต้อง audit, แก้ deterministic implementation, วิเคราะห์ diagnostic package, เพิ่ม profile หรือปรับ compatibility หลัง Metashape upgrade

ก่อนแก้ให้อ่าน `skills/drone-metashape-local-one-click/SKILL.md`, root `SKILLS.md`, worktree และ legacy scripts ที่เกี่ยวข้อง รักษา user changes, secrets, generated data และ `work/` ไว้

การวิเคราะห์ failure ควรเริ่มจาก `job.json`, `state.json`, `profile.json`, `error.txt`, `processing.log`, `environment.json` และ `summary.md` แยกสิ่งที่ verified จาก assumed และห้ามรัน AI-generated code โดยอัตโนมัติ

Profile ใหม่ต้องใช้ schema เดิมหรือเพิ่ม schema migration, fixed enum mapping, tests, resource/quality description และ legacy/real-version evidence ห้ามใช้ `eval`

หลัง Metashape upgrade ให้ทำ Phase 5-style compatibility run ด้วย dataset copy, บันทึก version/build, แยก version-specific adapter behavior, เพิ่ม regression tests และ review diff ก่อน commit/PR การ push หรือ PR ต้องได้รับคำสั่งแยกจากผู้ใช้
