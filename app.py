"""Localhost-only API and Thai web UI for deterministic Metashape jobs."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from metashape_pipeline.adapter import MockAdapter
from metashape_pipeline.job_config import JobConfig, JobValidationError
from metashape_pipeline.launcher import launch_metashape
from metashape_pipeline.pipeline import Pipeline, PipelineCancelled, PipelineFailed
from metashape_pipeline.profiles import ProfileValidationError, list_profiles, load_profile
from metashape_pipeline.state_manager import StateManager
from metashape_pipeline.utilities import inspect_folder, output_conflicts, safe_plot_code, supported_images


APP_ROOT = Path(__file__).resolve().parent
WEB_ROOT = APP_ROOT / "web"
JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
MOCK_SCENARIOS = {
    "success": (1.0, {}),
    "alignment_warning": (0.70, {}),
    "dem_failure": (1.0, {"DEM": 2}),
    "retry_then_success": (1.0, {"DEM": 1}),
    "permanent_failure": (1.0, {"ORTHOMOSAIC": 2}),
}


def load_config(root: Path) -> dict[str, Any]:
    local = root / "config.local.json"
    source = local if local.is_file() else APP_ROOT / "config.example.json"
    with source.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("host") != "127.0.0.1":
        raise ValueError("host must remain 127.0.0.1 in this local application")
    return config


def native_folder_picker() -> str | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(title="เลือกโฟลเดอร์ภาพโดรน", mustexist=True)
        return str(Path(selected).resolve()) if selected else None
    finally:
        root.destroy()


def default_opener(path: Path) -> None:
    if os.name != "nt":
        raise RuntimeError("open-folder is available only on Windows")
    os.startfile(str(path))  # type: ignore[attr-defined]


class LocalJobService:
    def __init__(
        self, *, data_root: Path, profiles_dir: Path, mock_mode: bool,
        picker: Callable[[], str | None], opener: Callable[[Path], None],
    ):
        self.data_root = data_root.resolve()
        self.profiles_dir = profiles_dir.resolve()
        self.mock_mode = mock_mode
        self.picker = picker
        self.opener = opener
        self.jobs_root = self.data_root / "jobs"
        self.logs_root = self.data_root / "logs"
        self.diagnostics_root = self.data_root / "diagnostics"
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.threads: dict[str, threading.Thread] = {}
        self.config = load_config(self.data_root)

    def job_dir(self, job_id: str) -> Path:
        if not JOB_ID_PATTERN.fullmatch(job_id):
            raise HTTPException(404, "ไม่พบงาน")
        path = self.jobs_root / job_id
        if not path.is_dir():
            raise HTTPException(404, "ไม่พบงาน")
        return path

    def state_for(self, job_id: str) -> dict[str, Any]:
        return StateManager(self.job_dir(job_id) / "state.json").read()

    def list_states(self) -> list[dict[str, Any]]:
        states = []
        for path in self.jobs_root.iterdir():
            state_path = path / "state.json"
            if path.is_dir() and state_path.is_file():
                try:
                    states.append(StateManager(state_path).read())
                except (ValueError, OSError, json.JSONDecodeError):
                    continue
        return sorted(states, key=lambda value: value.get("created_at", ""), reverse=True)

    def active_job(self) -> dict[str, Any] | None:
        return next((state for state in self.list_states() if state.get("overall_status") in {"pending", "running"}), None)

    def _unique_id(self, plot_code: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{plot_code}_{stamp}_{uuid.uuid4().hex[:6]}"

    def _versioned_output(self, base: Path) -> Path:
        if not base.exists():
            return base
        for number in range(2, 10_000):
            candidate = base.with_name(f"{base.name}_v{number}")
            if not candidate.exists():
                return candidate
        raise HTTPException(409, "ไม่สามารถสร้างชื่อผลลัพธ์เวอร์ชันใหม่ได้")

    def _build_job(self, payload: dict[str, Any]) -> tuple[JobConfig, str]:
        if not isinstance(payload, dict):
            raise HTTPException(422, "ข้อมูลต้องเป็น JSON object")
        try:
            inspection = inspect_folder(
                payload.get("photo_dir", ""), default_crs=self.config["default_crs"],
                output_folder=self.config["default_output_folder_name"],
            )
            plot_code = safe_plot_code(payload.get("plot_code") or inspection.get("plot_code") or "")
        except (ValueError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        if payload.get("image_count") is not None and payload["image_count"] != inspection["image_count"]:
            raise HTTPException(409, "จำนวนภาพเปลี่ยนไป กรุณาตรวจโฟลเดอร์ใหม่")
        if inspection["image_count"] <= 0:
            raise HTTPException(422, "ไม่พบภาพที่รองรับ")

        profile_name = payload.get("profile", self.config["default_profile"])
        try:
            load_profile(profile_name, self.profiles_dir)
        except (ProfileValidationError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

        default_output = Path(inspection["path"]).parent / self.config["default_output_folder_name"] / plot_code
        output = Path(payload.get("output_dir") or default_output).expanduser().resolve(strict=False)
        policy = payload.get("conflict_policy", "require_user_choice")
        if policy == "version":
            output = self._versioned_output(output)
        paths = {
            "project_path": str(output / f"{plot_code}.psx"),
            "orthomosaic_path": str(output / f"{plot_code}_orthomosaic.tif"),
            "report_path": str(output / f"{plot_code}_report.pdf"),
        }
        conflicts = output_conflicts(paths)
        if conflicts and policy == "require_user_choice":
            raise HTTPException(409, detail={"message": "พบผลลัพธ์เดิม", "conflicts": conflicts})
        if policy == "resume":
            raise HTTPException(409, "Resume ต้องตรวจ project จริงและยังไม่เปิดใช้ก่อน Phase 5")
        if policy == "overwrite" and not payload.get("confirm_overwrite", False):
            raise HTTPException(409, "ต้องยืนยัน overwrite อย่างชัดเจน")
        scenario = payload.get("mock_scenario", "success")
        if self.mock_mode and scenario not in MOCK_SCENARIOS:
            raise HTTPException(422, "mock scenario ไม่ถูกต้อง")

        job_id = self._unique_id(plot_code)
        try:
            job = JobConfig.from_dict({
                "schema_version": 1, "job_id": job_id, "plot_code": plot_code,
                "photo_dir": inspection["path"], "output_dir": str(output), **paths,
                "crs": payload.get("crs", inspection["crs"]), "profile": profile_name,
                "conflict_policy": policy,
                "close_metashape_when_finished": bool(payload.get("close_metashape_when_finished", True)),
                "telegram_enabled": bool(payload.get("telegram_enabled", False)),
            })
        except JobValidationError as exc:
            raise HTTPException(422, str(exc)) from exc
        return job, scenario

    def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            active = self.active_job()
            if active:
                raise HTTPException(409, detail={"message": "มีงานกำลังทำอยู่", "active_job": active["job_id"]})
            job, scenario = self._build_job(payload)
            directory = self.jobs_root / job.job_id
            directory.mkdir(parents=True)
            job_path = directory / "job.json"
            job.to_json(job_path)
            manager = StateManager(directory / "state.json")
            manager.create(job.job_id)
            thread = threading.Thread(target=self._run, args=(job, scenario), name=f"job-{job.job_id}", daemon=True)
            self.threads[job.job_id] = thread
            thread.start()
        return {"job_id": job.job_id, "mock_mode": self.mock_mode}

    def _run(self, job: JobConfig, scenario: str) -> None:
        directory = self.jobs_root / job.job_id
        state_path = directory / "state.json"
        log_path = directory / "processing.log"
        try:
            if self.mock_mode:
                alignment, fail_plan = MOCK_SCENARIOS[scenario]
                Pipeline(
                    job=job, profile=load_profile(job.profile, self.profiles_dir),
                    adapter=MockAdapter(alignment_ratio=alignment, fail_plan=fail_plan),
                    state_manager=StateManager(state_path), log_path=log_path,
                    diagnostics_root=self.diagnostics_root,
                ).run()
            else:
                executable = self.config.get("metashape_executable")
                if not executable:
                    raise RuntimeError("ยังไม่ได้ตั้งค่า Metashape executable")
                process = launch_metashape(executable, directory / "job.json", self.profiles_dir, log_path, state_path)
                return_code = process.wait()
                handle = getattr(process, "_drone_metashape_log_handle", None)
                if handle:
                    handle.close()
                if return_code and StateManager(state_path).read()["overall_status"] not in {"failed", "cancelled"}:
                    raise RuntimeError(f"Metashape exited with code {return_code}")
        except (PipelineFailed, PipelineCancelled):
            pass
        except Exception as exc:
            manager = StateManager(state_path)
            state = manager.read()
            state["overall_status"] = "failed"
            state["error"] = {"stage": state.get("current_stage") or "PREFLIGHT", "message": f"{type(exc).__name__}: {exc}"}
            manager.write(state)

    def retry_job(self, job_id: str) -> dict[str, Any]:
        old = JobConfig.from_json(self.job_dir(job_id) / "job.json")
        state = self.state_for(job_id)
        if state["overall_status"] not in {"failed", "cancelled"}:
            raise HTTPException(409, "retry ได้เฉพาะงานที่ failed หรือ cancelled")
        return self.create_job({
            "photo_dir": old.photo_dir, "plot_code": old.plot_code, "crs": old.crs,
            "profile": old.profile, "conflict_policy": "version",
            "mock_scenario": "success", "close_metashape_when_finished": old.close_metashape_when_finished,
        })

    def open_known(self, job_id: str, kind: str) -> dict[str, str]:
        directory = self.job_dir(job_id)
        job = JobConfig.from_json(directory / "job.json")
        path = Path(job.output_dir) if kind == "output" else self.diagnostics_root / job_id
        if kind == "diagnostics" and not path.is_dir():
            worker = self.threads.get(job_id)
            if worker and worker.is_alive():
                worker.join(timeout=1.0)
        if not path.is_dir():
            raise HTTPException(404, "ยังไม่มีโฟลเดอร์ที่ขอเปิด")
        self.opener(path.resolve())
        return {"opened": str(path.resolve())}


def create_app(
    *, data_root: str | Path = APP_ROOT, profiles_dir: str | Path = APP_ROOT / "profiles",
    mock_mode: bool = False, picker: Callable[[], str | None] = native_folder_picker,
    opener: Callable[[Path], None] = default_opener,
) -> FastAPI:
    app = FastAPI(title="Drone Metashape Local", docs_url=None, redoc_url=None)
    service = LocalJobService(
        data_root=Path(data_root), profiles_dir=Path(profiles_dir), mock_mode=mock_mode,
        picker=picker, opener=opener,
    )
    app.state.jobs = service

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mock_mode": service.mock_mode, "host": "127.0.0.1"}

    @app.post("/api/select-folder")
    async def select_folder():
        selected = await asyncio.to_thread(service.picker)
        return {"cancelled": not bool(selected), "path": selected}

    @app.post("/api/inspect-folder")
    def inspect(payload: dict[str, Any] = Body(...)):
        try:
            return inspect_folder(
                payload.get("path", ""), default_crs=service.config["default_crs"],
                output_folder=service.config["default_output_folder_name"],
            )
        except (ValueError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/profiles")
    def profiles():
        return list_profiles(service.profiles_dir)

    @app.post("/api/jobs", status_code=202)
    def create_job(payload: dict[str, Any] = Body(...)):
        return service.create_job(payload)

    @app.get("/api/jobs")
    def jobs():
        return service.list_states()

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        return service.state_for(job_id)

    @app.get("/api/jobs/{job_id}/log", response_class=PlainTextResponse)
    def job_log(job_id: str):
        path = service.job_dir(job_id) / "processing.log"
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""

    @app.post("/api/jobs/{job_id}/retry", status_code=202)
    def retry(job_id: str):
        return service.retry_job(job_id)

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel(job_id: str):
        state = StateManager(service.job_dir(job_id) / "state.json").request_cancel()
        return {"job_id": job_id, "cancel_requested": state["cancel_requested"]}

    @app.post("/api/jobs/{job_id}/open-output")
    def open_output(job_id: str):
        return service.open_known(job_id, "output")

    @app.post("/api/jobs/{job_id}/open-diagnostics")
    def open_diagnostics(job_id: str):
        return service.open_known(job_id, "diagnostics")

    @app.get("/")
    def index():
        return FileResponse(WEB_ROOT / "index.html")

    app.mount("/web", StaticFiles(directory=WEB_ROOT), name="web")
    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock-metashape", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    config = load_config(APP_ROOT)
    import uvicorn
    uvicorn.run(create_app(mock_mode=args.mock_metashape), host="127.0.0.1", port=int(config["port"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
