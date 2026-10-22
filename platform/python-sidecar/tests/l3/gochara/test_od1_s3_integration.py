"""SR-OD1 S3 — the window solver wired END TO END: sweep (builder) -> stored window -> independent verifier (prover), the bumped qualification table, the named
solver reasons, the numerical gate, the seal-brief counts and the lane gate.

Every oracle states its source. The numbers come from the frozen objective definitions (PLAN §2.1; spec §7.2/§7.3, O-RP-3 / S:321-323 for the P4 max-min) and
from closed-form worlds, never from the code under test:

  * the activity kernel is `1 - d/orb` (activity_kernel@1.1.0, draft AM-13), `d` the seam-safe angular distance;
  * P4's objective is `min(act_Jupiter(t), act_Saturn(t))`; the frozen tie rule takes the EARLIEST distinct local extremum (spec §7.2 inv. 2);
  * a window is NUMBERED (a proven global maximum, its earliest tie instant) or BLANK under a named reason; never a best-found value (PLAN §2.2 G).

CLAIMS and the single planted reversion that must FAIL each (the reversions are applied in-memory to the production module by the `_planted` helper, or are
the explicit `*_reverted` assertions beside the oracle):

  C1  a time-varying window is numbered by the solver, builder and verifier agree         revert: `use_solver` off  -> the window is blank under the retired switch
  C2  the verifier refutes a wrong stored peak / maximum                                    revert: the verifier skips the prover -> the wrong window is "reproduced"
  C3  a structural defect blanks the window under its named reason and the verifier
      CONFIRMS the blank with its own derivation; a blank where the table yields a value
      is refused                                                                            revert: confirm without the probe -> the unjustified blank passes
  C4  the budget is PER WINDOW: a window that exhausts is blank, the next easy window is
      numbered, in either order; a budget blank is never a pass at the verifier             revert: a shared (grain) budget -> order dependence
  C5  a deferred or unavailable check is never a pass                                       revert: count the deferred window as reproduced
  C6  a step factor (graduated dṛṣṭi) times a tent: the verifier derives the step itself    revert: ignore the step's boundaries -> the peak moves
  C7  the table is /2 and says "solved or named reason"; the digest is one value everywhere
  C8  the numerical gate: solver reasons are grouped; the retired switch is a refusal;
      the attestation requires the solver table; blanks are counted per grain
  C9  the lane gate no longer demands search edges
  C10 the seal-approval check refuses a brief without the per-grain counts or with the retired reason
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import numerical_window_gate as nwg
from services.gochara_kernel import result_policy as rp
from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from .test_a53_window_sweep import _drishti_row, _kernel_row, _rec, _rows_declared  # noqa: F401
from .test_a53_window_sweep import _restore_factor_registry  # noqa: F401  (autouse: synthetic rows never outlive their test)
from .test_od1_w0_interface import _Rows

UTC = timezone.utc
T0 = datetime(2010, 1, 1, tzinfo=UTC)
DAY = 86400.0
GRAIN_P4 = dict(chart_id="c", generation="g", event_class="marriage", path_id="P4", rule_version="1.0.0")
GRAIN_P3 = {**GRAIN_P4, "path_id": "P3"}


def _d(days: float) -> datetime:
    return T0 + timedelta(days=days)


def _days(t: datetime) -> float:
    return (t - T0).total_seconds() / DAY


# ── the worlds ───────────────────────────────────────────────────────────────────────────────────────────────────────

def _jup(t):                      # rises through the point target at 0.1 deg/day, exact on day 5
    return (99.5 + 0.1 * _days(t)) % 360.0


def _sat(t):                      # leaves the target at 0.05 deg/day, exact on day 0
    return (100.0 + 0.05 * _days(t)) % 360.0


def _position(fns):
    return lambda body, t: fns[body.lower()](t)


def _p4_records(span=(0, 10), jup=_jup, sat=_sat, offset=0.0):
    lo, hi = span[0] + offset, span[1] + offset
    return [_rec("J", path="P4", agent="jupiter", root="RJ", supports=((lo, hi),), relation="conjunction", kind="degree_point", longitude_at=jup),
            _rec("S", path="P4", agent="saturn", root="RS", supports=((lo, hi),), relation="conjunction", kind="degree_point", longitude_at=sat)]


ROWS = lambda p, v: _rows_declared(p, v, orb=1.0)          # noqa: E731  (a TEST orb: the shipped registry is unratified, so no real window is numbered by it)


def _solve(records, rows_for=ROWS, cfg=ws.PRODUCTION_SOLVER, cls="marriage"):
    return ws.draft_windows(cls, records, rows_for, solver=cfg)[0]


# The exact answer of the P4 world (closed form): Jupiter's activity rises as 0.5 + 0.1 d until day 5, Saturn's falls as 1 - 0.05 d, so the max-min is where
# they cross: 0.5 + 0.1 d = 1 - 0.05 d  =>  d* = 10/3 (3 d 8 h exactly), M = 1 - 0.05 * 10/3 = 5/6. After day 5 Jupiter falls too, so the minimum only falls.
P4_PEAK_DAYS, P4_MAX = 10.0 / 3.0, 5.0 / 6.0


class _Cov:
    def __init__(self, lower, upper):
        self.lower, self.upper = lower, upper


class _Conn:
    """The SQL surface `verify_window_semantics` reads (the W0 harness plus the three reads the solver check adds), answered from lists."""

    def __init__(self, windows, records, targets=None, ingress=None, provenance=True, completed=None):
        self.windows, self.records = windows, records
        self.links = [(w[0], r[0]) for w in windows for r in records]
        self.targets, self.ingress, self.provenance, self.completed = targets or [], ingress or {}, provenance, completed

    def execute(self, sql, params=()):
        if "kala_gochara_publication" in sql:
            return _Rows([])
        if "kala_gochara_coverage" in sql:
            return _Rows([] if self.completed is None else [(self.completed,)])
        if "pg_attribute" in sql:
            return _Rows([(3 if self.provenance else 0,)])
        if "ka_gochara_physical_object" in sql:
            return _Rows(self.targets)
        if "ka_gochara_sky_event" in sql:
            return _Rows([(t,) for t in self.ingress.get(params[0], [])])
        if "ka_gochara_eval_window_record" in sql:
            return _Rows(self.links)
        if "ka_gochara_relationship_record" in sql:
            return _Rows(self.records)
        if "ka_gochara_eval_window" in sql:
            return _Rows(self.windows)
        raise AssertionError(sql)


def _stored(draft, wid="w"):
    lo, hi = draft.interval
    return (wid, lo, hi, draft.peak_instant, draft.score, draft.evidence_for, draft.evidence_against, None, list(draft.null_states_used),
            draft.outcome_valence_for_native, draft.objective, draft.objective_value, draft.qualification())


def _member_rows(records):
    return [(r.record_id, r.root_id, r.relation, r.object_kind, r.agent, None, r.supports[0][0], r.supports[0][1]) for r in records]


def _verify(drafts, records, rows, position_at, *, grain=GRAIN_P4, targets=None, ingress=None, completed=None, **kw):
    targets = targets if targets is not None else [(r.record_id, r.canonical_target) for r in records]
    conn = _Conn([_stored(d, f"w{i}") for i, d in enumerate(drafts)], _member_rows(records), targets, ingress, completed=completed)
    if len(drafts) > 1:                                     # one window per record set: link by overlap
        conn.links = [(f"w{i}", r.record_id) for i, d in enumerate(drafts) for r in records
                      if any(a < d.interval[1] and b > d.interval[0] for a, b in r.supports)]
    return wv.verify_window_semantics(conn, factor_rows=rows, policy=wv.POLICY_VERSION, position_at=position_at, **grain, **kw)


# ═════ C1: a time-varying window is numbered, proven, and independently agreed ═══════════════════════════════════════

def test_c1_a_time_varying_window_gets_a_proven_maximum_and_instant_and_the_verifier_agrees():
    recs = _p4_records()
    (draft,) = _solve(recs)
    # the builder: the closed-form answer, not the code's own output
    assert draft.unqualified_reason is None and draft.unresolved == {}
    assert draft.peak_instant == _d(0) + timedelta(days=0) + timedelta(hours=80)          # d* = 10/3 d = 80 h exactly, to the microsecond
    assert abs(draft.objective_value - P4_MAX) < 1e-12 and abs(draft.score - P4_MAX) < 1e-12
    assert draft.outcome_valence_for_native != "unqualified"
    # the verifier: a second implementation, from the stored row, the factor rows and the ephemeris alone
    report = _verify([draft], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}))
    assert report["status"] == "VERIFIED" and report["dynamic_enabled"] is True
    assert (report["solver_checked_windows"], report["numeric_reproduced"], report["fully_reproduced"], report["unverified_dynamic"]) == (1, 1, 1, 0)
    # the prover's own maximum is located to a microsecond on a kinked crest: it agrees with the closed form to ~1e-11 (its stated 1e-10 certificate)
    assert report["windows_detail"][0]["objective_value"] == pytest.approx(P4_MAX, abs=1e-10) and wv.satisfies_gate(report)


def test_c1_reverted_without_the_solver_the_same_window_is_blank_under_the_retired_switch_and_the_oracle_notices():
    """Planted reversion of C1: the caller passes neither `solver` nor the legacy sampler (what the writer did before S3)."""
    (draft,) = ws.draft_windows("marriage", _p4_records(), ROWS)[0]
    assert draft.peak_instant is None and draft.unqualified_reason == ws.DYNAMIC_SWITCH_REASON
    with pytest.raises(AssertionError):
        assert draft.unqualified_reason is None                                       # C1's first assertion fails on the reverted build


def test_c1_the_solver_and_the_legacy_sampler_are_never_both_asked_for_and_the_writer_asks_for_the_solver():
    with pytest.raises(ws.SweepRefusal, match="mutually exclusive"):
        ws.draft_windows("marriage", _p4_records(), ROWS, solver=ws.PRODUCTION_SOLVER, allow_dynamic=True)
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    src = inspect.getsource(writer)
    call = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "draft_windows")
    kwargs = {k.arg for k in call.keywords}
    assert "solver" in kwargs and "allow_dynamic" not in kwargs
    # the speed seam is a KEYWORD of the writer's read_grain call (RV-INT part 1 B5: `"speed_at" in src` was satisfied by the `def speed_at` beside it)
    read = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "read_grain")
    assert "speed_at" in {k.arg for k in read.keywords}


# ═════ C2: the verifier refutes wrong numbers ════════════════════════════════════════════════════════════════════════

def _tamper(draft, **fields):
    import dataclasses
    return dataclasses.replace(draft, **fields)


def _lie(draft, **fields):
    """A builder that lies CONSISTENTLY: the stored fields and its own certificate agree on the false peak / maximum (R-7: the certificate is the builder's claim, never evidence).
    The certificate check's agreement test (`certificate_disagrees_with_stored_window`) then passes, so only the verifier's OWN proof can refute it."""
    cert = dict(draft.solver_certificate)
    if "peak_instant" in fields:
        cert["instant"] = (fields["peak_instant"] - datetime.fromisoformat(cert["t0"])).total_seconds()
    if "objective_value" in fields:
        cert["value"] = fields["objective_value"]
    return _tamper(draft, solver_certificate=cert, **fields)


@pytest.mark.parametrize("what,fields,match", [
    ("a peak 30 s from the crest (Q12: exact to the second)", {"peak_instant": _d(0) + timedelta(hours=80, seconds=30)}, "earlier_tie_not_taken|peak_instant_mismatch|peak_value_mismatch"),
    ("a stored maximum below the true one", {"objective_value": P4_MAX - 1e-3, "score": P4_MAX - 1e-3}, "objective_exceeds_stored_maximum|peak_value_mismatch"),
    ("a peak on the other side of the crossing", {"peak_instant": _d(5)}, "peak_value_mismatch|earlier_tie_not_taken"),
])
def test_c2_the_verifier_refutes_a_wrong_stored_peak_or_maximum(what, fields, match):
    recs = _p4_records()
    (draft,) = _solve(recs)
    with pytest.raises(RuntimeError, match=match):
        _verify([_lie(draft, **fields)], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}))
    # merge-back (R67): a stored value that merely disagrees with the builder's own certificate is refused one step earlier, by the certificate check
    with pytest.raises(RuntimeError, match="certificate_disagrees_with_stored_window"):
        _verify([_tamper(draft, **fields)], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}))


def test_c2_reverted_a_verifier_that_skips_the_prover_would_reproduce_the_wrong_window(monkeypatch):
    """Planted reversion of C2: the prover (`window_solver_check`, reached through the certificate check) always says VERIFIED. The wrong window is then 'reproduced' — and the C2
    refutation test above would fail."""
    recs = _p4_records()
    (draft,) = _solve(recs)
    wrong = _lie(draft, peak_instant=_d(0) + timedelta(hours=80, seconds=30))
    monkeypatch.setattr(wv._chk, "check_window", lambda **kw: chk.CheckReport(chk.VERIFIED, (), (), 0, {"maximum": wrong.objective_value}))
    monkeypatch.setattr(wv._cc.chk._Engine, "run", lambda self: chk.CheckReport(chk.VERIFIED, (), (), 0, {"maximum": wrong.objective_value}))
    report = _verify([wrong], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}))
    assert report["solver_checked_windows"] == 1                       # the reverted verifier "reproduced" a window whose peak is 30 s off the true one


# ═════ C3: a structural defect blanks the window; the verifier confirms the blank itself ═════════════════════════════

def _turning(t):                  # Saturn reverses at day 5: the velocity changes sign inside the support, no station listed
    return (100.0 + 0.05 * (_days(t) - 5.0) ** 2) % 360.0


def test_c3_a_reversal_inside_the_support_blanks_the_window_under_its_named_reason_and_the_verifier_confirms_it():
    recs = _p4_records(sat=_turning)
    (draft,) = _solve(recs)
    assert draft.peak_instant is None and draft.score is None and draft.unqualified_reason == "monotone_arc_not_established"
    assert draft.unresolved == {"monotone_arc_not_established": 1} and draft.outcome_valence_for_native == "unqualified"
    report = _verify([draft], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _turning}))
    assert report["status"] == "VERIFIED" and report["solver_blank_windows"] == {"monotone_arc_not_established": 1}
    assert (report["solver_checked_windows"], report["fully_reproduced"], report["numeric_reproduced"]) == (1, 1, 0)


def test_c3_a_blank_where_the_table_yields_a_value_is_refused():
    """The same stored blank, but the sky is monotone: the independent prover finds NO such defect, so the blank is a blank where the table yields a number.
    Planted reversion: the verifier takes the stored reason on trust (no probe) -> this passes."""
    recs = _p4_records(sat=_turning)
    (draft,) = _solve(recs)
    with pytest.raises(RuntimeError, match="the independent prover finds no such defect"):
        _verify([draft], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}))


def test_c3_a_blank_with_no_reason_or_a_number_beside_a_reason_is_refused():
    recs = _p4_records(sat=_turning)
    (draft,) = _solve(recs)
    nameless = _tamper(draft, unqualified_reason=None, unresolved={})
    with pytest.raises(RuntimeError, match="no usable reason"):
        _verify([nameless], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _turning}))


# ═════ C4: the budget is per WINDOW ═════════════════════════════════════════════════════════════════════════════════

_BODIES = ("jupiter", "saturn", "mars", "venus")


def _p3_pos(first, second):
    """One ephemeris for the grain's two windows (starting `first` and `second` days after T0): body k rises through the target at 0.1 deg/day, crest 5 days in."""
    def pos(body, t):
        d = _days(t)
        off = first if abs(d - first - 5.0) < abs(d - second - 5.0) else second
        return (99.5 + 0.1 * (d - off) + 0.001 * _BODIES.index(body.lower())) % 360.0
    return pos


def _p3_records(n_tents_first, offset_first, offset_second):
    """Two windows in one P3 grain: a HARD one (`n_tents_first` tent records of distinct roots and bodies) and an EASY one (one record)."""
    pos = _p3_pos(offset_first, offset_second)

    def tent(name, agent, off):
        return _rec(name, path="P3", agent=agent, root=f"R{name}", supports=((off, off + 10),), relation="conjunction", kind="degree_point",
                    longitude_at=lambda t, _a=agent: pos(_a, t))
    return [tent(f"h{k}", _BODIES[k], offset_first) for k in range(n_tents_first)] + [tent("easy", "jupiter", offset_second)]


def test_c4_a_window_that_exhausts_its_budget_is_blank_and_the_next_easy_window_is_numbered_in_either_order():
    """Source: PLAN §2.3 item 6 / RECONCILIATION R-6 — "builder budget is per WINDOW only (no grain-level budget, so no order dependence)". The cap sits between an
    easy window's cost (one record: ~170 evaluations) and the hard window's (four records: ~680)."""
    cfg = ws.SolverConfig(max_evals=400)
    for first, second in ((0, 100), (100, 0)):
        recs = _p3_records(4, first, second)
        drafts = ws.draft_windows("marriage", recs, ROWS, solver=cfg)[0]
        by_start = {_days(d.interval[0]): d for d in drafts}
        hard, easy = by_start[float(first)], by_start[float(second)]
        assert hard.peak_instant is None and hard.unqualified_reason == "solver_budget_exhausted" and hard.unresolved == {"solver_budget_exhausted": 1}
        assert easy.peak_instant is not None and easy.unqualified_reason is None
        assert abs(_days(easy.peak_instant) - (second + 5.0)) < 1e-6 and abs(easy.objective_value - 1.0) < 1e-9      # the crest: d = 0 -> value 1


def test_c4_reverted_with_one_budget_shared_by_the_grain_the_easy_window_depends_on_its_neighbour(monkeypatch):
    """Planted reversion of C4: a grain-level budget. The solver's `Budget` exists for exactly that mistake; the sweep must not pass one."""
    seen = []
    real = sol.solve
    monkeypatch.setattr(sol, "solve", lambda problem, **kw: (seen.append(kw.get("grain")), real(problem, **kw))[1])
    ws.draft_windows("marriage", _p3_records(1, 0, 100), ROWS, solver=ws.SolverConfig(max_evals=400))
    assert seen == [None, None]                                                       # one call per window, never a shared grain budget


def test_c4_a_budget_blank_is_never_a_pass_at_the_verifier():
    """A budget blank is justified by its certificate (R-6/R-7; merge-back R67 wires that check): a blank that declares a per-window budget below the policy's (here 400
    evaluations, a builder blanking a window cheaply) is a DISAGREEMENT, so the verifier raises and nothing is sealed. The genuine 500,000-evaluation blank and its demotion
    are measured end to end in `test_od1_r67_certificate.py`."""
    recs = _p3_records(4, 0, 100)
    drafts = ws.draft_windows("marriage", recs, ROWS, solver=ws.SolverConfig(max_evals=400))[0]
    with pytest.raises(RuntimeError, match="budget_declared_below_policy"):
        _verify(drafts, recs, ROWS("P3", "1.0.0"), _p3_pos(0, 100), grain=GRAIN_P3)


def test_c11_the_production_sweep_stores_the_solvers_certificate_on_the_solved_window_and_on_the_budget_blank():
    """Merge-back wave 3a (R-7 x S3): the window the PRODUCTION sweep builds carries the piece tree of the very solve that numbered it (its stored maximum is the certificate's, the objective
    is the solver's own name) — and a budget-exhausted window keeps its partial tree with the cells still open. Revert: the sweep does not attach `solver_certificate`."""
    recs = _p4_records()
    (draft,) = _solve(recs)
    cert = draft.solver_certificate
    assert cert is not None and cert["outcome"] == "solved" and cert["objective"] == sol.OBJECTIVE_MINMAX and cert["budget_scope"] == "window"
    assert cert["value"] == pytest.approx(draft.objective_value, abs=1e-12) and cert["max_evals"] == ws.PRODUCTION_SOLVER.max_evals
    assert draft.qualification()["solver_certificate"] is cert
    (blank,) = _solve(recs, cfg=ws.SolverConfig(max_evals=3))
    assert blank.peak_instant is None and blank.unqualified_reason == "solver_budget_exhausted"
    assert blank.solver_certificate["outcome"] == "blank" and blank.solver_certificate["max_evals"] == 3 and blank.solver_certificate["open"]


# ═════ C5: a deferral or a missing ephemeris is never a pass ════════════════════════════════════════════════════════

@pytest.mark.parametrize("kw,counter", [({"solver_check": False}, "solver_check_deferred_windows"), ({"position_at": None}, "solver_check_unavailable_windows")])
def test_c5_a_window_whose_independent_check_did_not_run_is_unverified(kw, counter):
    recs = _p4_records()
    (draft,) = _solve(recs)
    pos = _position({"jupiter": _jup, "saturn": _sat})
    report = _verify([draft], recs, ROWS("P4", "1.0.0"), kw.pop("position_at", pos), **kw)
    assert report[counter] == 1 and report["solver_checked_windows"] == 0 and report["status"] == "UNVERIFIED_DYNAMIC" and not wv.satisfies_gate(report)


def test_c5_the_verifiers_own_budget_running_out_demotes_the_window_to_a_named_blank_end_to_end(monkeypatch):
    """S3 lane review N1, adapted at the merge-back to R-6: when the independent prover cannot settle a window inside ITS budget (here 5 evaluations of the real prover) the
    window is neither a pass nor a refusal — it is INCONCLUSIVE: listed among `inconclusive_windows` with its stored window_id and the named reason `verifier_budget_exhausted`,
    reproduced as the blank it will be served as, never numeric, and the report stays VERIFIED (the numerical gate then caps the share at 0.5 %)."""
    recs = _p4_records()
    (draft,) = _solve(recs)
    real = wv._cc.check_numbered
    monkeypatch.setattr(wv._cc, "check_numbered", lambda **kw: real(**{**kw, "max_evals": 5}))
    report = _verify([draft], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}))
    assert [w["reason"] for w in report["inconclusive_windows"]] == ["verifier_budget_exhausted"] and report["inconclusive_windows"][0]["stored_numbered"] is True
    assert (report["numeric_reproduced"], report["fully_reproduced"], report["status"]) == (0, 1, "VERIFIED")


