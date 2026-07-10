# Codex development workflow

The repository-specific implementation skill is stored at:

```text
skills/drone-metashape-local-one-click/SKILL.md
```

Codex should read and follow it when auditing or refactoring the legacy Metashape scripts, implementing the local one-click application, adding processing profiles, testing mock flows, diagnosing failed jobs, or adapting the application to a Metashape API change.

The existing root `SKILLS.md` remains the legacy operational workflow and is intentionally preserved during migration.

Codex is a development and exception-analysis tool only. Normal users will run the completed local application without Codex, ChatGPT, or another AI service.

Implementation is divided into reviewable phases. Keep phase changes and validation results separate, distinguish mock tests from real Metashape validation, and retain the scripts under `work/` until a separate removal decision is approved.
