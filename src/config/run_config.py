"""Immutable run configuration (fixes audit finding A9).

Every simulation takes a ``RunConfig`` explicitly. There is no module-level mutable state;
two runs with the same ``RunConfig`` (including ``seed``) produce bit-identical outputs.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Mapping

import yaml

from src.trust.sleeper_guard import SleeperGuardConfig

AttackName = Literal["none", "nma", "cra", "aaa", "bfi", "tdp", "mda"]
TrustBackend = Literal["sleeper_guard", "legacy_beta", "none"]
TallyBackend = Literal["plain", "he"]
Selection = Literal["trust_softmax", "random", "fixed", "all"]

ATTACKS = ("none", "nma", "cra", "aaa", "bfi", "tdp", "mda")


@dataclass(frozen=True)
class RunConfig:
    # ---- identity -------------------------------------------------------------------------
    seed: int = 0

    # ---- network --------------------------------------------------------------------------
    num_nodes: int = 16
    malicious_fraction: float = 0.3125      # 5 of 16 nodes; matches the 5-of-16 toy check
    committee_size: int = 16                # k; clipped to num_nodes
    steps: int = 600
    tx_per_step: int = 16                   # T transactions decided per step (one HE batch)
    invalid_tx_rate: float = 0.3            # fraction of submitted transactions that are invalid

    # ---- vote model (Phase 2) -------------------------------------------------------------
    honest_fault_rate: float = 0.05         # honest delegate misreads validity with this prob.

    # ---- audit evidence -------------------------------------------------------------------
    audit_rate: float = 0.2                 # fraction of decided transactions re-verified

    # ---- consensus ------------------------------------------------------------------------
    theta: float = 0.667                    # commit threshold on weighted approval share
    weighted: bool = True                   # False => one-delegate-one-vote (PBFT/DPoS/majority)
    tally_backend: TallyBackend = "plain"
    he_sign_iters: int = 3

    # ---- delegate selection ---------------------------------------------------------------
    selection: Selection = "trust_softmax"
    selection_temperature: float = 0.1

    # ---- trust ----------------------------------------------------------------------------
    trust_backend: TrustBackend = "sleeper_guard"
    sleeper_guard: SleeperGuardConfig = field(default_factory=SleeperGuardConfig)
    cap_method: Literal["exact", "verified_iterative"] = "exact"   # see src/trust/capping.py
    flag_threshold: float = 0.5             # node is *flagged* if trust < this (or quarantined)

    # ---- attack ---------------------------------------------------------------------------
    attack: AttackName = "tdp"
    t_switch: int = 300                     # TDP: sleepers turn malicious at this step
    attack_intensity: float = 1.0           # prob. a malicious delegate deviates when active
    aaa_cooldown: int = 25                  # AAA: dormant steps after observing an audit hit
    attack_target: Literal["invalid", "both"] = "invalid"   # MDA: what the coalition lies about

    # ---- simulated cost model (see docs/DECISIONS.md D7) ----------------------------------
    latency_base_ms: float = 5.0
    latency_per_msg_ms: float = 0.05        # PBFT-style O(k^2) message cost
    latency_per_audit_ms: float = 2.0

    # ------------------------------------------------------------------------------------
    def with_overrides(self, **kw: Any) -> "RunConfig":
        sg = kw.pop("sleeper_guard", None)
        sg_over = {k[3:]: kw.pop(k) for k in list(kw) if k.startswith("sg_")}
        cfg = dataclasses.replace(self, **kw)
        if sg is not None:
            cfg = dataclasses.replace(cfg, sleeper_guard=sg)
        if sg_over:
            cfg = dataclasses.replace(cfg, sleeper_guard=dataclasses.replace(cfg.sleeper_guard, **sg_over))
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if not 0.0 <= self.malicious_fraction < 1.0:
            raise ValueError("malicious_fraction must be in [0, 1)")
        if not 0.0 < self.theta <= 1.0:
            raise ValueError("theta must be in (0, 1]")
        if not 0.0 <= self.audit_rate <= 1.0:
            raise ValueError("audit_rate must be in [0, 1]")
        if self.attack not in ATTACKS:
            raise ValueError(f"unknown attack {self.attack!r}")
        if self.committee_size < 1:
            raise ValueError("committee_size must be >= 1")

    @property
    def k(self) -> int:
        return min(self.committee_size, self.num_nodes)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "RunConfig":
        d = dict(d)
        sg = d.pop("sleeper_guard", None)
        cfg = RunConfig(**d)
        if sg is not None:
            cfg = dataclasses.replace(cfg, sleeper_guard=SleeperGuardConfig(**sg))
        cfg.validate()
        return cfg


def load_yaml(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def config_from_yaml(path: str | Path, base: RunConfig | None = None) -> RunConfig:
    """Load the ``base:`` section of an experiment YAML onto a RunConfig."""
    raw = load_yaml(path)
    return (base or RunConfig()).with_overrides(**raw.get("base", {}))