# ═════ C6: a step factor times a tent ════════════════════════════════════════════════════════════════════════════════

def _jup_aspect(t):               # crosses 300 deg (Capricorn -> Aquarius) on day 2 at 0.1 deg/day; the 240 deg ray meets the target level on day 5
    return (299.8 + 0.1 * _days(t)) % 360.0


def test_c6_a_graduated_drishti_step_times_the_tent_is_solved_and_derived_independently():
    """The 9th-house ray (240 deg) of Jupiter: eff = lon + 240 meets the target level 180.3 deg on day 5 (a tent crest of 1.0). The dṛṣṭi offset (Stream B's table,
    CALLED) steps when Jupiter changes sign on day 2: from the target sign Libra (idx 6) to Jupiter's sign Capricorn (9): offset 10 -> 0.25; Aquarius (10): 9 -> 1.0.
    So F = 0.25 * tent before day 2 and 1.0 * tent after: the maximum is the crest, 1.0, on day 5 (a step UP at day 2, a tent crest after it)."""
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from services.gochara_kernel.window_store import _aspect_offset_provider
    pos = _position({"jupiter": _jup_aspect})
    rec = _rec("A", path="P3", agent="jupiter", root="RA", supports=((0, 10),), relation="aspect", kind="degree_point", target="point:180.3",
               longitude_at=_jup_aspect, aspect_rays=(120.0, 180.0, 240.0), state_boundaries=lambda lo, hi: [c for c in (_d(2),) if lo < c < hi],
               state_boundaries_complete=True)
    rec = rec.__class__(**{**rec.__dict__, "aspect_offset_at": _aspect_offset_provider("point:180.3", "jupiter", lambda name, t: pos(name, t))})
    (draft,) = ws.draft_windows("marriage", [rec], ROWS, drishti=writer.DRISHTI_SOURCE, solver=ws.PRODUCTION_SOLVER)[0]
    assert draft.unqualified_reason is None and abs(_days(draft.peak_instant) - 5.0) < 1e-5 and abs(draft.objective_value - 1.0) < 1e-9
    ingress = {"jupiter": [_d(2)]}
    completed = _Cov(_d(-100), _d(100))
    report = _verify([draft], [rec], ROWS("P3", "1.0.0"), pos, grain=GRAIN_P3, ingress=ingress, completed=completed, drishti_bound=True)
    assert report["status"] == "VERIFIED" and report["solver_checked_windows"] == 1
    # planted reversion of C6: the verifier's step has NO change instants -> the sign change is hidden; its own H2 detector (the step must hold across a piece)
    # then refuses the window — "state_boundaries_incomplete" — instead of reproducing it
    with pytest.raises(RuntimeError, match="state_boundaries_incomplete"):
        _verify([draft], [rec], ROWS("P3", "1.0.0"), pos, grain=GRAIN_P3, ingress={"jupiter": []}, completed=completed, drishti_bound=True)


