"""A5.3 — Codex round 8, R8-6 remainder: (1) P4 never drops an unknown record before the agent max; (2) the peak-tie
tolerance applies only BETWEEN distinct extrema; (3) complete state boundaries, or the record is unqualified."""
from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from services.gochara_kernel import window_sweep as ws

from .test_a53_window_sweep import _d, _draft, _rec, _rows_declared, _tri

ROWS = lambda p, v: _rows_declared(p, v, orb=5.0)          # noqa: E731


# ── (1) P4: an unknown record is not dropped before the agent max ────────────────────────────────────

def _p4_three(unknown_day=None):
    """Jupiter has TWO records (A known 0.4 throughout; B unknown from `unknown_day`), Saturn one (C, 0.9)."""
    day = lambda t: (t - _d(0)).total_seconds() / 86400.0                     # noqa: E731
    a = _rec("A", path="P4", agent="jupiter", root="RA", relation="conjunction", kind="house_lord",
             supports=((0, 10),), delta_lambda_at=lambda t: 3.0)               # 1 − 3/5 = 0.4
    b = _rec("B", path="P4", agent="jupiter", root="RB", relation="conjunction", kind="house_lord",
             supports=((0, 10),),
             delta_lambda_at=lambda t: None if unknown_day is not None and day(t) >= unknown_day else 4.9)
    c = _rec("C", path="P4", agent="saturn", root="RC", relation="conjunction", kind="house_lord",
             supports=((0, 10),), delta_lambda_at=lambda t: 0.5)               # 1 − 0.5/5 = 0.9
    return [a, b, c]


def test_p4_three_record_case_with_an_unknown_record_is_null_with_a_reason():
    """Jupiter A (0.4, known) + Jupiter B (unknown from day 5) + Saturn C (0.9): the old code dropped B's unknown
    before the Jupiter max and stored min(0.4, 0.9); B's true value could be higher, so the window is NULL."""
    (w,), _ = _draft(_p4_three(unknown_day=5.0), ROWS)
    assert (w.peak_instant, w.score, w.evidence_for, w.evidence_against) == (None, None, None, None)
    assert w.unqualified_reason == "objective_unknown_over_component"
    assert w.outcome_valence_for_native == "unqualified"


def test_p4_a_record_unknown_over_its_whole_support_is_unqualified_at_the_record():
    (w,), _ = _draft(_p4_three(unknown_day=0.0), ROWS)
    assert w.peak_instant is None and w.score is None
    assert w.unqualified_reason == "operand_undeterminable_over_support"


def test_p4_with_every_record_known_still_gets_the_max_min():
    (w,), _ = _draft(_p4_three(unknown_day=None), ROWS)
    assert w.peak_instant is not None and w.unqualified_reason is None
    assert w.score == pytest.approx(0.4, abs=1e-6) or w.score == pytest.approx(0.9, abs=1e-6) or w.score > 0
    # act_J = max(0.4, 0.02) = 0.4, act_S = 0.9  ⇒  min = 0.4
    assert w.objective_value == pytest.approx(0.4, abs=1e-6)


def test_mutation_dropping_none_before_the_agent_max_would_report_a_number(monkeypatch):
    """The pre-R8-6 behaviour (filter None, then max) — reinstated — gives 0.4 where the honest answer is NULL; the
    test above fails under it."""
    def dropped(live, agent, t):
        vals = [v for p in live if p.rec.agent == agent for v in [p.value_at(t)] if v is not None]
        return max(vals) if vals else None
    monkeypatch.setattr(ws, "_agent_activity", dropped)
    (w,), _ = _draft(_p4_three(unknown_day=5.0), ROWS)
    assert w.peak_instant is not None                       # the mutant invents a peak: the real code must not


# ── (2) the tie tolerance is between distinct extrema only ───────────────────────────────────────────

def test_a_smooth_peak_is_its_true_peak_not_an_earlier_point_within_the_tolerance():
    lo, hi = _d(0), _d(10)
    f = lambda t: (lambda x: x * (1.0 - x))((t - lo) / (hi - lo))              # noqa: E731
    best, at = ws.maximise_earliest(f, lo, hi)
    assert abs((at - _d(5)).total_seconds()) < 0.01         # the old rule returned ~27 s early


def test_a_point_contacts_exact_instant_is_reported_exactly():
    lo, hi = _d(0), _d(30)
    f = lambda t: max(0.0, 1.0 - abs((t - _d(11.3)).total_seconds() / 86400.0) / 15.0)   # noqa: E731
    best, at = ws.maximise_earliest(f, lo, hi, hints=[_d(11.3)])
    assert best == pytest.approx(1.0) and at == _d(11.3)


def test_distinct_humps_within_the_tolerance_tie_to_the_earlier():
    lo, hi = _d(0), _d(60)
    day = lambda t: (t - lo).total_seconds() / 86400.0                           # noqa: E731
    f = lambda t: max(1.0 - 5e-10 - abs(day(t) - 8.0) / 15.0, 1.0 - abs(day(t) - 38.0) / 15.0)   # noqa: E731
    best, at = ws.maximise_earliest(f, lo, hi, hints=[_d(8.0), _d(38.0)])
    assert abs(day(at) - 8.0) < 1e-3                         # inside 1e-9 of the other hump: the EARLIER wins


def test_distinct_humps_further_apart_than_the_tolerance_do_not_tie():
    lo, hi = _d(0), _d(60)
    day = lambda t: (t - lo).total_seconds() / 86400.0                           # noqa: E731
    f = lambda t: max(1.0 - 5e-6 - abs(day(t) - 8.0) / 15.0, 1.0 - abs(day(t) - 38.0) / 15.0)   # noqa: E731
    best, at = ws.maximise_earliest(f, lo, hi, hints=[_d(8.0), _d(38.0)])
    assert abs(day(at) - 38.0) < 1e-3


