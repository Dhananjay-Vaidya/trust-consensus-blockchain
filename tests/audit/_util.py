from __future__ import annotations

from src.config.run_config import RunConfig


def small(**kw) -> RunConfig:
    base = dict(seed=3, steps=80, t_switch=40, num_nodes=12, committee_size=12, tx_per_step=12)
    base.update(kw)
    return RunConfig().with_overrides(**base)
