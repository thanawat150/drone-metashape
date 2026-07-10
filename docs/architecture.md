# Architecture

The application keeps normal Python separate from the Agisoft Metashape runtime:

```text
Thai browser UI -> localhost API -> job manager -> Metashape executable
                                             job JSON ↓
                    persisted state <- reusable pipeline -> outputs
```

Normal Python owns folder inspection, validated JSON, job history, the local API, and UI. It must not import `Metashape`. A later real adapter imports the module only inside the installed Metashape runtime. Automated tests use a mock adapter.

## Data on disk

- `profiles/*.json`: source-controlled processing settings.
- `config.local.json`: machine-local executable/defaults; ignored by Git.
- `jobs/`: validated jobs and atomic state files.
- `logs/`: processing/startup logs.
- `diagnostics/<job_id>/`: sanitized failure evidence.
- user-selected output directories: `.psx`, GeoTIFF, and optional PDF report.

The first production implementation permits one active job. State is written with a temporary file plus atomic replacement. Existing outputs require an explicit policy; no pipeline code embeds plot-specific paths.

Phase 1 implements only the non-Metashape foundation. Backend, UI, launcher, and real Metashape calls belong to later phases.
