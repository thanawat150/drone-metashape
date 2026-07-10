---
name: metashape-diagnostic-analysis
description: Analyze a failed drone Metashape job from its diagnostic package, identify the most likely failure stage and cause, distinguish configuration, data, environment, and code failures, and propose safe next actions without automatically executing changes.
---

# Metashape Diagnostic Analysis

Follow root `AGENTS.md`. This is a read-first analysis workflow, not authorization to modify code, profiles, jobs, or outputs.

## Minimum evidence

Inspect only the files needed from one package:

```text
job.json
state.json
profile.json
error.txt
processing.log
environment.json
summary.md
```

Do not scan unrelated jobs or expose secrets or sensitive paths in the report.

## Analysis workflow

1. Verify all evidence belongs to one job.
2. Identify the failed stage and last successful stage.
3. Record retry count and whether later stages stopped.
4. Classify the likely cause as source data, path/permission, disk/memory, license, Metashape version/API, processing profile, output conflict, application bug, or unknown.
5. Separate direct evidence from inference and state confidence.
6. Recommend the safest next action for a non-technical operator.

Do not automatically modify profiles, restart jobs, overwrite output, execute generated code, or delete projects. If a source change is warranted, recommend a separate issue, branch, implementation, tests, and PR.

## Diagnostic report

Provide a concise job/stage summary, direct evidence, likely cause, safe next action, items needing technical review, and evidence still missing. Do not claim compatibility beyond the package evidence.
