# Repository guidance

This repository is a local Windows one-click application for deterministic Agisoft Metashape Orthomosaic jobs. Normal processing uses scripts and the Metashape API, never Codex or a cloud AI service.

## Before editing

1. Read this file.
2. Read the nearest scoped `AGENTS.md`.
3. Read one relevant skill from `.agents/skills/`, if the task matches.
4. Inspect only task-related code, tests, docs, and the current worktree.

Preserve unrelated user changes. Scoped rules may be stricter but cannot weaken root safety.

## Skill selection

| Task | Skill |
|---|---|
| App, schemas, pipeline, mock adapter, API/UI, launcher | `drone-metashape-local-one-click` |
| Real installed Metashape/API/CLI validation | `metashape-runtime-validation` |
| One failed-job diagnostic package | `metashape-diagnostic-analysis` |
| Small maintenance or docs-only work | None unless relevant |

Do not load every skill. Runtime code must not depend on governance files.

## Safety

- Keep the server on `127.0.0.1`; never upload drone images.
- Use Metashape's Python API, never GUI click automation.
- Never expose arbitrary commands, use `shell=True` with user input, or silently overwrite output.
- Keep paths and processing settings in validated config/job/profile data.
- Keep mock output visibly fake; do not claim real validation without evidence.
- Preserve `work/` legacy scripts unless an approved migration task says otherwise.
- Do not commit images, `.psx`, `.files/`, GeoTIFFs, generated jobs/logs/diagnostics, local config, secrets, tokens, license data, or large outputs.
- Never delete user data or generated projects.

## Git: solo maintainer

- Work directly on `main`; do not create an issue, branch, or PR unless explicitly requested.
- Keep commits focused and run relevant tests before committing.
- Push `main` only when explicitly requested.
- Never force-push, rewrite history, merge another branch, deploy, or delete branches unless explicitly requested.

## Testing

- Run targeted tests first.
- Run the full non-Metashape suite for shared behavior.
- Keep mock evidence separate from real-Metashape evidence.
- Report skipped tests and never weaken assertions merely to pass.

```powershell
python -m pytest -q
python -m compileall -q app.py scripts metashape_pipeline
node.exe --check web\app.js
```

## Handoff

Report files changed, tests/results, mock versus real evidence, unverified behavior, risks, and any commit, push, merge, deployment, or branch deletion performed.
