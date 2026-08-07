"""
tests/test_taranga_missing_valence.py — Regression guard for Fix 3:
taranga_service._load_leverage_and_valence missing-valence → benefic default.

TDD: tests written BEFORE the fix.

The bug (taranga_service.py lines ~262-267):

    sign = 1.0                      # <-- default is positive (benefic)
    v = graha_valence.get(subj)
    if v is not None and v < 0:
        sign = -1.0
    signed[subj] = magnitude * sign

When graha_valence has no entry for a subject (e.g. no valence_pass rows for
that graha), sign stays 1.0 (benefic). The signed domain weight is therefore
always positive for unknown grahas, regardless of their actual classical nature.

The fix: when valence is missing, the sign is None (unknown) — the domain weight
should be emitted as 0.0 (no-signal / absent weight) rather than defaulting to
a positive/benefic assumption that silently biases the activation formula.

Specifically: _load_leverage_and_valence's `signed` dict must NOT include a
graha for which the valence is unknown (None). That graha should be absent from
the returned domain_weights for that domain, so the activation formula sees
zero contribution from it rather than an invented benefic contribution.
"""
from __future__ import annotations

import sys
from collections import namedtuple
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_FakeColumn = namedtuple("_FakeColumn", ["name"])

SIDECAR = Path(__file__).parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services import taranga_service as svc  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_cache():
    svc.clear_substrate_cache()
    yield
    svc.clear_substrate_cache()


# ── Minimal mock DB helpers ───────────────────────────────────────────────────

class _FakeCursor:
    def __init__(self, tables):
        self._tables = tables
        self._current_cols = []
        self._current_rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        sql_norm = " ".join(sql.split())
        for marker, (cols, rows) in self._tables.items():
            if marker in sql_norm:
                self._current_cols = cols
                self._current_rows = rows
                return
        self._current_cols = []
        self._current_rows = []

    @property
    def description(self):
        return [_FakeColumn(name=c) for c in self._current_cols]

    def fetchall(self):
        return list(self._current_rows)

    def fetchone(self):
        return self._current_rows[0] if self._current_rows else None


class _FakeConn:
    def __init__(self, tables):
        self._tables = tables

    def cursor(self):
        return _FakeCursor(self._tables)

    def commit(self):
        pass

    def close(self):
        pass


def _make_tables_with_missing_valence():
    """
    A chart substrate where:
      - SUN has a leverage_index for 'wealth' domain (magnitude 1.5) and a valence_pass row (positive)
      - MAR has a leverage_index for 'wealth' domain (magnitude 2.0) but NO valence_pass row

    After the fix: MAR's domain weight for 'wealth' must NOT be present (or must be 0.0)
    because we cannot know its sign without a valence row.

    Before the fix: MAR gets sign=1.0 (benefic default) → weight=+2.0 (wrong).
    """
    return {
        "fact_category = 'graha_position'": (
            ["fact_subject", "fact_value_num"],
            [("SUN", 10.0), ("MAR", 200.0)],
        ),
        "FROM chart_dashas": (
            ["lord_graha", "start_date", "end_date"],
            [("Sun", datetime(1984, 2, 5, tzinfo=timezone.utc), datetime(2100, 2, 5, tzinfo=timezone.utc))],
        ),
        "FROM chart_vichara": (
            ["vichara_family", "subject", "actor", "domain", "varga_id", "value_num"],
            [
                # SUN: has both leverage_index and valence_pass
                ("leverage_index", "SUN", None, "wealth", None, 1.5),
                ("valence_pass",   "SUN", "SUN", None, "D1",  0.6),
                # MAR: has leverage_index but NO valence_pass row → valence unknown
                ("leverage_index", "MAR", None, "wealth", None, 2.0),
                # (no valence_pass for MAR)
            ],
        ),
        "FROM bodha_mechanisms": (
            ["mechanism_id", "mechanism_name", "mechanism_class", "valence",
             "member_node_ids_array", "edge_strength_avg", "domains_affected_array",
             "centrality_summary_jsonb"],
            [],
        ),
        "FROM bodha_cgm_nodes": (
            ["node_id", "node_subject", "node_type"],
            [],
        ),
        "fact_category = 'ashtakavarga_bindu_sign'": (
            ["fact_subject", "fact_value_num"],
            [],
        ),
    }


