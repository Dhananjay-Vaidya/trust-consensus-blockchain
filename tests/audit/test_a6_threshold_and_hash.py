"""A6: theta is configurable; hashing is process-independent; runs are bit-identical."""
from __future__ import annotations

import inspect
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

import src.consensus.tdcb as tdcb
from src.consensus.tdcb import TDCB, tx_digest

ROOT = Path(__file__).resolve().parents[2]


def test_no_literal_threshold_and_no_builtin_hash():
    src = inspect.getsource(tdcb)
    assert "0.667" not in src
    assert " hash(" not in src and "(hash(" not in src


def test_theta_changes_decisions():
    w = np.ones(4)
    v = np.array([[1, 1, 0, 0], [1, 1, 1, 0]], float)
    assert TDCB(0.5).tally(w, v).accept.tolist() == [True, True]
    assert TDCB(0.8).tally(w, v).accept.tolist() == [False, False]


def test_digest_stable():
    assert tx_digest("a", 1, 2.5) == tx_digest("a", 1, 2.5)
    assert tx_digest("a", 1) != tx_digest("a", 2)


SNIPPET = """
import hashlib
import numpy as np
from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.consensus.tdcb import tx_digest
e = HonestEnv(RunConfig(seed=5, steps=60, t_switch=30, trust_backend="legacy_beta")).run()
blob = b"".join(np.concatenate([r.accept, r.flagged, r.trust, r.weights,
                                r.committee_idx.astype(float)]).tobytes() for r in e.records)
print(hashlib.blake2b(blob).hexdigest() + "|" + tx_digest("x", 1))
"""


def test_bit_identical_across_processes_with_different_hash_seeds():
    outs = []
    for hs in ("1", "999"):
        env = dict(os.environ, PYTHONHASHSEED=hs)
        r = subprocess.run([sys.executable, "-c", SNIPPET], cwd=ROOT, env=env,
                           capture_output=True, text=True, check=True)
        outs.append(r.stdout.strip().splitlines()[-1])
    assert outs[0] == outs[1]
