---
name: metashape-runtime-validation
description: Validate the drone-metashape application against an installed Agisoft Metashape version, including CLI invocation, Python runtime compatibility, API calls, hardware configuration, project creation, Orthomosaic export, and controlled failure behavior.
---

# Metashape Runtime Validation

Follow root and nearest scoped `AGENTS.md` files. Use this skill only for approved real-runtime validation, never to infer production readiness from mock tests.

## Preconditions

Require an approved Windows machine, an installed licensed Metashape, and a copied or disposable test dataset. Confirm that the first validation does not use irreplaceable production originals. Stop and report any missing prerequisite.

## Record the environment

Record Windows version, Metashape edition/version/build, embedded Python version, backend Python version, executable path, license availability without license secrets, CPU, GPU, RAM, free disk space, dataset identity/image count/size, copy status, and profile.

## Validation workflow

1. Verify the actual `metashape.exe -r` argument array, script execution, job argument passing, exit code, and stdout/stderr/log behavior.
2. Verify imports inside Metashape's embedded Python separately from normal Python.
3. Validate actual project creation/open, photo loading/count, alignment/tie points, depth maps when enabled, DEM, Orthomosaic, GeoTIFF export, project save, and configured close behavior.
4. Verify CPU/GPU configuration actually applied.
5. Validate outputs with evidence, not merely absence of exceptions.
6. Exercise controlled failures without corrupting a real project.
7. Add regression tests for version-specific fixes while preserving mock behavior.

Do not use GUI click automation, silently change profile meaning, overwrite production output, or generalize sample performance.

## Results and report

Create or update `docs/real-metashape-validation.md`. Categorize every item as passed, warning, failed, or not tested. Include dataset size, stage outcomes, output types, sample timings, compatibility changes, untested items, and whether pilot use is justified.

Do not commit generated images, projects, `.files/`, GeoTIFFs, reports, logs, secrets, or license data. Never claim a profile or stage was verified unless it actually ran with evidence.
