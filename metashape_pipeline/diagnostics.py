"""Sanitized diagnostic package generation independent of Metashape."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


FILES = ("job.json", "state.json", "profile.json", "error.txt", "processing.log", "environment.json", "summary.md")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_environment() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "cwd": os.getcwd(),
    }


def create_diagnostic_package(
    root: str | Path, job_id: str, *, job: dict[str, Any], state: dict[str, Any],
    profile: dict[str, Any], error: str, processing_log: str | Path | None = None,
) -> Path:
    destination = Path(root) / job_id
    destination.mkdir(parents=True, exist_ok=True)
    _write_json(destination / "job.json", job)
    _write_json(destination / "state.json", state)
    _write_json(destination / "profile.json", profile)
    (destination / "error.txt").write_text(error.rstrip() + "\n", encoding="utf-8")
    log_target = destination / "processing.log"
    if processing_log and Path(processing_log).is_file():
        shutil.copyfile(processing_log, log_target)
    else:
        log_target.write_text("No processing log was available.\n", encoding="utf-8")
    _write_json(destination / "environment.json", safe_environment())
    failed_stage = (state.get("error") or {}).get("stage", "unknown")
    (destination / "summary.md").write_text(
        "# Job diagnostic summary\n\n"
        f"- Job: `{job_id}`\n"
        f"- Overall status: `{state.get('overall_status', 'unknown')}`\n"
        f"- Failed stage: `{failed_stage}`\n"
        "- Review `error.txt`, `processing.log`, and the sanitized JSON snapshots.\n",
        encoding="utf-8",
    )
    return destination