def test_c6_the_builder_honours_a_step_that_drops_under_a_rising_tent_the_peak_is_the_last_microsecond_before_the_drop():
    """A stub dṛṣṭi table (builder only) makes the factor 1.0 before day 4 and 0.4 from day 4 (a change instant listed and complete). The tent (9th-house ray, crest
    1.0 on day 5) is still rising at day 4 with value 1 - 0.1 * |4 - 5| = 0.9, so the maximum is 0.9 at the LAST MICROSECOND before the drop (a half-open piece);
    after it the factor caps the window at 0.4. Planted reversion: the sweep ignores the state factors -> the maximum is the crest, 1.0, on day 5."""
    pos = _position({"jupiter": _jup_aspect})
    rec = _rec("A", path="P3", agent="jupiter", root="RA", supports=((0, 10),), relation="aspect", kind="degree_point", target="point:180.3",
               longitude_at=_jup_aspect, aspect_rays=(240.0,), state_boundaries=lambda lo, hi: [c for c in (_d(4),) if lo < c < hi], state_boundaries_complete=True,
               aspect_offset_at=lambda t: 10 if t < _d(4) else 9)
    table = {10: 1.0, 9: 0.4}
    (draft,) = ws.draft_windows("marriage", [rec], ROWS, drishti=lambda agent, offset, ref: table[offset], solver=ws.PRODUCTION_SOLVER)[0]
    assert draft.unqualified_reason is None
    assert draft.peak_instant == _d(4) - timedelta(microseconds=1) and abs(draft.objective_value - 0.9) < 1e-9
    assert pos("jupiter", _d(5)) == pytest.approx(180.3 - 240.0 + 360.0, abs=1e-9)          # the world is what the docstring says


