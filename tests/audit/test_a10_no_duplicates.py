"""A10: one canonical module per concept."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_no_root_shims_or_duplicate_packages():
    for name in ("abac.py", "trust.py", "tdcb.py", "simulation_manager.py", "fhe.py", "parameters.py",
                 "drl_d3p.py", "marl_agent.py", "rl_agent.py", "reward.py", "attack_util.py"):
        assert not (ROOT / name).exists(), name
    assert not (ROOT / "api" / "main.py").exists()
    assert not (ROOT / "baselines").exists()
    assert not (ROOT / "src" / "baselines").exists()


def test_unique_module_basenames_under_src():
    seen: dict[str, Path] = {}
    for p in (ROOT / "src").rglob("*.py"):
        if p.name == "__init__.py" or "__pycache__" in p.parts:
            continue
        assert p.name not in seen, f"{p} duplicates {seen[p.name]}"
        seen[p.name] = p
