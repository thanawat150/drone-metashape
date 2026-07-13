"""Windows-friendly bootstrap used by start.bat."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
VENV = APP_ROOT / ".venv"
REQUIREMENTS = APP_ROOT / "requirements.txt"
FINGERPRINT = VENV / ".requirements.sha256"
STARTUP_LOG = APP_ROOT / "logs" / "startup.log"


def venv_python() -> Path:
    return VENV / "Scripts" / "python.exe"


def requirements_fingerprint(path: Path = REQUIREMENTS) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependencies_available(python: Path) -> bool:
    result = subprocess.run(
        [str(python), "-c", "import fastapi, uvicorn; fastapi.FastAPI(docs_url=None, redoc_url=None)"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False,
    )
    return result.returncode == 0


def ensure_environment() -> Path:
    if sys.version_info < (3, 11) or sys.version_info >= (3, 14):
        raise RuntimeError("เธฃเธญเธเธฃเธฑเธ Python 3.11โ€“3.13 เน€เธ—เนเธฒเธเธฑเนเธ")
    current_python = Path(sys.executable)
    if dependencies_available(current_python):
        return current_python
    python = venv_python()
    if not python.is_file():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True, shell=False)
    current = requirements_fingerprint()
    installed = FINGERPRINT.read_text(encoding="ascii").strip() if FINGERPRINT.is_file() else ""
    if installed != current or not dependencies_available(python):
        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REQUIREMENTS)],
            cwd=APP_ROOT, check=True, shell=False,
        )
        FINGERPRINT.write_text(current + "\n", encoding="ascii")
    return python


def health(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=0.75) as response:
            payload = json.load(response)
        if payload.get("status") == "ok" and payload.get("host") == "127.0.0.1":
            return payload
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return None


def wait_for_health(url: str, process: subprocess.Popen, timeout: float = 30) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if payload := health(url):
            return payload
        if process.poll() is not None:
            raise RuntimeError(f"backend stopped with exit code {process.returncode}")
        time.sleep(0.2)
    raise RuntimeError("backend was not ready before timeout")


def configure_engine_if_needed(mock_mode: bool) -> None:
    if mock_mode:
        return
    sys.path.insert(0, str(APP_ROOT))
    from metashape_pipeline.configuration import load_merged_config
    config = load_merged_config(APP_ROOT)
    if config.get("engine", "odm") == "odm":
        executable = str(config.get("odm_executable") or "docker")
        if shutil.which(executable) is None and not Path(executable).is_file():
            print("Warning: Docker/ODM engine was not found. The UI can open, but real processing needs Docker Desktop.")
        return
    from metashape_pipeline.configuration import discover_metashape, pick_metashape_executable, save_local_config
    executable = discover_metashape(config, picker=pick_metashape_executable)
    if not executable:
        raise RuntimeError("เนเธกเนเธเธ Agisoft Metashape executable เธซเธฃเธทเธญเนเธเธฅเนเธ—เธตเนเน€เธฅเธทเธญเธเนเธกเนเธ–เธนเธเธ•เนเธญเธ")
    if config.get("metashape_executable") != str(executable):
        config["metashape_executable"] = str(executable)
        save_local_config(APP_ROOT, config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock-metashape", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    STARTUP_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        python = ensure_environment()
        configure_engine_if_needed(args.mock_metashape)
        sys.path.insert(0, str(APP_ROOT))
        from metashape_pipeline.configuration import load_merged_config
        config = load_merged_config(APP_ROOT)
        base_url = f"http://127.0.0.1:{config['port']}"
        health_url = base_url + "/api/health"
        if existing := health(health_url):
            print("App is already running; opening the existing window.")
            if not args.no_browser:
                webbrowser.open(base_url + "/")
            return 0
        command = [str(python), str(APP_ROOT / "app.py"), "--no-browser"]
        if args.mock_metashape:
            command.append("--mock-metashape")
        with STARTUP_LOG.open("a", encoding="utf-8") as log:
            process = subprocess.Popen(
                command, cwd=APP_ROOT, stdout=log, stderr=subprocess.STDOUT,
                shell=False, close_fds=True,
            )
            wait_for_health(health_url, process)
            print(f"Ready: {base_url}/")
            if not args.no_browser:
                webbrowser.open(base_url + "/")
            return process.wait()
    except Exception as exc:
        message = f"Startup failed: {type(exc).__name__}: {exc}\nSee log: {STARTUP_LOG}"
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

