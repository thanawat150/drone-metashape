# Release readiness checklist

## Automated-test validated

- job/profile schemas, Unicode paths, inspection/naming/conflicts
- atomic state, diagnostics, mock pipeline retry/stop behavior
- localhost API revalidation, single active job, path restrictions
- launcher configuration, dependency fingerprint and health helpers

## Mock validated

- success and alignment warning
- retry then success and permanent failure with diagnostics
- persisted job history/retry and cancellation request
- Thai UI/API use the same job/state path as the real launcher

Mock files are simulated and do not validate geospatial content.

## Requires real Metashape (Phase 5)

- exact `metashape.exe -r` CLI arguments and exit/log behavior
- API names/enums for installed edition/version
- camera/tie-point/depth/DEM/orthomosaic validators against real objects
- actual GeoTIFF/project/report, CRS metadata and Thai end-to-end paths
- CPU/GPU selection, license behavior, close behavior and resource observations
- safe failure path and at least one complete Preview or Standard job

## Requires user acceptance

- profile quality and threshold decisions
- output naming/location and report requirement
- usability on the intended Windows workstation
- pilot approval after reviewing `docs/real-metashape-validation.md`

Phase 4 is mock-ready, not production-validated.
