"""A5: no decrypt-compare-re-encrypt, no mock fallback, no silent plaintext path."""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
BANNED = ("compute_encrypted_comparison", "compute_encrypted_mean", "enforce_policy_with_fhe",
          "Fernet", "use_real_fhe", "TENSEAL_AVAILABLE")


def test_fake_fhe_symbols_deleted():
    for p in SRC.rglob("*.py"):
        s = p.read_text(encoding="utf-8")
        for bad in BANNED:
            assert bad not in s, f"{bad} in {p}"
    assert not (SRC / "abac" / "fhe.py").exists()


def test_he_tally_raises_without_tenseal(monkeypatch):
    real_import = builtins.__import__

    def fake(name, *a, **k):
        if name == "tenseal" or name.startswith("tenseal."):
            raise ImportError("no tenseal")
        return real_import(name, *a, **k)

    saved = sys.modules.pop("src.crypto.he_tally", None)
    monkeypatch.setattr(builtins, "__import__", fake)
    monkeypatch.delitem(sys.modules, "tenseal", raising=False)
    with pytest.raises(ImportError, match="tenseal is required"):
        importlib.import_module("src.crypto.he_tally")
    monkeypatch.undo()
    if saved is not None:
        sys.modules["src.crypto.he_tally"] = saved


def test_he_path_decrypts_once_after_the_sign_polynomial():
    src = (SRC / "crypto" / "he_tally.py").read_text(encoding="utf-8")
    body = src[src.index("    def tally"):src.index("def plaintext_tally")]
    assert body.count(".decrypt(") == 1
    assert body.index(".decrypt(") > body.index("polyval")
