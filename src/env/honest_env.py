"""Oracle-free trust-consensus environment (Phase 2).

Per step:
  1. a controller (rule, RL agent, or fixed config) sets the knobs (A4: every knob is used);
  2. a committee of k delegates is selected from *observable* trust;
  3. the world generates T transactions and the committee's public votes (vote model, A2);
  4. the TDCB tally (plain or HE) decides commits;
  5. a random ``audit_rate`` fraction of the T transactions is independently re-verified;
     each committee member's vote on an audited tx is *inconsistent* if it disagrees with the
     audit. Only this evidence reaches the trust backend; un-audited tx produce no update (A1).

Nothing in this module reads which transactions are valid or which nodes are adversarial: those live in
:class:`src.env.world.World` and are consumed after the fact by ``src/metrics`` only.
"""
from __future__ import annotations

import itertools
import random
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, List, Optional, Sequence, Tuple

import numpy as np

from src.config.run_config import RunConfig
from src.consensus.tdcb import TDCB
from src.env.attacks import AdaptiveBriber, PublicView, make_attack
from src.env.world import World
from src.trust.trust import make_trust_backend

# ---------------------------------------------------------------------------------------------
#  Control knobs (factored discrete action space, 3^4 = 81 actions)
# ---------------------------------------------------------------------------------------------
KNOB_LEVELS = {
    "committee_frac": (0.5, 0.75, 1.0),
    "audit_rate": (0.1, 0.2, 0.4),
    "temperature": (0.05, 0.2, 1.0),
    "theta_margin": (0.0, 0.05, 0.1),
}
KNOB_NAMES: Tuple[str, ...] = tuple(KNOB_LEVELS)
ACTIONS: List[Tuple[int, ...]] = list(itertools.product(range(3), repeat=len(KNOB_NAMES)))
N_ACTIONS = len(ACTIONS)


@dataclass(frozen=True)
class Knobs:
    committee_frac: float = 1.0
    audit_rate: Optional[float] = None       # None -> RunConfig.audit_rate
    temperature: Optional[float] = None      # None -> RunConfig.selection_temperature
    theta_margin: float = 0.0

    @staticmethod
    def from_levels(levels: Sequence[int]) -> "Knobs":
        vals = {n: KNOB_LEVELS[n][i] for n, i in zip(KNOB_NAMES, levels)}
        return Knobs(**vals)

    @staticmethod
    def from_action(a: int) -> "Knobs":
        return Knobs.from_levels(ACTIONS[a])


# ---------------------------------------------------------------------------------------------
#  Public observation and per-step record
# ---------------------------------------------------------------------------------------------
OBS_DIM = 12


@dataclass
class Observation:
    """Everything a controller may see. Contains no ground truth."""

    step_frac: float
    audited_err_recent: float     # fraction of audited tx where the commit decision disagreed with the audit
    audited_err_last: float
    commit_rate_recent: float
    weight_mean: float
    weight_std: float
    weight_min: float
    frac_quarantined: float
    alarms_recent: float
    disagree_dispersion: float    # std over nodes of their recent audited disagreement rate
    knob_levels: Tuple[float, float, float, float] = (1.0, 0.2, 0.1, 0.0)

    def vector(self) -> np.ndarray:
        kl = self.knob_levels
        return np.array([
            self.step_frac, self.audited_err_recent, self.audited_err_last, self.commit_rate_recent,
            self.weight_mean, self.weight_std, self.weight_min, self.frac_quarantined,
            min(self.alarms_recent, 5.0) / 5.0, self.disagree_dispersion,
            kl[1] / 0.4, kl[3] / 0.1,
        ], dtype=np.float32)


@dataclass
class StepRecord:
    step: int
    committee_idx: np.ndarray
    weights: np.ndarray
    accept: np.ndarray
    audited: np.ndarray
    audited_err: float            # NaN if nothing audited
    n_audited: int
    aborted: bool
    alarms: List[int]
    flagged: np.ndarray           # (N,) bool: quarantined or trust < flag_threshold
    quarantined: np.ndarray       # (N,) bool
    trust: np.ndarray             # (N,) float
    latency_ms: float             # simulated (cost model, D7)
    wall_ms: float                # measured wall-clock of the step
    he_ms: float
    he_flips: int
    knobs: Knobs
    reward: float = 0.0


