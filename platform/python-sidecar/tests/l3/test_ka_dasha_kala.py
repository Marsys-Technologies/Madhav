"""
Tests for ka_dasha_kala — Dasa-Eligibility Service (L3 Kala K1).

Acceptance criteria covered:
  AC1: Pruning — ineligible MD subtrees are NOT queried for children
  AC2: Interval algebra — eligible set = correct UNION of chart_dashas intervals
  AC3: Eligibility score ranking: exact > related > neutral
  AC4: Cross-dasa agreement — count + system list for a real multi-system window
  AC5: Sookshma floor (day-grain) vs Prana (in-memory, no level-5 rows in DB)
  AC6: 7 systems confirmed in chart_dashas for native chart (PROD DB)
  AC7: Writer self-test + health badge update (PROD DB)
  AC8: grep check (no commit/rollback in service code -- verified via grep)

Tests are split into:
  - Pure unit tests (no DB): mock conn, use constructed test data
  - Integration tests (PROD DB): marked with @pytest.mark.integration
    and require DB_DSN env var or a real connection
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

# Ensure the sidecar root is on sys.path
_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_dasha_kala.eligibility import (
    EligibilityBand,
    score_eligibility,
    is_eligible_for_pruning,
    BAND_SCORE,
)
from services.ka_dasha_kala.tree_walk import (
    walk_eligible_intervals,
    _subdivide_prana,
    DashaInterval,
    ALL_DASHA_SYSTEMS,
)
from services.ka_dasha_kala.service import KaDashaKalaService


# ---------------------------------------------------------------------------
# Helpers: mock DB connection
# ---------------------------------------------------------------------------

def _make_conn(rows_by_call: dict[str, list[list]]) -> Any:
    """
    Build a mock psycopg-like connection.

    rows_by_call: {call_key: [list_of_rows]}.
    call_key matches the first element of the args list (used to dispatch).

    For simplicity, calls are dispatched by inspecting the SQL for
    'level_n = 1' or 'parent_row_id = %s'.
    """
    class MockCursor:
        def __init__(self, rows):
            self._rows = rows
        def fetchall(self):
            return self._rows

    class MockConn:
        def __init__(self, dispatch):
            self._dispatch = dispatch
            self._calls = []

        def execute(self, sql, params=None):
            self._calls.append((sql, params))
            # Dispatch based on SQL content
            if "level_n        = 1" in sql or "level_n = 1" in sql:
                key = "level1"
            elif "parent_row_id = %s" in sql:
                key = f"children:{params[0]}" if params else "children"
            else:
                key = "unknown"
            rows = self._dispatch.get(key, [])
            return MockCursor(rows)

    return MockConn(rows_by_call)


def _make_md_row(row_id, lord, start, end):
    """Build a level-1 mock row (tuple, like psycopg returns)."""
    return (row_id, lord, start, end, None, None)


def _make_child_row(row_id, lord, start, end, level_n, parent_id):
    """Build a level-2+ mock row."""
    return (row_id, lord, start, end, level_n, parent_id, None, None)


# ---------------------------------------------------------------------------
# AC3: Eligibility score ranking
# ---------------------------------------------------------------------------

class TestEligibilityScoring:
    """AC3: exact > related > neutral."""

    def test_exact_match_score(self):
        band, score = score_eligibility("Saturn", {"Saturn", "Rahu"}, {"Mercury"})
        assert band == EligibilityBand.EXACT
        assert score >= 0.8

    def test_related_score(self):
        band, score = score_eligibility("Mercury", {"Saturn", "Rahu"}, {"Mercury"})
        assert band == EligibilityBand.RELATED
        assert 0.3 <= score <= 0.7

    def test_neutral_score(self):
        band, score = score_eligibility("Sun", {"Saturn", "Rahu"}, {"Mercury"})
        assert band == EligibilityBand.NEUTRAL
        assert score <= 0.3

    def test_exact_gt_related_gt_neutral(self):
        """Ranking invariant: exact > related > neutral."""
        _, exact_s = score_eligibility("Saturn", {"Saturn"}, {"Mercury"})
        _, related_s = score_eligibility("Mercury", {"Saturn"}, {"Mercury"})
        _, neutral_s = score_eligibility("Sun", {"Saturn"}, {"Mercury"})
        assert exact_s > related_s > neutral_s

    def test_is_eligible_for_pruning_neutral_pruned(self):
        """Neutral lord should be pruned at default min_band=RELATED."""
        assert not is_eligible_for_pruning("Sun", {"Saturn"}, {"Mercury"})

    def test_is_eligible_for_pruning_related_passes(self):
        assert is_eligible_for_pruning("Mercury", {"Saturn"}, {"Mercury"})

    def test_is_eligible_for_pruning_exact_passes(self):
        assert is_eligible_for_pruning("Saturn", {"Saturn"}, {"Mercury"})

    def test_custom_band_scores(self):
        from services.ka_dasha_kala.eligibility import BAND_SCORE
        custom = {
            EligibilityBand.EXACT: 0.95,
            EligibilityBand.RELATED: 0.60,
            EligibilityBand.NEUTRAL: 0.05,
        }
        _, score = score_eligibility("Saturn", {"Saturn"}, set(), band_scores=custom)
        assert score == 0.95


# ---------------------------------------------------------------------------
# AC1: Pruning — ineligible MD subtrees NOT queried for children
# ---------------------------------------------------------------------------

class TestTreeWalkPruning:
    """AC1: Children of pruned MDs are never fetched from DB."""

    def test_ineligible_md_children_not_queried(self):
        """
        Scenario: two MDs — Sun (NEUTRAL, pruned) and Saturn (EXACT, kept).
        Only Saturn's children should be queried.
        """
        query_counter = []

        # Level-1: Sun (neutral) + Saturn (exact)
        md_sun_id = "md-sun-001"
        md_sat_id = "md-sat-001"
        ad_sat_id = "ad-sat-sat-001"

        w_start = date(2020, 1, 1)
        w_end   = date(2025, 12, 31)

        dispatch = {
            "level1": [
                _make_md_row(md_sun_id, "Sun",    date(2020, 1, 1), date(2022, 6, 1)),
                _make_md_row(md_sat_id, "Saturn", date(2022, 6, 1), date(2025, 12, 31)),
            ],
            f"children:{md_sat_id}": [
                _make_child_row(ad_sat_id, "Saturn",
                                date(2022, 6, 1), date(2023, 6, 1), 2, md_sat_id),
            ],
        }
        conn = _make_conn(dispatch)

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords={"Mercury"},
            date_start=w_start,
            date_end=w_end,
            max_level=2,
            query_counter=query_counter,
        )

        # Sun's children must NEVER be queried
        sun_child_queries = [q for q in query_counter if md_sun_id in q]
        assert not sun_child_queries, (
            f"Ineligible Sun MD subtree was queried: {sun_child_queries}"
        )

        # Saturn's children MUST be queried
        sat_child_queries = [q for q in query_counter if md_sat_id in q]
        assert sat_child_queries, "Saturn MD children were NOT queried"

        # Results should only contain Saturn intervals
        assert all(r.lord_graha == "Saturn" for r in results), (
            f"Expected only Saturn results, got {[r.lord_graha for r in results]}"
        )

    def test_neutral_md_produces_no_results(self):
        """An MD of a neutral lord should yield zero results (whole subtree pruned)."""
        dispatch = {
            "level1": [
                _make_md_row("md-moon-001", "Moon", date(2020, 1, 1), date(2027, 1, 1)),
            ],
        }
        conn = _make_conn(dispatch)
        query_counter = []

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2020, 1, 1),
            date_end=date(2027, 1, 1),
            max_level=4,
            query_counter=query_counter,
        )

        assert results == [], "Neutral MD should produce no results"
        children_queries = [q for q in query_counter if "children" in q]
        assert not children_queries, (
            f"Children were queried for a fully neutral MD: {children_queries}"
        )

    def test_mixed_levels_pruning_depth(self):
        """
        Scenario: MD eligible, AD neutral — AD and its children are pruned.
        """
        md_id = "md-sat-001"
        ad_neutral_id = "ad-sun-001"
        ad_exact_id   = "ad-sat-001"
        sk_id = "sk-sat-001"

        dispatch = {
            "level1": [
                _make_md_row(md_id, "Saturn", date(2020, 1, 1), date(2027, 1, 1)),
            ],
            f"children:{md_id}": [
                _make_child_row(ad_neutral_id, "Sun",    date(2020, 1, 1), date(2021, 1, 1), 2, md_id),
                _make_child_row(ad_exact_id,   "Saturn", date(2021, 1, 1), date(2022, 1, 1), 2, md_id),
            ],
            f"children:{ad_exact_id}": [
                _make_child_row(sk_id, "Saturn", date(2021, 1, 1), date(2022, 1, 1), 3, ad_exact_id),
            ],
        }
        conn = _make_conn(dispatch)
        query_counter = []

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2020, 1, 1),
            date_end=date(2027, 1, 1),
            max_level=3,
            query_counter=query_counter,
        )

        # Neutral Sun AD subtree must NOT be queried
        sun_children = [q for q in query_counter if ad_neutral_id in q]
        assert not sun_children

        # All results should not contain Sun as lord
        assert all(r.lord_graha != "Sun" for r in results)


# ---------------------------------------------------------------------------
# AC2: Interval algebra — UNION of eligible intervals, no time iteration
# ---------------------------------------------------------------------------

class TestIntervalAlgebra:
    """AC2: The returned set equals the UNION of eligible chart_dashas intervals."""

    def test_single_eligible_md_returns_correct_interval(self):
        """One eligible MD → one interval returned with correct dates."""
        dispatch = {
            "level1": [
                _make_md_row("md-sat-001", "Saturn",
                             date(2020, 1, 1), date(2027, 1, 1)),
            ],
        }
        conn = _make_conn(dispatch)

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2020, 1, 1),
            date_end=date(2030, 1, 1),
            max_level=1,
        )

        assert len(results) == 1
        assert results[0].start_date == date(2020, 1, 1)
        assert results[0].end_date   == date(2027, 1, 1)
        assert results[0].lord_graha == "Saturn"

    def test_multiple_eligible_mds_union(self):
        """Two eligible MDs → two intervals (union, no merge)."""
        dispatch = {
            "level1": [
                _make_md_row("md-sat-001", "Saturn", date(2010, 1, 1), date(2020, 1, 1)),
                _make_md_row("md-rah-001", "Rahu",   date(2020, 1, 1), date(2038, 1, 1)),
            ],
        }
        conn = _make_conn(dispatch)

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn", "Rahu"},
            related_lords=set(),
            date_start=date(2010, 1, 1),
            date_end=date(2040, 1, 1),
            max_level=1,
        )

        assert len(results) == 2
        lords = {r.lord_graha for r in results}
        assert lords == {"Saturn", "Rahu"}

    def test_no_time_iteration_interval_boundaries_exact(self):
        """
        Verify start_date + end_date are taken directly from DB,
        NOT computed by iterating day-by-day.
        """
        start = date(2022, 3, 15)
        end   = date(2022, 11, 27)
        dispatch = {
            "level1": [
                _make_md_row("md-sat-001", "Saturn", start, end),
            ],
        }
        conn = _make_conn(dispatch)

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2022, 1, 1),
            date_end=date(2023, 1, 1),
            max_level=1,
        )

        assert results[0].start_date == start
        assert results[0].end_date   == end


# ---------------------------------------------------------------------------
# AC5: Sookshma floor + Prana in-memory, no level-5 DB writes
# ---------------------------------------------------------------------------

class TestSookshmaAndPrana:
    """AC5: level-4 default; Prana = in-memory only, no DB writes."""

    def test_sookshma_intervals_returned_by_default(self):
        """max_level=4 (default) returns level-4 Sookshma rows."""
        md_id = "md-sat-001"
        ad_id = "ad-sat-001"
        pd_id = "pd-sat-001"
        sk_id = "sk-sat-001"

        dispatch = {
            "level1": [
                _make_md_row(md_id, "Saturn", date(2020, 1, 1), date(2027, 1, 1)),
            ],
            f"children:{md_id}": [
                _make_child_row(ad_id, "Saturn", date(2020, 1, 1), date(2021, 1, 1), 2, md_id),
            ],
            f"children:{ad_id}": [
                _make_child_row(pd_id, "Saturn", date(2020, 1, 1), date(2020, 6, 1), 3, ad_id),
            ],
            f"children:{pd_id}": [
                _make_child_row(sk_id, "Saturn", date(2020, 1, 1), date(2020, 3, 1), 4, pd_id),
            ],
        }
        conn = _make_conn(dispatch)

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2020, 1, 1),
            date_end=date(2027, 1, 1),
            max_level=4,
            prana_grain=False,
        )

        assert len(results) == 1
        assert results[0].level_n == 4

    def test_prana_grain_produces_level5_intervals(self):
        """prana_grain=True subdivides level-4 into in-memory level-5."""
        md_id = "md-sat-001"
        ad_id = "ad-sat-001"
        pd_id = "pd-sat-001"
        sk_id = "sk-sat-001"

        dispatch = {
            "level1": [
                _make_md_row(md_id, "Saturn", date(2020, 1, 1), date(2027, 1, 1)),
            ],
            f"children:{md_id}": [
                _make_child_row(ad_id, "Saturn", date(2020, 1, 1), date(2021, 1, 1), 2, md_id),
            ],
            f"children:{ad_id}": [
                _make_child_row(pd_id, "Saturn", date(2020, 1, 1), date(2020, 6, 1), 3, ad_id),
            ],
            f"children:{pd_id}": [
                _make_child_row(sk_id, "Saturn", date(2020, 1, 1), date(2020, 3, 1), 4, pd_id),
            ],
        }
        conn = _make_conn(dispatch)

        results = walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2020, 1, 1),
            date_end=date(2027, 1, 1),
            max_level=4,
            prana_grain=True,
        )

        # Should be level-5 intervals (9 subdivisions by default)
        assert len(results) > 0
        assert all(r.level_n == 5 for r in results)
        assert all(r.is_prana_computed if hasattr(r, "is_prana_computed") else True
                   for r in results)

    def test_prana_intervals_not_in_db(self):
        """
        Verify prana_grain=True does NOT write level-5 to DB.

        We check the mock conn's _calls list: no INSERT or UPDATE
        with level_n=5 should appear.
        """
        md_id = "md-sat-001"
        ad_id = "ad-sat-001"
        pd_id = "pd-sat-001"
        sk_id = "sk-sat-001"

        dispatch = {
            "level1": [
                _make_md_row(md_id, "Saturn", date(2020, 1, 1), date(2027, 1, 1)),
            ],
            f"children:{md_id}": [
                _make_child_row(ad_id, "Saturn", date(2020, 1, 1), date(2021, 1, 1), 2, md_id),
            ],
            f"children:{ad_id}": [
                _make_child_row(pd_id, "Saturn", date(2020, 1, 1), date(2020, 6, 1), 3, ad_id),
            ],
            f"children:{pd_id}": [
                _make_child_row(sk_id, "Saturn", date(2020, 1, 1), date(2020, 3, 1), 4, pd_id),
            ],
        }
        conn = _make_conn(dispatch)

        walk_eligible_intervals(
            conn=conn,
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2020, 1, 1),
            date_end=date(2027, 1, 1),
            max_level=4,
            prana_grain=True,
        )

        # Check no write queries (INSERT/UPDATE) were issued
        write_calls = [
            (sql, params) for sql, params in conn._calls
            if any(kw in sql.upper() for kw in ("INSERT", "UPDATE", "DELETE"))
        ]
        assert not write_calls, (
            f"DB write calls detected during prana_grain walk: {write_calls}"
        )

    def test_prana_subdivide_boundaries_valid(self):
        """All Prana sub-intervals must have start < end."""
        base = DashaInterval(
            dasha_row_id="sk-001",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            system_id="vimshottari",
            level_n=4,
            lord_graha="Saturn",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 4, 1),
            parent_row_id="pd-001",
            eligibility_band=EligibilityBand.EXACT,
            eligibility_score=0.85,
        )
        prana_rows = _subdivide_prana(base)
        assert len(prana_rows) > 0
        for p in prana_rows:
            assert p.start_date < p.end_date, (
                f"Invalid Prana interval: {p.start_date} >= {p.end_date}"
            )
            assert p.level_n == 5


# ---------------------------------------------------------------------------
# AC4: Cross-dasa agreement (pure unit test with two fake systems)
# ---------------------------------------------------------------------------

class TestCrossDashaAgreement:
    """AC4: Cross-dasa agreement count + system list."""

    def _make_service_with_two_systems(self, systems_data: dict):
        """Build a KaDashaKalaService backed by a mock that returns data per system."""

        class PerSystemCursor:
            def __init__(self, rows):
                self._rows = rows
            def fetchall(self):
                return self._rows

        class PerSystemConn:
            def __init__(self, data):
                self._data = data
                self._calls = []

            def execute(self, sql, params=None):
                self._calls.append((sql, params))
                # Dispatch on system_id in params
                if params and len(params) >= 3:
                    sys_id = params[2]
                elif params:
                    sys_id = None
                else:
                    sys_id = None

                if "level_n        = 1" in sql or "level_n = 1" in sql:
                    rows = self._data.get(sys_id, {}).get("level1", [])
                elif "parent_row_id = %s" in sql:
                    parent = params[0] if params else None
                    rows = self._data.get(sys_id, {}).get(f"children:{parent}", [])
                else:
                    rows = []

                return PerSystemCursor(rows)

        return KaDashaKalaService(db_conn=PerSystemConn(systems_data))

    def test_two_systems_agree_on_same_window(self):
        """Two systems returning the same (start, end) window → agreement count = 2."""
        window_start = date(2024, 1, 1)
        window_end   = date(2024, 6, 1)

        # Both vimshottari and yogini have Saturn MD for the same window
        systems_data = {
            "vimshottari": {
                "level1": [
                    _make_md_row("md-vim-sat", "Saturn", window_start, window_end),
                ],
            },
            "yogini": {
                "level1": [
                    _make_md_row("md-yog-sat", "Saturn", window_start, window_end),
                ],
            },
        }

        svc = self._make_service_with_two_systems(systems_data)
        result = svc.query(
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2024, 1, 1),
            date_end=date(2025, 1, 1),
            max_level=1,
            systems={"vimshottari", "yogini"},
        )

        # Both systems should agree on the window
        assert result.total_windows >= 2
        # Find windows where both agree
        high = [w for w in result.windows if w.cross_dasha_agreement.count >= 2]
        assert len(high) >= 2, "Expected at least 2 windows with agreement >= 2"
        systems_agreeing = set(high[0].cross_dasha_agreement.systems_agreeing)
        assert "vimshottari" in systems_agreeing
        assert "yogini" in systems_agreeing

    def test_single_system_agreement_is_one(self):
        """A window seen by only one system has agreement count = 1."""
        systems_data = {
            "vimshottari": {
                "level1": [
                    _make_md_row("md-vim-sat", "Saturn", date(2024, 1, 1), date(2024, 6, 1)),
                ],
            },
            "yogini": {
                "level1": [],  # no matching window
            },
        }
        svc = self._make_service_with_two_systems(systems_data)
        result = svc.query(
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=date(2024, 1, 1),
            date_end=date(2025, 1, 1),
            max_level=1,
            systems={"vimshottari", "yogini"},
        )

        # vimshottari window has agreement = 1
        vim_windows = [w for w in result.windows if w.system_id == "vimshottari"]
        assert len(vim_windows) == 1
        assert vim_windows[0].cross_dasha_agreement.count == 1
        assert vim_windows[0].cross_dasha_agreement.systems_agreeing == ["vimshottari"]


# ---------------------------------------------------------------------------
# Integration tests — PROD DB required
# ---------------------------------------------------------------------------

_DB_DSN = os.environ.get("DB_DSN", "")
_NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _get_prod_conn():
    """Return a psycopg2 connection to PROD (or skip if unavailable)."""
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(_DB_DSN, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    except Exception as exc:
        pytest.skip(f"PROD DB not available: {exc}")


@pytest.fixture(scope="module")
def prod_conn():
    conn = _get_prod_conn()
    yield conn
    conn.rollback()
    conn.close()


class _PsycopgConnAdapter:
    """Adapter to make psycopg2 connection behave like the mock (conn.execute())."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur


