from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Dict, Optional

from src.api.models import RunMetadata, SimulationConfig, SimulationStatusResponse

MAX_CONCURRENT = 4

_runs: Dict[str, Dict[str, Any]] = {}
_threads: Dict[str, threading.Thread] = {}


def _build_run_id(cfg: SimulationConfig) -> str:
    malicious_pct = int(cfg.malicious_fraction * 100)
    return f"{cfg.nodes}_{cfg.episodes}_{cfg.agent}_{cfg.attack}_{malicious_pct}_seed{cfg.seed}"


def _make_run_state(run_id: str, cfg: SimulationConfig) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "config": cfg,
        "status": "running",
        "episode": 0,
        "total_episodes": cfg.episodes,
        "current_f1": 0.0,
        "current_reward": 0.0,
        "started_at": time.time(),
        "completed_at": None,
        "stop_flag": threading.Event(),
        "queue": None,
        "loop": None,
        "error": None,
    }


def _run_simulation_thread(run_id: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue) -> None:
    """Run the simulation synchronously in a worker thread and forward events to an async queue."""
    import random

    import numpy as np
    import torch

    import parameters as params
    from config.config_loader import load_config
    from src.simulation.simulation_manager import SimulationManager

    state = _runs[run_id]
    cfg: SimulationConfig = state["config"]
    stop: threading.Event = state["stop_flag"]

    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    params.TOTAL_NODES = cfg.nodes
    params.EPISODES = cfg.episodes
    params.STEPS_PER_EPISODE = cfg.steps_per_episode
    params.MALICIOUS_RATIO = cfg.malicious_fraction
    params.FHE_ENABLED = cfg.fhe_enabled
    params.FHE_OVERHEAD_LOG = []
    params.NO_ABAC = False
    params.NO_DECAY = False
    params.DELEGATE_STRATEGY = "thompson"
    params.ACTION_DIMS = 3

    try:
        sim_config = load_config(
            "config/default.yaml",
            {
                "num_nodes": cfg.nodes,
                "episodes": cfg.episodes,
                "malicious_fraction": cfg.malicious_fraction,
                "steps_per_episode": cfg.steps_per_episode,
                "fhe_enabled": cfg.fhe_enabled,
            },
        )
    except Exception:
        sim_config = None

    def _callback(event: Dict[str, Any]) -> None:
        if stop.is_set():
            return
        state["episode"] = event.get("episode", 0)
        state["current_f1"] = event.get("f1_score", 0.0)
        state["current_reward"] = event.get("reward", 0.0)
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    try:
        sim = SimulationManager(
            episodes=cfg.episodes,
            agent_type=cfg.agent,
            attack_mode=cfg.attack,
            config=sim_config,
            seed=cfg.seed,
            consensus_type=cfg.consensus,
            step_callback=_callback,
        )

        original_run_episode = sim.run_episode

        def _patched_run_episode(ep: int):
            if stop.is_set():
                raise InterruptedError("Simulation stopped by user")
            return original_run_episode(ep)

        sim.run_episode = _patched_run_episode
        sim.run_simulation()
        state["status"] = "completed"
    except InterruptedError as exc:
        state["status"] = "stopped"
        state["error"] = str(exc)
    except Exception as exc:
        state["status"] = "error"
        state["error"] = str(exc)
        asyncio.run_coroutine_threadsafe(
            queue.put(
                {
                    "type": "error",
                    "run_id": run_id,
                    "episode": 0,
                    "step": 0,
                    "trust_scores": {},
                    "is_malicious": {},
                    "is_detected": {},
                    "delegate_nodes": [],
                    "transactions_verified": 0,
                    "transactions_rejected": 0,
                    "byzantine_detections": 0,
                    "f1_score": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "reward": 0.0,
                    "blockchain_length": 0,
                    "trust_separation": 0.0,
                    "action_taken": 0,
                    "action_description": f"ERROR: {exc}",
                    "fhe_overhead_ms": None,
                    "timestamp": time.time(),
                }
            ),
            loop,
        )
    finally:
        state["completed_at"] = time.time()
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)


async def start_simulation(cfg: SimulationConfig) -> tuple[str, asyncio.Queue]:
    """Start a simulation asynchronously and return its run id and event queue."""
    if len([r for r in _runs.values() if r["status"] == "running"]) >= MAX_CONCURRENT:
        raise RuntimeError(f"Maximum {MAX_CONCURRENT} concurrent simulations reached")

    run_id = _build_run_id(cfg)
    if run_id in _runs and _runs[run_id]["status"] == "running":
        raise RuntimeError(f"Run {run_id} is already active")
    queue: asyncio.Queue = asyncio.Queue(maxsize=0)
    loop = asyncio.get_event_loop()

    state = _make_run_state(run_id, cfg)
    state["queue"] = queue
    state["loop"] = loop
    _runs[run_id] = state

    thread = threading.Thread(target=_run_simulation_thread, args=(run_id, loop, queue), daemon=True)
    _threads[run_id] = thread
    thread.start()
    return run_id, queue


def stop_simulation(run_id: str) -> bool:
    """Signal a running simulation to stop."""
    state = _runs.get(run_id)
    if not state:
        return False
    state["stop_flag"].set()
    return True


def get_status(run_id: str) -> Optional[SimulationStatusResponse]:
    """Return the current status snapshot for a run."""
    state = _runs.get(run_id)
    if not state:
        return None
    elapsed = time.time() - (state["started_at"] or time.time())
    progress = ((state["episode"] + 1) / max(1, state["total_episodes"])) * 100
    return SimulationStatusResponse(
        run_id=run_id,
        status=state["status"],
        episode=state["episode"],
        total_episodes=state["total_episodes"],
        progress_pct=round(min(progress, 100.0), 1),
        current_f1=state["current_f1"],
        current_reward=state["current_reward"],
        started_at=state["started_at"],
        elapsed_seconds=round(elapsed, 1),
        error=state["error"],
    )


def get_metadata(run_id: str) -> Optional[RunMetadata]:
    """Return stable metadata for a run."""
    state = _runs.get(run_id)
    if not state:
        return None
    cfg: SimulationConfig = state["config"]
    return RunMetadata(
        run_id=run_id,
        agent=cfg.agent,
        attack=cfg.attack,
        consensus=cfg.consensus,
        nodes=cfg.nodes,
        episodes=cfg.episodes,
        steps_per_episode=cfg.steps_per_episode,
        malicious_fraction=cfg.malicious_fraction,
        started_at=state["started_at"],
        completed_at=state["completed_at"],
        status=state["status"],
    )


def list_runs() -> list[RunMetadata]:
    """List all runs known to the live runner registry."""
    rows: list[RunMetadata] = []
    for run_id in _runs:
        metadata = get_metadata(run_id)
        if metadata is not None:
            rows.append(metadata)
    return rows
