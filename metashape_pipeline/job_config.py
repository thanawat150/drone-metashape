"""Validated, serializable job configuration without a Metashape dependency."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
CONFLICT_POLICIES = {"require_user_choice", "resume", "version", "overwrite"}
CRS_PATTERN = re.compile(r"^EPSG(?:::|:)(\d{4,6})$", re.IGNORECASE)


class JobValidationError(ValueError):
    """Raised when untrusted job data does not satisfy the stable schema."""


def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise JobValidationError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise JobValidationError(f"{field} contains a null byte")
    return value.strip()


def _path(value: Any, field: str, *, optional: bool = False) -> str | None:
    text = _text(value, field, optional=optional)
    if text is None:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise JobValidationError(f"{field} must be an absolute path")
    return str(path)


@dataclass(frozen=True, slots=True)
class JobConfig:
    job_id: str
    plot_code: str
    photo_dir: str
    output_dir: str
    project_path: str
    orthomosaic_path: str
    report_path: str | None
    crs: str
    profile: str
    conflict_policy: str = "require_user_choice"
    close_metashape_when_finished: bool = True
    telegram_enabled: bool = False
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobConfig":
        if not isinstance(data, dict):
            raise JobValidationError("job must be a JSON object")
        allowed = set(cls.__dataclass_fields__)
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise JobValidationError(f"unknown job fields: {', '.join(unknown)}")
        missing = sorted(
            name
            for name in (
                "job_id", "plot_code", "photo_dir", "output_dir", "project_path",
                "orthomosaic_path", "crs", "profile"
            )
            if name not in data
        )
        if missing:
            raise JobValidationError(f"missing job fields: {', '.join(missing)}")

        version = data.get("schema_version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            raise JobValidationError(f"unsupported schema_version: {version}")
        policy = _text(data.get("conflict_policy", "require_user_choice"), "conflict_policy")
        if policy not in CONFLICT_POLICIES:
            raise JobValidationError(f"unsupported conflict_policy: {policy}")
        crs = _text(data["crs"], "crs")
        match = CRS_PATTERN.fullmatch(crs)
        if not match:
            raise JobValidationError("crs must use EPSG:<code> format")

        bool_fields = {}
        for name, default in (
            ("close_metashape_when_finished", True),
            ("telegram_enabled", False),
        ):
            value = data.get(name, default)
            if not isinstance(value, bool):
                raise JobValidationError(f"{name} must be boolean")
            bool_fields[name] = value

        job = cls(
            schema_version=version,
            job_id=_text(data["job_id"], "job_id"),
            plot_code=_text(data["plot_code"], "plot_code"),
            photo_dir=_path(data["photo_dir"], "photo_dir"),
            output_dir=_path(data["output_dir"], "output_dir"),
            project_path=_path(data["project_path"], "project_path"),
            orthomosaic_path=_path(data["orthomosaic_path"], "orthomosaic_path"),
            report_path=_path(data.get("report_path"), "report_path", optional=True),
            crs=f"EPSG:{match.group(1)}",
            profile=_text(data["profile"], "profile"),
            conflict_policy=policy,
            **bool_fields,
        )
        job._validate_output_paths()
        return job

    def _validate_output_paths(self) -> None:
        output = Path(self.output_dir).resolve(strict=False)
        for field in ("project_path", "orthomosaic_path", "report_path"):
            value = getattr(self, field)
            if value is None:
                continue
            try:
                Path(value).resolve(strict=False).relative_to(output)
            except ValueError as exc:
                raise JobValidationError(f"{field} must be inside output_dir") from exc

    @classmethod
    def from_json(cls, path: str | Path) -> "JobConfig":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