# ═════ C7: the table ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_c7_the_table_is_version_2_and_rule_2_says_solved_or_a_named_solver_reason():
    t = rp.QUALIFICATION_TABLE
    assert t["schema"] == rp.QUALIFICATION_TABLE_SCHEMA == "window_qualification_table/2" and t["policy"] == rp.POLICY_QUALIFICATION
    rule2 = next(r for r in t["rules"] if r["n"] == 2)
    assert "SOLVED" in rule2["then"] and rp.DYNAMIC_SWITCH_REASON not in rule2["then"] and all(reason in rule2["then"] for reason in rp.SOLVER_BLANK_REASONS)
    # the reasons the table lists are the solver's, the verifier's and the gate's own literals
    assert set(rp.SOLVER_BLANK_REASONS) == {sol.REASON_BUDGET, sol.REASON_MONOTONE, sol.REASON_CERTIFICATE, sol.REASON_BOUNDARIES, sol.REASON_UNKNOWN, sol.REASON_UNDETERMINABLE}
    assert set(wv.SOLVER_STRUCTURAL) | set(wv.SOLVER_BUDGET_REASONS) | set(wv.SOLVER_UNKNOWN_REASONS) == set(rp.SOLVER_BLANK_REASONS)
    assert wv.SOLVER_STRUCTURAL == {sol.REASON_MONOTONE: chk.F_H1, sol.REASON_BOUNDARIES: chk.F_H2}
    from services.gochara_kernel import input_vector_verifier as ivv
    assert ivv.QUALIFICATION_TABLE_BINDING == rp.qualification_table_component(rp.POLICY_QUALIFICATION)


