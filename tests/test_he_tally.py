from __future__ import annotations

import numpy as np
import pytest

from src.consensus.tdcb import TDCB
from src.crypto.he_tally import HETally, plaintext_tally


@pytest.fixture(scope="module")
def he0():
    return HETally(sign_iters=0)


def test_raw_margin_mode_matches_plaintext(he0):
    rng = np.random.default_rng(0)
    for _ in range(5):
        w = rng.random(8)
        v = (rng.random((16, 8)) < 0.6).astype(float)
        r = he0.tally(w, v, 0.667)
        acc, m = plaintext_tally(w, v, 0.667)
        outside = np.abs(m) > 1e-3
        assert np.array_equal(r.accept[outside], acc[outside])
        assert np.allclose(r.squashed, m, atol=1e-5)
        assert r.ciphertext_bytes > 0 and set(r.timings_ms) == {"encrypt", "margin", "sign_poly", "decrypt"}


def test_parameter_selection_respects_128bit_budget():
    assert HETally(0).poly_modulus_degree == 8192
    assert HETally(1).poly_modulus_degree == 16384


def test_tdcb_he_backend_agrees_with_plain():
    rng = np.random.default_rng(1)
    w = rng.random(8)
    v = (rng.random((8, 8)) < 0.7).astype(float)
    a = TDCB(0.6, "plain").tally(w, v)
    b = TDCB(0.6, "he", he_sign_iters=0).tally(w, v)
    assert np.array_equal(a.accept, b.accept) and b.he_flips == 0 and b.he_ms > 0


def test_tdcb_aborts_when_cap_violated():
    w = np.array([1.0, 0.0, 0.0, 0.0])
    out = TDCB(0.667).tally(w, np.ones((2, 4)), max_share=0.5)
    assert out.aborted and not out.accept.any()
