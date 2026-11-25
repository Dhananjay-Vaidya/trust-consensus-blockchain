"""Integration smoke test: the main.py entry point runs end to end, with and without the CKKS tally."""
from __future__ import annotations

import importlib.util
import math

import pytest

import main


def _check(res: dict) -> None:
    assert 0.0 <= res["det_f1"] <= 1.0 and not math.isnan(res["det_f1"])
    assert res["confirmed_blocks"] >= 1 and res["chain_valid"]
    assert res["pending_tx_count"] >= 0


def test_main_plain_smoke():
    res = main.main(["--attack", "nma", "--nodes", "8", "--steps", "20", "--seed", "42",
                     "--difficulty", "1", "--log-level", "WARNING"])
    _check(res)
    assert res["fhe_enabled"] is False and "fhe_avg_overhead_ms" not in res
    # same seed => identical decisions and ledger size
    again = main.main(["--attack", "nma", "--nodes", "8", "--steps", "20", "--seed", "42",
                       "--difficulty", "1", "--log-level", "WARNING"])
    assert (again["det_f1"], again["confirmed_blocks"], again["pending_tx_count"]) == \
           (res["det_f1"], res["confirmed_blocks"], res["pending_tx_count"])


@pytest.mark.skipif(importlib.util.find_spec("tenseal") is None, reason="tenseal not installed")
def test_main_fhe_smoke():
    res = main.main(["--attack", "nma", "--nodes", "8", "--steps", "10", "--seed", "42",
                     "--difficulty", "1", "--fhe", "--log-level", "WARNING"])
    _check(res)
    assert res["tally_backend"] == "he" and res["fhe_avg_overhead_ms"] > 0.0
    assert res["fhe_flips"] == 0
