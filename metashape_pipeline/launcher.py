"""Safe process launcher and development CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .adapter import MockAdapter, RealMetashapeAdapter
from .job_config import JobConfig
from .pipeline import Pipeline, PipelineCancelled, PipelineFailed
from .profiles import load_profile
from .state_manager import StateManager


APP_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = APP_ROOT / "metashape_pipeline" / "entrypoint.py"


def validate_metashape_executable(value: str | Path) -> Path:
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".exe" or "metashape" not in path.name.lower():
        raise ValueError("configured executable is not a plausible Metashape .exe")
    return path


def build_metashape_command(executable: str | Path, job_path: str | Path, profiles_dir: str | Path) -> list[str]:
    exe = validate_metashape_executable(executable)
    job = Path(job_path).resolve(strict=True)
    profiles = Path(profiles_dir).resolve(strict=True)
    return [str(exe), "-r", str(ENTRYPOINT), "--job", str(job), "--profiles", str(profiles)]


def launch_metashape(
    executable: str | Path, job_path: str | Path, profiles_dir: str | Path,
    log_path: str | Path, state_path: str | Path,
) -> subprocess.Popen:
    command = build_metashape_command(executable, job_path, profiles_dir)
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    handle = log.open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(
            command, cwd=APP_ROOT, stdout=handle, stderr=subprocess.STDOUT,
            shell=False, close_fds=True,
        )
    except Exception:
        handle.close()
        manager = StateManager(state_path)
        state = manager.read()
        state["overall_status"] = "failed"
        state["error"] = {"stage": "PREFLIGHT", "message": "Metashape process launch failed"}
        manager.write(state)
        raise
    process._drone_metashape_log_handle = handle  # type: ignore[attr-defined]
    manager = StateManager(state_path)
    state = manager.read()
    state["process_pid"] = process.pid
    manager.write(state)
    return process


def run_job(job_path: str | Path, profiles_dir: str | Path, *, mock: bool = False, scenario: str = "success") -> dict[str, Any]:
    job_file = Path(job_path).resolve(strict=True)
    job = JobConfig.from_json(job_file)
    profile = load_profile(job.profile, profiles_dir)
    state_path = job_file.with_name("state.json")
    log_path = job_file.with_name("processing.log")
    diagnostics_root = APP_ROOT / "diagnostics"
    scenarios = {
        "success": {}, "alignment_warning": {}, "dem_retry": {"DEM": 1},
        "dem_failure": {"DEM": 2}, "export_failure": {"EXPORT": 2},
    }
    if scenario not in scenarios:
        raise ValueError(f"unknown mock scenario: {scenario}")
    alignment = 0.70 if scenario == "alignment_warning" else 1.0
    adapter = MockAdapter(alignment_ratio=alignment, fail_plan=scenarios[scenario]) if mock else RealMetashapeAdapter()
    manager = StateManager(state_path)
    if not state_path.exists():
        manager.create(job.job_id)
    return Pipeline(
        job=job, profile=profile, adapter=adapter, state_manager=manager,
        log_path=log_path, diagnostics_root=diagnostics_root,
    ).run()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a validated drone Metashape job")
    parser.add_argument("--job", required=True)
    parser.add_argument("--profiles", default=str(APP_ROOT / "profiles"))
    parser.add_argument("--mock", action="store_true", help="use the explicit non-Metashape adapter")
    parser.add_argument("--scenario", default="success")
    return parser


def metashape_main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        run_job(args.job, args.profiles, mock=args.mock, scenario=args.scenario)
        return 0
    except (PipelineFailed, PipelineCancelled, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.mock:
        print(
            "Normal Python cannot run the real adapter. Launch through the configured Metashape executable or use --mock.",
            file=sys.stderr,
        )
        return 2
    return metashape_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
