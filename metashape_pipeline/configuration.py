"""Machine-local configuration and Metashape executable discovery."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from .state_manager import atomic_write_json


COMMON_METASHAPE_PATHS = (
    Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Agisoft" / "Metashape Pro" / "metashape.exe",
    Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Agisoft" / "Metashape" / "metashape.exe",
    Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Agisoft" / "Metashape Pro" / "metashape.exe",
)


def plausible_metashape_executable(value: str | Path) -> Path | None:
    try:
        path = Path(value).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return None
    if path.is_file() and path.suffix.lower() == ".exe" and "metashape" in path.name.lower():
        return path
    return None


def load_merged_config(app_root: str | Path) -> dict:
    root = Path(app_root)
    with (root / "config.example.json").open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    local = root / "config.local.json"
    if local.is_file():
        with local.open("r", encoding="utf-8") as handle:
            overrides = json.load(handle)
        allowed = set(config)
        unknown = set(overrides) - allowed
        if unknown:
            raise ValueError(f"unknown local config fields: {', '.join(sorted(unknown))}")
        config.update(overrides)
    if config.get("host") != "127.0.0.1":
        raise ValueError("host must remain 127.0.0.1")
    port = config.get("port")
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("port must be an integer from 1024 to 65535")
    return config


def pick_metashape_executable() -> str | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askopenfilename(
            title="เลือกไฟล์ Agisoft Metashape",
            filetypes=[("Metashape", "metashape.exe"), ("Executable", "*.exe")],
        )
        return selected or None
    finally:
        root.destroy()


def discover_metashape(
    config: dict, *, candidates: tuple[Path, ...] = COMMON_METASHAPE_PATHS,
    picker: Callable[[], str | None] | None = None,
) -> Path | None:
    configured = config.get("metashape_executable")
    if configured and (found := plausible_metashape_executable(configured)):
        return found
    for candidate in candidates:
        if found := plausible_metashape_executable(candidate):
            return found
    if picker:
        selected = picker()
        if selected:
            return plausible_metashape_executable(selected)
    return None


def save_local_config(app_root: str | Path, config: dict) -> None:
    root = Path(app_root)
    allowed = set(load_merged_config(root))
    clean = {key: value for key, value in config.items() if key in allowed}
    atomic_write_json(root / "config.local.json", clean)
