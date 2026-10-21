"""SR-OD1 W0 — the interface refactor the P1 / vedha / solver lanes build on (plan §2.7, §3.3 N-3, N-6; behaviour unchanged).

W0 adds four seams and no value: nothing here decides a doctrine number, every table is an analytic stub, and the existing
suites (`test_a53_window_sweep`, `test_a53_r86_sweep`, `test_a53_window_verification_*`) pin that the all-null and the
current `window_qualification/1` outputs did not move.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  W-1 completeness is PER FACTOR: a complete boundary list for one state-valued factor never vouches for another's
      (revert: judge completeness record-wide / "any factor complete");
  W-2 each factor's own change instants cut the pieces: an island only one factor's list names is found
      (revert: `_pieces` reads the record-wide provider only);
  W-3 the channel can be decided PER INSTANT by a factor (P1 agent_nature, Q3(a); the Moon's paksa flips at 180° elongation,
      BPHS 3.11): the for/against reduction at t follows the side AT t, and the flip instant is a piece boundary
      (revert: `reduce_at` reads the static `RecordProgram.channel`);
  W-4 exactly one factor decides a record's side (revert: drop the refusal);
  W-5 a factor's named reason for being unknown is carried to the window instead of the generic reason, and the generic reason
      stays where no factor names one (revert: always the generic reason);
  W-6 the verifier derives the same per-instant channel itself: builder and verifier agree on the same world, and a
      P1 member with no channel derivation is still refused (revert: the verifier ignores the channel boundaries);
  W-7 the `solver_check` switch reports what ran: a deferral is counted as deferred, never as checked, and never satisfies a
      gate (revert: a deferred window reported VERIFIED / not counted).
"""
from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_kernel.window_sweep import OperandSource, SweepRefusal
from services.gochara_rules import registry as reg

from .test_a53_window_sweep import _d, _draft, _rec, _rows_declared, _tri

NATURE = {"factor_id": "agent_nature", "rule_version": "9.0.0", "null_state": "unqualified",
          "direction": "higher = stronger", "function": "step", "range": [0.0, 1.0], "units": "unitless"}
P1_ROWS = lambda path, version: [NATURE]                       # noqa: E731  — one categorical factor, no kernel
P3_PLUS_NATURE = lambda p, v: _rows_declared(p, v, orb=5.0) + [NATURE]      # noqa: E731
FOR, AGAINST = ws.CHANNEL_FOR, ws.CHANNEL_AGAINST
DRISHTI = lambda agent, off, ref: 1.0                           # noqa: E731
NO_CHANGE = lambda lo, hi: []                                   # noqa: E731


@pytest.fixture(autouse=True)
def _restore_factor_registry():
    saved = dict(reg.FACTORS)
    yield
    reg.FACTORS.clear()
    reg.FACTORS.update(saved)


def _aspect(sources, **kw):
    """An aspect record whose dṛṣṭi boundaries are NOT stated record-wide: only its per-factor sources speak."""
    rec = _rec("asp", path="P3", relation="aspect", kind="house_lord", supports=((0, 30),),
               delta_lambda_at=_tri(11.3, 15.0), state_boundaries=None, state_boundaries_complete=False, **kw)
    return dataclasses.replace(rec, aspect_offset_at=lambda t: 7, operand_sources=sources)


# ── W-1: completeness per factor ─────────────────────────────────────────────────────────────────────────────────────

def test_w1_a_complete_list_for_one_factor_does_not_vouch_for_another():
    """dṛṣṭi's list is complete; the categorical factor's is not ⇒ the record (and window) is blank
    `state_boundaries_incomplete`. Planted reversion: completeness judged by ANY factor's flag ⇒ this record scores."""
    nature = OperandSource(value_at=lambda t: 0.5, boundaries=NO_CHANGE, complete=False)
    drishti = OperandSource(boundaries=NO_CHANGE, complete=True)
    (w,), _ = _draft([_aspect({"graduated_drishti": drishti, "agent_nature": nature})], P3_PLUS_NATURE, drishti=DRISHTI)
    assert w.peak_instant is None and w.score is None
    assert w.unqualified_reason == ws.STATE_BOUNDARIES_REASON


def test_w1_the_same_record_with_every_factor_complete_is_numbered():
    nature = OperandSource(value_at=lambda t: 0.5, boundaries=NO_CHANGE, complete=True)
    drishti = OperandSource(boundaries=NO_CHANGE, complete=True)
    (w,), _ = _draft([_aspect({"graduated_drishti": drishti, "agent_nature": nature})], P3_PLUS_NATURE, drishti=DRISHTI)
    assert w.unqualified_reason is None and w.peak_instant is not None