@dataclass
class RewardWeights:
    """Reward uses observable quantities only (A1)."""

    latency: float = 0.1
    audit_cost: float = 0.2


class HonestEnv:
    def __init__(self, cfg: RunConfig, reward_weights: RewardWeights | None = None,
                 briber: AdaptiveBriber | None = None) -> None:
        cfg.validate()
        self.cfg = cfg
        self.rw = reward_weights or RewardWeights()
        self.rng = np.random.default_rng([cfg.seed, 0])            # system randomness
        world_rng = np.random.default_rng([cfg.seed, 1])           # world randomness
        self.nodes = [f"Node_{i}" for i in range(cfg.num_nodes)]
        self.node_idx = {n: i for i, n in enumerate(self.nodes)}
        n_bad = 0 if cfg.attack == "none" else int(round(cfg.num_nodes * cfg.malicious_fraction))
        coalition = set(world_rng.choice(self.nodes, size=n_bad, replace=False).tolist()) if n_bad else set()
        self._world = World(self.nodes, coalition,
                            make_attack(cfg.attack, cfg.t_switch, cfg.attack_intensity, cfg.aaa_cooldown,
                                        cfg.attack_target),
                            cfg.invalid_tx_rate, cfg.honest_fault_rate, world_rng)
        self.trust = make_trust_backend(cfg.trust_backend, self.nodes, cfg.sleeper_guard,
                                        random.Random(cfg.seed * 7919 + 17), cfg.cap_method)
        self.tdcb = TDCB(cfg.theta, cfg.tally_backend, cfg.he_sign_iters)
        self.fixed_committee = np.sort(self.rng.choice(cfg.num_nodes, size=cfg.k, replace=False))
        self.briber = briber
        self.t = 0
        self.records: List[StepRecord] = []
        self.knobs = Knobs()
        self._err_hist: Deque[float] = deque(maxlen=20)
        self._commit_hist: Deque[float] = deque(maxlen=20)
        self._alarm_hist: Deque[int] = deque(maxlen=20)
        self._dis_num = np.zeros(cfg.num_nodes)
        self._dis_den = np.zeros(cfg.num_nodes)
        self.on_step: Optional[Callable[[StepRecord], None]] = None

    # -----------------------------------------------------------------------------------------
    @property
    def done(self) -> bool:
        return self.t >= self.cfg.steps

    def _effective(self, kn: Knobs) -> Tuple[int, float, float, float]:
        c = self.cfg
        k = int(np.clip(round(c.k * kn.committee_frac), 1, c.num_nodes))
        if c.selection == "all":
            k = c.num_nodes
        audit = c.audit_rate if kn.audit_rate is None else kn.audit_rate
        temp = c.selection_temperature if kn.temperature is None else kn.temperature
        theta = float(np.clip(c.theta + kn.theta_margin, 0.05, 0.99))
        return k, audit, temp, theta

    def _select(self, k: int, temp: float) -> np.ndarray:
        c, n = self.cfg, self.cfg.num_nodes
        if c.selection == "all" or k >= n:
            return np.arange(n)
        if c.selection == "fixed":
            return self.fixed_committee[:k]
        if c.selection == "random":
            return np.sort(self.rng.choice(n, size=k, replace=False))
        tr = np.array([self.trust.trust(x) for x in self.nodes])
        z = (tr - tr.max()) / max(temp, 1e-6)
        p = np.exp(z)
        p /= p.sum()
        return np.sort(self.rng.choice(n, size=k, replace=False, p=p))

    # -----------------------------------------------------------------------------------------
    def observation(self) -> Observation:
        last = self.records[-1] if self.records else None
        w = last.weights / max(last.weights.max(), 1e-12) if last is not None and last.weights.size else np.ones(1)
        rate = np.divide(self._dis_num, self._dis_den, out=np.zeros_like(self._dis_num), where=self._dis_den > 0)
        kn = self.knobs
        _, audit, temp, _ = self._effective(kn)
        return Observation(
            step_frac=self.t / max(1, self.cfg.steps),
            audited_err_recent=float(np.mean(self._err_hist)) if self._err_hist else 0.0,
            audited_err_last=self._err_hist[-1] if self._err_hist else 0.0,
            commit_rate_recent=float(np.mean(self._commit_hist)) if self._commit_hist else 0.0,
            weight_mean=float(w.mean()), weight_std=float(w.std()), weight_min=float(w.min()),
            frac_quarantined=float(last.quarantined.mean()) if last is not None else 0.0,
            alarms_recent=float(sum(self._alarm_hist)),
            disagree_dispersion=float(rate.std()),
            knob_levels=(kn.committee_frac, audit, temp, kn.theta_margin),
        )

    # -----------------------------------------------------------------------------------------
    def step(self, knobs: Optional[Knobs] = None) -> StepRecord:
        if self.done:
            raise RuntimeError("episode finished; create a new HonestEnv (A8)")
        t0 = time.perf_counter()
        c = self.cfg
        if knobs is not None:
            self.knobs = knobs
        k, audit_rate, temp, theta = self._effective(self.knobs)

        if self.briber is not None and self.t == self.briber.t_bribe:
            candidates = [n for n in self.nodes if n not in self._world.coalition]
            self._world.corrupt(self.briber.choose(candidates, self.rng), self.t)

        cidx = self._select(k, temp)
        committee = [self.nodes[i] for i in cidx]
        t_count = self._world.new_transactions(c.tx_per_step)
        votes = self._world.cast_votes(self.t, committee)

        if c.weighted:
            w = self.trust.weights(committee)
        else:
            w = np.ones(len(committee))
        capped = c.weighted and c.trust_backend == "sleeper_guard" and c.sleeper_guard.use_share_cap
        max_share = c.sleeper_guard.cap_factor / len(committee) if capped else None
        out = self.tdcb.tally(w, votes, theta, max_share)

        audited = self.rng.random(t_count) < audit_rate
        outcome = self._world.audit(audited)
        a_idx = np.flatnonzero(audited)
        alarms: List[int] = []
        for j, node in enumerate(committee):
            gi = cidx[j]
            for ti in a_idx:
                inc = bool(votes[ti, j] != float(outcome[ti]))
                self._dis_num[gi] = 0.98 * self._dis_num[gi] + inc
                self._dis_den[gi] = 0.98 * self._dis_den[gi] + 1.0
                if self.trust.observe(node, inc):
                    alarms.append(int(gi))
        self.trust.end_step(self.t)

        n_aud = int(audited.sum())
        err = float((out.accept[audited] != outcome[audited]).mean()) if n_aud else float("nan")
        if n_aud:
            self._err_hist.append(err)
        self._commit_hist.append(float(out.accept.mean()))
        self._alarm_hist.append(len(alarms))

        trust_now = np.array([self.trust.trust(n) for n in self.nodes])
        quar = np.array([self.trust.is_quarantined(n) for n in self.nodes])
        flagged = quar | (trust_now < c.flag_threshold)
        latency = (c.latency_base_ms + c.latency_per_msg_ms * len(committee) ** 2
                   + c.latency_per_audit_ms * n_aud + out.he_ms)

        view = PublicView(self.t, committee, votes, out.accept, audited, outcome,
                          weights=(w.copy() if c.tally_backend == "plain" else None))
        self._world.publish(view)
        if self.briber is not None:
            self.briber.observe(view)

        # reward: audited agreement - latency cost - audit cost (all observable)
        agree = 1.0 - (err if n_aud else (self._err_hist[-1] if self._err_hist else 0.0))
        lat_norm = (c.latency_per_msg_ms * len(committee) ** 2) / max(1e-9, c.latency_per_msg_ms * c.num_nodes ** 2)
        reward = agree - self.rw.latency * lat_norm - self.rw.audit_cost * audit_rate

        rec = StepRecord(self.t, cidx, w, out.accept, audited, err, n_aud, out.aborted, alarms,
                         flagged, quar, trust_now, latency, (time.perf_counter() - t0) * 1e3,
                         out.he_ms, out.he_flips, self.knobs, reward)
        self.records.append(rec)
        self.t += 1
        if self.on_step is not None:
            self.on_step(rec)
        return rec

    def run(self, controller: Optional[Callable[["HonestEnv"], Optional[Knobs]]] = None) -> "HonestEnv":
        while not self.done:
            self.step(controller(self) if controller is not None else None)
        return self
