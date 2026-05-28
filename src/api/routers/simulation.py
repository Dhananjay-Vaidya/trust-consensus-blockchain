from __future__ import annotations

import asyncio
import glob
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from src.api import simulation_runner as runner
from src.api.models import SimulationStartRequest, SimulationStartResponse, SimulationStatusResponse, StepEventPayload

router = APIRouter(prefix="/simulation", tags=["simulation"])
RESULTS_DIR = Path("experiments/results")


@router.post(
    "/start",
    response_model=SimulationStartResponse,
    summary="Start a simulation run",
    description="Start a new simulation asynchronously and return the run id and metadata required to open a live event stream.",
)
async def start_simulation(cfg: SimulationStartRequest):
    """Create a background simulation run and return its identifier."""
    try:
        run_id, _ = await runner.start_simulation(cfg)
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    metadata = runner.get_metadata(run_id)
    return SimulationStartResponse(run_id=run_id, status="running", metadata=metadata)


@router.get(
    "/{run_id}/status",
    response_model=SimulationStatusResponse,
    summary="Get current run status",
    description="Return the current status snapshot for a live or completed simulation run.",
)
async def get_status(run_id: str):
    """Fetch the latest known status for a run."""
    status = runner.get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return status


@router.post(
    "/{run_id}/stop",
    summary="Stop a running simulation",
    description="Signal a running simulation to stop at the next safe interruption point.",
)
async def stop_simulation(run_id: str):
    """Stop a running simulation."""
    if not runner.stop_simulation(run_id):
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "stopped": True}


@router.websocket("/{run_id}/stream")
async def stream_simulation(websocket: WebSocket, run_id: str):
    """Stream live per-step simulation events over a WebSocket connection."""
    await websocket.accept()

    state = runner._runs.get(run_id)
    if state is None:
        await websocket.send_json({"type": "error", "detail": "Run not found"})
        await websocket.close()
        return

    queue: asyncio.Queue = state.get("queue")
    if queue is None:
        await websocket.send_json({"type": "error", "detail": "No event queue for run"})
        await websocket.close()
        return

    try:
        while True:
            event = await queue.get()
            if event is None:
                await websocket.send_json({"type": "simulation_end", "run_id": run_id})
                break
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/{run_id}/replay")
async def replay_simulation(websocket: WebSocket, run_id: str, speed_multiplier: float = Query(10.0, ge=0.1, le=100.0)):
    """Replay a completed run by reading its saved JSONL event log and pushing events over WebSocket."""
    await websocket.accept()
    pattern = RESULTS_DIR / f"{run_id}_stream.jsonl"
    if not pattern.exists():
        matches = glob.glob(str(RESULTS_DIR / f"{run_id}*_stream.jsonl"))
        if not matches and "_seed" in run_id:
            matches = glob.glob(str(RESULTS_DIR / f"{run_id.rsplit('_seed', 1)[0]}*_stream.jsonl"))
        if not matches:
            await websocket.send_json({"type": "error", "detail": "Replay log not found"})
            await websocket.close()
            return
        pattern = Path(matches[0])

    try:
        with open(pattern, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        delay = max(0.001, 0.1 / speed_multiplier)
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            await websocket.send_json(json.loads(line))
            await asyncio.sleep(delay)
        await websocket.send_json({"type": "simulation_end", "run_id": run_id, "replay": True})
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