def test_w1_a_state_valued_factor_with_no_source_inherits_the_record_wide_list_unchanged():
    """The pre-W0 contract: the store's record-wide `state_boundaries` still serves dṛṣṭi when no per-factor source exists."""
    rec = dataclasses.replace(_aspect({}), state_boundaries=NO_CHANGE, state_boundaries_complete=True)
    (w,), _ = _draft([rec], lambda p, v: _rows_declared(p, v, orb=5.0), drishti=DRISHTI)
    assert w.unqualified_reason is None and w.peak_instant is not None


# ── W-2: a factor's own change instants cut the pieces ───────────────────────────────────────────────────────────────

def test_w2_an_island_only_one_factors_list_names_is_found():
    """A categorical factor is 0.2 except 1.0 on an 8-second island at day 14 that only ITS list names (the 96-point scan
    cannot see it). The earliest maximum is the island's start. Planted reversion: `_pieces` ignores per-factor lists."""
    start = _d(14)
    value = lambda t: 1.0 if start <= t < start + timedelta(seconds=8) else 0.2          # noqa: E731
    src = OperandSource(value_at=value, channel_at=lambda t: FOR, complete=True,
                        boundaries=lambda lo, hi: [c for c in (start, start + timedelta(seconds=8)) if lo < c < hi])
    rec = _rec("a", path="P1", supports=((0, 30),), operand_sources={"agent_nature": src},
               state_boundaries=None, state_boundaries_complete=False)
    (w,), _ = _draft([rec], P1_ROWS)
    assert w.peak_instant == start and w.objective_value == pytest.approx(1.0)


# ── W-3: the per-instant channel ─────────────────────────────────────────────────────────────────────────────────────

def _moon_like(flip_day, *, before, after, value=0.5):
    """A record whose side flips at `flip_day` (the paksa flip: the same graha is a benefic on one side of 180° elongation
    and a malefic on the other) and is `value` strong throughout."""
    side = lambda t: before if t < _d(flip_day) else after                                 # noqa: E731
    src = OperandSource(value_at=lambda t: value, channel_at=side, complete=True,
                        boundaries=lambda lo, hi: [_d(flip_day)] if lo < _d(flip_day) < hi else [])
    return _rec("moon", path="P1", root="R-moon", supports=((0, 10),), operand_sources={"agent_nature": src})


def _steady(rid, value):
    src = OperandSource(value_at=lambda t: value, channel_at=lambda t: FOR, complete=True, boundaries=NO_CHANGE)
    return _rec(rid, path="P1", root=f"R-{rid}", supports=((0, 10),), operand_sources={"agent_nature": src})


def test_w3_the_reduction_follows_the_side_at_t_and_the_flip_is_a_piece_boundary():
    """Moon-like record: AGAINST before day 4, FOR from day 4; a steady FOR record of 0.3. F(t) = 0.3 before the flip and
    0.8 after, so the window's peak is the flip instant itself with evidence_for 0.8 / evidence_against 0.
    Planted reversion: `reduce_at` reads the static channel ⇒ the moon-like record is unplaced and F is not 0.8 at day 4."""
    moon, steady = _moon_like(4, before=AGAINST, after=FOR), _steady("s", 0.3)
    (w,), _ = _draft([moon, steady], P1_ROWS)
    assert w.unqualified_reason is None
    assert w.peak_instant == _d(4) and w.objective_value == pytest.approx(0.8)
    assert (w.evidence_for, w.evidence_against) == (pytest.approx(0.8), pytest.approx(0.0))
    progs = [ws.build_program(r, P1_ROWS("P1", "9.0.0")) for r in (moon, steady)]
    before, after = ws.reduce_at(progs, _d(1), "marriage"), ws.reduce_at(progs, _d(6), "marriage")
    assert (before[FOR], before[AGAINST]) == (pytest.approx(0.3), pytest.approx(0.5))
    assert (after[FOR], after[AGAINST]) == (pytest.approx(0.8), pytest.approx(0.0))


def test_w3_a_side_that_is_undeterminable_makes_the_objective_unknown_never_a_default_channel():
    src = OperandSource(value_at=lambda t: 0.5, channel_at=lambda t: None if t >= _d(5) else FOR, complete=True,
                        boundaries=lambda lo, hi: [_d(5)] if lo < _d(5) < hi else [])
    rec = _rec("m", path="P1", supports=((0, 10),), operand_sources={"agent_nature": src})
    (w,), _ = _draft([rec], P1_ROWS)
    assert w.peak_instant is None and w.score is None and w.unqualified_reason == ws.UNKNOWN_OVER_COMPONENT


def test_w3_a_value_that_is_not_a_channel_is_refused():
    src = OperandSource(value_at=lambda t: 0.5, channel_at=lambda t: "both", complete=True, boundaries=NO_CHANGE)
    rec = _rec("m", path="P1", supports=((0, 10),), operand_sources={"agent_nature": src})
    with pytest.raises(SweepRefusal, match="neither the for nor the against channel"):
        _draft([rec], P1_ROWS)


