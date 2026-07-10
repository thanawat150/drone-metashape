import os
import sys
import traceback

import Metashape


PHOTO_DIR = r"F:\ภาพโดรน\Drone\สุราษฎร์ธานี\20-05-2569\DJI_202605200909_063_37-STC"
OUT_DIR = r"F:\ภาพโดรน\Drone\สุราษฎร์ธานี\20-05-2569\Agisoft_Output"
PROJECT_PATH = os.path.join(OUT_DIR, "surat_37-STC.psx")
ORTHO_PATH = os.path.join(OUT_DIR, "surat_37-STC_orthomosaic.tif")
REPORT_PATH = os.path.join(OUT_DIR, "surat_37-STC_report.pdf")


def log(message):
    print(message, flush=True)


def image_files(root):
    exts = {".jpg", ".jpeg", ".tif", ".tiff", ".dng"}
    files = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in exts:
            files.append(path)
    return files


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    photos = image_files(PHOTO_DIR)
    if not photos:
        raise RuntimeError("No drone photos found in: " + PHOTO_DIR)

    log("Agisoft Metashape version: " + Metashape.app.version)
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
        downscale=1,
        generic_preselection=True,
        reference_preselection=True,
        keypoint_limit=40000,
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
