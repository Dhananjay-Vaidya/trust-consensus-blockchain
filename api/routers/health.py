from __future__ import annotations

from fastapi import APIRouter

from api import simulation_runner as runner

router = APIRouter()


@router.get("/health")
async def health():
    active = len([r for r in runner._runs.values() if r["status"] == "running"])
    return {"status": "ok", "active_runs": active}
