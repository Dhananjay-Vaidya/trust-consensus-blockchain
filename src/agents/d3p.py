"""D3P controller: dueling double DQN with prioritized replay and noisy linear layers.

Acts on the 81-action factored knob space (3 levels x 4 knobs).  ``freeze()`` switches to the
deterministic greedy policy with the noise turned off (mean weights) for evaluation (A8).
"""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.agents.protocol import Controller
from src.env.honest_env import ACTIONS, KNOB_LEVELS, KNOB_NAMES, N_ACTIONS, OBS_DIM, Knobs, Observation


class NoisyLinear(nn.Module):
    def __init__(self, n_in: int, n_out: int, sigma0: float = 0.5) -> None:
        super().__init__()
        self.n_in, self.n_out = n_in, n_out
        self.mu_w = nn.Parameter(torch.empty(n_out, n_in))
        self.sig_w = nn.Parameter(torch.empty(n_out, n_in))
        self.mu_b = nn.Parameter(torch.empty(n_out))
        self.sig_b = nn.Parameter(torch.empty(n_out))
        self.register_buffer("eps_w", torch.zeros(n_out, n_in))
        self.register_buffer("eps_b", torch.zeros(n_out))
        bound = 1.0 / math.sqrt(n_in)
        nn.init.uniform_(self.mu_w, -bound, bound)
        nn.init.uniform_(self.mu_b, -bound, bound)
        nn.init.constant_(self.sig_w, sigma0 / math.sqrt(n_in))
        nn.init.constant_(self.sig_b, sigma0 / math.sqrt(n_out))
        self.noisy = True

    @staticmethod
    def _f(x: torch.Tensor) -> torch.Tensor:
        return x.sign() * x.abs().sqrt()

    def reset_noise(self, gen: torch.Generator) -> None:
        ei = self._f(torch.randn(self.n_in, generator=gen))
        eo = self._f(torch.randn(self.n_out, generator=gen))
        self.eps_w.copy_(torch.outer(eo, ei))
        self.eps_b.copy_(eo)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.noisy:
            return F.linear(x, self.mu_w + self.sig_w * self.eps_w, self.mu_b + self.sig_b * self.eps_b)
        return F.linear(x, self.mu_w, self.mu_b)


class DuelingNet(nn.Module):
    def __init__(self, n_in: int, n_act: int, hidden: int = 64) -> None:
        super().__init__()
        self.body = nn.Sequential(nn.Linear(n_in, hidden), nn.ReLU(), nn.Linear(hidden, hidden), nn.ReLU())
        self.v = NoisyLinear(hidden, 1)
        self.a = NoisyLinear(hidden, n_act)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.body(x)
        a = self.a(h)
        return self.v(h) + a - a.mean(dim=1, keepdim=True)

    def noisy_layers(self) -> List[NoisyLinear]:
        return [self.v, self.a]


class PER:
    """Proportional prioritized replay (array-based; buffers here are small)."""

    def __init__(self, cap: int, alpha: float = 0.6) -> None:
        self.cap, self.alpha = cap, alpha
        self.data: List[Tuple[np.ndarray, int, float, np.ndarray, float]] = []
        self.prio = np.zeros(cap)
        self.pos = 0

    def add(self, item: Tuple[np.ndarray, int, float, np.ndarray, float]) -> None:
        p = self.prio[: len(self.data)].max() if self.data else 1.0
        if len(self.data) < self.cap:
            self.data.append(item)
        else:
            self.data[self.pos] = item
        self.prio[self.pos] = p
        self.pos = (self.pos + 1) % self.cap

    def sample(self, n: int, rng: np.random.Generator, beta: float = 0.4):
        p = self.prio[: len(self.data)] ** self.alpha
        p = p / p.sum()
        idx = rng.choice(len(self.data), size=n, p=p)
        w = (len(self.data) * p[idx]) ** (-beta)
        return idx, [self.data[i] for i in idx], w / w.max()

    def update(self, idx: np.ndarray, td: np.ndarray) -> None:
        self.prio[idx] = np.abs(td) + 1e-4

    def __len__(self) -> int:
        return len(self.data)


