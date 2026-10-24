"""SR-P1-SLIVER-D2 — a piece shorter than the stored-edge resolution is no candidate for a window's maximum, on the builder AND, in its own code, on the verifier.

WHY (doctrine). A record's stored support end and the lord's sign change are the SAME sky event computed on two paths, at most one JD-double ulp apart (≈ 40.2 µs at
JD 2.46e6; measured 19-21 µs, P1_BOUNDARY_EXPLAIN §4, P1_EVIDENCE_4 §3-4). A maximum that exists only on the piece between those two edges is not a sky configuration
(CLAUDE.md §N.7.6: an honest 0.0 beats an invented number). The rule: exclude from the MAXIMUM any piece shorter than the JD ulp at its start, COMPUTED
(`math.ulp(jd) * 86400` s), never a literal; count the excluded pieces per window and carry the count (`sliver_pieces_excluded`).

Every world is analytic and handed to both sides — the sky of P1_EVIDENCE_4 reduced to its edge skew: a lord whose state is against-side (0 for the event) until E and
for-side (0.625, the NEU malefic) from E, whose record ends 19 µs after E (chronic_onset day 2241.66: 0.625 -> 0.0). The real windows are in the job notes (measured on a
harness-built database; the analytic fixture is the regression that runs everywhere).

Claims, each with ONE oracle and ONE planted reversion (a single patch of the production seam; the SAME oracle must FAIL under it):

  L-1  builder solver: the 19 µs piece is not a candidate (0.625 -> 0.0), the instant moves with it                                  N.7.6 / P1_EVIDENCE_4 §4
  L-2  builder solver: a 10 ms piece (a different rung) is NOT excluded and the value stays 0.625                                    the resolution is the ulp, not an epsilon
  L-3  the resolution is COMPUTED from the instant (it doubles above JD 2^22), on all four implementations                             "never a literal"
  L-4  builder solver: the excluded pieces are counted and listed in the certificate geometry                                         diagnostics
  V-1  checker (window_solver_check): honest 0.0 VERIFIED, the sliver-valued 0.625 REFUTED                                           N.7.6
  V-2  checker: a 10 ms piece is not excluded: 0.625 VERIFIED, 0.0 REFUTED                                                           the resolution is the ulp
  V-3  checker: a stored peak that lies ON a sliver is refuted by name                                                               N.8 (a detector that can read false)
  S-1  sweep, piece path (constant members): an overlap sliver of two roots is excluded (1.0, not 2.0); the count rides in qualification.certificate
  S-2  verifier, piece path (`verify_window_semantics`): the honest window is VERIFIED; the sliver-valued one is refused
  S-3  the count the sweep stores is the count the verifier re-derives (a stored count nothing backs is refused)
"""
from __future__ import annotations

import dataclasses
import math
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from .test_a53_window_sweep import T0 as SWEEP_T0, _d, _draft, _rec, _rows_declared
from .test_od1_r67_certificate import GRAIN, ProvConn

JD0 = 2450814.5                                   # 1998-01-01T00:00:00Z
LO = datetime(1998, 1, 1, tzinfo=timezone.utc)
E_S = 50.0                                        # the lord's sign change, seconds from the window start
SLIVER_S = 19e-6                                  # the measured stored-edge skew (19-21 µs, P1_EVIDENCE_4 §3)
TEN_MS = 0.010
VALUE = 0.625                                     # NEU, malefic, adverse (Q3(c) Form B): the value the sliver carried in chronic_onset day 2241.66


# ── the builder's world: the solver ────────────────────────────────────────────────────────────────────────────────────────────────

def _problem(skew_s: float, origin_jd=JD0) -> sol.Problem:
    """One record, supported until E + skew. Its side is against (the step reads 0 for the for-sum) before E and for from E: the only positive piece is [E, E + skew)."""
    side = sol.Step(value_at=lambda t: 1.0 if t >= E_S else 0.0, boundaries=lambda lo, hi: [E_S] if lo < E_S < hi else [], complete=True)
    member = sol.Member("rec", "root", ((0.0, E_S + skew_s),), steps=(side, sol.constant_step(VALUE)))
    return sol.Problem(0.0, 100.0, sol.OBJECTIVE_SUM, (member,), origin_jd=origin_jd)


