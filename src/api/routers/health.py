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
    from pathlib import Path
    active_states = [r for r in runner._runs.values() if r["status"] == "running"]
    active = len(active_states)
    results_dir = Path("experiments/results")
    results_count = len(list(results_dir.glob("*_episode_metrics.csv"))) if results_dir.exists() else 0
    run_details = [
        {
            "run_id": s["run_id"],
            "episode": s["episode"],
            "total_episodes": s["total_episodes"],
            "agent": s["config"].agent,
            "attack": s["config"].attack,
        }
        for s in active_states
    ]
    return {
        "status": "ok",
        "active_runs": active,
        "run_details": run_details,
        "results_count": results_count,
        "api_version": "2.0.0",
    }
