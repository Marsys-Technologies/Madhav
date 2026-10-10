"""SS N-412 items 5 and 6 (Lahiri-primary combined batch, PR-5): sade-sati read hardening.

  (5a) the ayanamsha id must travel compute_permission -> sade_sati_phase -> the SQL (pass-through);
  (5b) the sade-sati read needs a TOTAL order (CLAUDE.md N.7.2): ORDER BY ends in the unique `fact_id`;
  (6)  an empty sade-sati read for an ayanamsha is reported with an explicit `empty_reason` (N.6.4), never as a silent
       "not active"; a real read that simply is not inside a phase stays an honest, reason-less "not active".

DB-free: fake connections, primitives monkeypatched where they would need an ephemeris.
"""
from __future__ import annotations

import re

import pytest
import swisseph as swe

from services.gochara_grammar import primitives as P
from services.gochara_grammar.models import ResonanceTarget
from services.gochara_intensity import permission as PERM

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
LAHIRI = "lahiri_chitrapaksha"
T_JD = swe.julday(2026, 8, 4, 12.0)  # 2026-08-04 12:00 UT


def _target() -> ResonanceTarget:
    # no longitude / no sign: the point primitives that need geometry are not reached
    return ResonanceTarget(chart_id=CHART_ID, event_class="marriage", target_type="karaka",
                           target_ref="Venus", weight=0.5, classical_citation="TEST")


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Conn:
    """Records chart_facts queries; returns `rows_by_ayanamsha[params[1]]` (rows keyed per ayanamsha)."""

    def __init__(self, rows_by_ayanamsha):
        self.rows_by_ayanamsha = rows_by_ayanamsha
        self.queries: list[tuple[str, list]] = []
        self.autocommit = False

    def execute(self, sql, params=None):
        s = sql if isinstance(sql, str) else str(sql)
        if s.strip().startswith(("SAVEPOINT ", "RELEASE SAVEPOINT ", "ROLLBACK TO SAVEPOINT ")):
            return _Cur([])
        self.queries.append((s, list(params or [])))
        return _Cur(list(self.rows_by_ayanamsha.get((params or [None, None])[1], [])))

    def rollback(self):
        pass


def _phase_rows(start_iso: str, end_iso: str) -> list[dict]:
    base = {"fact_value_num": None, "citation_human": None}
    return [
        {"fact_subject": "cycle_1", "fact_key": "phase_start_iso", "fact_value_text": start_iso, **base},
        {"fact_subject": "cycle_1", "fact_key": "phase_end_iso", "fact_value_text": end_iso, **base},
        {"fact_subject": "cycle_1", "fact_key": "phase_name", "fact_value_text": "rising", **base},
    ]


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    P.clear_primitive_read_caches()
    # the point primitives need an ephemeris and are irrelevant here
    for name in ("drishti_contact", "degree_contact", "sign_occupation", "av_threshold_state", "planetary_return"):
        monkeypatch.setattr(P, name, lambda *a, **k: [])
    yield
    P.clear_primitive_read_caches()


def _sade_sati(detail: dict) -> dict:
    return next(s for s in detail["systems"] if s["system_id"] == "sade_sati")


# ── (5a) permission pass-through ───────────────────────────────────────────────────

def test_permission_passes_the_ayanamsha_id_to_the_sade_sati_read(monkeypatch):
    seen: list[str] = []
    real = P.sade_sati_phase

    def spy(chart_id, target, conn=None, fixture_phases=None, ayanamsha_id=LAHIRI):
        seen.append(ayanamsha_id)
        return real(chart_id, target, conn=conn, fixture_phases=fixture_phases, ayanamsha_id=ayanamsha_id)

    monkeypatch.setattr(P, "sade_sati_phase", spy)
    conn = _Conn({})
    PERM.compute_permission(swe, conn, CHART_ID, "marriage", [_target()], T_JD, dasha_periods=[], ayanamsha_id="raman")
    PERM.compute_permission(swe, conn, CHART_ID, "marriage", [_target()], T_JD, dasha_periods=[])
    assert seen == ["raman", LAHIRI], "the caller's id must reach the sade-sati read; omitted = the Lahiri primary"
    assert [q[1][1] for q in conn.queries] == ["raman", LAHIRI], "and the SQL is bound to that id"


