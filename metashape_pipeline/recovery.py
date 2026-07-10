"""Conservative resume decisions based on persisted state and adapter evidence."""

from __future__ import annotations

from typing import Any


STAGE_CAPABILITY = {
    "CREATE_PROJECT": "project",
    "ADD_PHOTOS": "photos",
    "ALIGN": "alignment",
    "DEPTH_MAPS": "depth_maps",
    "DEM": "dem",
    "ORTHOMOSAIC": "orthomosaic",
}


def resume_decision(state: dict[str, Any], capabilities: dict[str, bool]) -> dict[str, Any]:
    last = state.get("last_successful_stage")
    if not last:
        return {"safe": False, "resume_after": None, "reason": "no successful stage is recorded"}
    required = STAGE_CAPABILITY.get(last)
    if required and not capabilities.get(required, False):
        return {"safe": False, "resume_after": None, "reason": f"project evidence for {last} is missing"}
    if last in {"EXPORT", "VALIDATE_OUTPUT", "SAVE_PROJECT", "COMPLETE"}:
        return {"safe": False, "resume_after": None, "reason": "finished/output stages require fresh output validation"}
    return {"safe": True, "resume_after": last, "reason": "persisted state agrees with inspected project evidence"}
