import json
from pathlib import Path

import pytest

from metashape_pipeline.diagnostics import FILES, create_diagnostic_package
from metashape_pipeline.job_config import JobConfig, JobValidationError
from metashape_pipeline.profiles import ProfileValidationError, load_profile, validate_profile
from metashape_pipeline.state_manager import StateManager, atomic_write_json, finish_stage, initial_state, start_stage
from metashape_pipeline.utilities import (
    detect_flight_date, detect_plot_code, inspect_folder, output_conflicts,
    proposed_output_paths, supported_images,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_job(tmp_path: Path) -> dict:
    photos = tmp_path / "ภาพโดรน" / "DJI_202606221038_092_28-VSD"
    output = tmp_path / "ผลลัพธ์" / "28-VSD"
    return {
        "schema_version": 1,
        "job_id": "28-VSD_20260710_103000",
        "plot_code": "28-VSD",
        "photo_dir": str(photos),
        "output_dir": str(output),
        "project_path": str(output / "28-VSD.psx"),
        "orthomosaic_path": str(output / "28-VSD_orthomosaic.tif"),
        "report_path": str(output / "28-VSD_report.pdf"),
        "crs": "EPSG:32647",
        "profile": "standard",
        "conflict_policy": "require_user_choice",
        "close_metashape_when_finished": True,
        "telegram_enabled": False,
    }


@pytest.mark.parametrize("value, expected", [
    ("DJI_202606221038_092_28-VSD", "28-VSD"),
    ("DJI_202605200909_063_37-STC", "37-STC"),
    ("28-vsd", "28-VSD"),
    ("ไม่มีรหัส", None),
])
def test_plot_code_detection(value, expected):
    assert detect_plot_code(value) == expected


def test_flight_date_detection():
    assert detect_flight_date("DJI_202606221038_092_28-VSD") == "2026-06-22"
    assert detect_flight_date("DJI_202613991038") is None


def test_image_count_is_non_recursive_and_case_insensitive(tmp_path):
    folder = tmp_path / "ภาพโดรน" / "28-VSD"
    folder.mkdir(parents=True)
    for name in ("a.JPG", "b.jpeg", "c.DNG", "note.txt"):
        (folder / name).write_bytes(b"image")
    nested = folder / "nested"
    nested.mkdir()
    (nested / "d.tif").write_bytes(b"image")
    assert len(supported_images(folder)) == 3
    assert len(supported_images(folder, recursive=True)) == 4


def test_inspection_supports_thai_path_and_naming(tmp_path):
    folder = tmp_path / "ภาพโดรน" / "DJI_202606221038_092_28-VSD"
    folder.mkdir(parents=True)
    (folder / "หนึ่ง.JPG").write_bytes(b"x")
    result = inspect_folder(folder)
    assert result["plot_code"] == "28-VSD"
    assert result["image_count"] == 1
    assert result["flight_date"] == "2026-06-22"
    assert "ผล" not in result["path"]
    assert result["output_proposal"]["project_path"].endswith("28-VSD.psx")


def test_missing_plot_code_is_warning(tmp_path):
    folder = tmp_path / "ภาพชุดใหม่"
    folder.mkdir()
    result = inspect_folder(folder)
    assert result["plot_code"] is None
    assert result["warnings"]


def test_output_conflicts(tmp_path):
    paths = proposed_output_paths(tmp_path / "28-VSD", "28-VSD")
    project = Path(paths["project_path"])
    project.parent.mkdir(parents=True)
    project.write_bytes(b"project")
    assert output_conflicts(paths) == [{"kind": "project_path", "path": str(project), "size": 7}]


def test_job_round_trip_and_unicode(tmp_path):
    job = JobConfig.from_dict(valid_job(tmp_path))
    path = tmp_path / "งาน.json"
    job.to_json(path)
    loaded = JobConfig.from_json(path)
    assert loaded == job
    assert "ภาพโดรน" in loaded.photo_dir


@pytest.mark.parametrize("change, message", [
    ({"photo_dir": "relative"}, "absolute"),
    ({"crs": "32647"}, "EPSG"),
    ({"conflict_policy": "delete"}, "conflict_policy"),
    ({"job_id": "bad\x00id"}, "null byte"),
    ({"project_path": "outside"}, "absolute"),
])
def test_job_validation_errors(tmp_path, change, message):
    data = valid_job(tmp_path)
    data.update(change)
    with pytest.raises(JobValidationError, match=message):
        JobConfig.from_dict(data)


def test_job_rejects_output_outside_output_dir(tmp_path):
    data = valid_job(tmp_path)
    data["project_path"] = str(tmp_path / "elsewhere.psx")
    with pytest.raises(JobValidationError, match="inside output_dir"):
        JobConfig.from_dict(data)


def test_all_profiles_load():
    profiles = [load_profile(name, ROOT / "profiles") for name in ("preview", "standard", "high_quality")]
    assert [profile["name"] for profile in profiles] == ["preview", "standard", "high_quality"]


def test_invalid_profile_value():
    profile = load_profile("standard", ROOT / "profiles")
    profile["depth_maps"]["filter_mode"] = "magic"
    with pytest.raises(ProfileValidationError, match="filter_mode"):
        validate_profile(profile)


def test_state_transitions_and_atomic_write(tmp_path):
    state = initial_state("job-1")
    state = start_stage(state, "PREFLIGHT")
    state = finish_stage(state, "PREFLIGHT", "passed", elapsed_seconds=1.5)
    assert state["last_successful_stage"] == "PREFLIGHT"
    path = tmp_path / "state.json"
    atomic_write_json(path, state)
    assert json.loads(path.read_text(encoding="utf-8"))["job_id"] == "job-1"
    assert not list(tmp_path.glob("*.tmp"))


def test_state_manager_persists_failure(tmp_path):
    manager = StateManager(tmp_path / "state.json")
    manager.create("job-2")
    manager.start("ALIGN")
    state = manager.finish("ALIGN", "failed", error="too few cameras")
    assert state["overall_status"] == "failed"
    assert manager.read()["error"]["stage"] == "ALIGN"


def test_diagnostics_contains_required_sanitized_files(tmp_path):
    job = valid_job(tmp_path)
    state = initial_state(job["job_id"])
    state = start_stage(state, "DEM")
    state = finish_stage(state, "DEM", "failed", error="controlled failure")
    profile = load_profile("standard", ROOT / "profiles")
    destination = create_diagnostic_package(
        tmp_path / "diagnostics", job["job_id"], job=job, state=state,
        profile=profile, error="controlled failure",
    )
    assert {path.name for path in destination.iterdir()} == set(FILES)
    environment = json.loads((destination / "environment.json").read_text(encoding="utf-8"))
    assert "environment" not in environment
    assert "token" not in json.dumps(environment).lower()
