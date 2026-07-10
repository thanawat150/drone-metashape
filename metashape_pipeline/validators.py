"""Stage validators that check evidence rather than absence of exceptions."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utilities import output_conflicts, supported_images


class StageValidationError(RuntimeError):
    pass


def validate_preflight(job: Any, profile: dict[str, Any]) -> list[Path]:
    photos = supported_images(job.photo_dir, recursive=False)
    if not photos:
        raise StageValidationError("no supported images found")
    output = Path(job.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    probe = output / ".write-test.tmp"
    try:
        probe.write_bytes(b"")
    finally:
        probe.unlink(missing_ok=True)
    conflicts = output_conflicts(job.to_dict())
    if conflicts and job.conflict_policy == "require_user_choice":
        raise StageValidationError("existing output requires an explicit conflict choice")
    if conflicts and job.conflict_policy == "version":
        raise StageValidationError("version policy must be resolved to unused output paths before launch")
    if conflicts and job.conflict_policy == "resume":
        raise StageValidationError("resume must be approved by recovery validation before launch")
    if profile["name"] != job.profile:
        raise StageValidationError("job profile does not match loaded profile")
    return photos


def validate_added_photos(expected: list[Path], actual_paths: list[str], source: str | Path) -> None:
    if len(actual_paths) != len(expected):
        raise StageValidationError(f"camera count mismatch: expected {len(expected)}, got {len(actual_paths)}")
    root = Path(source).resolve()
    expected_set = {str(path.resolve()).casefold() for path in expected}
    actual_set = {str(Path(path).resolve()).casefold() for path in actual_paths}
    if expected_set != actual_set:
        raise StageValidationError("camera paths do not match selected source images")
    if any(root not in Path(path).resolve().parents for path in actual_paths):
        raise StageValidationError("a camera path is outside the selected source folder")


def classify_alignment(metrics: dict[str, Any], profile: dict[str, Any]) -> tuple[str, str | None]:
    ratio = float(metrics.get("ratio", 0))
    if not metrics.get("tie_points"):
        raise StageValidationError("tie points are missing after alignment")
    qa = profile.get("qa", {})
    passed = float(qa.get("alignment_pass_ratio", 0.85))
    warning = float(qa.get("alignment_warning_ratio", 0.60))
    if not 0 <= warning <= passed <= 1:
        raise StageValidationError("invalid alignment thresholds")
    if ratio < warning:
        raise StageValidationError(f"aligned ratio {ratio:.3f} is below failure threshold {warning:.3f}")
    if ratio < passed:
        return "warning", f"aligned ratio {ratio:.3f} is below pass threshold {passed:.3f}"
    return "passed", None


def validate_export(job: Any, run_started_at: datetime) -> list[dict[str, Any]]:
    required = [("orthomosaic", job.orthomosaic_path), ("project", job.project_path)]
    if job.report_path:
        required.append(("report", job.report_path))
    results = []
    tolerance = 2.0
    for kind, value in required:
        path = Path(value)
        if not path.is_file() or path.stat().st_size <= 0:
            raise StageValidationError(f"{kind} output is missing or empty: {path}")
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if modified.timestamp() + tolerance < run_started_at.timestamp():
            raise StageValidationError(f"{kind} output is not from the current run: {path}")
        results.append({"kind": kind, "path": str(path), "size": path.stat().st_size})
    return results