class DQNLearner:
    """One dueling double DQN learner (used by D3P and, per knob, by the factored MARL)."""

    def __init__(self, n_in: int, n_act: int, seed: int, lr: float = 1e-3, gamma: float = 0.9,
                 batch: int = 32, buffer: int = 5000, target_every: int = 100) -> None:
        torch.manual_seed(seed)
        self.gen = torch.Generator().manual_seed(seed)
        self.rng = np.random.default_rng(seed)
        self.net = DuelingNet(n_in, n_act)
        self.tgt = DuelingNet(n_in, n_act)
        self.tgt.load_state_dict(self.net.state_dict())
        self.opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        self.mem = PER(buffer)
        self.gamma, self.batch, self.target_every = gamma, batch, target_every
        self.n_act = n_act
        self.steps = 0
        self._reset_noise()

    def _reset_noise(self) -> None:
        for m in (self.net, self.tgt):
            for layer in m.noisy_layers():
                layer.reset_noise(self.gen)

    def act(self, x: np.ndarray) -> int:
        with torch.no_grad():
            return int(self.net(torch.as_tensor(x[None], dtype=torch.float32)).argmax(1).item())

    def push(self, s: np.ndarray, a: int, r: float, s2: np.ndarray, done: bool) -> None:
        self.mem.add((s, a, r, s2, float(done)))
        if len(self.mem) >= self.batch:
            self._learn()

    def _learn(self) -> None:
        idx, b, w = self.mem.sample(self.batch, self.rng)
        s = torch.as_tensor(np.stack([x[0] for x in b]), dtype=torch.float32)
        a = torch.as_tensor([x[1] for x in b], dtype=torch.long)
        r = torch.as_tensor([x[2] for x in b], dtype=torch.float32)
        s2 = torch.as_tensor(np.stack([x[3] for x in b]), dtype=torch.float32)
        d = torch.as_tensor([x[4] for x in b], dtype=torch.float32)
        q = self.net(s).gather(1, a[:, None]).squeeze(1)
        with torch.no_grad():
            a2 = self.net(s2).argmax(1, keepdim=True)                 # double DQN: select with online
            y = r + (1 - d) * self.gamma * self.tgt(s2).gather(1, a2).squeeze(1)
        td = y - q
        loss = (torch.as_tensor(w, dtype=torch.float32) * F.smooth_l1_loss(q, y, reduction="none")).mean()
        self.opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.net.parameters(), 10.0)
        self.opt.step()
        self.mem.update(idx, td.detach().numpy())
        self.steps += 1
        if self.steps % self.target_every == 0:
            self.tgt.load_state_dict(self.net.state_dict())
        self._reset_noise()

    def freeze(self) -> None:
        for m in (self.net, self.tgt):
            for layer in m.noisy_layers():
                layer.noisy = False
        self.net.eval()


class D3PController(Controller):
    name = "d3p"

    def __init__(self, seed: int = 0) -> None:
        self.learner = DQNLearner(OBS_DIM, N_ACTIONS, seed)
        self._last_a = 0

    def act(self, obs: Observation, explore: bool = False) -> Knobs:
        self._last_a = self.learner.act(obs.vector())   # exploration comes from the noisy layers
        return Knobs.from_action(self._last_a)

    def observe_transition(self, obs, action, reward, next_obs, done) -> None:
        a = ACTIONS.index(tuple(KNOB_LEVELS[n].index(_knob_value(action, n)) for n in KNOB_NAMES))
        self.learner.push(obs.vector(), a, reward, next_obs.vector(), done)

    def freeze(self) -> None:
        self.learner.freeze()


def _knob_value(k: Knobs, name: str) -> float:
    v = getattr(k, name)
    if v is None:  # default knobs map to the middle/defaults of the grid
        return {"audit_rate": 0.2, "temperature": 0.2}[name]
    return v