# ── W-4: exactly one factor decides the side ─────────────────────────────────────────────────────────────────────────

def test_w4_two_factors_deciding_the_side_are_refused():
    side = OperandSource(value_at=lambda t: 0.5, channel_at=lambda t: FOR, complete=True, boundaries=NO_CHANGE)
    other = {**NATURE, "factor_id": "dignity_of_transit_sign"}
    rec = _rec("m", path="P1", supports=((0, 10),),
               operand_sources={"agent_nature": side, "dignity_of_transit_sign": side})
    with pytest.raises(SweepRefusal, match="more than one factor assigns the channel"):
        _draft([rec], lambda p, v: [NATURE, other])


# ── W-5: reason pass-through ─────────────────────────────────────────────────────────────────────────────────────────

def _unknown_from(day, reason):
    return OperandSource(value_at=lambda t: None if t >= _d(day) else 0.5, complete=True,
                         boundaries=lambda lo, hi: [_d(day)] if lo < _d(day) < hi else [],
                         channel_at=lambda t: FOR, unknown_reason=lambda t: reason if t >= _d(day) else None)


def test_w5_the_factors_named_reason_reaches_the_window():
    """The factor knows WHY its operand is unknown from day 5 (e.g. an obstructor's residence is not established);
    the window carries that reason. Planted reversion: always `objective_unknown_over_component`."""
    rec = _rec("a", path="P1", supports=((0, 10),), operand_sources={"agent_nature": _unknown_from(5, "obstructor_residence_unknown")})
    (w,), _ = _draft([rec], P1_ROWS)
    assert w.peak_instant is None and w.score is None
    assert w.unqualified_reason == "obstructor_residence_unknown"
    assert w.unresolved == {"obstructor_residence_unknown": 1}
    assert w.outcome_valence_for_native == "unqualified"


def test_w5_the_generic_reason_stays_where_no_factor_names_one():
    src = dataclasses.replace(_unknown_from(5, "x"), unknown_reason=lambda t: None)
    rec = _rec("a", path="P1", supports=((0, 10),), operand_sources={"agent_nature": src})
    (w,), _ = _draft([rec], P1_ROWS)
    assert w.unqualified_reason == ws.UNKNOWN_OVER_COMPONENT == "objective_unknown_over_component"
    assert w.unresolved == {ws.UNKNOWN_OVER_COMPONENT: 1}


# ── W-6: the verifier derives the same per-instant channel ───────────────────────────────────────────────────────────

class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class _Conn:
    """The SQL surface `verify_window_semantics` reads, answered from lists (it has no DB-specific behaviour of its own)."""

    def __init__(self, windows, records, links):
        self.windows, self.records, self.links = windows, records, links

    def execute(self, sql, params=()):
        if "kala_gochara_publication" in sql or "kala_gochara_coverage" in sql:
            return _Rows([])
        if "pg_attribute" in sql:
            return _Rows([(0,)])                       # no provenance columns: the structural fields are what is checked
        if "ka_gochara_eval_window_record" in sql:
            return _Rows(self.links)
        if "ka_gochara_relationship_record" in sql:
            return _Rows(self.records)
        if "ka_gochara_eval_window" in sql:
            return _Rows(self.windows)
        raise AssertionError(sql)


GRAIN = dict(chart_id="c", generation="g", event_class="marriage", path_id="P1", rule_version="9.0.0")


def _stored(draft, wid="w"):
    lo, hi = draft.interval
    return (wid, lo, hi, draft.peak_instant, draft.score, draft.evidence_for, draft.evidence_against, None,
            list(draft.null_states_used), draft.outcome_valence_for_native, None, None, None)


def _p1_world():
    """The W-3 world, drafted by the BUILDER, then handed to the VERIFIER with only the channel derivation."""
    moon, steady = _moon_like(4, before=AGAINST, after=FOR), _steady("s", 0.3)
    (draft,), _ = _draft([moon, steady], P1_ROWS)
    records = [(r.record_id, r.root_id, "residence", "sign_span", "jupiter", None, r.supports[0][0], r.supports[0][1])
               for r in (moon, steady)]
    links = [("w", r.record_id) for r in (moon, steady)]
    side = {"moon": lambda t: AGAINST if t < _d(4) else FOR, "s": lambda t: FOR}
    by_root = {"R-moon": "moon", "R-s": "s"}
    return draft, _Conn([_stored(draft)], records, links), \
        (lambda rec, t: side[by_root[rec["root"]]](t)), \
        (lambda rec, lo, hi: [_d(4)] if rec["root"] == "R-moon" and lo < _d(4) < hi else [])


