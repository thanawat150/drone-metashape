# Codex development workflow

This repository has one maintainer and uses `main` directly.

```text
Discuss requirement
    -> select applicable Skill
    -> inspect scoped files and worktree
    -> implement only the request
    -> run tests
    -> review diff
    -> commit on main when requested
    -> push main when requested
```

Do not create an issue, task branch, or pull request unless the user explicitly requests one. Keep the available GitHub templates for exceptional external review or collaboration.

## Selecting instructions

Read root `AGENTS.md`, the nearest scoped `AGENTS.md`, and one matching skill from `.agents/skills/`. See `skills/README.md`.

| Category | Typical skill |
|---|---|
| UI, API, pipeline, profile, launcher | `drone-metashape-local-one-click` |
| Failed-job analysis | `metashape-diagnostic-analysis` |
| Real installed Metashape compatibility | `metashape-runtime-validation` |
| Small documentation or maintenance | Usually none |

## Verification and Git

Run targeted tests first and the full non-Metashape suite for shared behavior. Review the diff for generated data, secrets, unrelated changes, and safety regressions.

Keep commits focused. Push `main` only after an explicit request. Never force-push or rewrite history.
