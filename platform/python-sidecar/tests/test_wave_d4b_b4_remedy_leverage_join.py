"""
test_wave_d4b_b4_remedy_leverage_join.py — Doctrine Wave D-4b, BRIEF_D4B.md §1
Lane B-4 (Remedy-leverage join = v2.0 Lane C-5)
================================================================================
The original B-4 design joined leverage_index with LEL sadhana history and a
resolved dasha runway. DP-SD-015 superseded that implementation: L2 may retain
the pure compatibility formula and structural leverage reader, but LEL reads,
resolved windows, and schedulable remedy output are L3-only.

Covers:
  - remedy_leverage_join_v1 (pure formula, bodha_writers/formulas.py)
  - _fetch_wealth_leverage_index / _fetch_leverage_weights (L2 structural readers)
  - fail-closed tombstones for dasha runway and schedulable remedy windows
  - absence of any L2 LEL reader or windowed-prescription insert path

All tests are pure unit tests: no real DB connections (MagicMock conn,
mirrors test_ba_p25_4_bo_upaya_resonance_wiring.py's harness exactly).
"""
from __future__ import annotations

import collections
import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock

import pytest

_WRITERS_DIR = str(
    pathlib.Path(__file__).parent.parent / "pipeline" / "orchestrator" / "writers"
)
_WORKTREE = _WRITERS_DIR + "/"
_PKG = "pipeline.orchestrator.writers"

FakeWriterResult = collections.namedtuple(
    "WriterResult", ["asset_id", "rows_inserted", "notes", "duration_seconds"],
    defaults=[None, 0, None, 0.0],
)


def _ensure_writers_stub():
    existing = sys.modules.get(_PKG)
    if existing is not None and hasattr(existing, "__file__"):
        return existing
    stub = types.ModuleType(_PKG)
    stub.WriterBase = object
    stub.ContextSpec = object
    stub.WriterResult = FakeWriterResult
    stub.SubStep = MagicMock
    stub.register = lambda x: (lambda cls: cls)
    stub.__path__ = [_WRITERS_DIR]
    stub.__package__ = _PKG
    sys.modules[_PKG] = stub
    return stub


def _load_module(filename: str) -> types.ModuleType:
    stub = _ensure_writers_stub()
    key = f"{_PKG}.{filename.replace('.py', '')}"
    prev_mod = sys.modules.pop(key, None)

    path = _WORKTREE + filename
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG
    sys.modules[key] = mod

    _noop_register = lambda asset_id: (lambda cls: cls)
    original_register = getattr(stub, "register", _noop_register)
    stub.register = _noop_register
    try:
        spec.loader.exec_module(mod)
    finally:
        stub.register = original_register
        if prev_mod is not None:
            sys.modules[key] = prev_mod
        else:
            sys.modules.pop(key, None)

    return mod


def _conn_returning(rows):
    conn = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = rows
    conn.execute.return_value = result
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# remedy_leverage_join_v1 — pure formula
# ─────────────────────────────────────────────────────────────────────────────

