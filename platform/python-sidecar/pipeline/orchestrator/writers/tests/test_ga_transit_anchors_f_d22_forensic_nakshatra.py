"""
F-D22 (L1_W2_DECIDE_v1_0.md §5.1): ga_transit_anchors' FORENSIC assertion used to check
Moon natal_sign == 'aquarius' for the canonical chart -- but Moon's nakshatra (Purva
Bhadrapada) straddles the Aquarius/Pisces sign boundary, so the sign varies legitimately
by ayanamsha (measured live: surya_siddhanta_classical correctly puts Moon in Pisces, the
other four ayanamshas in Aquarius, all five agreeing on nakshatra=Purva Bhadrapada). The old
assertion was build-fatal for a CORRECT value under one ayanamsha. Fixed to assert the true
ayanamsha-invariant anchor (nakshatra) instead.

NO DB required -- a fake psycopg-shaped connection/cursor records statements and returns
canned chart_facts rows.
"""
from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4]))

from pipeline.orchestrator.writers import ContextSpec, SubStep  # noqa: E402
from pipeline.orchestrator.writers.ga_transit_anchors import (  # noqa: E402
    CANONICAL_CHART_ID,
    GaTransitAnchorsWriter,
)

NON_CANONICAL_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


class _FakeSelectCursor:
    """Row-factory cursor for the SELECT (fact_subject, fact_key, fact_value_text, fact_value_num)."""

    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        return self

    def fetchall(self):
        return self._rows


class _FakePlainCursor:
    def __init__(self, statements):
        self._statements = statements

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._statements.append((sql, params))
        return self


class _FakeConn:
    def __init__(self, select_rows):
        self._select_rows = select_rows
        self.statements: list = []

    def cursor(self, row_factory=None):
        if row_factory is not None:
            return _FakeSelectCursor(self._select_rows)
        return _FakePlainCursor(self.statements)


def _rows_with(moon_sign: str, moon_nakshatra: str):
    """A minimal chart_facts row set: Moon sign + nakshatra + longitude, nothing else."""
    return [
        ("MOON", "sign", moon_sign, None),
        ("MOON", "nakshatra", moon_nakshatra, None),
        ("MOON", "longitude_sidereal", None, 328.5),
    ]


def _run(chart_id: str, rows) -> None:
    writer = GaTransitAnchorsWriter()
    conn = _FakeConn(rows)
    ctx = ContextSpec(
        asset_id="ga_transit_anchors",
        build_id="build-x",
        db_conn=conn,
        config={"chart_id": chart_id},
    )
    step = SubStep(key="ayanamsha_surya_siddhanta_classical")
    writer.run_substep(ctx, step)


def test_canonical_chart_passes_with_purva_bhadrapada_nakshatra_regardless_of_sign():
    """The real-world case this fix exists for: Moon in Pisces (surya_siddhanta_classical)
    but nakshatra=Purva Bhadrapada must NOT raise -- the old sign-based assertion would have."""
    _run(CANONICAL_CHART_ID, _rows_with(moon_sign="pisces", moon_nakshatra="Purva Bhadrapada"))


def test_canonical_chart_passes_with_aquarius_sign_too():
    """The other four ayanamshas' shape must keep working."""
    _run(CANONICAL_CHART_ID, _rows_with(moon_sign="aquarius", moon_nakshatra="Purva Bhadrapada"))


def test_canonical_chart_still_fails_closed_on_a_genuinely_wrong_nakshatra():
    """CAN-FAIL: the assertion must still catch a real corruption -- proves this isn't a
    disguised no-op that always passes now."""
    with pytest.raises(AssertionError, match="FORENSIC VIOLATION"):
        _run(CANONICAL_CHART_ID, _rows_with(moon_sign="aquarius", moon_nakshatra="Rohini"))


def test_canonical_chart_fails_closed_on_missing_nakshatra():
    with pytest.raises(AssertionError, match="FORENSIC VIOLATION"):
        _run(CANONICAL_CHART_ID, [
            ("MOON", "sign", "aquarius", None),
            ("MOON", "longitude_sidereal", None, 328.5),
        ])


def test_non_canonical_chart_never_asserts():
    """The FORENSIC gate is scoped to the canonical native chart only -- a different chart's
    Moon nakshatra must never be checked against Purva Bhadrapada."""
    _run(NON_CANONICAL_CHART_ID, _rows_with(moon_sign="taurus", moon_nakshatra="Rohini"))
