"""Metashape API boundary and deterministic mock implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class RetryableStageError(RuntimeError):
    """A transient stage error eligible for one same-settings retry."""


class PipelineAdapter(Protocol):
    def create_project(self, job: Any) -> None: ...
    def add_photos(self, paths: list[Path]) -> None: ...
    def camera_paths(self) -> list[str]: ...
    def align(self, profile: dict[str, Any]) -> None: ...
    def alignment_metrics(self) -> dict[str, Any]: ...
    def build_depth_maps(self, profile: dict[str, Any]) -> None: ...
    def has_depth_maps(self) -> bool: ...
    def build_dem(self, profile: dict[str, Any]) -> None: ...
    def has_elevation(self) -> bool: ...
    def build_orthomosaic(self, profile: dict[str, Any]) -> None: ...
    def has_orthomosaic(self) -> bool: ...
    def export(self, job: Any) -> list[str]: ...
    def save_project(self, job: Any) -> None: ...
    def resume_capabilities(self) -> dict[str, bool]: ...


class MockAdapter:
    """File-backed mock with injectable stage failures; never imports Metashape."""

    def __init__(self, *, alignment_ratio: float = 1.0, fail_plan: dict[str, int] | None = None):
        self.alignment_ratio = alignment_ratio
        self.fail_plan = dict(fail_plan or {})
        self.calls: list[str] = []
        self._camera_paths: list[str] = []
        self._project = False
        self._aligned = False
        self._depth_maps = False
        self._elevation = False
        self._orthomosaic = False

    def _call(self, stage: str) -> None:
        self.calls.append(stage)
        remaining = self.fail_plan.get(stage, 0)
        if remaining:
            self.fail_plan[stage] = remaining - 1
            raise RetryableStageError(f"mock retryable failure at {stage}")

    def create_project(self, job: Any) -> None:
        self._call("CREATE_PROJECT")
        Path(job.output_dir).mkdir(parents=True, exist_ok=True)
        Path(job.project_path).write_text("mock Metashape project\n", encoding="utf-8")
        self._project = True

    def add_photos(self, paths: list[Path]) -> None:
        self._call("ADD_PHOTOS")
        self._camera_paths = [str(path.resolve()) for path in paths]

    def camera_paths(self) -> list[str]:
        return list(self._camera_paths)

    def align(self, profile: dict[str, Any]) -> None:
        self._call("ALIGN")
        self._aligned = True

    def alignment_metrics(self) -> dict[str, Any]:
        total = len(self._camera_paths)
        aligned = round(total * self.alignment_ratio)
        return {"total": total, "aligned": aligned, "ratio": aligned / total if total else 0, "tie_points": self._aligned and aligned > 0}

    def build_depth_maps(self, profile: dict[str, Any]) -> None:
        self._call("DEPTH_MAPS")
        self._depth_maps = True

    def has_depth_maps(self) -> bool:
        return self._depth_maps

    def build_dem(self, profile: dict[str, Any]) -> None:
        self._call("DEM")
        source = profile["dem"]["source"]
        if source == "depth_maps" and not self._depth_maps:
            raise RuntimeError("depth maps are missing")
        if source == "tie_points" and not self._aligned:
            raise RuntimeError("tie points are missing")
        self._elevation = True

    def has_elevation(self) -> bool:
        return self._elevation

    def build_orthomosaic(self, profile: dict[str, Any]) -> None:
        self._call("ORTHOMOSAIC")
        if not self._elevation:
            raise RuntimeError("elevation is missing")
        self._orthomosaic = True

    def has_orthomosaic(self) -> bool:
        return self._orthomosaic

    def export(self, job: Any) -> list[str]:
        self._call("EXPORT")
        if not self._orthomosaic:
            raise RuntimeError("orthomosaic is missing")
        outputs = [job.orthomosaic_path]
        Path(job.orthomosaic_path).write_bytes(b"MOCK_GEOTIFF_NOT_FOR_PRODUCTION")
        if job.report_path:
            Path(job.report_path).write_bytes(b"MOCK_PDF_NOT_FOR_PRODUCTION")
            outputs.append(job.report_path)
        return outputs

    def save_project(self, job: Any) -> None:
        self._call("SAVE_PROJECT")
        Path(job.project_path).write_text("mock Metashape project saved\n", encoding="utf-8")

    def resume_capabilities(self) -> dict[str, bool]:
        return {
            "project": self._project,
            "photos": bool(self._camera_paths),
            "alignment": self._aligned,
            "depth_maps": self._depth_maps,
            "dem": self._elevation,
            "orthomosaic": self._orthomosaic,
        }


class RealMetashapeAdapter:
    """Thin API mapping loaded only by the Metashape runtime.

    Calls are implemented against the legacy scripts and remain unverified until Phase 5.
    """

    FILTERS = {
        "none": "NoFiltering", "mild": "MildFiltering",
        "moderate": "ModerateFiltering", "aggressive": "AggressiveFiltering",
    }

    def __init__(self):
        import Metashape  # type: ignore[import-not-found]

        self.ms = Metashape
        self.doc = None
        self.chunk = None

    def create_project(self, job: Any) -> None:
        self.doc = self.ms.Document()
        self.chunk = self.doc.addChunk()
        self.chunk.label = job.plot_code
        self.chunk.crs = self.ms.CoordinateSystem(job.crs.replace("EPSG:", "EPSG::"))
        self.doc.save(job.project_path)

    def add_photos(self, paths: list[Path]) -> None:
        self.chunk.addPhotos([str(path) for path in paths])
        self.doc.save()

    def camera_paths(self) -> list[str]:
        return [camera.photo.path for camera in self.chunk.cameras]

    def align(self, profile: dict[str, Any]) -> None:
        values = profile["align"]
        self.chunk.matchPhotos(
            downscale=values["downscale"], generic_preselection=values["generic_preselection"],
            reference_preselection=values["reference_preselection"], keypoint_limit=values["keypoint_limit"],
            tiepoint_limit=values["tiepoint_limit"], guided_matching=values["guided_matching"],
        )
        self.chunk.alignCameras()
        self.doc.save()

    def alignment_metrics(self) -> dict[str, Any]:
        total = len(self.chunk.cameras)
        aligned = sum(1 for camera in self.chunk.cameras if camera.transform)
        tie_points = bool(self.chunk.tie_points and self.chunk.tie_points.points)
        return {"total": total, "aligned": aligned, "ratio": aligned / total if total else 0, "tie_points": tie_points}

    def build_depth_maps(self, profile: dict[str, Any]) -> None:
        values = profile["depth_maps"]
        filter_value = getattr(self.ms, self.FILTERS[values["filter_mode"]])
        self.chunk.buildDepthMaps(downscale=values["downscale"], filter_mode=filter_value)
        self.doc.save()

    def has_depth_maps(self) -> bool:
        return bool(self.chunk.depth_maps)

    def build_dem(self, profile: dict[str, Any]) -> None:
        sources = {"tie_points": self.ms.TiePointsData, "depth_maps": self.ms.DepthMapsData}
        self.chunk.buildDem(source_data=sources[profile["dem"]["source"]])
        self.doc.save()

    def has_elevation(self) -> bool:
        return bool(self.chunk.elevation)

    def build_orthomosaic(self, profile: dict[str, Any]) -> None:
        self.chunk.buildOrthomosaic(
            surface_data=self.ms.ElevationData,
            fill_holes=profile["orthomosaic"]["fill_holes"],
        )
        self.doc.save()

    def has_orthomosaic(self) -> bool:
        return bool(self.chunk.orthomosaic)

    def export(self, job: Any) -> list[str]:
        self.chunk.exportRaster(path=job.orthomosaic_path, source_data=self.ms.OrthomosaicData)
        outputs = [job.orthomosaic_path]
        if job.report_path:
            self.chunk.exportReport(job.report_path)
            outputs.append(job.report_path)
        return outputs

    def save_project(self, job: Any) -> None:
        self.doc.save()

    def resume_capabilities(self) -> dict[str, bool]:
        return {
            "project": self.doc is not None, "photos": bool(self.chunk and self.chunk.cameras),
            "alignment": bool(self.chunk and any(camera.transform for camera in self.chunk.cameras)),
            "depth_maps": self.has_depth_maps(), "dem": self.has_elevation(),
            "orthomosaic": self.has_orthomosaic(),
        }
