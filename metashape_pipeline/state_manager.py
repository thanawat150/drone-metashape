"""Atomic persisted job state and guarded stage transitions."""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGES = (
    "PREFLIGHT", "CREATE_PROJECT", "ADD_PHOTOS", "ALIGN", "DEPTH_MAPS",
    "DEM", "ORTHOMOSAIC", "EXPORT", "VALIDATE_OUTPUT", "SAVE_PROJECT", "COMPLETE",
)
STAGE_STATES = {"pending", "running", "passed", "warning", "failed", "skipped"}
TERMINAL_STAGE_STATES = {"passed", "warning", "failed", "skipped"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initial_state(job_id: str) -> dict[str, Any]:
    timestamp = utc_now()
    return {
        "schema_version": 1,
        "job_id": job_id,
        "overall_status": "pending",
        "current_stage": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "started_at": None,
        "finished_at": None,
        "total_photos": 0,
        "aligned_photos": 0,
        "retry_count": 0,
        "last_successful_stage": None,
        "cancel_requested": False,
        "warnings": [],
        "error": None,
        "output_files": [],
        "stages": {
            stage: {
                "status": "pending", "started_at": None, "finished_at": None,
                "elapsed_seconds": None, "warning": None, "error": None,
            }
            for stage in STAGES
        },
    }


def atomic_write_json(path: str | Path, data: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def read_state(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("schema_version") != 1 or set(state.get("stages", {})) != set(STAGES):
        raise ValueError("unsupported or invalid state file")
    return state


def start_stage(state: dict[str, Any], stage: str) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage}")
    updated = deepcopy(state)
    entry = updated["stages"][stage]
    if entry["status"] not in {"pending", "failed"}:
        raise ValueError(f"cannot start {stage} from {entry['status']}")
    now = utc_now()
    entry.update(status="running", started_at=now, finished_at=None, elapsed_seconds=None, warning=None, error=None)
    updated["current_stage"] = stage
    updated["overall_status"] = "running"
    updated["started_at"] = updated["started_at"] or now
    updated["updated_at"] = now
    return updated


def finish_stage(
    state: dict[str, Any], stage: str, status: str, *, elapsed_seconds: float = 0,
    warning: str | None = None, error: str | None = None,
) -> dict[str, Any]:
    if stage not in STAGES or status not in TERMINAL_STAGE_STATES:
        raise ValueError("invalid stage completion")
    updated = deepcopy(state)
    entry = updated["stages"][stage]
    if entry["status"] != "running" and not (status == "skipped" and entry["status"] == "pending"):
        raise ValueError(f"cannot finish {stage} from {entry['status']}")
    now = utc_now()
    entry.update(status=status, finished_at=now, elapsed_seconds=max(0, elapsed_seconds), warning=warning, error=error)
    updated["updated_at"] = now
    if warning:
        updated["warnings"].append({"stage": stage, "message": warning})
    if status == "failed":
        updated["overall_status"] = "failed"
        updated["error"] = {"stage": stage, "message": error or "stage failed"}
        updated["finished_at"] = now
    elif status in {"passed", "warning"}:
        updated["last_successful_stage"] = stage
        if stage == "COMPLETE":
            updated["overall_status"] = "completed"
            updated["finished_at"] = now
    return updated


class StateManager:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def create(self, job_id: str) -> dict[str, Any]:
        state = initial_state(job_id)
        atomic_write_json(self.path, state)
        return state

    def read(self) -> dict[str, Any]:
        return read_state(self.path)

    def write(self, state: dict[str, Any]) -> None:
        atomic_write_json(self.path, state)

    def start(self, stage: str) -> dict[str, Any]:
        state = start_stage(self.read(), stage)
        self.write(state)
        return state

    def finish(self, stage: str, status: str, **details: Any) -> dict[str, Any]:
        state = finish_stage(self.read(), stage, status, **details)
        self.write(state)
        return state

    def request_cancel(self) -> dict[str, Any]:
        state = self.read()
        state["cancel_requested"] = True
        state["updated_at"] = utc_now()
        self.write(state)
        return state
