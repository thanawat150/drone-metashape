# Metashape pipeline

`metashape_pipeline.pipeline.Pipeline` is the sole stage orchestrator. It accepts a validated job, validated profile, adapter, state manager, log location, and diagnostics location. It persists evidence before and after every stage and stops after fatal failure.

The real adapter imports `Metashape` only inside its constructor. The mock adapter uses the same interface and creates visibly simulated output bytes. Real calls and `Metashape.exe -r` argument behavior are statically implemented from the legacy scripts but remain unverified until Phase 5.

## Profile-to-API mapping

| Profile field | Adapter behavior |
|---|---|
| `align.downscale` | `chunk.matchPhotos(downscale=...)` |
| generic/reference preselection | corresponding `matchPhotos` booleans |
| keypoint/tiepoint limits | corresponding `matchPhotos` integer limits |
| guided matching | explicit `matchPhotos(guided_matching=...)` |
| depth enabled | runs or skips `DEPTH_MAPS` |
| depth downscale/filter | `buildDepthMaps`; filter name mapped through a fixed dictionary |
| DEM source | explicit `TiePointsData` or `DepthMapsData` mapping |
| orthomosaic surface | currently validated to elevation only |
| fill holes | explicit `buildOrthomosaic(fill_holes=...)` |

Development mock command:

```powershell
python -m metashape_pipeline.launcher --job <absolute-job.json> --mock --scenario success
```

Without `--mock`, normal Python exits clearly. Production launch is performed through the configured Metashape executable using an internal fixed entrypoint and `shell=False`.