def oracle_l1():
    res = sol.solve(_problem(SLIVER_S))
    assert res.status == sol.SOLVED and res.value == 0.0 and res.instant == 0.0, (res.status, res.value, res.instant)


def oracle_l2():
    res = sol.solve(_problem(TEN_MS))
    assert res.status == sol.SOLVED and res.value == VALUE and res.instant == E_S, (res.status, res.value, res.instant)
    assert res.certificate["sliver_pieces_excluded"] == 0


def oracle_l3_builder():
    assert sol.sliver_resolution_s(JD0, 0.0) == math.ulp(JD0) * 86400.0
    assert 40e-6 < sol.sliver_resolution_s(JD0, 0.0) < 41e-6                       # 2^-31 d = 40.2 µs
    far = 5.0e6                                                                    # above JD 2^22: the ulp (and the resolution) doubles
    assert sol.sliver_resolution_s(far, 0.0) == 2.0 * sol.sliver_resolution_s(JD0, 0.0)
    assert sol.sliver_resolution_s(JD0, 0.0) == math.ulp(JD0 + 0.0) * 86400.0 and sol.sliver_resolution_s(JD0, 86400.0 * 3000) == math.ulp(JD0 + 3000) * 86400.0


def oracle_l3_sweep():
    near, far = datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(6800, 1, 1, tzinfo=timezone.utc)
    assert 40e-6 < ws.sliver_resolution_s(near) < 41e-6
    assert ws.sliver_resolution_s(far) == 2.0 * ws.sliver_resolution_s(near)


def oracle_l3_verifier():
    near, far = datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(6800, 1, 1, tzinfo=timezone.utc)
    assert 40e-6 < wv._sliver_resolution_s(near) < 41e-6
    assert wv._sliver_resolution_s(far) == 2.0 * wv._sliver_resolution_s(near)


def oracle_l3_checker():
    def engine(lo):
        rec = chk.CheckRecord("r", "root", "mars", ((lo, lo + timedelta(days=1)),), constant=1.0)
        return chk._Engine(lo, lo + timedelta(days=1), [rec], chk.OBJ_SUM, chk.StoredWindow(lo, 0.0), lambda b, d: 0.0, peak_tolerance_s=1.0,
                           max_evals=1000, event_class=None, against_evaluated=False)
    near, far = datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(6800, 1, 1, tzinfo=timezone.utc)
    assert 40e-6 < engine(near)._ulp_s(0.0) < 41e-6
    assert engine(far)._ulp_s(0.0) == 2.0 * engine(near)._ulp_s(0.0)


def oracle_l4():
    res = sol.solve(_problem(SLIVER_S))
    assert res.certificate["sliver_pieces_excluded"] == 1
    cert = sol.stored_certificate(res, objective=sol.OBJECTIVE_SUM, t0_iso=LO.isoformat())
    kinds = [p[2] for p in cert["geometry"]["pieces"]]
    assert kinds.count("sliver") == 1 and cert["geometry"]["pieces"][kinds.index("sliver")][0] == E_S
    assert not any(c[0] == "piece" and c[1] == E_S for c in cert["cells"])        # no closed cell claims a bound over the sliver
    assert cert["value"] == 0.0


# ── the verifier's world: the independent prover ──────────────────────────────────────────────────────────────────────────────────

def _checker_record(skew_s: float) -> chk.CheckRecord:
    e = LO + timedelta(seconds=E_S)
    return chk.CheckRecord("rec", "root", "mars", ((LO, e + timedelta(seconds=skew_s)),), constant=VALUE, channel=None,
                           channel_at=lambda d: chk.CH_FOR if d >= e else chk.CH_AGAINST,
                           channel_boundaries=lambda lo, hi: [e] if lo < e < hi else [])