# ── (5b) total ORDER BY ────────────────────────────────────────────────────────────────

def test_sade_sati_read_has_a_total_order_ending_in_the_unique_fact_id():
    conn = _Conn({LAHIRI: _phase_rows("2026-01-01T00:00:00+00:00", "2026-12-31T00:00:00+00:00")})
    P._fetch_sade_sati_rows(conn, CHART_ID, LAHIRI)
    sql = conn.queries[0][0]
    m = re.search(r"ORDER BY\s+(.+?)\s*$", " ".join(sql.split()), re.I)
    assert m, "the sade-sati read must carry an ORDER BY"
    terms = [t.strip() for t in m.group(1).split(",")]
    # (fact_subject, fact_key) repeats across sade_sati_cycle / sade_sati_phase and across rebuilt rows, so only the unique
    # fact_id (chart_facts.fact_id is UNIQUE NOT NULL) as the LAST term makes the order total (N.7.2: reproducible AND correct).
    assert terms[-1] == "fact_id", f"ORDER BY must end in the unique tiebreak fact_id, got {terms}"
    assert {"fact_subject", "fact_key"} <= set(terms)
    assert not re.search(r"\bLIMIT\b", sql, re.I) or terms[-1] == "fact_id"


# ── (6) explicit empty_reason ────────────────────────────────────────────────────────────

def test_empty_sade_sati_read_for_an_ayanamsha_has_an_explicit_empty_reason_not_a_silent_not_active():
    # facts exist for Lahiri only; the caller asks for raman -> the raman read is EMPTY
    conn = _Conn({LAHIRI: _phase_rows("2026-01-01T00:00:00+00:00", "2026-12-31T00:00:00+00:00")})
    _, detail = PERM.compute_permission(swe, conn, CHART_ID, "marriage", [_target()], T_JD, dasha_periods=[], ayanamsha_id="raman")
    ss = _sade_sati(detail)
    assert ss["active"] is False
    assert ss["state"] == "no_data"
    assert "raman" in ss["empty_reason"] and "NOT asserted" in ss["empty_reason"]
    assert ss["detail"] == {"empty_reason": ss["empty_reason"]}


def test_no_target_and_failed_read_also_carry_a_reason(monkeypatch):
    _, detail = PERM.compute_permission(swe, _Conn({}), CHART_ID, "marriage", [], T_JD, dasha_periods=[])
    assert "no resonance target" in _sade_sati(detail)["empty_reason"]

    def boom(*a, **k):
        raise RuntimeError("read blew up")

    monkeypatch.setattr(P, "sade_sati_phase", boom)
    _, detail = PERM.compute_permission(swe, _Conn({}), CHART_ID, "marriage", [_target()], T_JD, dasha_periods=[])
    ss = _sade_sati(detail)
    assert ss["state"] == "no_data" and "RuntimeError" in ss["empty_reason"] and ss["active"] is False


def test_a_real_read_outside_every_phase_is_an_honest_not_active_without_a_reason():
    conn = _Conn({LAHIRI: _phase_rows("2020-01-01T00:00:00+00:00", "2021-01-01T00:00:00+00:00")})
    _, detail = PERM.compute_permission(swe, conn, CHART_ID, "marriage", [_target()], T_JD, dasha_periods=[])
    ss = _sade_sati(detail)
    assert ss["active"] is False
    assert "empty_reason" not in ss and "state" not in ss  # facts WERE read: this is a finding, not a gap


def test_a_real_read_inside_a_phase_is_active_without_a_reason():
    conn = _Conn({LAHIRI: _phase_rows("2026-01-01T00:00:00+00:00", "2026-12-31T00:00:00+00:00")})
    _, detail = PERM.compute_permission(swe, conn, CHART_ID, "marriage", [_target()], T_JD, dasha_periods=[])
    ss = _sade_sati(detail)
    assert ss["active"] is True and "empty_reason" not in ss
    assert ss["detail"]["phase"] == "rising"
