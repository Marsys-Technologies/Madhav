"""
test_wave_d4b_b4_remedy_leverage_join.py — Doctrine Wave D-4b, BRIEF_D4B.md §1
Lane B-4 (Remedy-leverage join = v2.0 Lane C-5)
================================================================================
bo_upaya populated from: leverage_index (weakest load-bearing graha) x sadhana
history (LEL spiritual arc, pre-embargo only) x dasha runway (intervention
window = years BEFORE the weak lord's Mahadasha opens).

Covers:
  - remedy_leverage_join_v1 (pure formula, bodha_writers/formulas.py)
  - _fetch_wealth_leverage_index / _fetch_sadhana_milestones /
    _fetch_leverage_weights / _fetch_dasha_runway_fresh (bo_upaya.py fetchers)
  - _build_remedy_leverage_windows (the join itself — honest-skip behavior,
    currently-running vs future-MD window selection, multiplier = product
    of the three named factors)

All tests are pure unit tests: no real DB connections (MagicMock conn,
mirrors test_ba_p25_4_bo_upaya_resonance_wiring.py's harness exactly).
"""
from __future__ import annotations

import collections
import importlib.util
import pathlib
import sys
import types
import uuid
from datetime import datetime, timezone
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


def _conn_sequence(row_batches):
    """conn.execute() is called multiple times in sequence; each call returns
    the next batch of rows."""
    conn = MagicMock()
    results = []
    for rows in row_batches:
        r = MagicMock()
        r.fetchall.return_value = rows
        results.append(r)
    conn.execute.side_effect = results
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
# _fetch_sadhana_milestones — embargo discipline
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchSadhanaMilestones:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_embargo_literal_is_hardcoded_never_parameterized(self):
        """The 2020-01-01 embargo date must appear as a query parameter derived
        from the module constant, not from any caller-supplied value — this
        test asserts the module constant exists and is exactly that date."""
        mod = self._load()
        assert mod._SADHANA_EMBARGO_DATE == "2020-01-01"

    def test_passes_chart_id_and_embargo_date_as_params(self):
        mod = self._load()
        conn = _conn_returning([])
        mod._fetch_sadhana_milestones(conn, "chart-1")
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == ["chart-1", "2020-01-01"]

    def test_maps_rows_to_dicts(self):
        mod = self._load()
        rows = [(str(uuid.uuid4()), "2002-07-01", "spiritual/sadhana_initiation", "LEL cite")]
        conn = _conn_returning(rows)
        result = mod._fetch_sadhana_milestones(conn, "chart-1")
        assert result[0]["domain"] == "spiritual/sadhana_initiation"
        assert result[0]["source_citation"] == "LEL cite"


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_dasha_runway_fresh — mirrors ga_vichara's own _dasha_runway curve
# ─────────────────────────────────────────────────────────────────────────────

_WEIGHTS = {
    "runway_lookforward_years": 30, "runway_base": 1.0, "runway_scale": 0.5,
    "runway_duration_norm_years": 20, "runway_start_horizon_years": 15,
}