def test_c7_the_implementation_identity_covers_the_solver_and_its_prover():
    from services.gochara_kernel import input_vector as iv
    window = set(iv.IMPLEMENTATION_MODULES["window"])
    assert {"services.gochara_kernel.window_solver", "services.gochara_kernel.window_solver_check"} <= window
    # independence is kept: the prover imports neither the builder nor the solver, the builder imports the solver
    k = Path(inspect.getsourcefile(wv)).parent
    prover = ast.parse((k / "window_solver_check.py").read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(prover) if isinstance(n, (ast.Import, ast.ImportFrom))
                and any(m in (getattr(n, "module", "") or "") + " ".join(a.name for a in n.names) for m in ("window_sweep", "window_solver "))]
    assert "window_solver_check" in inspect.getsource(wv) and "window_solver_check" not in inspect.getsource(ws)


# ═════ C8: the numerical gate ═══════════════════════════════════════════════════════════════════════════════════════

def test_c8_the_solver_reasons_are_grouped_and_counted_never_a_refusal_by_themselves():
    for reason in ("solver_budget_exhausted", "monotone_arc_not_established", "solver_certificate_incomplete"):
        assert nwg.reason_group(reason) == nwg.SOLVER_CERTIFICATE == "solver_certificate"
    assert nwg.reason_group("state_boundaries_incomplete") == nwg.TIME_VARYING
    assert nwg.reason_group(rp.DYNAMIC_SWITCH_REASON) == nwg.OTHER and nwg.RETIRED_SWITCH_REASON == rp.DYNAMIC_SWITCH_REASON