def _check(skew_s: float, peak_s: float, value: float):
    return chk.check_window(lo=LO, hi=LO + timedelta(seconds=100.0), records=[_checker_record(skew_s)], objective=chk.OBJ_SUM,
                            stored=chk.StoredWindow(LO + timedelta(seconds=peak_s), value), position_at=lambda b, d: 0.0)


def oracle_v1():
    honest = _check(SLIVER_S, 0.0, 0.0)
    assert honest.status == chk.VERIFIED, (honest.status, honest.findings, honest.unverified)
    assert honest.rederived["sliver_pieces_excluded"] == 1
    sliver_valued = _check(SLIVER_S, E_S, VALUE)
    assert sliver_valued.status == chk.REFUTED and chk.F_VALUE in sliver_valued.codes(), (sliver_valued.status, sliver_valued.codes())


def oracle_v2():
    ok = _check(TEN_MS, E_S, VALUE)
    assert ok.status == chk.VERIFIED and ok.rederived["sliver_pieces_excluded"] == 0, (ok.status, ok.findings, ok.unverified)
    wrong = _check(TEN_MS, 0.0, 0.0)
    assert wrong.status == chk.REFUTED, (wrong.status, wrong.codes())


def oracle_v3():
    rep = _check(SLIVER_S, E_S + 5e-6, VALUE)                      # the stored peak sits inside the 19 µs piece
    assert rep.status == chk.REFUTED
    assert any(f.code == chk.F_VALUE and "shorter than the stored-edge resolution" in f.detail for f in rep.findings), rep.findings


# ── the sweep's piece path and the verifier's piece path (constant members) ─────────────────────────────────────────────────────────

OVERLAP = timedelta(microseconds=19)


def _overlap_records(overlap: timedelta):
    """Two roots whose supports overlap by `overlap` around day 10: R1 [0, 10d + overlap), R2 [10d, 20d). Only the overlap piece carries both roots (sum 2)."""
    a = dataclasses.replace(_rec("a", root="R1", supports=((0, 10),)), supports=((_d(0), _d(10) + overlap),))
    b = _rec("b", root="R2", supports=((10, 20),))
    return [a, b]


def _verify(draft, records):
    lo, hi = draft.interval
    q = draft.qualification()
    stored = [("w0", lo, hi, draft.peak_instant, draft.score, draft.evidence_for, draft.evidence_against, None, list(draft.null_states_used),
               draft.outcome_valence_for_native, draft.objective, draft.objective_value, q)]
    recs = [(r.record_id, r.root_id, r.relation, r.object_kind, r.agent, None, r.supports[0][0], r.supports[0][1]) for r in records]
    links = [("w0", r.record_id) for r in records]
    return wv.verify_window_semantics(ProvConn(stored, recs, links), factor_rows=_rows_declared("P3", "1.0.0"), dynamic_enabled=True, policy=wv.POLICY_VERSION, **GRAIN)


def oracle_s1():
    recs = _overlap_records(OVERLAP)
    (w,), _ = _draft(recs, _rows_declared)
    assert w.objective_value == 1.0 and w.evidence_for == 1.0 and w.peak_instant == _d(0), (w.objective_value, w.evidence_for, w.peak_instant)
    assert w.sliver_pieces_excluded == 1 and w.qualification()["certificate"] == {"sliver_pieces_excluded": 1}
    ten_ms, = _draft(_overlap_records(timedelta(milliseconds=10)), _rows_declared)[0]
    assert ten_ms.objective_value == 2.0 and ten_ms.peak_instant == _d(10) and "certificate" not in ten_ms.qualification()      # a 10 ms piece is a configuration
    assert _draft(_overlap_records(timedelta(0)), _rows_declared)[0][0].objective_value == 1.0                                       # abutting: no overlap piece at all


def oracle_s2():
    recs = _overlap_records(OVERLAP)
    (honest,), _ = _draft(recs, _rows_declared)
    rep = _verify(honest, recs)
    assert rep["status"] == "VERIFIED" and rep["numeric_reproduced"] == 1 and rep["windows_detail"][0]["sliver_pieces_excluded"] == 1, rep
    sliver_valued = dataclasses.replace(honest, objective_value=2.0, evidence_for=2.0, peak_instant=_d(10), sliver_pieces_excluded=None)
    with pytest.raises(RuntimeError, match=r"objective_value .* != re-derived"):
        _verify(sliver_valued, recs)


