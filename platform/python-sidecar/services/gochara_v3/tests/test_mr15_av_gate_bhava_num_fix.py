"""
tests/test_mr15_av_gate_bhava_num_fix.py — PARIṢKĀRA MR-15.

GAP (MASTER_REMEDIATION_REGISTER MR-15 / PG-22, recon L266): Ashtakavarga (AV)
gating is described as a flagship gochara_v3 mechanism, but it was silently
degraded during the only production build that has ever run.
``gochara_v3.context._fetch_all_av_gate_rows`` queried ``bg_transit_av_gates``
using a column, ``bhava_num``, that has NEVER existed on that table — the
live column (migration 397_bg_transit_av_gates.sql, confirmed live against
``information_schema.columns`` on the production DB, 2026-08-11) is
``house_from_moon``. The resulting ``UndefinedColumn`` error was caught and
logged at INFO — a level no operator watches — then silently degraded to an
honest-*looking* empty ``av_gate_rows`` tuple. Every downstream consumer
(``w21_av_gating`` mechanism, ``_check_av_threshold_from_context`` in
engine.py) treats an empty ``av_gate_rows`` as "no AV data for this chart"
(the honest-null branch), which is indistinguishable from "the query is
silently broken" — so AV gating ran fully disabled with zero visible signal
in the writer's build report.

Fix verified in this file:
  1. The query now reads ``house_from_moon`` (the real live column).
  2. Any AV-gate fetch failure now logs at ERROR (not INFO) and is surfaced
     via ``ClassContext.av_gate_fetch_error`` so a calling writer (see
     ``pipeline/orchestrator/writers/tests/test_mr15_av_gate_loud_failure.py``)
     can fold it into ``WriterResult.notes`` — build-report visible, not just
     a log line.

TDD discipline (PARIṢKĀRA campaign standing rule): every test in this file is
RED against the pre-fix ``context.py`` (bhava_num query, INFO-level swallow,
no ``av_gate_fetch_error`` field) and GREEN after the fix commit.
"""
from __future__ import annotations

import inspect
import logging
import os
from typing import Optional

import pytest

from services.gochara_grammar.models import ResonanceTarget
from services.gochara_v3 import context as context_mod
from services.gochara_v3.context import ClassContext, _fetch_all_av_gate_rows

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
LIVE_DSN = os.environ.get("DATABASE_URL", "")


# ── Fixtures ─────────────────────────────────────────────────────────────


def _mk_bhava_target(target_ref: str) -> ResonanceTarget:
    return ResonanceTarget(
        chart_id=CHART_ID,
        event_class="career_advancement",
        target_type="bhava",
        target_ref=target_ref,
        weight=1.0,
        uncited_extension=True,  # fixture target — no classical citation needed
    )


class _UndefinedColumn(Exception):
    """Stand-in for psycopg.errors.UndefinedColumn — same message shape this
    lane reproduced live against production (see PR description):
    'column "bhava_num" does not exist'."""


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeAVGateConn:
    """Minimal DB-API-shaped fake standing in for bg_transit_av_gates.

    Recognizes ONLY the column that actually exists on the live table
    (``house_from_moon``, migration 397) — a query naming any other column
    raises, exactly as Postgres does for a genuinely nonexistent column.
    This makes the fake a faithful reproduction of the live bug: it is NOT
    hardcoded to "reject bhava_num specifically", it rejects anything that
    isn't the real column, so it would also fail-loud against a
    *different* wrong column name.
    """

    REAL_COLUMN = "house_from_moon"

    def __init__(self, seed_rows: list[dict], *, always_fail: bool = False):
        self._seed_rows = seed_rows
        self._always_fail = always_fail
        self.autocommit = False

    def execute(self, sql: str, params: Optional[list] = None):
        stripped = sql.strip().upper()
        if stripped.startswith(("SAVEPOINT", "RELEASE SAVEPOINT", "ROLLBACK")):
            return _FakeCursor([])
        if self._always_fail:
            raise RuntimeError("simulated DB outage (AV gate fetch)")
        if self.REAL_COLUMN not in sql:
            raise _UndefinedColumn(
                f'column "bhava_num" does not exist'
                if "bhava_num" in sql
                else f"query does not reference {self.REAL_COLUMN}"
            )
        bhava_refs = params[0] if params else []
        rows = [r for r in self._seed_rows if r["target_ref"] in bhava_refs]
        return _FakeCursor(rows)


