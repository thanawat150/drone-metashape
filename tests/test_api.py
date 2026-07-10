import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import APP_ROOT, create_app


def make_photos(tmp_path: Path, count: int = 10) -> Path:
    folder = tmp_path / "ภาพโดรน" / "DJI_202606221038_092_28-VSD"
    folder.mkdir(parents=True)
    for index in range(count):
        (folder / f"photo-{index}.JPG").write_bytes(b"photo")
    return folder


@pytest.fixture
def api(tmp_path):
    opened = []
    app = create_app(
        data_root=tmp_path, profiles_dir=APP_ROOT / "profiles", mock_mode=True,
        picker=lambda: None, opener=lambda path: opened.append(path),
    )
    with TestClient(app) as client:
        yield client, app.state.jobs, opened


def wait_for(client: TestClient, job_id: str, statuses=("completed", "failed", "cancelled")):
    for _ in range(200):
        state = client.get(f"/api/jobs/{job_id}").json()
        if state["overall_status"] in statuses:
            return state
        time.sleep(0.01)
    raise AssertionError("job did not finish")


def create_payload(folder: Path, **changes):
    payload = {
        "photo_dir": str(folder), "plot_code": "28-VSD", "image_count": 10,
        "crs": "EPSG:32647", "profile": "standard",
        "conflict_policy": "version", "mock_scenario": "success",
    }
    payload.update(changes)
    return payload


def test_health_and_thai_ui(api):
    client, _, _ = api
    assert client.get("/api/health").json() == {"status": "ok", "mock_mode": True, "host": "127.0.0.1"}
    page = client.get("/")
    assert page.status_code == 200
    assert "เริ่มสร้าง Orthomosaic" in page.text
    assert "โหมดทดสอบ" in page.text


def test_folder_picker_cancellation(api):
    client, _, _ = api
    assert client.post("/api/select-folder").json() == {"cancelled": True, "path": None}


def test_inspection_and_profiles(api, tmp_path):
    client, _, _ = api
    folder = make_photos(tmp_path)
    result = client.post("/api/inspect-folder", json={"path": str(folder)})
    assert result.status_code == 200
    assert result.json()["image_count"] == 10
    assert result.json()["plot_code"] == "28-VSD"
    assert {item["name"] for item in client.get("/api/profiles").json()} == {"preview", "standard", "high_quality"}


def test_invalid_path_and_stale_image_count(api, tmp_path):
    client, _, _ = api
    assert client.post("/api/inspect-folder", json={"path": str(tmp_path / "missing")}).status_code == 422
    folder = make_photos(tmp_path)
    response = client.post("/api/jobs", json=create_payload(folder, image_count=9))
    assert response.status_code == 409


def test_mock_success_poll_log_and_open_output(api, tmp_path):
    client, _, opened = api
    folder = make_photos(tmp_path)
    response = client.post("/api/jobs", json=create_payload(folder))
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    state = wait_for(client, job_id)
    assert state["stages"]["COMPLETE"]["status"] == "passed"
    assert "PREFLIGHT started" in client.get(f"/api/jobs/{job_id}/log").text
    assert client.post(f"/api/jobs/{job_id}/open-output").status_code == 200
    assert opened and opened[-1].is_dir()


def test_duplicate_active_job_is_rejected(api, tmp_path):
    client, service, _ = api
    folder = make_photos(tmp_path)
    release = threading.Event()
    original = service._run
    service._run = lambda job, scenario: release.wait(2)
    try:
        first = client.post("/api/jobs", json=create_payload(folder))
        assert first.status_code == 202
        second = client.post("/api/jobs", json=create_payload(folder))
        assert second.status_code == 409
    finally:
        release.set()
        service._run = original


def test_mock_failure_diagnostics_retry_and_open_restrictions(api, tmp_path):
    client, _, opened = api
    folder = make_photos(tmp_path)
    response = client.post("/api/jobs", json=create_payload(folder, mock_scenario="permanent_failure"))
    job_id = response.json()["job_id"]
    state = wait_for(client, job_id)
    assert state["overall_status"] == "failed"
    assert state["error"]["stage"] == "ORTHOMOSAIC"
    assert client.post(f"/api/jobs/{job_id}/open-diagnostics").status_code == 200
    assert opened[-1].name == job_id
    retry = client.post(f"/api/jobs/{job_id}/retry")
    assert retry.status_code == 202
    assert wait_for(client, retry.json()["job_id"])["overall_status"] == "completed"
    assert client.post("/api/jobs/..%2F..%2Fetc/open-output").status_code in {404, 405}
    assert client.get("/api/jobs/not-a-real-job/log").status_code == 404


def test_cancellation_request_is_persisted(api, tmp_path):
    client, service, _ = api
    folder = make_photos(tmp_path)
    release = threading.Event()
    original = service._run
    service._run = lambda job, scenario: release.wait(2)
    try:
        job_id = client.post("/api/jobs", json=create_payload(folder)).json()["job_id"]
        result = client.post(f"/api/jobs/{job_id}/cancel")
        assert result.json()["cancel_requested"] is True
        assert client.get(f"/api/jobs/{job_id}").json()["cancel_requested"] is True
    finally:
        release.set()
        service._run = original


def test_overwrite_requires_explicit_confirmation(api, tmp_path):
    client, _, _ = api
    folder = make_photos(tmp_path)
    output = tmp_path / "existing"
    output.mkdir()
    (output / "28-VSD.psx").write_bytes(b"existing")
    response = client.post("/api/jobs", json=create_payload(folder, output_dir=str(output), conflict_policy="overwrite"))
    assert response.status_code == 409
