# Configuration and profiles

Copy `config.example.json` to `config.local.json` for machine-local settings. The local file is ignored by Git. Do not put Telegram tokens or other secrets in either file; notifications will read secrets from the runtime environment.

The default host is `127.0.0.1`. `EPSG:32647` reflects the current legacy scripts, not a universal assumption for every dataset. The user must review CRS before creating a job.

Jobs use schema version 1 and contain only validated processing inputs. Executable and pipeline script paths are deliberately excluded from job JSON.

## Profile decisions

- Preview follows the lower-cost 37-STC alignment settings, skips depth maps, and proposes a tie-point DEM.
- Standard follows the complete 37-STC script: downscale 1 alignment, mild depth maps at downscale 4, and a depth-map DEM.
- High Quality borrows the 28-VSD alignment limits/guided matching but proposes a depth-map DEM rather than silently preserving that script's tie-point DEM.

These mappings preserve observed differences; they are not claims of equivalence. Actual enum names, CLI behavior, hardware policy, and output quality remain subject to Phase 5 validation on the installed Metashape version.

Folder inspection is intentionally non-recursive, matching all four legacy scripts. Supported extensions are JPG, JPEG, TIF, TIFF, and DNG. A missing plot code is a warning and may be corrected in the UI later.