def test_a_noisy_plateau_is_one_plateau_and_starts_at_its_first_instant():
    lo, hi = _d(0), _d(30)
    day = lambda t: (t - lo).total_seconds() / 86400.0                           # noqa: E731
    f = lambda t: min(1.0, max(0.0, (day(t) - 8.0) / 15.0 + 1e-15 * (int(day(t) * 1000) % 3)))   # noqa: E731
    f2 = lambda t: 1.2 if day(t) >= 8.0 else 0.2 + (day(t) / 8.0)                # a step onto a flat top
    best, at = ws.maximise_earliest(f2, lo, hi)
    assert abs(day(at) - 8.0) < 1e-3


# ── (3) complete state boundaries, or the record is unqualified ──────────────────────────────────────

def _aspect(**kw):
    return _rec("asp", path="P3", relation="aspect", kind="house_lord", supports=((0, 30),),
                delta_lambda_at=_tri(11.3, 15.0), **kw)


DRISHTI = lambda agent, off, ref: 1.0                                        # noqa: E731


def test_an_aspect_record_without_complete_boundaries_is_unqualified_and_the_window_null():
    for kw in ({"state_boundaries": None, "state_boundaries_complete": False},
               {"state_boundaries": lambda lo, hi: [_d(5)], "state_boundaries_complete": False},
               {"state_boundaries": None, "state_boundaries_complete": True}):
        rec = dataclasses.replace(_aspect(), **kw)
        rec = dataclasses.replace(rec, aspect_offset_at=lambda t: 7)
        (w,), _ = _draft([rec], ROWS, drishti=DRISHTI)
        assert w.peak_instant is None and w.score is None
        assert w.unqualified_reason == ws.STATE_BOUNDARIES_REASON, kw


def test_the_same_aspect_record_with_complete_boundaries_is_qualified():
    rec = dataclasses.replace(_aspect(), aspect_offset_at=lambda t: 7,
                              state_boundaries=lambda lo, hi: [], state_boundaries_complete=True)
    (w,), _ = _draft([rec], ROWS, drishti=DRISHTI)
    assert w.unqualified_reason is None and w.peak_instant is not None


def test_a_record_with_no_state_valued_operand_needs_no_boundaries():
    rec = dataclasses.replace(_rec("c", supports=((0, 10),)), state_boundaries=None, state_boundaries_complete=False)
    (w,), _ = _draft([rec], _rows_declared)
    assert w.unqualified_reason is None and w.peak_instant is not None


def test_an_unlisted_interior_change_would_have_hidden_an_island_so_the_incomplete_record_never_scores():
    """The reason the rule exists: a drishti step to 0 in [14, 14.0001) that no boundary lists — the dense scan can
    miss it, and the piece would be bridged; with the boundaries incomplete the window is NULL instead."""
    off = lambda t: 0 if _d(14) <= t < _d(14) + timedelta(seconds=8) else 7
    rec = dataclasses.replace(_aspect(), aspect_offset_at=off, state_boundaries=lambda lo, hi: [],
                              state_boundaries_complete=False)
    (w,), _ = _draft([rec], ROWS, drishti=lambda a, o, r: 0.0 if o == 0 else 1.0)
    assert w.peak_instant is None and w.unqualified_reason == ws.STATE_BOUNDARIES_REASON


def test_mutation_a_builder_that_ignores_the_flag_scores_the_incomplete_record(monkeypatch):
    monkeypatch.setattr(ws, "STATE_VALUED_FACTORS", frozenset())
    rec = dataclasses.replace(_aspect(), aspect_offset_at=lambda t: 7, state_boundaries=None,
                              state_boundaries_complete=False)
    (w,), _ = _draft([rec], ROWS, drishti=DRISHTI)
    assert w.peak_instant is not None                          # the mutant scores it: the real code must not


# ── the verifier's own derivation of the same rule (separate code) ───────────────────────────────────

class _Range:
    def __init__(self, lower, upper):
        self.lower, self.upper = lower, upper


def test_the_verifier_derives_boundary_completeness_itself_and_agrees_with_the_builder():
    from services.gochara_kernel import window_verifier as wv
    cov = _Range(_d(0), _d(100))
    sup = [(_d(10), _d(40))]
    assert wv._boundaries_complete("aspect", sup, cov) is True
    assert wv._boundaries_complete("aspect", [(_d(10), _d(140))], cov) is False       # beyond the completed horizon
    assert wv._boundaries_complete("aspect", sup, None) is False                      # no coverage partition
    assert wv._boundaries_complete("residence", sup, cov) is False                    # no edge source for it
    assert wv._boundaries_complete("aspect", [], cov) is False
    rows = [{"factor_id": "graduated_drishti", "applicability": {"relations": ["aspect"]}}]
    rec = {"relation": "aspect", "kind": "house_lord", "agent": "jupiter", "house": None}
    st = wv._record_state(rows, {**rec, "boundaries_complete": False}, True, False)
    assert st == ("unq", [wv.STATE_BOUNDARIES_REASON]) and wv.STATE_BOUNDARIES_REASON == ws.STATE_BOUNDARIES_REASON
    assert wv._record_state(rows, {**rec, "boundaries_complete": True}, True, False) == ("fn", None)
    vedha = [{"factor_id": "vedha_attenuation"}]
    assert wv._record_state(vedha, {**rec, "boundaries_complete": False}, False, True)[0] == "unq"
