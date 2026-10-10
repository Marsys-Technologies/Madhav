"""TI-L0-20 ordering rule, ENFORCED IN CODE (independent review L0C H-1; SS N-113 ruling: the registry flips first, then the writers).

The hazard: the frozen orchestrator's writer-gap pre-flight (runner.py `_check_writer_registry_gaps`, default `enforce`) exits 1 for EVERY
run when an @register()'d writer has has_writer = false. Mechanism chosen (does not touch the orchestrator or writers/__init__.py):
`pipeline/orchestrator/writers/_l0_static_gate.py` - the two new writers register only when ORCHESTRATOR_L0_STATIC_WRITERS is on, default OFF.
This file proves the pre-flight, run against the REAL runner function with the gate off and on, behaves as the order requires.
"""
from __future__ import annotations

import importlib

import pytest

from pipeline.orchestrator import runner
from pipeline.orchestrator import writers as W
from pipeline.orchestrator.writers import _l0_static_gate as gate

IDS = ("bg_gochara_citation_resolution", "bg_sarvatobhadra_grid")


class _Cur:
    """Minimal cursor for _check_writer_registry_gaps: serves the has_writer rows given in `flags` (None = no registry row)."""
    def __init__(self, flags):
        self.flags, self._rows = flags, []

    def execute(self, sql, params=None):
        ids = params[0]
        self._rows = [{"asset_id": i, "has_writer": self.flags[i]} for i in ids if self.flags.get(i) is not None]

    def fetchall(self):
        return self._rows


def _reload_writers():
    from pipeline.orchestrator.writers import bg_gochara_citation_resolution as m1, bg_sarvatobhadra_grid as m2
    for i in IDS:
        W._REGISTRY.pop(i, None)
    importlib.reload(m1)
    importlib.reload(m2)


@pytest.fixture(autouse=True)
def _restore(monkeypatch):
    yield
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    _reload_writers()


def _flags_for_every_registered(extra: dict):
    """has_writer = true for everything registered EXCEPT what `extra` overrides (the production state apart from the two L0 rows)."""
    flags = {i: True for i in W._REGISTRY}
    flags.update(extra)
    return flags


def test_gate_is_off_unless_the_variable_is_set(monkeypatch):
    assert gate.ENV_VAR == "ORCHESTRATOR_L0_STATIC_WRITERS"
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    assert gate.enabled() is False


def test_registry_NOT_yet_flipped_and_gate_OFF_the_pre_flight_sees_no_gap(monkeypatch):
    """Code deployed first (today's production): has_writer false for both, gate off -> the new writers are not registered -> no gap."""
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    _reload_writers()
    assert all(W.get_writer(i) is None for i in IDS)
    gaps = runner._check_writer_registry_gaps(_Cur(_flags_for_every_registered({i: False for i in IDS})))
    assert not set(IDS) & set(gaps)


def test_the_hazard_is_real_gate_ON_with_the_registry_not_flipped_the_pre_flight_reports_both_as_gaps(monkeypatch):
    """The failure the gate prevents (reproduces review L0C H-1): registered writers + has_writer false -> enforce-mode exit 1."""
    monkeypatch.setenv(gate.ENV_VAR, "1")
    _reload_writers()
    assert all(W.get_writer(i) is not None for i in IDS)
    gaps = runner._check_writer_registry_gaps(_Cur(_flags_for_every_registered({i: False for i in IDS})))
    assert set(IDS) <= set(gaps)


def test_registry_flipped_FIRST_then_gate_ON_the_pre_flight_is_clean(monkeypatch):
    """The ruled order: migration 1280 (has_writer true) applied, SS verifies it, then the gate is switched on."""
    monkeypatch.setenv(gate.ENV_VAR, "1")
    _reload_writers()
    gaps = runner._check_writer_registry_gaps(_Cur(_flags_for_every_registered({i: True for i in IDS})))
    assert not set(IDS) & set(gaps)


def test_registry_flipped_and_gate_OFF_is_benign_the_assets_are_just_not_dispatchable_yet(monkeypatch):
    """The flip applies before the code (and before the gate): has_writer true with no registered writer is not a gap."""
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    _reload_writers()
    gaps = runner._check_writer_registry_gaps(_Cur(_flags_for_every_registered({i: True for i in IDS})))
    assert not set(IDS) & set(gaps)
