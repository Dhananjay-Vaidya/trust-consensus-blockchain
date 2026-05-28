from __future__ import annotations

import asyncio
import threading
import time
import uuid
from typing import Any, Dict, Optional

from api.models import SimulationConfig, SimulationStatus

# Max concurrent simulations
MAX_CONCURRENT = 4

# Registry
_runs: Dict[str, Dict[str, Any]] = {}   # run_id → state dict
_threads: Dict[str, threading.Thread] = {}


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
        "stop_flag": threading.Event(),
        "queue": None,            # asyncio.Queue set by caller if needed
        "loop": None,             # event loop for the caller
        "error": None,
    }


def _run_simulation_thread(run_id: str, loop: asyncio.AbstractEventLoop,
                            queue: asyncio.Queue) -> None:
    """Worker thread: runs SimulationManager synchronously and pushes events."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    import random, numpy as np, torch
    import parameters as params
    from config.config_loader import load_config
    from simulation_manager import SimulationManager

    state = _runs[run_id]
    cfg: SimulationConfig = state["config"]
    stop: threading.Event = state["stop_flag"]

    # Seed
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    # Apply params
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
        sim_config = load_config("config/default.yaml", {
            "num_nodes": cfg.nodes,
            "episodes": cfg.episodes,
            "malicious_fraction": cfg.malicious_fraction,
            "steps_per_episode": cfg.steps_per_episode,
            "fhe_enabled": cfg.fhe_enabled,
        })
    except Exception:
        sim_config = None

    def _callback(event: Dict[str, Any]) -> None:
        if stop.is_set():
            return
        # Update run state
        state["episode"] = event.get("episode", 0)
        state["current_f1"] = event.get("f1_score", 0.0)
        state["current_reward"] = event.get("reward", 0.0)
        # Push to asyncio queue from thread
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

        # Override run to check stop flag between episodes
        original_run_episode = sim.run_episode

        def _patched_run_episode(ep: int):
            if stop.is_set():
                raise InterruptedError("Simulation stopped by user")
            return original_run_episode(ep)

        sim.run_episode = _patched_run_episode
        sim.run_simulation()
        state["status"] = "completed"
    except InterruptedError:
        state["status"] = "completed"
    except Exception as e:
        state["status"] = "error"
        state["error"] = str(e)
        asyncio.run_coroutine_threadsafe(
            queue.put({"type": "error", "run_id": run_id,
                       "episode": 0, "step": 0,
                       "trust_scores": {}, "is_malicious": {}, "is_detected": {},
                       "delegate_nodes": [], "transactions_verified": 0,
                       "transactions_rejected": 0, "byzantine_detections": 0,
                       "f1_score": 0.0, "precision": 0.0, "recall": 0.0,
                       "reward": 0.0, "blockchain_length": 0, "trust_separation": 0.0,
                       "action_taken": 0, "action_description": f"ERROR: {e}",
                       "fhe_overhead_ms": None, "timestamp": time.time()}),
            loop,
        )
    finally:
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # sentinel


async def start_simulation(cfg: SimulationConfig) -> tuple[str, asyncio.Queue]:
    """Create run, start background thread, return (run_id, queue)."""
    if len([r for r in _runs.values() if r["status"] == "running"]) >= MAX_CONCURRENT:
        raise RuntimeError(f"Maximum {MAX_CONCURRENT} concurrent simulations reached")

    run_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue(maxsize=0)
    loop = asyncio.get_event_loop()

    state = _make_run_state(run_id, cfg)
    state["queue"] = queue
    state["loop"] = loop
    _runs[run_id] = state

    t = threading.Thread(target=_run_simulation_thread,
                         args=(run_id, loop, queue), daemon=True)
    _threads[run_id] = t
    t.start()
    return run_id, queue


def stop_simulation(run_id: str) -> bool:
    state = _runs.get(run_id)
    if not state:
        return False
    state["stop_flag"].set()
    state["status"] = "completed"
    return True


def get_status(run_id: str) -> Optional[SimulationStatus]:
    state = _runs.get(run_id)
    if not state:
        return None
    elapsed = time.time() - (state["started_at"] or time.time())
    progress = (state["episode"] / max(1, state["total_episodes"])) * 100
    return SimulationStatus(
        run_id=run_id,
        status=state["status"],
        episode=state["episode"],
        total_episodes=state["total_episodes"],
        progress_pct=round(progress, 1),
        current_f1=state["current_f1"],
        current_reward=state["current_reward"],
        started_at=state["started_at"],
        elapsed_seconds=round(elapsed, 1),
    )


def list_runs() -> list:
    return [
        {
            "run_id": rid,
            "status": s["status"],
            "agent": s["config"].agent,
            "attack": s["config"].attack,
            "episodes": s["config"].episodes,
            "current_f1": s["current_f1"],
        }
        for rid, s in _runs.items()
    ]
