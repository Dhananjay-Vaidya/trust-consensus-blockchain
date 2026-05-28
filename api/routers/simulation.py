from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from api.models import SimulationConfig, SimulationStatus
from api import simulation_runner as runner

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/start")
async def start_simulation(cfg: SimulationConfig):
    try:
        run_id, _ = await runner.start_simulation(cfg)
        return {"run_id": run_id, "status": "running"}
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/{run_id}/status", response_model=SimulationStatus)
async def get_status(run_id: str):
    status = runner.get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return status


@router.post("/{run_id}/stop")
async def stop_simulation(run_id: str):
    ok = runner.stop_simulation(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"stopped": True}


@router.websocket("/{run_id}/stream")
async def stream_simulation(websocket: WebSocket, run_id: str):
    """Live stream of StepEvent dicts over WebSocket."""
    await websocket.accept()

    state = runner._runs.get(run_id)
    if state is None:
        await websocket.send_json({"type": "error", "detail": "Run not found"})
        await websocket.close()
        return

    queue: asyncio.Queue = state.get("queue")
    if queue is None:
        await websocket.send_json({"type": "error", "detail": "No queue for run"})
        await websocket.close()
        return

    try:
        while True:
            event = await queue.get()
            if event is None:   # sentinel — simulation finished
                break
            try:
                await websocket.send_json(event)
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/{run_id}/replay")
async def replay_simulation(run_id: str, speed_multiplier: float = 10.0):
    """
    Replay a completed simulation by streaming its JSONL file.
    Returns a Server-Sent Events stream.
    """
    import os
    from pathlib import Path

    # Find the JSONL file
    pattern = f"results/{run_id}_stream.jsonl"
    if not os.path.exists(pattern):
        # Try partial match by run_id prefix
        import glob
        matches = glob.glob(f"results/*{run_id[:8]}*_stream.jsonl")
        if not matches:
            raise HTTPException(status_code=404, detail="JSONL stream not found")
        pattern = matches[0]

    async def _event_generator():
        with open(pattern, "r", encoding="utf-8") as f:
            lines = f.readlines()
        delay = max(0.001, 0.1 / speed_multiplier)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            yield f"data: {line}\n\n"
            await asyncio.sleep(delay)
        yield "data: {\"type\": \"replay_end\"}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")
