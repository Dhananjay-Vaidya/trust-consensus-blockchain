from __future__ import annotations

import argparse
import logging
import random
import sys

import numpy as np
import torch

import parameters as params
from config.config_loader import _flatten, load_config
from src.simulation.simulation_manager import SimulationManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def main() -> None:
    arg_list = []
    for arg in sys.argv[1:]:
        if "=" in arg and not arg.startswith("--"):
            key, value = arg.split("=", 1)
            arg_list.extend([f"--{key}", value])
        else:
            arg_list.append(arg)

    parser = argparse.ArgumentParser(description="Blockchain IoT Trust Simulation")
    parser.add_argument("--nodes", type=int, default=params.TOTAL_NODES)
    parser.add_argument("--episodes", type=int, default=params.EPISODES)
    parser.add_argument("--steps", type=int, default=params.STEPS_PER_EPISODE)
    parser.add_argument("--agent", type=str, default="drl", choices=["rl", "drl", "marl"])
    parser.add_argument("--attack", type=str, default="none", choices=["none", "nma", "cra", "bfi", "aaa", "tdp"])
    parser.add_argument("--malicious", type=float, default=params.MALICIOUS_RATIO)
    parser.add_argument("--consensus", type=str, default="tdcb", choices=["tdcb", "pbft", "static_dpos", "majority", "random"])
    parser.add_argument("--fhe", action="store_true", default=False)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING"])
    parser.add_argument("--no-abac", action="store_true", default=False)
    parser.add_argument("--no-decay", action="store_true", default=False)
    parser.add_argument("--delegate-strategy", type=str, default="thompson", choices=["thompson", "ucb"])
    parser.add_argument("--action-dims", type=int, default=3, choices=[1, 3])
    parser.add_argument("--scenario", type=str, default=None)

    args = parser.parse_args(arg_list)

    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)
    logger.setLevel(numeric_level)
    set_global_seed(args.seed)

    params.TOTAL_NODES = args.nodes
    params.EPISODES = args.episodes
    params.MALICIOUS_RATIO = args.malicious
    params.STEPS_PER_EPISODE = args.steps
    params.FHE_ENABLED = args.fhe
    params.FHE_OVERHEAD_LOG = []
    params.NO_ABAC = args.no_abac
    params.NO_DECAY = args.no_decay
    params.DELEGATE_STRATEGY = args.delegate_strategy
    params.ACTION_DIMS = args.action_dims

    try:
        cli_overrides = {
            "num_nodes": args.nodes,
            "episodes": args.episodes,
            "malicious_fraction": args.malicious,
            "steps_per_episode": args.steps,
            "fhe_enabled": args.fhe,
        }
        sim_config = load_config("config/default.yaml", cli_overrides)
        attack_override = args.attack
        if args.scenario:
            import yaml
            with open(args.scenario, "r", encoding="utf-8") as f:
                scenario_raw = yaml.safe_load(f)
            scenario_flat = _flatten(scenario_raw)
            for key, value in scenario_flat.items():
                if hasattr(sim_config, key) and not isinstance(value, dict):
                    setattr(sim_config, key, value)
            if "num_nodes" in scenario_flat:
                params.TOTAL_NODES = scenario_flat["num_nodes"]
            if "malicious_fraction" in scenario_flat:
                params.MALICIOUS_RATIO = scenario_flat["malicious_fraction"]
            if "episodes" in scenario_flat:
                params.EPISODES = scenario_flat["episodes"]
            if "steps_per_episode" in scenario_flat:
                params.STEPS_PER_EPISODE = scenario_flat["steps_per_episode"]
            if "primary" in scenario_flat and args.attack == "none":
                attack_override = scenario_flat["primary"]
    except Exception as exc:
        logger.warning(f"Could not load YAML config ({exc}), using parameters.py only")
        sim_config = None
        attack_override = args.attack

    simulator = SimulationManager(
        episodes=params.EPISODES,
        agent_type=args.agent,
        attack_mode=attack_override,
        config=sim_config,
        seed=args.seed,
        consensus_type=args.consensus,
    )
    simulator.run_simulation()


if __name__ == "__main__":
    main()
