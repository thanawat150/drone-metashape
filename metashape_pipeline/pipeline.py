"""Single reusable, stateful orthomosaic processing pipeline."""

from __future__ import annotations

import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .adapter import PipelineAdapter, RetryableStageError
from .diagnostics import create_diagnostic_package
from .notifier import NoOpNotifier, Notifier, notify_safely
from .state_manager import StateManager, finish_stage
from .validators import (
    StageValidationError, classify_alignment, validate_added_photos,
    validate_export, validate_preflight,
)


class PipelineFailed(RuntimeError):
    def __init__(self, stage: str, message: str, diagnostic_path: Path | None = None):
        super().__init__(f"{stage}: {message}")
        self.stage = stage
        self.diagnostic_path = diagnostic_path


class PipelineCancelled(RuntimeError):
    pass


class Pipeline:
    def __init__(
        self, *, job: Any, profile: dict[str, Any], adapter: PipelineAdapter,
        state_manager: StateManager, log_path: str | Path,
        diagnostics_root: str | Path, notifier: Notifier | None = None,
    ):
        self.job = job
        self.profile = profile
        self.adapter = adapter
        self.state = state_manager
        self.log_path = Path(log_path)
        self.diagnostics_root = Path(diagnostics_root)
        self.notifier = notifier or NoOpNotifier()
        self.photos: list[Path] = []
        self.run_started_at = datetime.now(timezone.utc)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat()
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {message}\n")

    def _notify(self, message: str) -> None:
        notify_safely(self.notifier, message, self.log)

    def _check_cancel(self) -> None:
        state = self.state.read()
        if state.get("cancel_requested"):
            state["overall_status"] = "cancelled"
            state["finished_at"] = datetime.now(timezone.utc).isoformat()
            self.state.write(state)
            self.log("Cancellation honored between stages")
            self._notify(f"{self.job.plot_code}: ยกเลิกหลังจบขั้นตอนปัจจุบัน")
            raise PipelineCancelled("cancellation requested")

    def _diagnose(self, error: str) -> Path:
        return create_diagnostic_package(
            self.diagnostics_root, self.job.job_id, job=self.job.to_dict(),
            state=self.state.read(), profile=self.profile, error=error,
            processing_log=self.log_path,
        )

    def _execute(self, stage: str, action: Callable[[], tuple[str, str | None] | None]) -> None:
        self._check_cancel()
        for attempt in range(2):
            self.state.start(stage)
            started = time.monotonic()
            self.log(f"{stage} started (attempt {attempt + 1})")
            try:
                result = action() or ("passed", None)
                status, warning = result
                self.state.finish(stage, status, elapsed_seconds=time.monotonic() - started, warning=warning)
                self.log(f"{stage} {status}" + (f": {warning}" if warning else ""))
                if warning:
                    self._notify(f"{self.job.plot_code}: WARNING {stage}: {warning}")
                else:
                    self._notify(f"{self.job.plot_code}: {stage} เสร็จแล้ว")
                return
            except Exception as exc:
                detail = f"{type(exc).__name__}: {exc}"
                self.state.finish(stage, "failed", elapsed_seconds=time.monotonic() - started, error=detail)
                self.log(f"{stage} failed: {detail}")
                if isinstance(exc, RetryableStageError) and attempt == 0:
                    state = self.state.read()
                    state["retry_count"] += 1
                    self.state.write(state)
                    self.log(f"{stage} retrying once with unchanged profile")
                    continue
                trace = traceback.format_exc()
                diagnostic = self._diagnose(trace)
                self._notify(f"{self.job.plot_code}: ERROR {stage}: {detail}")
                raise PipelineFailed(stage, detail, diagnostic) from exc

    def _skip(self, stage: str, reason: str) -> None:
        state = self.state.read()
        state = finish_stage(state, stage, "skipped", warning=reason)
        self.state.write(state)
        self.log(f"{stage} skipped: {reason}")

    def run(self) -> dict[str, Any]:
        if not self.state.path.exists():
            self.state.create(self.job.job_id)

        def preflight():
            self.photos = validate_preflight(self.job, self.profile)
        self._execute("PREFLIGHT", preflight)
        self._execute("CREATE_PROJECT", lambda: self.adapter.create_project(self.job))

        def add_photos():
            self.adapter.add_photos(self.photos)
            validate_added_photos(self.photos, self.adapter.camera_paths(), self.job.photo_dir)
            state = self.state.read()
            state["total_photos"] = len(self.photos)
            self.state.write(state)
        self._execute("ADD_PHOTOS", add_photos)

        def align():
            self.adapter.align(self.profile)
            metrics = self.adapter.alignment_metrics()
            status, warning = classify_alignment(metrics, self.profile)
            state = self.state.read()
            state["total_photos"] = metrics["total"]
            state["aligned_photos"] = metrics["aligned"]
            self.state.write(state)
            return status, warning
        self._execute("ALIGN", align)

        if self.profile["depth_maps"]["enabled"]:
            def depth_maps():
                self.adapter.build_depth_maps(self.profile)
                if not self.adapter.has_depth_maps():
                    raise StageValidationError("depth maps are missing after build")
            self._execute("DEPTH_MAPS", depth_maps)
        else:
            self._skip("DEPTH_MAPS", "disabled by profile")

        def dem():
            self.adapter.build_dem(self.profile)
            if not self.adapter.has_elevation():
                raise StageValidationError("elevation is missing after DEM build")
        self._execute("DEM", dem)

        def orthomosaic():
            self.adapter.build_orthomosaic(self.profile)
            if not self.adapter.has_orthomosaic():
                raise StageValidationError("orthomosaic is missing after build")
        self._execute("ORTHOMOSAIC", orthomosaic)

        def export():
            outputs = self.adapter.export(self.job)
            state = self.state.read()
            state["output_files"] = [{"path": path, "validated": False} for path in outputs]
            self.state.write(state)
        self._execute("EXPORT", export)

        def validate_outputs():
            outputs = validate_export(self.job, self.run_started_at)
            state = self.state.read()
            state["output_files"] = outputs
            self.state.write(state)
        self._execute("VALIDATE_OUTPUT", validate_outputs)
        self._execute("SAVE_PROJECT", lambda: self.adapter.save_project(self.job))
        self._execute("COMPLETE", lambda: None)
        return self.state.read()
