# Legacy Metashape script audit

All four scripts select supported files only from the immediate source directory. None performs current-run output validation, atomic state writes, conflict handling, recovery, diagnostics, or safe resume.

| Script | Source/output | CRS | Hardware | Align | Depth/DEM | Orthomosaic/export | Errors and proposed mapping |
|---|---|---|---|---|---|---|---|
| `work/align_surat_37_stc.py` | Hard-coded 37-STC source; sibling `Agisoft_Output`; align-only PSX | Not explicitly set | GPU mask 0, CPU enabled | downscale 2; generic/reference on; 30k/4k; no explicit guided matching | None | None | Top-level traceback and exit 1; no ratio threshold. Basis for Preview alignment, but the new Preview continues to a tie-point DEM and is therefore not equivalent. |
| `work/process_surat_metashape.py` | Hard-coded 37-STC source/output; PSX/TIF/PDF names | Not explicitly set | No explicit policy | downscale 1; generic/reference on; 40k/4k; guided default | mild depth maps downscale 4; DEM from depth maps | elevation surface; GeoTIFF; best-effort report | Fails below roughly 60% aligned (minimum 3); report failure is logged and ignored; traceback/exit 1. Basis for Standard. Explicit CRS and GPU policy remain unresolved. |
| `work/process_surat_metashape_cpu.py` | Hard-coded 37-STC source; sibling output; PSX/TIF/PDF | Not explicitly set | GPU mask 0, CPU enabled | downscale 2; generic/reference on; 30k/4k | mild depth maps downscale 4; DEM from depth maps | elevation surface; GeoTIFF; best-effort report | Same 60% failure rule and top-level exit handling. This is a CPU-stability variant, not equivalent to the prior script because alignment differs. Its CPU-only choice should become an explicit hardware option after real validation. |
| `work/process_phangnga_28_vsd.py` | Hard-coded 28-VSD source; hard-coded user Downloads output; PSX/TIF; no report | Explicit `EPSG::32647` | GPU mask 0, CPU enabled | downscale 2 despite “Medium” log; generic on/reference off; 80k/10k; stationary filter and guided matching on; adaptive fitting | no depth maps; DEM from tie points with interpolation/projection | elevation surface, mosaic blending, fill holes, explicit projection; GeoTIFF | Clears `Metashape.app.document`, which can discard unrelated open work; no alignment failure threshold; traceback/re-raise. Alignment values inform High Quality, but its tie-point DEM conflicts with the 37-STC production path and is not silently adopted. |

## Unresolved decisions before real validation

- Whether the intended high-quality alignment downscale is 1 or the 28-VSD script's actual value 2.
- Correct GPU selection across target machines; GPU mask 0 means disabled in the CPU variants.
- Whether reference preselection should default on for datasets with reliable photo GPS.
- Version-specific support for guided matching, stationary-point filtering, adaptive fitting, interpolation, projections, and report export.
- Whether Preview tie-point DEM quality is sufficient even for visual checking.
- Required CRS per operating area; `EPSG:32647` must remain editable and validated.
- Whether report export is required or best-effort for production jobs.

Legacy scripts remain unchanged until migration is validated separately.