_SEED_ROWS = [
    {
        "target_ref": "2",
        "graha": "Jupiter",
        "min_sav_score": 28,
        "effect": "SAV >=28 in 2H",
        "classical_citation": "BPHS ch.66-68",
    },
    {
        "target_ref": "1",
        "graha": "Saturn",
        "min_sav_score": 28,
        "effect": "SAV >=28 in 1H",
        "classical_citation": "BPHS ch.66-68 SAV bindhu thresholds",
    },
]


# ── 1. Static regression guard: the query must not name bhava_num ─────────


def test_av_gate_query_does_not_reference_bhava_num():
    """Regression guard: bg_transit_av_gates has never had a bhava_num
    column (migration 397 — house_from_moon is the real column). If this
    ever fails again, the MR-15 defect has been reintroduced.

    The function's own docstring legitimately names the bare word
    'bhava_num' for documentation (explaining the historical MR-15 defect)
    — the invariant is about the EXECUTABLE SQL, not the prose, so this
    checks the SQL-specific token (`bhava_num::text`, the exact cast used
    in the query) rather than the bare word."""
    source = inspect.getsource(context_mod._fetch_all_av_gate_rows)
    assert "bhava_num::text" not in source, (
        "_fetch_all_av_gate_rows still references the nonexistent "
        "bhava_num column in its executable query — MR-15 regression."
    )
    assert "house_from_moon::text" in source, (
        "_fetch_all_av_gate_rows must query the real live column, "
        "house_from_moon (migration 397_bg_transit_av_gates.sql)."
    )


# ── 2. Behavioural: the fixed query actually returns real rows ────────────


def test_fetch_all_av_gate_rows_returns_real_rows_once_column_is_correct():
    """With the real column name, matching bhava targets get real AV gate
    rows back — not a silently-empty honest-null."""
    conn = _FakeAVGateConn(seed_rows=_SEED_ROWS)
    targets = [_mk_bhava_target("1"), _mk_bhava_target("2"), _mk_bhava_target("9")]

    rows, error = _fetch_all_av_gate_rows(conn, targets)

    assert error is None, f"Expected no error, got {error!r}"
    assert len(rows) == 2, f"Expected 2 matching AV gate rows, got {len(rows)}: {rows}"
    grahas = {r.graha for r in rows}
    assert grahas == {"Jupiter", "Saturn"}


# ── 3. Loud-failure: any AV-gate fetch failure logs ERROR + is surfaced ───


def test_fetch_all_av_gate_rows_failure_logs_error_not_info(caplog):
    """A DB failure fetching AV gate rows must be visible at ERROR level —
    not silently swallowed at INFO (the original MR-15 defect)."""
    conn = _FakeAVGateConn(seed_rows=[], always_fail=True)
    targets = [_mk_bhava_target("1")]

    with caplog.at_level(logging.DEBUG, logger=context_mod.__name__):
        rows, error = _fetch_all_av_gate_rows(conn, targets)

    assert rows == [], "A failed fetch must degrade to zero rows, never fabricate data"
    assert error, "A failed fetch must return a non-empty error message, not a silent None"

    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert error_records, (
        "Expected at least one ERROR-level log record for the AV-gate fetch "
        f"failure — got levels {[r.levelname for r in caplog.records]}"
    )
    info_records_mentioning_failure = [
        r for r in caplog.records
        if r.levelno == logging.INFO and "av_gate" in r.message.lower()
    ]
    assert not info_records_mentioning_failure, (
        "AV-gate fetch failure must not be logged at INFO — an operator "
        "watching build logs would never see it (the original MR-15 defect)."
    )