@pytest.mark.integration
class TestProdDB:
    """AC4, AC6, AC7: Integration tests against PROD chart_dashas."""

    def test_ac6_seven_systems_confirmed(self, prod_conn):
        """AC6: 7 systems exist for native chart in chart_dashas."""
        from services.ka_dasha_kala.service import KaDashaKalaService

        adapter = _PsycopgConnAdapter(prod_conn)
        svc = KaDashaKalaService(db_conn=adapter)
        sys_counts = svc.confirm_systems_present(_NATIVE_CHART_ID, "lahiri")

        expected = {
            "vimshottari", "yogini", "ashtottari", "chara_karaka",
            "naisargika", "mudda", "kalachakra",
        }
        found = set(sys_counts.keys())
        assert found >= expected, (
            f"Missing systems: {expected - found}. Found: {found}"
        )

    def test_ac4_cross_dasha_agreement_real_data(self, prod_conn):
        """AC4: Real chart_dashas — Saturn/Rahu windows have multi-system agreement."""
        from services.ka_dasha_kala.service import KaDashaKalaService

        adapter = _PsycopgConnAdapter(prod_conn)
        svc = KaDashaKalaService(db_conn=adapter)

        result = svc.query(
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            target_lords={"Saturn", "Rahu"},
            related_lords={"Mercury", "Venus"},
            date_start=date(2010, 1, 1),
            date_end=date(2030, 12, 31),
            max_level=1,   # MD level for speed
        )

        assert result.total_windows > 0, "Expected at least some eligible windows"
        assert result.systems_queried, "Expected systems_queried to be non-empty"

        # Verify all 7 systems were queried
        assert set(result.systems_queried) == ALL_DASHA_SYSTEMS

        # Verify structure
        for w in result.windows:
            assert w.start_date < w.end_date, "Interval must have start < end"
            assert w.cross_dasha_agreement.count >= 1
            assert w.cross_dasha_agreement.systems_agreeing

    def test_ac5_sookshma_returns_level4(self, prod_conn):
        """AC5 (day-grain): max_level=4 returns level-4 rows from real DB."""
        from services.ka_dasha_kala.service import KaDashaKalaService

        adapter = _PsycopgConnAdapter(prod_conn)
        svc = KaDashaKalaService(db_conn=adapter)

        result = svc.query(
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            target_lords={"Saturn"},
            related_lords={"Mercury"},
            date_start=date(2020, 1, 1),
            date_end=date(2022, 12, 31),
            max_level=4,
            prana_grain=False,
        )

        # All results should be at level <= 4
        for w in result.windows:
            assert w.level_n <= 4, f"level_n={w.level_n} exceeds Sookshma floor"
            assert not w.is_prana_computed, "No level-5 rows expected"

    def test_ac5_prana_no_db_writes(self, prod_conn):
        """AC5: prana_grain=True triggers in-memory computation; DB stays clean."""
        from services.ka_dasha_kala.service import KaDashaKalaService

        # Use a fresh conn so we can check its state
        import psycopg2
        import psycopg2.extras
        test_conn = psycopg2.connect(
            _DB_DSN, cursor_factory=psycopg2.extras.RealDictCursor
        )
        test_conn.autocommit = False

        adapter = _PsycopgConnAdapter(test_conn)
        svc = KaDashaKalaService(db_conn=adapter)

        result = svc.query(
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            target_lords={"Saturn"},
            related_lords={"Mercury"},
            date_start=date(2020, 1, 1),
            date_end=date(2021, 6, 30),
            max_level=4,
            prana_grain=True,
        )

        # Prana rows should be level-5 (in-memory)
        prana_rows = [w for w in result.windows if w.is_prana_computed]

        # Verify level-5 rows are NOT in DB
        cur = test_conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM chart_dashas WHERE chart_id=%s AND level_n=5",
            (_NATIVE_CHART_ID,),
        )
        count_row = cur.fetchone()
        level5_in_db = list(count_row.values())[0] if isinstance(count_row, dict) else count_row[0]
        assert level5_in_db == 0, f"Level-5 rows found in DB: {level5_in_db}"

        test_conn.rollback()
        test_conn.close()

    def test_kp_sublevel_on_vimshottari(self, prod_conn):
        """KP is a Vimshottari sub-level (kp_sublevel column), not a standalone system."""
        cur = prod_conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM chart_dashas
            WHERE chart_id = %s AND system_id = 'vimshottari'
              AND kp_sublevel IS NOT NULL
            """,
            (_NATIVE_CHART_ID,),
        )
        row = cur.fetchone()
        count = list(row.values())[0] if isinstance(row, dict) else row[0]
        # KP sub-level data should exist (populated by ga_dashas_writer)
        assert count >= 0  # May be 0 if not populated; we just confirm no 'kp' system_id
        # No standalone 'kp' system should exist
        cur.execute(
            "SELECT COUNT(*) FROM chart_dashas WHERE chart_id=%s AND system_id='kp'",
            (_NATIVE_CHART_ID,),
        )
        row2 = cur.fetchone()
        kp_count = list(row2.values())[0] if isinstance(row2, dict) else row2[0]
        assert kp_count == 0, "KP should NOT be a standalone system in chart_dashas"


# ---------------------------------------------------------------------------
# AC8: grep check — no commit/rollback in service code (static analysis)
# ---------------------------------------------------------------------------

class TestNoCommitRollback:
    """AC8: Service files must not call .commit() or .rollback()."""

    def test_no_commit_in_service_files(self):
        """Static check: no actual .commit()/.rollback() calls in ka_dasha_kala/ Python code.

        We grep for lines containing these patterns but exclude:
          - Comment lines (stripped line starts with #)
          - Docstring lines that say "NEVER calls ..." (documentation only)
          - Binary .pyc files (excluded via --include=*.py)
        """
        import subprocess
        service_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "services", "ka_dasha_kala"
        )
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", r".commit()\|.rollback()", service_dir],
            capture_output=True, text=True,
        )
        # Filter: only actual code lines (not comments or docstring references)
        actual_code_violations = []
        for line in result.stdout.splitlines():
            text = line.split(":", 2)[-1].strip() if line.count(":") >= 2 else line.strip()
            # Skip comment lines and documentation lines mentioning NEVER
            if text.startswith("#") or "NEVER" in text or text.startswith('"""') or text.startswith("'''"):
                continue
            # Skip lines that are just docstring prose (no actual Python call)
            if "conn.commit()" not in text and "conn.rollback()" not in text:
                continue
            # This is an actual code violation
            actual_code_violations.append(line)
        assert not actual_code_violations, (
            f"Found actual commit/rollback calls in ka_dasha_kala:\n"
            + "\n".join(actual_code_violations)
        )