class TestRemedyLeverageJoinFormula:
    def _formula(self):
        from bodha_writers.formulas import RemedyLeverageJoinInputs, remedy_leverage_join_v1
        return RemedyLeverageJoinInputs, remedy_leverage_join_v1

    def test_score_is_plain_product_of_three_factors(self):
        Inputs, formula = self._formula()
        result = formula(Inputs(
            leverage_index_value=3.9375, sadhana_milestone_count=4, dasha_runway_weight=1.298,
        ))
        expected_sadhana_factor = 1.0 + 0.15 * 4
        expected_score = 3.9375 * expected_sadhana_factor * 1.298
        assert result["sadhana_history_factor"] == pytest.approx(expected_sadhana_factor)
        assert result["remedy_leverage_score"] == pytest.approx(expected_score, rel=1e-6)

    def test_zero_milestones_is_neutral_not_penalized(self):
        Inputs, formula = self._formula()
        result = formula(Inputs(leverage_index_value=2.0, sadhana_milestone_count=0, dasha_runway_weight=1.0))
        assert result["sadhana_history_factor"] == 1.0
        assert result["remedy_leverage_score"] == pytest.approx(2.0)

    def test_milestone_count_bounded_at_5(self):
        Inputs, formula = self._formula()
        at_5 = formula(Inputs(leverage_index_value=1.0, sadhana_milestone_count=5, dasha_runway_weight=1.0))
        at_50 = formula(Inputs(leverage_index_value=1.0, sadhana_milestone_count=50, dasha_runway_weight=1.0))
        assert at_5["sadhana_history_factor"] == at_50["sadhana_history_factor"]

    def test_negative_milestone_count_clamped_to_zero(self):
        Inputs, formula = self._formula()
        result = formula(Inputs(leverage_index_value=1.0, sadhana_milestone_count=-3, dasha_runway_weight=1.0))
        assert result["sadhana_history_factor"] == 1.0

    def test_zero_leverage_index_yields_zero_score(self):
        Inputs, formula = self._formula()
        result = formula(Inputs(leverage_index_value=0.0, sadhana_milestone_count=5, dasha_runway_weight=2.0))
        assert result["remedy_leverage_score"] == 0.0

    def test_formula_version_stamped(self):
        Inputs, formula = self._formula()
        result = formula(Inputs())
        assert result["remedy_leverage_join_formula_version"] == "v1.0"


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_wealth_leverage_index
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchWealthLeverageIndex:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_maps_columns_from_tuples(self):
        mod = self._load()
        rows = [(101, "VEN", 3.9375, ["fid1", "fid2"]), (102, "JUP", 1.336301, ["fid3"])]
        conn = _conn_returning(rows)
        result = mod._fetch_wealth_leverage_index(conn, "chart-1", "lahiri_chitrapaksha")
        assert result[0] == {
            "vichara_row_id": 101, "subject": "VEN", "value_num": 3.9375,
            "constituent_fact_ids": ["fid1", "fid2"],
        }
        assert result[1]["subject"] == "JUP"

    def test_dict_rows_pass_through_unchanged(self):
        mod = self._load()
        rows = [{"vichara_row_id": 101, "subject": "VEN", "value_num": 3.9375,
                 "constituent_fact_ids": ["fid1"]}]
        conn = _conn_returning(rows)
        result = mod._fetch_wealth_leverage_index(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == rows

    def test_empty_result_returns_empty_list(self):
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_wealth_leverage_index(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# LEL and resolved daśā inputs — L3-only authority boundary
# ─────────────────────────────────────────────────────────────────────────────

class TestTemporalAndLelInputsUnavailableAtL2:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_l2_writer_has_no_sadhana_or_lel_reader(self):
        mod = self._load()
        import inspect

        source = inspect.getsource(mod)
        assert not hasattr(mod, "_SADHANA_EMBARGO_DATE")
        assert not hasattr(mod, "_fetch_sadhana_milestones")
        assert "FROM life_events" not in source

    def test_dasha_runway_tombstone_fails_closed(self):
        mod = self._load()
        with pytest.raises(RuntimeError, match="L3-only"):
            mod._fetch_dasha_runway_fresh()


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_leverage_weights
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchLeverageWeights:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_reads_registry_not_hardcoded(self):
        mod = self._load()
        conn = _conn_returning([({"runway_base": 1.0, "runway_scale": 0.5},)])
        result = mod._fetch_leverage_weights(conn)
        assert result == {"runway_base": 1.0, "runway_scale": 0.5}

    def test_empty_registry_returns_empty_dict(self):
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_leverage_weights(conn)
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# _build_remedy_leverage_windows — L3-only compatibility tombstone
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildRemedyLeverageWindows:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_schedulable_window_builder_fails_closed(self):
        mod = self._load()
        with pytest.raises(RuntimeError, match="L3-only"):
            mod._build_remedy_leverage_windows()

    def test_l2_has_no_windowed_prescription_insert(self):
        mod = self._load()
        assert not hasattr(mod, "_WINDOWED_INSERT")
