---
name: drone-orthomosaic-metashape
description: Workflow for continuing or running Agisoft Metashape drone orthomosaic jobs from opening the project through add photos, alignment, DEM, orthomosaic, GeoTIFF export, project save, program close, Telegram notification, and automation cleanup. Use when the user asks to stitch drone photos, continue an Agisoft/Metashape job, verify an orthomosaic pipeline, or close an automation after completion.
---

> **Legacy reference:** Repository agent instructions now live in `AGENTS.md`. Reusable Codex workflows are registered in `skills/README.md` and stored under `.agents/skills/`. This file is retained as historical operational workflow reference and is not the canonical repository governance file.

# Drone Orthomosaic With Agisoft Metashape

Use this workflow when processing a drone plot in Agisoft Metashape from start to finish. Prefer the existing project and output naming pattern in `C:\Users\TC0192\Downloads\Drone_Orthomosaic`.

## Inputs To Confirm

Before starting, identify these values:

- Project path: `.psx` file to open or create.
- Photo folder: source folder containing drone images, usually under `F:\ภาพโดรน\Drone`.
- Expected image count: number of `.JPG` images in the source folder.
- Output GeoTIFF path: final orthomosaic `.tif`.
- CRS: normally `EPSG:32647 / WGS 84 UTM zone 47N`.
- Automation id: only needed when a recurring automation must be deleted after completion.
- Telegram settings: use existing secure runtime values when available; do not write bot tokens into files.

## Operating Rules

- Stay quiet while a stage is merely running normally.
- Notify the user only when a stage completes and the next stage starts, when an error/blocker occurs, when the whole workflow completes, or when the automation is deleted.
- Send Telegram only for important events: stage transitions, errors, and final completion.
- Do not send routine progress percentages.
- Verify every stage before advancing.
- Retry a failed stage once with the same settings. If the retry fails, stop and report the blocker to the user and Telegram.
- Use CPU enabled and GPU disabled when the user requests that setting.
- Do not overwrite unrelated existing projects or exports without confirming they belong to the same plot.

## Open Program And Project

1. Open Agisoft Metashape.
2. Open the existing `.psx` project if it exists.
3. If no project exists, create a new project and save it to the requested project path.
4. Confirm the active chunk is selected.
5. If photos are not loaded, add photos from the source folder.
6. After adding photos, verify the Workspace/Chunk image count equals the expected `.JPG` count.

Required verification after Add Photos:

- Workspace shows the expected camera/image count.
- Photo paths point to the intended source folder.
- No obvious missing-image warnings are present.

## Align Photos

Run Align Photos with:

- Accuracy: Medium.
- Generic preselection: enabled.
- Reference preselection: leave default unless the project requires otherwise.
- Key point limit / tie point limit: defaults.
- GPU: disabled when requested.
- CPU: enabled.

After Align completes, verify:

- Aligned camera count is greater than zero and ideally equals total cameras.
- Tie Points exist in Workspace.
- No fatal error dialog is open.

If verification passes, notify:

- User: `Align เสร็จแล้ว เริ่ม DEM`
- Telegram: `<plot>: Align เสร็จ เริ่ม DEM`

## Build DEM

Before DEM, verify CRS:

- Project/chunk CRS is `EPSG:32647 / WGS 84 UTM zone 47N`.
- If CRS is missing or wrong, set it before building DEM.

Build DEM with default settings unless the user specifies otherwise:

- Source data: Tie Points or default available source.
- Projection: `EPSG:32647`.

After DEM completes, verify:

- DEM/Elevation appears in Workspace.
- CRS remains `EPSG:32647`.
- No fatal error dialog is open.

If verification passes, notify:

- User: `DEM เสร็จแล้ว เริ่ม Orthomosaic`
- Telegram: `<plot>: DEM เสร็จ เริ่ม Orthomosaic`

## Build Orthomosaic

Before starting, verify the Build Orthomosaic dialog/settings:

- Surface: DEM/Elevation.
- Projection: `EPSG:32647`.
- Other settings: defaults unless user specified otherwise.

After Orthomosaic completes, verify:

- Orthomosaic appears in Workspace.
- It is based on DEM/Elevation.
- No fatal error dialog is open.

If verification passes, notify:

- User: `Orthomosaic เสร็จแล้ว เริ่ม Export`
- Telegram: `<plot>: Orthomosaic เสร็จ เริ่ม Export`

## Export GeoTIFF

Export Orthomosaic as GeoTIFF to the requested output path.

After export, verify on disk:

- The `.tif` exists.
- File size is greater than zero.
- The last modified time is consistent with the current run.

If available, also verify CRS metadata with GIS tools or Metashape export settings.

## Save And Close

After export verification:

1. Save the Metashape project.
2. Close the project or exit Agisoft Metashape.
3. Confirm Metashape is no longer actively processing.
4. Send final Telegram message:
   - `<plot>: เสร็จครบ Export/Save/ปิดโปรแกรมแล้ว`
5. Notify the user with the final output path and file size.

## Close Automation

When the workflow is complete:

1. Use the Codex automation tool to delete the matching automation id.
2. Verify the automation is deleted or no longer scheduled.
3. Notify the user:
   - `ปิด Automation แล้ว`

Do not delete an automation until the output GeoTIFF has been verified and the project has been saved.

## Error Handling

For each stage:

1. Check for completion or error.
2. If the stage failed verification, retry the same stage once with the same settings.
3. If retry fails, stop the workflow.
4. Send Telegram:
   - `<plot>: ERROR <short blocker>`
5. Tell the user the exact stage and blocker.

Common blockers to report:

- Source photo count does not match expected count.
- CRS cannot be set to `EPSG:32647`.
- Align completed with zero aligned cameras.
- Tie Points are missing after Align.
- DEM did not appear after Build DEM.
- Orthomosaic did not appear after Build Orthomosaic.
- Exported GeoTIFF is missing or zero bytes.
- Metashape is locked, frozen, or showing a modal error.

## Lightweight Check Cadence

- Every heartbeat: do a lightweight completion/error check.
- Align and Orthomosaic: while actively running, avoid noisy progress reports.
- DEM: check more frequently because it usually finishes faster.
- If a stage is complete, advance immediately; do not wait for the next long interval.

## Example Stage Messages

Use short messages:

- `<plot>: Align เสร็จ เริ่ม DEM`
- `<plot>: DEM เสร็จ เริ่ม Orthomosaic`
- `<plot>: Orthomosaic เสร็จ เริ่ม Export`
- `<plot>: เสร็จครบ Export/Save/ปิดโปรแกรมแล้ว`
- `<plot>: ERROR <stage/blocker>`

## Final User Reply Template

When everything completes:

```text
เสร็จแล้วครับ <plot>
ไฟล์ Orthomosaic: <output-path>
ขนาดไฟล์: <size>
Save project แล้ว ปิด Metashape แล้ว และปิด Automation แล้ว
```

