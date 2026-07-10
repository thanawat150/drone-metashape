"""Stable internal script passed to Metashape's `-r` option."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from metashape_pipeline.launcher import metashape_main


if __name__ == "__main__":
    raise SystemExit(metashape_main(sys.argv[1:]))
