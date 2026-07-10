"""Folder inspection, naming, and path helpers shared by UI and pipeline."""

from __future__ import annotations

import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".dng"}
PLOT_PATTERN = re.compile(r"(?<![A-Z0-9])(\d{1,3}-[A-Z]{2,8})(?![A-Z0-9])", re.IGNORECASE)
FLIGHT_PATTERN = re.compile(r"(?:DJI[_-])?(20\d{2})(\d{2})(\d{2})")


def ensure_safe_text(value: str, field: str = "value") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise ValueError(f"{field} contains a null byte")
    return value.strip()


def supported_images(folder: str | Path, *, recursive: bool = False) -> list[Path]:
    root = Path(folder)
    if not root.is_dir():
        raise ValueError(f"photo folder does not exist: {root}")
    candidates = root.rglob("*") if recursive else root.iterdir()
    return sorted(
        (path for path in candidates if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda path: str(path).casefold(),
    )


def detect_plot_code(value: str | Path) -> str | None:
    match = PLOT_PATTERN.search(str(value))
    return match.group(1).upper() if match else None


def detect_flight_date(value: str | Path) -> str | None:
    match = FLIGHT_PATTERN.search(str(value))
    if not match:
        return None
    try:
        return datetime.strptime("".join(match.groups()), "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def safe_plot_code(value: str) -> str:
    code = ensure_safe_text(value, "plot_code").upper()
    if not PLOT_PATTERN.fullmatch(code):
        raise ValueError("plot_code must look like 28-VSD")
    return code


def proposed_output_paths(photo_dir: str | Path, plot_code: str, output_folder: str = "Agisoft_Output") -> dict[str, str]:
    root = Path(photo_dir)
    code = safe_plot_code(plot_code)
    output = root.parent / ensure_safe_text(output_folder, "output_folder") / code
    return {
        "output_dir": str(output),
        "project_path": str(output / f"{code}.psx"),
        "orthomosaic_path": str(output / f"{code}_orthomosaic.tif"),
        "report_path": str(output / f"{code}_report.pdf"),
    }


def output_conflicts(paths: dict[str, str]) -> list[dict[str, Any]]:
    conflicts = []
    for kind in ("project_path", "orthomosaic_path", "report_path"):
        value = paths.get(kind)
        if value and Path(value).exists():
            path = Path(value)
            conflicts.append({"kind": kind, "path": str(path), "size": path.stat().st_size})
    return conflicts


def available_disk_space(path: str | Path) -> int:
    candidate = Path(path).resolve(strict=False)
    while not candidate.exists() and candidate.parent != candidate:
        candidate = candidate.parent
    return shutil.disk_usage(candidate).free


def inspect_folder(folder: str | Path, *, default_crs: str = "EPSG:32647", output_folder: str = "Agisoft_Output") -> dict[str, Any]:
    root = Path(ensure_safe_text(str(folder), "folder")).expanduser().resolve(strict=True)
    images = supported_images(root, recursive=False)
    plot_code = detect_plot_code(root.name)
    warnings = []
    if not images:
        warnings.append("ไม่พบไฟล์ภาพที่รองรับในโฟลเดอร์ระดับบนสุด")
    if not plot_code:
        warnings.append("ตรวจหารหัสแปลงไม่ได้ กรุณากรอกด้วยตนเอง")
    extensions = Counter(path.suffix.lower() for path in images)
    paths = proposed_output_paths(root, plot_code, output_folder) if plot_code else None
    return {
        "path": str(root),
        "recursive": False,
        "plot_code": plot_code,
        "flight_date": detect_flight_date(root.name),
        "image_count": len(images),
        "extension_summary": dict(sorted(extensions.items())),
        "crs": default_crs,
        "output_proposal": paths,
        "available_disk_space": available_disk_space(paths["output_dir"] if paths else root),
        "conflicts": output_conflicts(paths) if paths else [],
        "warnings": warnings,
    }