def oracle_s3():
    recs = _overlap_records(OVERLAP)
    (honest,), _ = _draft(recs, _rows_declared)
    for stored_count in (None, 2):                                  # the count dropped, or invented: the verifier's own count (1) decides
        bad = dataclasses.replace(honest, sliver_pieces_excluded=stored_count)
        with pytest.raises(RuntimeError, match=r"qualification .* != re-derived"):
            _verify(bad, recs)


# ── the claims: oracle + the single planted reversion that must make it fail ───────────────────────────────────────────────────────

def _off(monkeypatch, target, name, replacement):
    monkeypatch.setattr(target, name, replacement)


CLAIMS = {
    "L-1": (oracle_l1, lambda mp: _off(mp, sol, "sliver_resolution_s", lambda jd, t: 0.0)),
    "L-2": (oracle_l2, lambda mp: _off(mp, sol, "sliver_resolution_s", lambda jd, t: 1.0)),           # an epsilon of one second swallows the 10 ms rung
    "L-3 builder": (oracle_l3_builder, lambda mp: _off(mp, sol, "sliver_resolution_s", lambda jd, t: 40.2e-6)),   # a literal
    "L-3 sweep": (oracle_l3_sweep, lambda mp: _off(mp, ws, "sliver_resolution_s", lambda t: 40.2e-6)),
    "L-3 verifier": (oracle_l3_verifier, lambda mp: _off(mp, wv, "_sliver_resolution_s", lambda t: 40.2e-6)),
    "L-3 checker": (oracle_l3_checker, lambda mp: _off(mp, chk._Engine, "_ulp_s", lambda self, t: 40.2e-6)),
    "L-4": (oracle_l4, lambda mp: _off(mp, sol, "sliver_resolution_s", lambda jd, t: 0.0)),
    "V-1": (oracle_v1, lambda mp: _off(mp, chk._Engine, "_ulp_s", lambda self, t: 0.0)),
    "V-2": (oracle_v2, lambda mp: _off(mp, chk._Engine, "_ulp_s", lambda self, t: 1.0)),
    "V-3": (oracle_v3, lambda mp: _off(mp, chk._Engine, "_ulp_s", lambda self, t: 0.0)),
    "S-1": (oracle_s1, lambda mp: _off(mp, ws, "sliver_resolution_s", lambda t: 0.0)),
    "S-2": (oracle_s2, lambda mp: _off(mp, wv, "_sliver_resolution_s", lambda t: 0.0)),
    "S-3": (oracle_s3, lambda mp: _off(mp, wv, "_sliver_resolution_s", lambda t: 0.0)),
}


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_oracle_passes_on_the_real_code(cid):
    CLAIMS[cid][0]()


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_the_single_planted_reversion_fails_the_oracle(cid, monkeypatch):
    oracle, plant = CLAIMS[cid]
    plant(monkeypatch)
    with pytest.raises((AssertionError, RuntimeError, pytest.fail.Exception)):
        oracle()


# ── guards ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_two_sides_share_no_code_for_the_rule():
    """The verifier's rule is its own: neither the checker nor the verifier imports the builder (K12) — the rule is restated, not shared."""
    import inspect
    for mod in (chk, wv):
        imports = [l.strip() for l in inspect.getsource(mod).splitlines() if l.startswith(("import ", "from "))]
        assert not any("window_sweep" in l or "window_solver " in l or l.endswith("window_solver") or "window_solver as" in l for l in imports), imports


def test_no_sliver_when_the_problem_has_no_jd_axis():
    res = sol.solve(_problem(SLIVER_S, origin_jd=None))
    assert res.value == VALUE and res.certificate["sliver_pieces_excluded"] == 0           # an analytic world without a JD axis excludes nothing
