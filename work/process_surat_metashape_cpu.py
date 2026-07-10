import os
import sys
import traceback

import Metashape


PHOTO_DIR = (
    "F:\\"
    "\u0e20\u0e32\u0e1e\u0e42\u0e14\u0e23\u0e19\\"
    "Drone\\"
    "\u0e2a\u0e38\u0e23\u0e32\u0e29\u0e0e\u0e23\u0e4c\u0e18\u0e32\u0e19\u0e35\\"
    "20-05-2569\\"
    "DJI_202605200909_063_37-STC"
)
OUT_DIR = os.path.join(os.path.dirname(PHOTO_DIR), "Agisoft_Output")
PROJECT_PATH = os.path.join(OUT_DIR, "surat_37-STC.psx")
ORTHO_PATH = os.path.join(OUT_DIR, "surat_37-STC_orthomosaic.tif")
REPORT_PATH = os.path.join(OUT_DIR, "surat_37-STC_report.pdf")


def log(message):
    print(message, flush=True)


def image_files(root):
    exts = {".jpg", ".jpeg", ".tif", ".tiff", ".dng"}
    return [
        os.path.join(root, name)
        for name in sorted(os.listdir(root))
        if os.path.isfile(os.path.join(root, name))
        and os.path.splitext(name)[1].lower() in exts
    ]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    photos = image_files(PHOTO_DIR)
    if not photos:
        raise RuntimeError("No drone photos found in: " + PHOTO_DIR)

    log("Agisoft Metashape version: " + Metashape.app.version)
    Metashape.app.gpu_mask = 0
    Metashape.app.cpu_enable = True
    log("GPU disabled for stability; CPU processing enabled.")
    log("Photos: {}".format(len(photos)))
    log("Output: " + OUT_DIR)

    doc = Metashape.Document()
    chunk = doc.addChunk()
    chunk.label = "Surat Thani 37-STC"

    log("Adding photos...")
    chunk.addPhotos(photos)
    doc.save(PROJECT_PATH)

    log("Matching photos...")
    chunk.matchPhotos(
        downscale=2,
        generic_preselection=True,
        reference_preselection=True,
        keypoint_limit=30000,
        tiepoint_limit=4000,
    )
    doc.save()

    log("Aligning cameras...")
    chunk.alignCameras()
    aligned = sum(1 for camera in chunk.cameras if camera.transform)
    log("Aligned cameras: {}/{}".format(aligned, len(chunk.cameras)))
    doc.save()

    if aligned < max(3, int(len(chunk.cameras) * 0.6)):
        raise RuntimeError("Too few cameras aligned: {}/{}".format(aligned, len(chunk.cameras)))

    log("Building depth maps...")
    chunk.buildDepthMaps(downscale=4, filter_mode=Metashape.MildFiltering)
    doc.save()

    log("Building DEM...")
    chunk.buildDem(source_data=Metashape.DepthMapsData)
    doc.save()

    log("Building orthomosaic...")
    chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)
    doc.save()

    log("Exporting orthomosaic GeoTIFF...")
    chunk.exportRaster(path=ORTHO_PATH, source_data=Metashape.OrthomosaicData)

    log("Exporting report...")
    try:
        chunk.exportReport(REPORT_PATH)
    except Exception as exc:
        log("Report export skipped: {}".format(exc))

    doc.save()
    log("Done.")
    log("Project: " + PROJECT_PATH)
    log("Orthomosaic: " + ORTHO_PATH)
    log("Report: " + REPORT_PATH)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
