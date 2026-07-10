import json
import sys
from pathlib import Path

import pytest

from metashape_pipeline.configuration import (
    discover_metashape, load_merged_config, plausible_metashape_executable,
)
from scripts import start_app


ROOT = Path(__file__).resolve().parents[1]


def write_example(root: Path):
    (root / "config.example.json").write_text(json.dumps({
        "schema_version": 1, "host": "127.0.0.1", "port": 8765,
        "metashape_executable": "", "default_crs": "EPSG:32647",
    }), encoding="utf-8")


def test_requirements_fingerprint_is_stable_and_changes(tmp_path):
    path = tmp_path / "requirements.txt"
    path.write_text("fastapi\n", encoding="utf-8")
    first = start_app.requirements_fingerprint(path)
    assert first == start_app.requirements_fingerprint(path)
    path.write_text("fastapi\nuvicorn\n", encoding="utf-8")
    assert start_app.requirements_fingerprint(path) != first


def test_current_python_has_runtime_dependencies():
    assert start_app.dependencies_available(Path(sys.executable)) is True


def test_local_config_merges_only_known_fields(tmp_path):
    write_example(tmp_path)
    (tmp_path / "config.local.json").write_text(json.dumps({"port": 9000}), encoding="utf-8")
    config = load_merged_config(tmp_path)
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 9000
    (tmp_path / "config.local.json").write_text(json.dumps({"secret_token": "no"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown local config"):
        load_merged_config(tmp_path)


def test_config_rejects_lan_binding(tmp_path):
    write_example(tmp_path)
    (tmp_path / "config.local.json").write_text(json.dumps({"host": "0.0.0.0"}), encoding="utf-8")
    with pytest.raises(ValueError, match="127.0.0.1"):
        load_merged_config(tmp_path)


def test_metashape_discovery_prefers_config_then_common_then_picker(tmp_path):
    configured = tmp_path / "configured" / "metashape.exe"
    common = tmp_path / "common" / "metashape.exe"
    picked = tmp_path / "picked" / "metashape.exe"
    for path in (configured, common, picked):
        path.parent.mkdir()
        path.write_bytes(b"exe")
    assert discover_metashape({"metashape_executable": str(configured)}, candidates=(common,), picker=lambda: str(picked)) == configured.resolve()
    assert discover_metashape({"metashape_executable": ""}, candidates=(common,), picker=lambda: str(picked)) == common.resolve()
    assert discover_metashape({"metashape_executable": ""}, candidates=(), picker=lambda: str(picked)) == picked.resolve()
    assert plausible_metashape_executable(tmp_path / "other.exe") is None


def test_health_accepts_only_our_local_service(monkeypatch):
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, *args): return b'{"status":"ok","host":"127.0.0.1","mock_mode":true}'
    monkeypatch.setattr(start_app.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    assert start_app.health("http://127.0.0.1:8765/api/health")["mock_mode"] is True


def test_start_bat_and_docs_exist():
    text = (ROOT / "start.bat").read_text(encoding="utf-8")
    assert "scripts\\start_app.py" in text
    assert "%~dp0" in text
    assert (ROOT / "README.md").is_file()
    assert (ROOT / "docs" / "release-checklist.md").is_file()
    assert (ROOT / "AGENTS.md").is_file()
    assert (ROOT / ".agents" / "skills" / "drone-metashape-local-one-click" / "SKILL.md").is_file()
    assert not (ROOT / "skills" / "drone-metashape-local-one-click" / "SKILL.md").exists()
