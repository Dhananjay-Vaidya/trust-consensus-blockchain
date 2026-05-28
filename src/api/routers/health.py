from __future__ import annotations

from fastapi import APIRouter

from src.api import simulation_runner as runner

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health probe",
    description="Return service health and the number of currently active simulation runs.",
)
async def health():
    """Simple health endpoint used by local development, tests, and deployments."""
    active = len([r for r in runner._runs.values() if r["status"] == "running"])
    return {"status": "ok", "active_runs": active}
