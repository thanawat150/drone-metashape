"""External profile loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROFILE_NAMES = {"preview", "standard", "high_quality"}
FILTER_MODES = {"none", "mild", "moderate", "aggressive"}
DEM_SOURCES = {"tie_points", "depth_maps"}
SURFACES = {"elevation"}
GPU_MODES = {"auto", "disabled"}


class ProfileValidationError(ValueError):
    pass


def _require(data: dict[str, Any], key: str, expected: type, context: str) -> Any:
    value = data.get(key)
    if not isinstance(value, expected):
        raise ProfileValidationError(f"{context}.{key} must be {expected.__name__}")
    return value


def validate_profile(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ProfileValidationError("profile must be a JSON object")
    if data.get("schema_version") != 1:
        raise ProfileValidationError("unsupported profile schema_version")
    name = _require(data, "name", str, "profile")
    if name not in PROFILE_NAMES:
        raise ProfileValidationError(f"unsupported profile name: {name}")
    _require(data, "label_th", str, "profile")
    _require(data, "description", str, "profile")

    align = _require(data, "align", dict, "profile")
    for key in ("downscale", "keypoint_limit", "tiepoint_limit"):
        value = _require(align, key, int, "align")
        if value < 0 or (key == "downscale" and value < 1):
            raise ProfileValidationError(f"align.{key} is out of range")
    for key in ("generic_preselection", "reference_preselection", "guided_matching"):
        _require(align, key, bool, "align")

    depth = _require(data, "depth_maps", dict, "profile")
    _require(depth, "enabled", bool, "depth_maps")
    if _require(depth, "downscale", int, "depth_maps") < 1:
        raise ProfileValidationError("depth_maps.downscale is out of range")
    if _require(depth, "filter_mode", str, "depth_maps") not in FILTER_MODES:
        raise ProfileValidationError("unsupported depth_maps.filter_mode")

    dem = _require(data, "dem", dict, "profile")
    source = _require(dem, "source", str, "dem")
    if source not in DEM_SOURCES:
        raise ProfileValidationError("unsupported dem.source")
    if source == "depth_maps" and not depth["enabled"]:
        raise ProfileValidationError("depth_maps must be enabled for a depth_maps DEM")

    ortho = _require(data, "orthomosaic", dict, "profile")
    if _require(ortho, "surface", str, "orthomosaic") not in SURFACES:
        raise ProfileValidationError("unsupported orthomosaic.surface")
    _require(ortho, "fill_holes", bool, "orthomosaic")

    hardware = _require(data, "hardware", dict, "profile")
    _require(hardware, "cpu_enabled", bool, "hardware")
    if _require(hardware, "gpu_mode", str, "hardware") not in GPU_MODES:
        raise ProfileValidationError("unsupported hardware.gpu_mode")
    odm_args = data.get("odm_args", [])
    if not isinstance(odm_args, list) or not all(isinstance(item, str) for item in odm_args):
        raise ProfileValidationError("odm_args must be a list of strings")
    return data


def load_profile(name: str, directory: str | Path = "profiles") -> dict[str, Any]:
    if name not in PROFILE_NAMES:
        raise ProfileValidationError(f"unsupported profile name: {name}")
    path = Path(directory) / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("name") != name:
        raise ProfileValidationError("profile filename and name do not match")
    return validate_profile(data)


def list_profiles(directory: str | Path = "profiles") -> list[dict[str, Any]]:
    return [load_profile(name, directory) for name in sorted(PROFILE_NAMES)]
