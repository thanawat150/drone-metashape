import os
import traceback

import Metashape


PHOTO_DIR = (
    "F:\\"
    "\u0e20\u0e32\u0e1e\u0e42\u0e14\u0e23\u0e19\\"
    "Drone\\"
    "\u0e1e\u0e31\u0e07\u0e07\u0e32\\"
    "22-06-2569\\"
    "DJI_202606221038_092_28-VSD"
)
OUT_DIR = (
    "C:\\Users\\TC0192\\Downloads\\Drone_Orthomosaic"
)
PROJECT_PATH = os.path.join(OUT_DIR, "\u0e1e\u0e31\u0e07\u0e07\u0e32_28-VSD_new.psx")
ORTHO_PATH = os.path.join(OUT_DIR, "\u0e1e\u0e31\u0e07\u0e07\u0e32_28-VSD_new_orthomosaic.tif")


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
    photos = image_files(PHOTO_DIR)
    if not photos:
        raise RuntimeError("No images found: " + PHOTO_DIR)

    Metashape.app.gpu_mask = 0
    Metashape.app.cpu_enable = True

    doc = Metashape.app.document
    doc.clear()
    chunk = doc.addChunk()
    chunk.label = "\u0e1e\u0e31\u0e07\u0e07\u0e32_28-VSD"
    chunk.crs = Metashape.CoordinateSystem("EPSG::32647")

    log("New project: " + PROJECT_PATH)
    log("Adding folder/photos: " + PHOTO_DIR)
    log("Photos: {}".format(len(photos)))
    chunk.addPhotos(photos)
    doc.save(PROJECT_PATH)

    log("Align Photos: Medium/default UI-style settings, CPU")
    chunk.matchPhotos(
        downscale=2,
        generic_preselection=True,
        reference_preselection=False,
        keypoint_limit=80000,
        tiepoint_limit=10000,
        filter_stationary_points=True,
        guided_matching=True,
    )
    chunk.alignCameras(adaptive_fitting=True)
    aligned = sum(1 for camera in chunk.cameras if camera.transform)
    log("Aligned cameras: {}/{}".format(aligned, len(chunk.cameras)))
    doc.save()

    log("Build DEM from tie points, default interpolation")
    chunk.buildDem(
        source_data=Metashape.TiePointsData,
        interpolation=Metashape.EnabledInterpolation,
        projection=Metashape.OrthoProjection(chunk.crs),
    )
    doc.save()

    log("Build Orthomosaic from DEM, default mosaic blending")
    chunk.buildOrthomosaic(
        surface_data=Metashape.ElevationData,
        blending_mode=Metashape.MosaicBlending,
        fill_holes=True,
        projection=Metashape.OrthoProjection(chunk.crs),
    )
    doc.save()

    log("Export Orthomosaic: " + ORTHO_PATH)
    chunk.exportRaster(
        path=ORTHO_PATH,
        source_data=Metashape.OrthomosaicData,
    )
    doc.save()
    log("Done.")


try:
    main()
except Exception:
    traceback.print_exc()
    raise