class TestFetchDashaRunwayFresh:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_future_md_years_to_start_is_positive_not_zero(self):
        """Regression guard for the exact discrepancy this lane found live:
        a future Mahadasha must never be reported with years_to_start=0."""
        mod = self._load()
        now = datetime(2026, 7, 17, 1, 39, 23, tzinfo=timezone.utc)
        start = datetime(2034, 8, 18, 15, 50, 23, tzinfo=timezone.utc)
        end = datetime(2054, 8, 18, 15, 50, 23, tzinfo=timezone.utc)
        rows = [(str(uuid.uuid4()), start, end, 7305.0)]
        conn = _conn_returning(rows)
        result = mod._fetch_dasha_runway_fresh(conn, "chart-1", "lahiri_chitrapaksha", "Venus", now, _WEIGHTS)
        assert result is not None
        assert result["years_to_start"] == pytest.approx(8.08, abs=0.02)
        assert result["years_to_start"] != 0
        assert result["currently_running"] is False
        assert result["md_duration_years"] == pytest.approx(20.0, abs=0.01)

    def test_currently_running_md_flagged_and_zero_years_to_start(self):
        mod = self._load()
        now = datetime(2015, 1, 1, tzinfo=timezone.utc)
        start = datetime(2010, 8, 18, tzinfo=timezone.utc)
        end = datetime(2027, 8, 18, tzinfo=timezone.utc)
        rows = [(str(uuid.uuid4()), start, end, 6209.0)]
        conn = _conn_returning(rows)
        result = mod._fetch_dasha_runway_fresh(conn, "chart-1", "lahiri_chitrapaksha", "Mercury", now, _WEIGHTS)
        assert result["currently_running"] is True
        assert result["years_to_start"] == 0.0

    def test_no_matching_md_row_returns_none(self):
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_dasha_runway_fresh(
            conn, "chart-1", "lahiri_chitrapaksha", "Venus",
            datetime(2026, 1, 1, tzinfo=timezone.utc), _WEIGHTS,
        )
        assert result is None

    def test_already_elapsed_md_is_skipped(self):
        mod = self._load()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        elapsed = (str(uuid.uuid4()), datetime(1991, 1, 1, tzinfo=timezone.utc),
                   datetime(2010, 1, 1, tzinfo=timezone.utc), 6940.0)
        conn = _conn_returning([elapsed])
        result = mod._fetch_dasha_runway_fresh(conn, "chart-1", "lahiri_chitrapaksha", "Saturn", now, _WEIGHTS)
        assert result is None

    def test_beyond_lookforward_horizon_is_skipped(self):
        mod = self._load()
        now = datetime(2000, 1, 1, tzinfo=timezone.utc)
        far_future = (str(uuid.uuid4()), datetime(2060, 1, 1, tzinfo=timezone.utc),
                      datetime(2080, 1, 1, tzinfo=timezone.utc), 7305.0)
        conn = _conn_returning([far_future])
        result = mod._fetch_dasha_runway_fresh(conn, "chart-1", "lahiri_chitrapaksha", "Venus", now, _WEIGHTS)
        assert result is None


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
# _build_remedy_leverage_windows — the join itself
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildRemedyLeverageWindows:
    def _load(self):
        return _load_module("bo_upaya.py")

    def _prescriptions(self, graha="Venus"):
        return [{
            "prescription_id": "presc-1", "target_graha": graha,
            "resonance_match_score": 0.8,
        }]

    def test_honest_skip_when_no_prescription_for_target_graha(self):
        """B.10: never fabricate a base_prescription_id — a graha with a
        positive leverage_index but no G27 prescription must be skipped, not
        invented."""
        mod = self._load()
        conn = _conn_sequence([
            [("VEN", "VEN", 3.9375, [])],  # _fetch_wealth_leverage_index (aliased id)
        ])
        windows = mod._build_remedy_leverage_windows(
            "chart-1", "lahiri_chitrapaksha", "build-1", conn,
            datetime(2026, 7, 21, tzinfo=timezone.utc),
            self._prescriptions(graha="Saturn"),  # no Venus prescription
            [], _WEIGHTS, "2026-07-21T00:00:00+00:00",
        )
        assert windows == []

    def test_honest_skip_when_no_resolvable_dasha(self):
        mod = self._load()
        conn = _conn_sequence([
            [("VEN", "VEN", 3.9375, [])],  # leverage rows
            [],                             # dasha rows — none found
        ])
        windows = mod._build_remedy_leverage_windows(
            "chart-1", "lahiri_chitrapaksha", "build-1", conn,
            datetime(2026, 7, 21, tzinfo=timezone.utc),
            self._prescriptions(graha="Venus"),
            [], _WEIGHTS, "2026-07-21T00:00:00+00:00",
        )
        assert windows == []

    def test_pre_md_window_uses_now_to_md_start(self):
        mod = self._load()
        now = datetime(2026, 7, 21, tzinfo=timezone.utc)
        md_start = datetime(2034, 8, 18, tzinfo=timezone.utc)
        md_end = datetime(2054, 8, 18, tzinfo=timezone.utc)
        conn = _conn_sequence([
            [("VEN", "VEN", 3.9375, ["fid1"])],
            [(str(uuid.uuid4()), md_start, md_end, 7305.0)],
        ])
        sadhana = [{"event_id": "e1"}, {"event_id": "e2"}]
        windows = mod._build_remedy_leverage_windows(
            "chart-1", "lahiri_chitrapaksha", "build-1", conn, now,
            self._prescriptions(graha="Venus"), sadhana, _WEIGHTS,
            "2026-07-21T00:00:00+00:00",
        )
        assert len(windows) == 1
        w = windows[0]
        assert w["dasha_lord"] == "Venus"
        assert w["window_start_iso"] == now
        assert w["window_end_iso"] == md_start
        assert w["phase_within_window"] == "pre_md_preparation_window"
        assert w["base_prescription_id"] == "presc-1"
        assert w["window_intensity_multiplier"] > 0
        # score = leverage(3.9375) x sadhana_factor(1 + 0.15*2 = 1.3) x runway_weight —
        # cross-check the served multiplier against the three cited sub-factors
        # independently reported in schedule_jsonb (no hidden 4th term).
        import json
        schedule = json.loads(w["schedule_jsonb"])
        expected = (
            schedule["leverage_index"]["value"]
            * schedule["sadhana_history"]["factor"]
            * schedule["dasha_runway"]["runway_weight"]
        )
        assert schedule["sadhana_history"]["factor"] == pytest.approx(1.3)
        assert w["window_intensity_multiplier"] == pytest.approx(expected, rel=1e-6)

    def test_active_md_window_uses_now_to_md_end(self):
        mod = self._load()
        now = datetime(2015, 1, 1, tzinfo=timezone.utc)
        md_start = datetime(2010, 8, 18, tzinfo=timezone.utc)
        md_end = datetime(2027, 8, 18, tzinfo=timezone.utc)
        conn = _conn_sequence([
            [("VEN", "VEN", 3.9375, [])],
            [(str(uuid.uuid4()), md_start, md_end, 6209.0)],
        ])
        windows = mod._build_remedy_leverage_windows(
            "chart-1", "lahiri_chitrapaksha", "build-1", conn, now,
            self._prescriptions(graha="Venus"), [], _WEIGHTS,
            "2015-01-01T00:00:00+00:00",
        )
        assert len(windows) == 1
        w = windows[0]
        assert w["window_start_iso"] == now
        assert w["window_end_iso"] == md_end
        assert w["phase_within_window"] == "active_md_direct_intervention"

    def test_no_positive_leverage_rows_returns_empty(self):
        mod = self._load()
        conn = _conn_sequence([[]])
        windows = mod._build_remedy_leverage_windows(
            "chart-1", "lahiri_chitrapaksha", "build-1", conn,
            datetime(2026, 7, 21, tzinfo=timezone.utc),
            self._prescriptions(), [], _WEIGHTS, "2026-07-21T00:00:00+00:00",
        )
        assert windows == []

    def test_schedule_jsonb_cites_all_three_factor_sources(self):
        mod = self._load()
        now = datetime(2026, 7, 21, tzinfo=timezone.utc)
        md_start = datetime(2034, 8, 18, tzinfo=timezone.utc)
        md_end = datetime(2054, 8, 18, tzinfo=timezone.utc)
        conn = _conn_sequence([
            [("VEN", "VEN", 3.9375, ["fid1", "fid2"])],
            [(str(uuid.uuid4()), md_start, md_end, 7305.0)],
        ])
        windows = mod._build_remedy_leverage_windows(
            "chart-1", "lahiri_chitrapaksha", "build-1", conn, now,
            self._prescriptions(graha="Venus"),
            [{"event_id": "e1"}], _WEIGHTS, "2026-07-21T00:00:00+00:00",
        )
        import json
        schedule = json.loads(windows[0]["schedule_jsonb"])
        assert schedule["leverage_index"]["value"] == 3.9375
        assert schedule["leverage_index"]["domain"] == "wealth"
        assert schedule["leverage_index"]["constituent_fact_ids"] == ["fid1", "fid2"]
        assert schedule["sadhana_history"]["pre_embargo_milestone_count"] == 1
        assert schedule["dasha_runway"]["years_before_md_open"] > 0
        assert schedule["dasha_runway"]["currently_running"] is False
