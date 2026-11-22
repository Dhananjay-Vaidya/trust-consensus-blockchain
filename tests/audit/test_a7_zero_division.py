"""A7: no free precision when nothing is flagged."""
from __future__ import annotations

import numpy as np

from src.metrics.ground_truth_metrics import _prf


def test_no_positive_predictions_gives_zero_not_one():
    r = _prf(np.array([1, 0, 1, 0]), np.array([0, 0, 0, 0]))
    assert r["precision"] == 0.0 and r["recall"] == 0.0 and r["f1"] == 0.0


def test_mcc_reported_separately():
    r = _prf(np.array([1, 0, 1, 0]), np.array([1, 0, 1, 0]))
    assert r["mcc"] == 1.0 and set(r) == {"precision", "recall", "f1", "mcc"}
