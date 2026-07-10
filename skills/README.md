# Codex Skill registry

Skills are focused development workflows that Codex selects for repeatable task classes. They are Codex instructions, not application runtime dependencies, and normal Orthomosaic processing never reads them.

Canonical repo-discoverable skills live under `.agents/skills/`. This registry remains at `skills/README.md` for human discoverability and migration compatibility.

| Skill | Use for | Example request |
|---|---|---|
| `drone-metashape-local-one-click` | Architecture, schemas, pipeline, mock adapter, local API/UI, launcher, tests, docs | “เพิ่ม preset ใหม่และทดสอบ mock pipeline” |
| `metashape-runtime-validation` | A real installed Metashape version/API/CLI/hardware/output validation | “ทดสอบกับ Metashape รุ่นที่ติดตั้งบนเครื่องนี้จริง” |
| `metashape-diagnostic-analysis` | Read-only analysis of one failed-job diagnostic package | “ช่วยวิเคราะห์ diagnostics ของ job นี้” |

The explicit task selects the narrowest matching skill. Do not apply all skills together. Documentation-only or small maintenance work normally uses no specialized skill unless its content directly matches one.

## Add a future skill

1. Use a lowercase hyphenated folder name under `.agents/skills/`.
2. Add `SKILL.md` with YAML frontmatter containing only `name` and a trigger-focused `description`.
3. Keep responsibilities focused and non-overlapping.
4. Add scripts, references, or assets only when needed.
5. Add matching `agents/openai.yaml` metadata.
6. Register and validate the skill.