class _GateConn:
    """`numerical_window_gate.census`' SQL surface: the provenance probe and the one GROUP BY."""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=()):
        if "pg_attribute" in sql:
            return _Rows([(1,)])
        return _Rows(self.rows)


def _census(rows):
    return nwg.census(_GateConn(rows), "c", "g", "marriage", "P4", "1.0.0")


def test_c8_the_census_counts_solver_blanks_by_reason_and_refuses_the_retired_switch():
    ok = _census([(True, None, "favourable", True, True, 3), (False, "solver_budget_exhausted", "unqualified", False, False, 2),
                  (False, "monotone_arc_not_established", "unqualified", False, False, 1)])
    assert ok["problems"] == [] and ok["numbered"] == 3 and ok["blank"] == {"monotone_arc_not_established": 1, "solver_budget_exhausted": 2}
    stale = _census([(False, rp.DYNAMIC_SWITCH_REASON, "unqualified", False, False, 4)])
    assert stale["blank"] == {} and any("retired" in p and "without the solver" in p for p in stale["problems"])      # a refusal, not an honest null


def _report(**kw):
    base = {"policy_version": nwg.POLICY_QUALIFICATION, "status": "VERIFIED", "unverified_windows": [], "fully_reproduced": 3, "numeric_reproduced": 3,
            "dynamic_enabled": True, "solver_check_deferred_windows": 0, "solver_check_unavailable_windows": 0}
    return {**base, **kw}


@pytest.mark.parametrize("override,message", [
    ({"dynamic_enabled": False}, "retired switch"),
    ({"solver_check_deferred_windows": 1, "status": "UNVERIFIED_DYNAMIC", "unverified_windows": ["w"]}, "deferred"),
    ({"solver_check_unavailable_windows": 2, "status": "UNVERIFIED_DYNAMIC", "unverified_windows": ["w"]}, "no ephemeris"),
])
def test_c8_an_attestation_is_refused_unless_the_rederivation_ran_under_the_solver_table_with_the_prover(override, message):
    conn = _GateConn([(True, None, "favourable", True, True, 3)])
    ok = nwg.grain_attestation(conn, chart_id="c", generation="g", event_class="marriage", path_id="P4", rule_version="1.0.0", report=_report(),
                               policy=nwg.POLICY_QUALIFICATION)
    assert ok["status"] == nwg.PASSED and ok["numbered"] == 3
    with pytest.raises(nwg.NumericalGateDisagrees, match=message):
        nwg.grain_attestation(conn, chart_id="c", generation="g", event_class="marriage", path_id="P4", rule_version="1.0.0", report=_report(**override),
                              policy=nwg.POLICY_QUALIFICATION)


