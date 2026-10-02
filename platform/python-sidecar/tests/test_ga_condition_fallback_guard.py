"""
test_ga_condition_fallback_guard.py -- X2 / I-29 (SS ruling N-62): a D1-fallback composite row on
a chart that HAS divisionals is a failure; the fallback is visible when it is legitimate.

The guard must be a REAL detector (CLAUDE.md N.8): it can fire (divisional rows present), it can
pass (genuinely none, table readable), and it can refuse to pass on an unprovable "none"
(row-level security active). These tests drive each branch, then drive the whole
`build_ga_condition_substep` to show the guard sits on the write path (nothing is written when it
fires) and that the stored row carries the visible flag + reason when the fallback is legitimate.

DB-free: a fake psycopg-shaped connection answers by SQL text.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_writer as w  # noqa: E402

CHART = "00000000-0000-0000-0000-00000000c0de"
AYA = "lahiri_chitrapaksha"


class _FakeCursor:
    def __init__(self, conn):
        self._c = conn
        self.rowcount = 1
        self._rows: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._c.calls.append((s, params))
        up = s.upper()
        if self._c.raise_on_divisional_count and "FROM CHART_DIVISIONALS" in up and "COUNT(*)" in up:
            raise RuntimeError("canceling statement due to statement timeout")
        if "COUNT(*)" in up and "FROM CHART_DIVISIONALS" in up:
            self._rows = [(self._c.divisional_rows,)]
        elif "ROW_SECURITY_ACTIVE" in up:
            self._rows = [(self._c.rls_active,)]
        elif up.startswith("SELECT EXISTS") and "FROM CHART_DIVISIONALS" in up:
            self._rows = [(self._c.table_visible_rows,)]
        elif up.startswith("INSERT INTO GA_CONDITION_COMPOSITE"):
            self._c.inserted.append(params)
            self._rows = []
        else:
            self._rows = []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _FakeConn:
    def __init__(self, divisional_rows=0, rls_active=False, raise_on_divisional_count=False,
                 table_visible_rows=False):
        self.divisional_rows = divisional_rows
        self.rls_active = rls_active
        # does ANY chart_divisionals row show up for this role (the registry clause (f) EXISTS probe)
        self.table_visible_rows = table_visible_rows
        self.raise_on_divisional_count = raise_on_divisional_count
        self.calls: list = []
        self.inserted: list = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    @property
    def wrote_composite(self) -> bool:
        return any(
            s.upper().startswith("DELETE FROM GA_CONDITION_COMPOSITE")
            or s.upper().startswith("INSERT INTO GA_CONDITION_COMPOSITE")
            for s, _ in self.calls
        )


# ── the guard function: every branch ──────────────────────────────────────────

def test_guard_raises_when_the_chart_has_divisional_rows():
    conn = _FakeConn(divisional_rows=58)
    with pytest.raises(w.VargaFallbackWithDivisionalsError) as ei:
        w.assert_fallback_legitimate(conn, CHART, AYA, "Saturn", None)
    assert "58 divisional row(s)" in str(ei.value)
    assert "X2" in str(ei.value)


def test_guard_passes_when_the_chart_genuinely_has_no_divisionals():
    conn = _FakeConn(divisional_rows=0, rls_active=False)
    assert w.assert_fallback_legitimate(conn, CHART, AYA, "Saturn", None) is None


def test_guard_refuses_an_empty_read_it_cannot_trust_rls_active():
    """The 2026-09-18 incident class: RLS on with no policy reads as empty to every non-owner."""
    conn = _FakeConn(divisional_rows=0, rls_active=True)
    with pytest.raises(w.VargaFallbackWithDivisionalsError) as ei:
        w.assert_fallback_legitimate(conn, CHART, AYA, "Saturn", None)
    assert "row-level security is ACTIVE" in str(ei.value)
    assert "no divisional row is visible" in str(ei.value)


def test_guard_passes_under_rls_when_other_divisional_rows_are_visible():
    """Registry clause (f): `NOT row_security_active OR EXISTS (a visible divisional row)` is the
    can-see case. RLS on, but the role reads other rows of the table: the empty read for this graha
    is a real empty, so the (legitimate) fallback is allowed."""
    conn = _FakeConn(divisional_rows=0, rls_active=True, table_visible_rows=True)
    assert w.assert_fallback_legitimate(conn, CHART, AYA, "Saturn", None) is None
    assert any("SELECT EXISTS" in s and "LIMIT 1" in s for s, _ in conn.calls)   # the probe really ran


def test_guard_still_raises_on_divisionals_even_when_rls_is_active_and_visible():
    conn = _FakeConn(divisional_rows=3, rls_active=True, table_visible_rows=True)
    with pytest.raises(w.VargaFallbackWithDivisionalsError):
        w.assert_fallback_legitimate(conn, CHART, AYA, "Saturn", None)


def test_blind_to_us_is_exactly_the_negation_of_clause_f():
    cases = [  # (rls_active, any_row_visible, blind)
        (False, False, False),   # no RLS: an empty table is genuinely empty
        (False, True,  False),
        (True,  True,  False),   # RLS but rows visible: the role can see the table
        (True,  False, True),    # RLS and nothing visible: the empty read proves nothing
    ]
    for rls, visible, blind in cases:
        conn = _FakeConn(rls_active=rls, table_visible_rows=visible)
        assert w.divisional_table_blind_to_us(conn) is blind, (rls, visible)


def test_guard_fails_closed_when_the_divisional_read_itself_fails():
    conn = _FakeConn(raise_on_divisional_count=True)
    with pytest.raises(RuntimeError):
        w.assert_fallback_legitimate(conn, CHART, AYA, "Saturn", None)


def test_guard_counts_only_the_categories_the_composite_reads_scoped_to_chart_aya_graha():
    conn = _FakeConn(divisional_rows=0)
    w.assert_fallback_legitimate(conn, CHART, AYA, "Mars", None)
    sql, params = next((s, p) for s, p in conn.calls if "COUNT(*)" in s.upper())
    assert "fact_category IN ('varga_position', 'varga_dignity')" in sql
    assert params == (CHART, AYA, "Mars")


# ── the guard on the WRITE PATH (build_ga_condition_substep) ──────────────────

def _wire_minimal_build(monkeypatch, *, spread):
    """One graha (Saturn, Libra 10 deg: exalted), no combustion; `_load_varga_dignity_spread`
    returns `spread` (None = the swallowed-failure / no-rows case)."""
    monkeypatch.setattr(w, "_load_dignity_ref", lambda conn: {})
    monkeypatch.setattr(w, "_load_combustion_orbs", lambda conn: {})
    monkeypatch.setattr(w, "_load_naisargika_friendships", lambda conn: {})
    monkeypatch.setattr(w, "_load_motion_thresholds", lambda conn: {})
    monkeypatch.setattr(
        w, "_load_graha_positions",
        lambda conn, chart_id, aya: [{
            "graha": "Saturn", "sign": "Libra", "degree_in_sign": 10.0,
            "longitude": 190.0, "house": 7, "is_retrograde": False,
        }],
    )
    monkeypatch.setattr(w, "_load_varga_dignity_spread", lambda conn, c, a, g: spread)
    monkeypatch.setattr(w, "_load_dasha_periods", lambda *a, **k: (None, None))
    monkeypatch.setattr(w, "_build_per_varga_avastha_rows", lambda *a, **k: [])
    monkeypatch.setattr(w, "_build_d1_avastha_rows", lambda *a, **k: [])


def test_build_raises_and_writes_nothing_when_fallback_would_be_used_on_a_chart_with_divisionals(monkeypatch):
    # the F-C8 class: divisional rows exist, but no usable composite came out (spread None here)
    _wire_minimal_build(monkeypatch, spread=None)
    conn = _FakeConn(divisional_rows=1305)
    with pytest.raises(w.VargaFallbackWithDivisionalsError):
        w.build_ga_condition_substep(CHART, "build-1", AYA, conn)
    assert conn.wrote_composite is False, "a refused fallback must not delete or insert any composite row"


def test_build_raises_when_divisionals_exist_but_every_label_is_unscorable(monkeypatch):
    """The exact F-C8 symptom: spread populated, composite NULL (labels the composite cannot score)."""
    _wire_minimal_build(monkeypatch, spread={"D9": {"sign": "Aries", "dignity": "NotAClassicalLabel"}})
    conn = _FakeConn(divisional_rows=1305)
    with pytest.raises(w.VargaFallbackWithDivisionalsError):
        w.build_ga_condition_substep(CHART, "build-1", AYA, conn)
    assert conn.wrote_composite is False


def test_build_with_a_usable_composite_never_consults_the_guard_and_flags_no_fallback(monkeypatch):
    _wire_minimal_build(monkeypatch, spread={"D9": {"sign": "Libra", "dignity": "Exalted"}})
    conn = _FakeConn(divisional_rows=1305)
    n = w.build_ga_condition_substep(CHART, "build-1", AYA, conn)
    assert n == 1
    assert not any("COUNT(*)" in s.upper() and "CHART_DIVISIONALS" in s.upper() for s, _ in conn.calls)
    breakdown = _stored_breakdown(conn)
    assert breakdown["varga_fallback_used"] is False
    assert "varga_fallback_reason" not in breakdown


def test_build_allows_and_marks_the_fallback_when_the_chart_genuinely_has_no_divisionals(monkeypatch):
    _wire_minimal_build(monkeypatch, spread=None)
    conn = _FakeConn(divisional_rows=0, rls_active=False)
    n = w.build_ga_condition_substep(CHART, "build-1", AYA, conn)
    assert n == 1
    breakdown = _stored_breakdown(conn)
    assert breakdown["varga_fallback_used"] is True
    assert breakdown["varga_fallback_reason"] == w.VARGA_FALLBACK_REASON_NO_DIVISIONALS


def test_build_refuses_a_fallback_when_the_empty_read_is_rls_blind(monkeypatch):
    _wire_minimal_build(monkeypatch, spread=None)
    conn = _FakeConn(divisional_rows=0, rls_active=True)
    with pytest.raises(w.VargaFallbackWithDivisionalsError):
        w.build_ga_condition_substep(CHART, "build-1", AYA, conn)
    assert conn.wrote_composite is False


def _stored_breakdown(conn: _FakeConn) -> dict:
    cols = [
        "chart_id", "build_id", "ayanamsha_id", "graha",
        "dignity_d1", "dignity_score_d1",
        "varga_dignity_spread", "varga_dignity_composite",
        "avastha_baladi", "avastha_jagradadi", "avastha_deeptaadi",
        "avastha_lajjitaadi", "avastha_sayanadi",
        "motion_state", "speed_degrees_per_day", "is_retrograde",
        "combustion_arc_from_sun", "is_combust", "is_deeply_combust",
        "naisargika_relation", "tatkalika_relation", "panchadha_relation",
        "graha_yuddha_with", "graha_yuddha_result",
        "condition_score", "condition_formula_version", "condition_score_breakdown",
        "peak_dasha_periods", "weak_dasha_periods",
        "computed_at",
    ]
    assert len(conn.inserted) == 1
    row = dict(zip(cols, conn.inserted[0]))
    return json.loads(row["condition_score_breakdown"])


# ── verifier side: the read-side detector of the same claim ───────────────────

class _VerifierCursor(_FakeCursor):
    def execute(self, sql, params=None):
        self._c.calls.append((" ".join(sql.split()), params))
        self._rows = list(self._c.violations)


class _VerifierConn(_FakeConn):
    def __init__(self, violations):
        super().__init__()
        self.violations = violations

    def cursor(self, row_factory=None):
        return _VerifierCursor(self)


def test_verifier_returns_the_violating_rows_and_scopes_by_chart_when_asked():
    rows = [(CHART, AYA, "Sun"), (CHART, AYA, "Moon")]
    conn = _VerifierConn(rows)
    assert w.fallback_integrity_violations(conn) == rows
    assert w.fallback_integrity_violations(conn, CHART) == rows
    sql_all, params_all = conn.calls[0]
    sql_one, params_one = conn.calls[1]
    assert params_all == () and "gc.chart_id = %s" not in sql_all
    assert params_one == (CHART,) and "gc.chart_id = %s" in sql_one
    # the detector measures the claim: the flag AND the existence of divisional rows
    for sql in (sql_all, sql_one):
        assert "varga_fallback_used" in sql
        assert "FROM chart_divisionals cd" in sql
        assert "cd.fact_category IN ('varga_position', 'varga_dignity')" in sql


def test_verifier_can_come_back_empty():
    assert w.fallback_integrity_violations(_VerifierConn([])) == []


def test_registry_clause_text_in_the_intent_document_matches_the_predicate_constant():
    """The intent document carries the registry clause for a LATER migration (not applied here);
    its predicate must be byte-identical to the one this verifier and the writer-side tests use."""
    doc = (
        pathlib.Path(__file__).resolve().parents[3]
        / "00_ARCHITECTURE/briefs/suvarna/exec/band_x2/BAND_X2_LANE_INTENT_v1_0.md"
    )
    assert doc.exists(), doc
    assert w.FALLBACK_VIOLATION_PREDICATE_SQL in doc.read_text(encoding="utf-8")
