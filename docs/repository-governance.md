# Repository governance

## Instruction hierarchy

```text
Root AGENTS.md
    -> nearest scoped AGENTS.md
    -> relevant .agents/skills/<skill-name>/SKILL.md
    -> task-specific user instruction
```

`AGENTS.md` files define durable constraints. Skills define focused reusable workflows. The explicit task selects the narrowest skill; Codex must not apply all skills indiscriminately. Scoped rules may be stricter but may not weaken root safety. Resolve conflicts toward the safer and more specific applicable instruction.

Current Codex discovers repo skills under `.agents/skills/`. The requested `skills/README.md` is a human-facing registry and migration pointer; skill implementations are not duplicated under both paths.

Runtime code does not read or depend on governance documents.

## Protected files and generated data

Do not commit or delete drone images, Metashape projects, `.files/`, GeoTIFFs, production reports without approval, job/runtime directories, sensitive logs, unsanitized diagnostics, local config, environment files, tokens, license material, or large generated outputs.

Legacy scripts under `work/` remain migration evidence and require a separately approved task before modification or removal.

## Mock versus real validation

Mock tests validate deterministic application behavior, state, API/UI wiring, retry, cancellation, and diagnostics. They do not validate Metashape's installed CLI/API, license, geospatial correctness, hardware selection, or production readiness.

Only `metashape-runtime-validation` on an approved licensed machine with a copied dataset may create real-validation claims. Record passed, warning, failed, and not-tested items in `docs/real-metashape-validation.md`.

## Release readiness

A release is not production-ready solely because automated or mock tests pass. Require:

1. successful non-Metashape tests;
2. documented real-runtime evidence for the target Metashape version;
3. review of generated-output safety;
4. user acceptance of profiles and workflow;
5. human approval to merge and release.

## Human approval points

Require explicit human direction for production data use, overwrite, profile meaning changes, real Metashape runs, secrets/local configuration, push, PR, merge, deployment, branch deletion, history rewriting, and legacy-script removal.

## Solo Git workflow

The sole maintainer works directly on `main`. Issues, task branches, and pull requests are optional and created only when explicitly requested. Keep commits focused, test before committing, and push `main` only on request. Force-push and history rewriting remain prohibited unless explicitly authorized.