def test_c8_the_verdict_counts_blank_windows_per_grain_and_per_reason_group(monkeypatch):
    """FB53 P16 gap 1: the seal brief says where a solver reason concentrates — per (class, path, version) — not only per path.

    Merge-back wave 2: the seal brief reads the R8 AGGREGATE (`generation_verdict(conn, chart, gen)` with no class subset), which also demands the build epoch, the search
    inventory and its independent re-derivation, the pinned implementation and a shard stamp on every row. The fake connection therefore answers those reads consistently
    (one scored class, one grain, one stamped shard at the pinned code), so the per-grain / per-group counts are asserted on the production path, not on a subset shortcut."""
    from services.gochara_kernel import window_gate as wg
    table = nwg.table_binding()
    att = {"schema": nwg.SCHEMA, "status": nwg.PASSED, "policy": nwg.POLICY_QUALIFICATION, "table": table, "windows": 5, "reproduced": 5, "numbered": 3,
           "numbered_without_score": 0, "valence": {"favourable": 3}, "blank": {"solver_budget_exhausted": 2}, "stored_numbered": 3,
           "demoted": {}, "demoted_valence": {}, "demoted_without_score": 0, "unconfirmed_blank_windows": 0, "demoted_windows": []}
    impl = {"evaluation": "e" * 64, "geometry": "g" * 64, "window": "w" * 64}
    pinned = hashlib.sha256(wg._canon(impl).encode("utf-8")).hexdigest()
    head, image, execution = "h" * 40, "sha256:" + "a" * 64, "exec-1"

    class Conn:
        def execute(self, sql, params=()):
            if "kala_gochara_publication" in sql:
                return _Rows([("manifest-1",)])
            if "FROM pg_attribute" in sql:                                            # R8X (merge-back 3b): the G-6 provenance probe
                return _Rows([(1,)])
            if "qualification -> 'solver_certificate' IS NOT NULL" in sql:            # R8X: the G-6 population read (no certified window here)
                return _Rows([])
            if "SELECT window_id::text" in sql:                                       # R67 B-1: the grain's stored NUMBERED windows (no demotion here, so none are listed)
                return _Rows([("w0",), ("w1",), ("w2",)])
            if "ka_gochara_search_input_snapshot" in sql:
                return _Rows([("input-digest-1",)])
            if "ka_gochara_search_inventory_verification" in sql:
                return _Rows([("marriage", "inventory-digest-1")])
            if "ka_gochara_search_inventory" in sql:
                return _Rows([("marriage", "inventory-digest-1")])
            if "ka_gochara_search_path_pin" in sql:
                return _Rows([("marriage", "P4", "1.0.0")])
            if "ka_gochara_eval_window_verification" in sql:
                epoch = nwg.current_epoch(self, "c", "g")
                runner = {"commit": head, "implementation_digest": pinned, nwg.ATTESTATION_KEY: att,
                          nwg.SHARD_KEY: nwg.shard_stamp(generation="g", head=head, classes=["marriage"], epoch=epoch, image_digest=image, execution_id=execution),
                          nwg.WALL_KEY: {"class": "marriage", "wall_ms": 10, "lock_wait_ms": 0, "compute_ms": 10},
                          nwg.G6_KEY: {"schema": "g6_evidence/1", "plan_digest": __import__("services.gochara_kernel.g6_plan", fromlist=["x"]).PLAN_DIGEST, "sample_per_mille": 30, "population": 0, "windows": {}}}
                return _Rows([("marriage", "P4", "1.0.0", "VERIFIED", nwg.POLICY_QUALIFICATION, 5, json.dumps(runner))])
            raise AssertionError(sql)
    import services.gochara_kernel.result_policy as rpm
    monkeypatch.setattr(rpm, "manifest_vector", lambda conn, chart, gen: {"result_policy": nwg.POLICY_QUALIFICATION, "qualification_table": table,
                                                                           "scored_classes": ["marriage"], "implementation": impl})
    monkeypatch.setattr(nwg, "census", lambda *a, **k: {"windows": 5, "numbered": 3, "numbered_without_score": 0, "valence": {"favourable": 3},
                                                       "blank": {"solver_budget_exhausted": 2}, "problems": []})
    monkeypatch.setattr(nwg, "expected_classes", lambda *a: ["marriage"])                # R8X (T16): the one-class world sets the pinned 26-class universe aside
    verdict = nwg.generation_verdict(Conn(), "c", "g")
    assert verdict["status"] == nwg.PASSED, verdict["problems"]
    assert verdict["honest_nulls_by_grain"] == [{"event_class": "marriage", "path_id": "P4", "rule_version": "1.0.0", "group": "solver_certificate",
                                                  "reason": "solver_budget_exhausted", "windows": 2}]
    assert verdict["blank_by_group"] == {"solver_certificate": 2} and verdict["honest_nulls"][0]["group"] == "solver_certificate"


# ═════ C9: the lane gate ═══════════════════════════════════════════════════════════════════════════════════════════

def _lane():
    import importlib.util
    path = Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover" / "j4d_slice_qualify.py"
    spec = importlib.util.spec_from_file_location("j4d_slice_qualify_s3", path)
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _PeakConn:
    def __init__(self, policy, with_peak, windows=7):
        self.policy, self.with_peak, self.windows = policy, with_peak, windows

    def execute(self, sql, params=None):
        outer = self

        class _Cur:
            def fetchone(self):
                if "input_generation_vector" in sql:
                    return None if outer.policy is None else (outer.policy,)
                return (outer.with_peak,) if "peak_instant IS NOT NULL" in sql else (outer.windows,)
        return _Cur()


def _row(policy, with_peak, observed):
    return _lane().peak_windows_row(_PeakConn(policy, with_peak), chart_id="c", classes=["marriage"], observed=observed)


SOLVER_QUIET = {"calls": 0, "certified": 0, "blank": {}, "evals": 0, "max_window_evals": 0}


def test_c9_the_gate_demands_no_search_edges_under_a_constants_only_slice():
    """N-7: under `window_qualification/1` a slice whose windows are all constant has NO solver call and NO sampler call, and still passes. Planted reversion: the
    old rule (`maximise_earliest_edges > 0`) fails it, and this test fails with it."""
    row = _row(rp.POLICY_QUALIFICATION, 4, {"maximise_earliest_calls": 0, "solver": SOLVER_QUIET})
    assert row["passed"] and row["admitted"] and row["legacy_search_calls"] == 0 and row["solver"]["calls"] == 0


