---
name: drone-metashape-local-one-click
description: Implement and maintain the local Windows one-click drone Orthomosaic application. Use for application architecture, job/profile/state schemas, deterministic pipeline changes, mock adapter behavior, localhost API, Thai web UI, launcher, output safety, automated tests, documentation, and non-version-specific Metashape integration.
---

# Drone Metashape Local One-Click

Follow root and nearest scoped `AGENTS.md` files. Keep Codex out of the normal processing path.

## Mission

Turn this repository's four plot-specific scripts in `work/` into a local Windows application where a user launches `start.bat`, selects a drone-image folder in a Thai-first localhost UI, reviews detected metadata, starts one deterministic Metashape job, monitors stages, and opens saved outputs. Normal processing must not require Codex or any cloud service.

The root `SKILLS.md` is the legacy operational workflow. Preserve it and deliberately migrate useful deterministic behavior into the application and documentation.

## Scope exclusions

Do not use this skill for:

- real installed-version/API/CLI compatibility claims; use `metashape-runtime-validation`;
- diagnostic-package-only analysis; use `metashape-diagnostic-analysis`;
- processing production data;
- automatically executing AI-generated fixes.

## Mandatory working method

Before each implementation phase:

1. Inspect the current tree, branch, and worktree.
2. Read root `SKILLS.md`, `.gitignore`, relevant docs, and every Python file under `work/` when legacy behavior is in scope.
3. Preserve user changes and avoid destructive cleanup.
4. Work only on explicitly requested phases.
5. Do not delete or rewrite legacy scripts during Phases 0-4.
6. Report verified results separately from assumptions and real-Metashape work not performed.

At each phase boundary, run relevant checks, produce a completion summary, and do not proceed unless that phase was explicitly requested. A user may explicitly request several sequential phases; keep their implementation and commits separate.

## Architecture

Keep these boundaries explicit:

```text
web UI
  -> localhost backend
  -> job manager / safe launcher
  -> Metashape-side pipeline
  -> validators / state / recovery / diagnostics
```

Target structure:

```text
start.bat
app.py
requirements.txt
config.example.json
web/
metashape_pipeline/
profiles/
jobs/
logs/
diagnostics/
docs/
tests/
work/                 # retained legacy scripts
```

Normal Python hosts the web server. The installed Metashape executable runs the Metashape-side script. Do not assume system Python can import `Metashape`.

The backend writes a validated job JSON, launches Metashape with a subprocess argument list, and reads persisted state. Never use `shell=True` for user-controlled values, accept an arbitrary command/script path from a job, or expose arbitrary command/file-read endpoints.

## Metashape control

Use the Metashape Python API, never mouse/keyboard/screen automation. Isolate `Metashape` imports behind a real adapter so non-Metashape tests remain runnable. If the installed version cannot support an operation reliably, record it as unverified or incompatible until real-machine validation.

## Jobs and configuration

No plot, province, date, user, source, or output path belongs in pipeline source. Validate and load these values from config/job/profile data:

- photo/output/project/orthomosaic/report paths;
- plot code and CRS;
- processing profile;
- conflict policy;
- hardware policy;
- close-after-finish and notifications.

Support Thai Unicode and normal Windows paths. Reject null bytes. Normalize paths without silently redirecting them. Never store secrets in jobs, state, browser data, logs, diagnostics, or Git.

Existing outputs require an explicit choice: conservative resume, versioned output, confirmed overwrite, or cancel. Never silently overwrite.

## Profiles

Keep all processing parameters in validated JSON profiles. Provide `preview`, `standard`, and `high_quality`. Map strings to known adapter/API values with explicit dictionaries; never use `eval`.

Legacy scripts differ materially: alignment downscale and limits, reference preselection, guided matching, CPU/GPU policy, DEM source, and report behavior. Do not call them equivalent. Treat initial profiles as proposals until the audit and real-version validation support them.

## Stages and state

Stable stages:

```text
PREFLIGHT
CREATE_PROJECT
ADD_PHOTOS
ALIGN
DEPTH_MAPS
DEM
ORTHOMOSAIC
EXPORT
VALIDATE_OUTPUT
SAVE_PROJECT
COMPLETE
```

Stable stage states: `pending`, `running`, `passed`, `warning`, `failed`, `skipped`.

Persist state atomically before and after every stage. Prefer stage name, timestamps, elapsed time, counts, warnings, retry count, and exact errors over invented percentages.

Preflight validates schema, source images, profile, CRS, output access/conflicts, executable configuration, and practical disk-space warnings. Later validators confirm camera counts/source paths, alignment ratio and tie points, DEM/orthomosaic data, and current-run non-empty output files.

Default alignment classification is passed at 0.85 or above, warning from 0.60 to below 0.85, and failed below 0.60; thresholds remain configurable.

## Failure, retry, resume, and diagnostics

On failure, persist the exact stage and exception immediately and do not run later stages. Retry at most once only for classified retryable failures, using the same profile. Never silently reduce quality or substitute a different DEM source.

Resume conservatively from the last successful stage only after validating existing project data and receiving an explicit conflict/resume choice. Do not promise perfect crash recovery.

Create a sanitized diagnostic directory containing:

```text
job.json
state.json
profile.json
error.txt
processing.log
environment.json
summary.md
```

## Local application

Bind to `127.0.0.1` by default. Use a backend-controlled native folder picker because browsers do not reliably expose absolute Windows directory paths. Keep the UI Thai-first, desktop-friendly, and connected to persisted job state.

Start with one active Metashape job. Cancellation should request a stop between stages; do not kill Metashape during a save/export without a separately designed emergency action. Restrict open-folder operations to known output/diagnostic paths.

The optional “วิเคราะห์ปัญหาด้วย Codex” action may prepare/copy diagnostic instructions or open diagnostics, but must never execute AI-generated code.

## Mock mode and tests

Provide an explicit, visibly labelled mock adapter for success, alignment warning, selected-stage failure, retry, completion, cancellation, state updates, and diagnostics. Mock success never proves real Metashape compatibility.

Automate all non-Metashape behavior: parsing, folder inspection, Unicode paths, naming, schemas, profiles, state transitions/atomic writes, conflicts, diagnostics, launcher command construction, pipeline lifecycle, API security, and mock job flows. Do not weaken tests merely to pass them.

## Documentation and safety

Maintain user-facing installation/workflow/troubleshooting docs separately from Codex maintenance docs and a legacy migration table. Never claim real validation until Phase 5 runs on an approved licensed machine and validates actual outputs.

Do not push, merge, deploy, force-push, rewrite history, delete branches, delete legacy scripts/user data/generated projects, commit secrets, or modify unrelated repositories unless the user gives explicit authorization for the specific action. Commits requested by the user are allowed and should remain phase-scoped.

## Phase completion report

At each phase boundary report files created/modified, architecture choices, preserved legacy behavior, exact checks and results, manual checks, verified/unverified scope, unresolved issues, risks, the next phase, and confirmation that no unrequested later phase was started.

The full application is complete only after one-click launch, Thai paths, inspection, validated jobs/profiles, safe Metashape launch, persisted stages, safe conflicts, diagnostics, mock tests, user docs, and an honest real-machine validation report are all complete.