_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_CHART_REF = svc.ChartRef(chart_id=_CHART_ID)


def test_missing_valence_graha_not_treated_as_benefic():
    """
    MAR has a leverage_index row but no valence_pass row.
    After the fix, MAR must NOT appear in domain_weights['wealth'] with a positive
    (benefic) signed weight — that would be an invented assumption.
    """
    conn = _FakeConn(_make_tables_with_missing_valence())
    substrate = svc.build_chart_substrate(_CHART_REF, conn=conn)

    wealth_weights = substrate.domain_weights.get("wealth", {})

    # MAR's signed weight must NOT be positive (benefic default)
    mar_weight = wealth_weights.get("MAR")
    assert mar_weight is None or mar_weight == 0.0, (
        f"MAR has no valence_pass row — its domain weight must be absent or 0.0, "
        f"not a benefic default. Got: MAR weight = {mar_weight}. "
        "The old code defaulted sign=1.0 (benefic) when valence was missing."
    )


def test_known_valence_graha_is_still_signed_correctly():
    """
    SUN has a positive valence_pass row (0.6) → its weight must be positive.
    The fix must not break correctly-known grahas.
    """
    conn = _FakeConn(_make_tables_with_missing_valence())
    substrate = svc.build_chart_substrate(_CHART_REF, conn=conn)

    wealth_weights = substrate.domain_weights.get("wealth", {})
    sun_weight = wealth_weights.get("SUN")

    assert sun_weight is not None, "SUN has a leverage_index + valence_pass row — must be present"
    assert sun_weight > 0, (
        f"SUN has positive valence (0.6) → signed weight must be positive; got {sun_weight}"
    )


def test_negative_valence_graha_produces_negative_weight():
    """
    A graha with a negative valence_pass must produce a negative signed weight.
    Regression guard: the fix must not break the existing malefic-sign path.
    """
    tables = {
        "fact_category = 'graha_position'": (
            ["fact_subject", "fact_value_num"],
            [("SAT", 280.0)],
        ),
        "FROM chart_dashas": (
            ["lord_graha", "start_date", "end_date"],
            [("Saturn", datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2019, 1, 1, tzinfo=timezone.utc))],
        ),
        "FROM chart_vichara": (
            ["vichara_family", "subject", "actor", "domain", "varga_id", "value_num"],
            [
                ("leverage_index", "SAT", None, "health", None, 1.2),
                ("valence_pass",   "SAT", "SAT", None, "D1",  -0.7),  # malefic
            ],
        ),
        "FROM bodha_mechanisms": (
            ["mechanism_id", "mechanism_name", "mechanism_class", "valence",
             "member_node_ids_array", "edge_strength_avg", "domains_affected_array",
             "centrality_summary_jsonb"],
            [],
        ),
        "FROM bodha_cgm_nodes": (["node_id", "node_subject", "node_type"], []),
        "fact_category = 'ashtakavarga_bindu_sign'": (["fact_subject", "fact_value_num"], []),
    }
    conn = _FakeConn(tables)
    chart = svc.ChartRef(chart_id=_CHART_ID)
    substrate = svc.build_chart_substrate(chart, conn=conn)

    health_weights = substrate.domain_weights.get("health", {})
    sat_weight = health_weights.get("SAT")
    assert sat_weight is not None, "SAT has leverage_index + valence_pass → must be present"
    assert sat_weight < 0, (
        f"SAT has negative valence (-0.7) → signed weight must be negative; got {sat_weight}"
    )