def test_fetch_all_av_gate_rows_column_mismatch_would_also_be_loud(caplog):
    """Sanity check that the CURRENT (post-fix) query, if it somehow
    regressed to a wrong column again, would fail loud through this same
    path — proving the loud-failure plumbing is column-agnostic, not special
    cased to the literal string 'bhava_num'."""
    conn = _FakeAVGateConn(seed_rows=_SEED_ROWS)
    # Monkeypatch the fake's REAL_COLUMN to simulate the query drifting to
    # some other wrong column — the fake must still reject it and the
    # function must still surface a loud error.
    conn.REAL_COLUMN = "some_other_column_the_query_does_not_use"
    targets = [_mk_bhava_target("1")]

    with caplog.at_level(logging.DEBUG, logger=context_mod.__name__):
        rows, error = _fetch_all_av_gate_rows(conn, targets)

    assert rows == []
    assert error
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


# ── 4. ClassContext carries the error field ────────────────────────────────


def test_class_context_has_av_gate_fetch_error_field():
    """ClassContext must expose av_gate_fetch_error so a calling writer can
    fold a degraded AV fetch into its WriterResult.notes (build-report
    visible, per CLAUDE.md §N.8 Earned-Signal Principle)."""
    ctx = ClassContext(
        chart_id=CHART_ID,
        event_class="career_advancement",
        resonance_targets=(),
        promise=0.0,
        promise_detail={},
        dasha_periods=(),
        relevant_grahas=frozenset(),
        relevant_signs=frozenset(),
        temporal_shape="undefined",
        valence="neutral",
        is_adverse=False,
        beta_e=1.0,
        av_gate_fetch_error="column \"bhava_num\" does not exist",
    )
    assert ctx.av_gate_fetch_error == 'column "bhava_num" does not exist'


def test_class_context_av_gate_fetch_error_defaults_to_none():
    """When nothing went wrong, the field must default to None (never a
    falsy-but-truthy placeholder like an empty string)."""
    ctx = ClassContext(
        chart_id=CHART_ID,
        event_class="career_advancement",
        resonance_targets=(),
        promise=0.0,
        promise_detail={},
        dasha_periods=(),
        relevant_grahas=frozenset(),
        relevant_signs=frozenset(),
        temporal_shape="undefined",
        valence="neutral",
        is_adverse=False,
        beta_e=1.0,
    )
    assert ctx.av_gate_fetch_error is None


# ── 5. Live, read-only proof against production (execute-to-verify) ───────
# Excluded by the mandated `-m "not integration"` CI invocation (same
# convention as test_cr131_gochara_db_reachability.py / test_gochara_intensity.py).


def _live_conn_or_skip():
    import psycopg

    try:
        conn = psycopg.connect(LIVE_DSN, row_factory=psycopg.rows.dict_row, connect_timeout=2)
    except Exception:
        pytest.skip("live Cloud SQL proxy not reachable in this environment")
    return conn


@pytest.mark.integration
def test_live_bhava_num_column_does_not_exist_on_bg_transit_av_gates():
    """Reproduces the exact live error this lane found (read-only SELECT) —
    proves the OLD query really was broken against production, not just in
    theory."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur, pytest.raises(Exception) as exc_info:
            cur.execute(
                "SELECT bhava_num::text AS target_ref FROM bg_transit_av_gates "
                "WHERE gate_kind = 'sav_threshold' LIMIT 1"
            )
        assert "bhava_num" in str(exc_info.value)
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_live_house_from_moon_query_succeeds_and_matches_migration_397_seed():
    """Reproduces the FIXED query (read-only SELECT) against production and
    checks it returns the exact seed rows migration 397 inserted."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT house_from_moon::text AS target_ref, graha, min_sav_score "
                "FROM bg_transit_av_gates "
                "WHERE gate_kind = 'sav_threshold' "
                "AND house_from_moon::text = ANY(%s) "
                "ORDER BY graha, house_from_moon",
                (["1", "2", "5", "9", "11"],),
            )
            rows = cur.fetchall()
        assert rows, "Expected non-empty AV gate rows for houses 1/2/5/9/11 from moon"
        grahas = {r["graha"] for r in rows}
        assert grahas == {"Jupiter", "Saturn"}, f"Unexpected grahas: {grahas}"
    finally:
        conn.close()
