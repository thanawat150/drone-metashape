from pathlib import Path

import pytest

from metashape_pipeline.adapter import MockAdapter
from metashape_pipeline.job_config import JobConfig
from metashape_pipeline.launcher import build_metashape_command
from metashape_pipeline.pipeline import Pipeline, PipelineFailed
from metashape_pipeline.profiles import load_profile
from metashape_pipeline.recovery import resume_decision
from metashape_pipeline.state_manager import StateManager, finish_stage, initial_state, start_stage


ROOT = Path(__file__).resolve().parents[1]


def make_job(tmp_path: Path, profile: str = "standard", count: int = 10) -> JobConfig:
    photos = tmp_path / "ภาพโดรน" / "DJI_202606221038_092_28-VSD"
    photos.mkdir(parents=True)
    for index in range(count):
        (photos / f"DJI_{index:03d}.JPG").write_bytes(b"photo")
    output = tmp_path / "output" / "28-VSD"
    return JobConfig.from_dict({
        "job_id": f"test-{profile}", "plot_code": "28-VSD", "photo_dir": str(photos),
        "output_dir": str(output), "project_path": str(output / "28-VSD.psx"),
        "orthomosaic_path": str(output / "28-VSD_orthomosaic.tif"),
        "report_path": str(output / "28-VSD_report.pdf"), "crs": "EPSG:32647",
        "profile": profile, "conflict_policy": "version",
        "close_metashape_when_finished": True, "telegram_enabled": False,
    })


def run_pipeline(tmp_path: Path, adapter: MockAdapter, profile_name: str = "standard"):
    job = make_job(tmp_path, profile_name)
    manager = StateManager(tmp_path / "job" / "state.json")
    manager.create(job.job_id)
    pipeline = Pipeline(
        job=job, profile=load_profile(profile_name, ROOT / "profiles"), adapter=adapter,
        state_manager=manager, log_path=tmp_path / "job" / "processing.log",
        diagnostics_root=tmp_path / "diagnostics",
    )
    return pipeline.run(), manager, job


def test_successful_full_pipeline(tmp_path):
    state, _, job = run_pipeline(tmp_path, MockAdapter())
    assert state["overall_status"] == "completed"
    assert state["stages"]["COMPLETE"]["status"] == "passed"
    assert state["aligned_photos"] == 10
    assert Path(job.orthomosaic_path).read_bytes().startswith(b"MOCK_")
    assert all(item["size"] > 0 for item in state["output_files"])


def test_alignment_warning_continues(tmp_path):
    state, _, _ = run_pipeline(tmp_path, MockAdapter(alignment_ratio=0.7))
    assert state["stages"]["ALIGN"]["status"] == "warning"
    assert state["stages"]["DEM"]["status"] == "passed"
    assert state["overall_status"] == "completed"


def test_alignment_failure_stops_and_diagnoses(tmp_path):
    adapter = MockAdapter(alignment_ratio=0.5)
    with pytest.raises(PipelineFailed) as failure:
        run_pipeline(tmp_path, adapter)
    assert failure.value.stage == "ALIGN"
    assert "DEPTH_MAPS" not in adapter.calls
    assert (failure.value.diagnostic_path / "summary.md").is_file()


def test_preview_skips_depth_maps(tmp_path):
    state, _, _ = run_pipeline(tmp_path, MockAdapter(), "preview")
    assert state["stages"]["DEPTH_MAPS"]["status"] == "skipped"
    assert state["stages"]["DEM"]["status"] == "passed"


def test_dem_failure_retries_once_with_same_profile(tmp_path):
    adapter = MockAdapter(fail_plan={"DEM": 1})
    state, _, _ = run_pipeline(tmp_path, adapter)
    assert adapter.calls.count("DEM") == 2
    assert state["retry_count"] == 1
    assert state["overall_status"] == "completed"


def test_retry_failure_stops_and_generates_diagnostics(tmp_path):
    adapter = MockAdapter(fail_plan={"DEM": 2})
    with pytest.raises(PipelineFailed) as failure:
        run_pipeline(tmp_path, adapter)
    assert adapter.calls.count("DEM") == 2
    assert "ORTHOMOSAIC" not in adapter.calls
    assert (failure.value.diagnostic_path / "processing.log").is_file()


def test_output_validation_failure_stops_save(tmp_path):
    class EmptyExportAdapter(MockAdapter):
        def export(self, job):
            outputs = super().export(job)
            Path(job.orthomosaic_path).write_bytes(b"")
            return outputs

    adapter = EmptyExportAdapter()
    with pytest.raises(PipelineFailed) as failure:
        run_pipeline(tmp_path, adapter)
    assert failure.value.stage == "VALIDATE_OUTPUT"
    assert "SAVE_PROJECT" not in adapter.calls


def test_version_policy_never_overwrites_unresolved_output(tmp_path):
    job = make_job(tmp_path)
    output = Path(job.orthomosaic_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"keep me")
    manager = StateManager(tmp_path / "job" / "state.json")
    manager.create(job.job_id)
    pipeline = Pipeline(
        job=job, profile=load_profile("standard", ROOT / "profiles"), adapter=MockAdapter(),
        state_manager=manager, log_path=tmp_path / "job" / "processing.log",
        diagnostics_root=tmp_path / "diagnostics",
    )
    with pytest.raises(PipelineFailed) as failure:
        pipeline.run()
    assert failure.value.stage == "PREFLIGHT"
    assert output.read_bytes() == b"keep me"


def test_resume_requires_matching_project_evidence():
    state = initial_state("resume")
    state = start_stage(state, "ALIGN")
    state = finish_stage(state, "ALIGN", "passed")
    assert resume_decision(state, {"alignment": True})["safe"] is True
    assert resume_decision(state, {"alignment": False})["safe"] is False


def test_metashape_command_is_argument_array_with_internal_script(tmp_path):
    executable = tmp_path / "metashape.exe"
    executable.write_bytes(b"exe")
    job = tmp_path / "job.json"
    job.write_text("{}", encoding="utf-8")
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    command = build_metashape_command(executable, job, profiles)
    assert command[0] == str(executable.resolve())
    assert command[1] == "-r"
    assert command[2].endswith("metashape_pipeline\\entrypoint.py")
    assert command[3:] == ["--job", str(job.resolve()), "--profiles", str(profiles.resolve())]
    assert all(isinstance(part, str) for part in command)