def test_w6_builder_and_verifier_agree_on_a_per_instant_channel_world(monkeypatch):
    """Planted reversion: the verifier ignores `channel_boundaries` ⇒ it never evaluates the post-flip piece, derives the
    peak at day 0 and refuses the builder's day-4 peak."""
    monkeypatch.setattr(wv, "_row_state", lambda row, rec, d, v: ("const", 0.5 if rec["root"] == "R-moon" else 0.3))
    draft, conn, channel_at, channel_boundaries = _p1_world()
    report = wv.verify_window_semantics(conn, factor_rows=P1_ROWS("P1", "9.0.0"), channel_at=channel_at,
                                        channel_boundaries=channel_boundaries, policy=wv.POLICY_VERSION, **GRAIN)
    assert report["numeric_reproduced"] == 1 and report["status"] == "VERIFIED"
    assert draft.peak_instant == _d(4)
    with pytest.raises(RuntimeError, match="peak"):
        wv.verify_window_semantics(conn, factor_rows=P1_ROWS("P1", "9.0.0"), channel_at=channel_at,
                                   channel_boundaries=lambda rec, lo, hi: [], policy=wv.POLICY_VERSION, **GRAIN)


def test_w6_a_qualified_p1_member_with_no_channel_derivation_is_still_refused(monkeypatch):
    monkeypatch.setattr(wv, "_row_state", lambda row, rec, d, v: ("const", 0.5))
    _, conn, _, _ = _p1_world()
    with pytest.raises(RuntimeError, match="no channel derivation"):
        wv.verify_window_semantics(conn, factor_rows=P1_ROWS("P1", "9.0.0"), policy=wv.POLICY_VERSION, **GRAIN)


# ── W-7: the solver_check switch reports what ran ────────────────────────────────────────────────────────────────────

def _fn_world():
    """One function-valued (angular kernel) member: only the structural bounds can be checked here."""
    rec = _rec("k", path="P3", version="1.0.0", relation="conjunction", kind="house_lord", supports=((0, 10),),
               delta_lambda_at=lambda t: 1.0)
    (draft,), _ = _draft([rec], lambda p, v: _rows_declared(p, v, orb=5.0))
    stored = (_stored(draft)[:3] + (_d(5), 0.8, 0.8, 0.0, None, [], "mixed", None, None, None))
    records = [("k", "root-k", "conjunction", "house_lord", "jupiter", None, _d(0), _d(10))]
    return _Conn([stored], records, [("w", "k")])


def _verify_fn_world(**kw):
    return wv.verify_window_semantics(
        _fn_world(), factor_rows=_rows_declared("P3", "1.0.0", orb=5.0), dynamic_enabled=True, policy=wv.POLICY_VERSION,
        **{**GRAIN, "path_id": "P3", "rule_version": "1.0.0"}, **kw)


def test_w7_a_deferred_solver_check_is_counted_as_deferred_and_never_satisfies_a_gate():
    deferred = _verify_fn_world(solver_check=False)
    assert deferred["solver_check_requested"] is False
    assert deferred["solver_check_deferred_windows"] == 1 and deferred["unverified_dynamic"] == 1
    assert deferred["solver_checked_windows"] == 0
    assert deferred["status"] == "UNVERIFIED_DYNAMIC" and not wv.satisfies_gate(deferred)


def test_w7_requesting_the_check_defers_nothing_and_does_not_claim_a_check_that_no_code_ran():
    run = _verify_fn_world(solver_check=True)
    assert run["solver_check_requested"] is True and run["solver_check_deferred_windows"] == 0
    assert run["solver_checked_windows"] == 0 and not wv.satisfies_gate(run)


def test_w7_with_the_dynamic_switch_off_the_writers_switch_changes_nothing():
    """The writer's real configuration (`dynamic_enabled` False): a function-valued window is blank under the named switch,
    so there is nothing to defer — the deferral note is absent and the report is the pre-W0 one."""
    rec = _rec("k", path="P3", version="1.0.0", relation="conjunction", kind="house_lord", supports=((0, 10),),
               delta_lambda_at=lambda t: 1.0)
    (draft,), _ = _draft([rec], lambda p, v: _rows_declared(p, v, orb=5.0), allow_dynamic=False)
    conn = _Conn([_stored(draft)], [("k", "root-k", "conjunction", "house_lord", "jupiter", None, _d(0), _d(10))],
                 [("w", "k")])
    # S3: `dynamic_enabled` now follows the table (solved under window_qualification/1); the RETIRED switch is asked for by name
    report = wv.verify_window_semantics(conn, factor_rows=_rows_declared("P3", "1.0.0", orb=5.0), solver_check=False, dynamic_enabled=False,
                                        policy=wv.POLICY_VERSION, **{**GRAIN, "path_id": "P3", "rule_version": "1.0.0"})
    assert report["solver_check_deferred_windows"] == 0 and report["status"] == "VERIFIED"
