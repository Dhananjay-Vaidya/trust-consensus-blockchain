"""A9: immutable RunConfig, no global parameter module."""
from __future__ import annotations

import dataclasses
import importlib

import pytest

from src.config.run_config import RunConfig


def test_runconfig_is_frozen():
    c = RunConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.seed = 4  # type: ignore[misc]


def test_overrides_return_new_object():
    a = RunConfig()
    b = a.with_overrides(seed=9, sg_cusum_alarm=5.0)
    assert a.seed == 0 and b.seed == 9 and b.sleeper_guard.cusum_alarm == 5.0
    assert a.sleeper_guard.cusum_alarm == 3.0


def test_no_global_parameters_module():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("parameters")