def test_c9_the_gate_accounts_for_every_solver_call_and_refuses_a_numbering_by_search():
    seen = {"calls": 5, "certified": 3, "blank": {"solver_budget_exhausted": 2}, "evals": 900, "max_window_evals": 400}
    ok = _row(rp.POLICY_QUALIFICATION, 4, {"maximise_earliest_calls": 0, "solver": seen})
    assert ok["passed"] and ok["solver"] == {"calls": 5, "certified": 3, "blank_by_reason": {"solver_budget_exhausted": 2}, "evals": 900, "max_window_evals": 400}
    sampler = _row(rp.POLICY_QUALIFICATION, 4, {"maximise_earliest_calls": 9, "solver": seen})
    assert sampler["problems"][0].startswith("legacy_search_used")
    lost = _row(rp.POLICY_QUALIFICATION, 4, {"maximise_earliest_calls": 0, "solver": {**seen, "certified": 2}})
    assert lost["problems"][0].startswith("solver_calls_unaccounted")
    phantom = _row(rp.POLICY_QUALIFICATION, 1, {"maximise_earliest_calls": 0, "solver": seen})
    assert phantom["problems"][0].startswith("certificates_without_windows")
    assert _row(rp.POLICY_QUALIFICATION, 0, {"maximise_earliest_calls": 0, "solver": SOLVER_QUIET})["problems"][0].startswith("peak_windows_zero")


def test_c9_the_build_observer_sees_the_solver_at_the_call_and_restores_the_module():
    lane = _lane()
    recs = _p4_records()
    real = sol.solve
    with lane.observe_build() as seen:
        assert sol.solve is not real                                              # wrapped for the build ...
        ws.draft_windows("marriage", recs, ROWS, solver=ws.PRODUCTION_SOLVER)
        ws.draft_windows("marriage", _p4_records(sat=_turning), ROWS, solver=ws.PRODUCTION_SOLVER)
    assert sol.solve is real                                                      # ... and restored
    assert seen["maximise_earliest_calls"] == 0
    assert seen["solver"]["calls"] == 2 and seen["solver"]["certified"] == 1 and seen["solver"]["blank"] == {"monotone_arc_not_established": 1}
    assert seen["solver"]["evals"] > 0 and seen["solver"]["max_window_evals"] > 0


# ═════ C10: the seal-approval check ════════════════════════════════════════════════════════════════════════════════

def _brief_check():
    import importlib.util
    script = Path(__file__).resolve().parents[5] / "platform" / "scripts" / "gochara_seal_brief_check.py"
    spec = importlib.util.spec_from_file_location("gochara_seal_brief_check_s3", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _payload(bc, **gate_over):
    gate = {"schema": bc.NUMERICAL_GATE_SCHEMA, "status": "PASSED", "problems": [], "policy": bc.POLICY_QUALIFICATION, "table": bc.QUALIFICATION_TABLE_BINDING,
            "windows": 5, "numbered_windows": 3, "blank_windows": 2,
            "demoted_windows": 0, "demoted_by_reason": {}, "unconfirmed_blank_windows": 0, "inconclusive_cap_per_mille": 5,       # R-6 (R67)
            "honest_nulls": [{"path_id": "P4", "group": "solver_certificate", "reason": "solver_budget_exhausted", "windows": 2}],
            "honest_nulls_by_grain": [{"event_class": "marriage", "path_id": "P4", "rule_version": "1.0.0", "group": "solver_certificate",
                                       "reason": "solver_budget_exhausted", "windows": 2}]}
    att = json.dumps({"runner_identity": {"numerical_window_gate": {"status": "PASSED", "table": bc.QUALIFICATION_TABLE_BINDING, "windows": 5,
                                                                    "numbered": {**gate, **gate_over}["numbered_windows"]}}})
    return {"result_policy": bc.POLICY_QUALIFICATION, "numerical_window_gate": {**gate, **gate_over},
            "attestations": {"ka_gochara_eval_window_verification": [att]}}


def test_c10_the_approval_check_requires_the_per_grain_counts_and_refuses_the_retired_reason():
    bc = _brief_check()
    bc.check_numerical_gate(_payload(bc))                                          # a complete brief passes
    missing = _payload(bc)
    del missing["numerical_window_gate"]["honest_nulls_by_grain"]
    with pytest.raises(bc.Refused, match="per-grain honest nulls"):
        bc.check_numerical_gate(missing)
    # nothing blank, so the sum check cannot catch it: an ABSENT per-grain list is a brief that never counted by grain, not "zero blanks"
    clean = _payload(bc, numbered_windows=5, blank_windows=0, honest_nulls=[], honest_nulls_by_grain=[])
    bc.check_numerical_gate(clean)                                                 # an explicit empty list is the honest "no blanks"
    del clean["numerical_window_gate"]["honest_nulls_by_grain"]
    with pytest.raises(bc.Refused, match="lists no per-grain honest nulls"):
        bc.check_numerical_gate(clean)
    short = _payload(bc, honest_nulls_by_grain=[])
    with pytest.raises(bc.Refused, match="per-grain honest nulls account for 0 blank windows"):
        bc.check_numerical_gate(short)
    stale = _payload(bc, honest_nulls=[{"path_id": "P4", "group": "other_named_reason", "reason": rp.DYNAMIC_SWITCH_REASON, "windows": 2}])
    with pytest.raises(bc.Refused, match="retired reason"):
        bc.check_numerical_gate(stale)
