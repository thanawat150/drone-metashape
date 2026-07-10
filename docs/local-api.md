# Local API

The API binds to `127.0.0.1` only. It has no public deployment or arbitrary command/file-read endpoint. Job creation re-inspects the selected directory and rejects a stale client image count.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | readiness and explicit mock-mode flag |
| POST | `/api/select-folder` | local native directory picker |
| POST | `/api/inspect-folder` | inspect without starting processing |
| GET | `/api/profiles` | validated source profiles |
| POST/GET | `/api/jobs` | create a job / persisted history |
| GET | `/api/jobs/{id}` | persisted state |
| GET | `/api/jobs/{id}/log` | that job's processing log only |
| POST | `/api/jobs/{id}/retry` | create a new versioned retry job |
| POST | `/api/jobs/{id}/cancel` | request cooperative stop between stages |
| POST | `/api/jobs/{id}/open-output` | open only the recorded output directory |
| POST | `/api/jobs/{id}/open-diagnostics` | open only that job's diagnostics directory |

One active job is allowed. A retry creates a new version rather than mutating failed evidence. Resume remains disabled until existing Metashape project evidence can be validated on the real installed version.
