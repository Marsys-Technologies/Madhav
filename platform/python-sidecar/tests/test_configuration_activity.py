"""
D-4b readiness-pass perf fix verification: `gather_configuration_sentences`
must issue a `savepoint_scope` (real SAVEPOINT/RELEASE SAVEPOINT round-trip
on `conn`) ONLY for the two primitives that actually take a `conn` parameter
(kakshya_cell_crossing, gochara_vedha_pair) and the always-conn
sarvatobhadra_vedha call -- the six primitives with no `conn` parameter
(degree_contact, drishti_contact, sign_ingress, nakshatra_ingress_tara,
station_retro_loop, eclipse_degree) must be called with ZERO savepoint
overhead. Live profiling against chart 482012f1 found all nine primitives
costing the same ~110-120ms per call regardless of whether they touched the
DB -- this is the regression test proving the fix and pinning the behavior.
"""
from __future__ import annotations

import swisseph as swe

from services.gochara_grammar.models import ResonanceTarget
from services.gochara_intensity import configuration_activity as CA

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


class _SavepointTrackingConn:
    """Fake conn that records every SAVEPOINT/RELEASE SAVEPOINT issued, so a
    test can assert exactly which primitive calls paid for one."""

    def __init__(self):
        self.savepoints_opened: list[str] = []
        self.autocommit = False

    def execute(self, sql, params=None):
        s = (sql if isinstance(sql, str) else str(sql)).strip()
        if s.startswith("SAVEPOINT "):
            self.savepoints_opened.append(s[len("SAVEPOINT "):])

        class _Cur:
            def fetchall(self):
                return []

        return _Cur()

    def rollback(self):
        pass


def _target():
    return ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="11", weight=0.75, classical_citation="TEST FIXTURE",
        target_sign="Pisces",
    )


def test_needs_conn_false_primitives_issue_zero_savepoints(monkeypatch):
    """The six no-conn primitives must be called with NO savepoint at all --
    they take no `conn` parameter and issue zero queries, so a
    SAVEPOINT/RELEASE round-trip around them was pure overhead."""
    conn = _SavepointTrackingConn()
    calls: list[str] = []

    def _stub_no_conn(name):
        def _fn(swe_, chart_id, target, start_jd, end_jd, *a, **kw):
            calls.append(name)
            assert "conn" not in kw, f"{name} must not be called with a conn kwarg"
            return []
        return _fn

    for name in ("degree_contact", "drishti_contact", "sign_ingress",
                 "nakshatra_ingress_tara", "station_retro_loop", "eclipse_degree"):
        monkeypatch.setattr(CA.P, name, _stub_no_conn(name))

    def _stub_conn(name):
        def _fn(swe_, chart_id, target, start_jd, end_jd, *a, conn=None, **kw):
            calls.append(name)
            assert conn is not None, f"{name} must receive the real conn"
            return []
        return _fn

    monkeypatch.setattr(CA.P, "kakshya_cell_crossing", _stub_conn("kakshya_cell_crossing"))
    monkeypatch.setattr(CA.P, "gochara_vedha_pair", _stub_conn("gochara_vedha_pair"))
    monkeypatch.setattr(
        CA.SBC, "find_sarvatobhadra_vedha_states",
        lambda swe_, chart_id, target, start_jd, end_jd, *a, conn=None, **kw: (
            calls.append("sarvatobhadra_vedha"), [])[1],
    )

    CA.gather_configuration_sentences(swe, conn, CHART_ID, [_target()], 2451545.0, 2451555.0)

    assert set(calls) == {
        "degree_contact", "drishti_contact", "sign_ingress", "nakshatra_ingress_tara",
        "station_retro_loop", "eclipse_degree", "kakshya_cell_crossing",
        "gochara_vedha_pair", "sarvatobhadra_vedha",
    }
    # Exactly 3 savepoints: kakshya_cell_crossing, gochara_vedha_pair, sarvatobhadra_vedha.
    # The 6 no-conn primitives contributed zero.
    assert len(conn.savepoints_opened) == 3, (
        f"expected exactly 3 savepoints (the 2 needs_conn primitives + sarvatobhadra_vedha), "
        f"got {len(conn.savepoints_opened)}: {conn.savepoints_opened}"
    )


def test_no_conn_primitive_failure_still_degrades_honestly(monkeypatch):
    """Removing the savepoint around no-conn primitives must not change their
    error-resilience contract: a raised exception is caught and logged, the
    gather continues to the next primitive/target, never crashes."""
    conn = _SavepointTrackingConn()

    def _boom(*a, **kw):
        raise RuntimeError("simulated primitive failure")

    monkeypatch.setattr(CA.P, "degree_contact", _boom)
    monkeypatch.setattr(CA.P, "drishti_contact", lambda *a, **kw: [])
    monkeypatch.setattr(CA.P, "sign_ingress", lambda *a, **kw: [])
    monkeypatch.setattr(CA.P, "nakshatra_ingress_tara", lambda *a, **kw: [])
    monkeypatch.setattr(CA.P, "station_retro_loop", lambda *a, **kw: [])
    monkeypatch.setattr(CA.P, "eclipse_degree", lambda *a, **kw: [])
    monkeypatch.setattr(CA.P, "kakshya_cell_crossing", lambda *a, conn=None, **kw: [])
    monkeypatch.setattr(CA.P, "gochara_vedha_pair", lambda *a, conn=None, **kw: [])
    monkeypatch.setattr(CA.SBC, "find_sarvatobhadra_vedha_states", lambda *a, conn=None, **kw: [])

    # Must not raise.
    result = CA.gather_configuration_sentences(swe, conn, CHART_ID, [_target()], 2451545.0, 2451555.0)
    assert result == []
