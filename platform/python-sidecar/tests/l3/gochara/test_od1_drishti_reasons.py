"""SR-OD1 od1-drishti-reasons — N-1 (ruling SR-D6-OBJECTIVE-UNKNOWN): an undeterminable dṛṣṭi read is NAMED, never the generic code.

Evidence for the guard (DIAG_P34 §3): at the lane head major_loss holds 0 `objective_unknown_over_component` windows and no node aspect record; the 58
undeterminable reads PRETR saw were boundary-instant artefacts that drishti-edge removed. This file pins the behaviour that keeps it so for every class.

Doctrine: O-CF-DRISHTI (BPHS 1:16496-16502 graduation table; Brihat Jātaka ii.13) defines a value at house offsets 3-10 only; N-14 nodes cast no dṛṣṭi;
B.3/B.10 no invented value; N.7.6 an honest null beats an invented judgment; N.8 a signal needs a detector that can read false.

Claims, each with ONE oracle (the single planted reversion that must fail it is named):

  (a)  a node as the ASPECTING agent is declared not-applicable at the inventory — excluded from the obligations, counted per class and path — and
       is never a window-level blank
       (revert: `evaluator._decline_node_aspect` records nothing -> the count is 0);
  (b1) an offset the bound rule DEFINES as zero reads 0.0 (numbered), not blank
       (revert: `drishti.graduated_drishti` ignores `DEFINED_ZERO_OFFSETS`);
  (b2) an offset the bound rule leaves UNDEFINED is the named blank `no_aspect_rule_defined_at_offset` — on the builder's side
       (revert: delete the `unknown_reason=` wiring in `window_sweep.graduated_drishti` -> the generic code appears);
  (b2v) ... and on the verifier's side, from its OWN call of the rule authority: its prover's finding carries the name, and a stored blank under the
       generic code (or another name) is refused
       (revert: `window_verifier._drishti_step` passes no `unknown_reason`);
  (c)  no drishti-undeterminable window ever carries the generic code: the generic code is not among the names the rule authority gives, and a window
       built over EVERY undeterminable operand the authority names carries the authority's name each time (revert: as b2).
       The G-2 gate itself lives in the harness (branch tr-bind, not in this tree): the closed-set edit and the gate run are in the job report.
  (d)  the value path is untouched: the same source answers the known offsets exactly as before and names no reason for them
       (revert: `_drishti_source` returns the reason in place of the value).
"""
from __future__ import annotations

import ast
import inspect
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import drishti as rules_drishti

from .test_a53_inventory import FULL, SEALED, _plan
from .test_a53_window_sweep import _d, _draft, _rec, _rows_declared

REF = ("graduated_drishti", "9.0.0")            # the synthetic row `_rows_declared` registers
NO_RULE = "no_aspect_rule_defined_at_offset"
GENERIC = "objective_unknown_over_component"


def _source():
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    return writer_mod.DRISHTI_SOURCE


def _stepping_record(offset_before, offset_after, *, day=5, agent="mars"):
    """An aspect record whose whole-sign offset steps at `day` (a stored ingress of the aspecting body)."""
    return _rec("a", path="P3", relation="aspect", kind="house_span", agent=agent, supports=((0, 10),),
                aspect_offset_at=lambda t: offset_before if t < _d(day) else offset_after,
                state_boundaries=lambda lo, hi: [_d(day)] if lo < _d(day) < hi else [], state_boundaries_complete=True)


# ── (a) a node as the aspecting agent: declared not-applicable at the inventory, counted per class ───────────────────────

def test_a_a_node_as_the_aspecting_agent_is_not_applicable_at_the_inventory_counted_per_class_and_path():
    plan = _plan("marriage", FULL)
    # nothing is searched for it: no obligation has a node as the agent of an aspect
    assert not [o for o in plan.obligations if o.relation == "aspect" and o.agent in ("rahu", "ketu")]
    # the independent expectation: the nodes would have had exactly as many aspect candidates as an ordinary agent has aspect obligations on the
    # house / lord targets (P3 emits the same house and lord edges for every agent; K-B kāraka targets are Jupiter/Saturn only)
    for path_id in ("P3", "P4"):
        sun = len([o for o in plan.obligations if o.path_id == path_id and o.agent == "sun" and o.relation == "aspect"])
        got = {n.agent: n.count for n in plan.not_applicable if n.path_id == path_id and n.reason == inv.NODE_CASTS_NO_DRISHTI}
        if path_id == "P3":
            assert got == {"rahu": sun, "ketu": sun} and sun > 0, (got, sun)
    assert plan.node_aspect_not_applicable == sum(n.count for n in plan.not_applicable) > 0
    # an N/A is an accounting beside the ledger: the obligations and pins are what they were
    assert all(n.reason == inv.NODE_CASTS_NO_DRISHTI == rules_drishti.graduated_drishti("Rahu", 7)["reason"] for n in plan.not_applicable)


def test_a_enumeration_without_a_sink_is_exactly_what_it_was():
    before = ev.enumerate_edges("marriage", "P3", _plan.__globals__["CHART"])
    with ev.node_aspect_declined() as declined:
        inside = ev.enumerate_edges("marriage", "P3", _plan.__globals__["CHART"])
    assert before == inside and declined and set(declined) == {"rahu", "ketu"}


def test_a_a_node_aspect_record_is_refused_never_a_window_blank():
    node = _rec("n", relation="aspect", agent="rahu", supports=((0, 10),), aspect_offset_at=lambda t: 7)
    with pytest.raises(ws.SweepRefusal, match="N-14"):
        _draft([node], _rows_declared, drishti=_source())


# ── (b2) an offset the bound rule leaves undefined: the named blank, builder side ───────────────────────────────────────

@pytest.mark.parametrize("solver", [None, ws.PRODUCTION_SOLVER], ids=["legacy_piece_scan", "certified_solver"])
def test_b2_an_undefined_offset_is_blank_under_the_rule_authoritys_own_name(solver):
    kw = {} if solver is None else {"solver": solver, "allow_dynamic": False}      # one engine per window
    (w,), _ = _draft([_stepping_record(7, 6)], _rows_declared, drishti=_source(), **kw)
    assert w.peak_instant is None and w.score is None
    assert w.unqualified_reason == NO_RULE != GENERIC
    assert w.unresolved == {NO_RULE: 1} and GENERIC not in w.unresolved


def test_b2_a_record_undefined_over_its_whole_support_is_blank_under_the_same_name():
    rec = _rec("a", path="P3", relation="aspect", kind="house_span", agent="mars", supports=((0, 10),), aspect_offset_at=lambda t: 6)
    (w,), _ = _draft([rec], _rows_declared, drishti=_source())
    assert w.score is None and w.unqualified_reason == NO_RULE


def test_b2_a_source_with_no_reason_still_falls_back_to_the_generic_code():
    """The fallback is for an operand NO factor names (W0): a bare callable source names nothing."""
    (w,), _ = _draft([_stepping_record(7, 6)], _rows_declared, drishti=lambda a, o, r: {7: 1.0}.get(o))
    assert w.unqualified_reason == GENERIC


# ── (b1) an offset the bound rule defines as zero is a computed fact ────────────────────────────────────────────────────

def test_b1_an_offset_the_rule_defines_as_zero_reads_zero_numbered_not_blank(monkeypatch):
    # no BOUND row defines a zero today: the declaration table is empty (the real rows leave 1, 2, 6, 11, 12 undefined)
    assert rules_drishti.DEFINED_ZERO_OFFSETS == {}
    monkeypatch.setitem(rules_drishti.DEFINED_ZERO_OFFSETS, REF, frozenset({6}))
    assert rules_drishti.graduated_drishti("Mars", 6, factor_ref=REF)["value"] == 0.0
    whole = _rec("z", path="P3", relation="aspect", kind="house_span", agent="mars", supports=((0, 10),), aspect_offset_at=lambda t: 6)
    (w,), _ = _draft([whole], _rows_declared, drishti=_source())
    assert w.unqualified_reason is None and w.peak_instant is not None and w.score == 0.0
    # the declaration is per rule version and per offset: another offset of the same version, and the same offset of another version, stay undefined
    assert rules_drishti.graduated_drishti("Mars", 11, factor_ref=REF)["reason"] == NO_RULE
    assert rules_drishti.graduated_drishti("Mars", 6, factor_ref=("graduated_drishti", "1.1.0"))["reason"] == NO_RULE
    # the maximum over a window is still taken over the defined values: 1.0 before the step, a defined 0.0 after it
    (s,), _ = _draft([_stepping_record(7, 6)], _rows_declared, drishti=_source())
    assert s.score == 1.0 and s.peak_instant == _d(0)


# ── (d) the value path is untouched ─────────────────────────────────────────────────────────────────────────────────────

def test_d_the_known_offsets_keep_their_values_and_name_no_reason():
    src, why = _source(), _source().reason
    ref = ("graduated_drishti", "1.1.0")
    for agent, offset, value in (("jupiter", 7, 1.0), ("saturn", 3, 1.0), ("jupiter", 5, 1.0), ("mars", 4, 1.0), ("sun", 3, 0.25), ("sun", 5, 0.5), ("sun", 4, 0.75)):
        assert src(agent, offset, ref) == value, (agent, offset)
        assert why(agent, offset, ref) is None, (agent, offset)
    assert src("mars", 6, ref) is None and why("mars", 6, ref) == NO_RULE
    assert src("rahu", 7, ref) is None and why("rahu", 7, ref) == "node_casts_no_drishti"
    # the (agent, offset, ref) -> value signature every caller relies on is unchanged
    assert list(inspect.signature(src).parameters) == ["agent", "offset", "factor_ref"]


# ── (b2v) the verifier names the reason with its OWN call of the rule authority ─────────────────────────────────────────

class _NoIngress:
    def execute(self, sql, params=()):
        return type("C", (), {"fetchall": lambda s: []})()


def _aries(body, t):
    return 10.0                                  # the aspecting body sits in sign 0 throughout


def _prover_over_offset(target):
    """The verifier's prover over a 4-day support whose whole-sign offset is `target`'s sign index + 1 (the body is in Aries)."""
    step = wv._drishti_step(_NoIngress(), {"id": "r", "agent": "mars", "boundaries_complete": True},
                            {"factor_id": "graduated_drishti", "rule_version": "1.1.0"}, target, _aries)
    t0 = datetime(2011, 6, 4, tzinfo=timezone.utc)
    lo, hi = t0, t0 + timedelta(days=4)
    return chk.check_window(lo=lo, hi=hi, records=[chk.CheckRecord(record_id="r", root="R", agent="mars", supports=((lo, hi),), steps=(step,))],
                            objective=chk.OBJ_SUM, stored=chk.StoredWindow(peak_instant=lo, objective_value=0.0), position_at=_aries)


def test_b2v_the_verifiers_prover_names_the_undefined_offset_from_its_own_rule_call():
    report = _prover_over_offset("span:6")                     # Aries -> sign 6 (Virgo? index 5): offset 6, undefined
    undet = [f for f in report.findings if f.code == chk.F_UNDET]
    assert undet and {f.reason for f in undet} == {NO_RULE}
    # and the builder's source names the same thing for the same operand: two derivations, one name
    assert _source().reason("mars", 6, ("graduated_drishti", "1.1.0")) == NO_RULE


def test_b2v_a_stored_blank_must_carry_the_name_the_independent_derivation_gives():
    report = _prover_over_offset("span:6")
    assert wv._unknown_name_problem(NO_RULE, report) is None                         # the right name passes
    assert wv._unknown_name_problem(GENERIC, report) is not None                     # the generic code where an operand names its reason: a dropped name
    assert wv._unknown_name_problem("agent_unrecognised", report) is not None        # another dṛṣṭi name: a changed name
    assert wv._unknown_name_problem("monotone_arc_not_established", report) is None  # a non-dṛṣṭi reason is not this check's business
    defined = _prover_over_offset("span:8")                                          # offset 8 is defined: nothing undeterminable, nothing to name
    assert not [f for f in defined.findings if f.code == chk.F_UNDET]
    assert wv._unknown_name_problem(GENERIC, defined) is None


def test_b2v_the_verifier_imports_no_builder_module_for_the_name():
    builder = {"window_sweep", "window_store", "window_solver", "ka_gochara_v5"}
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(wv))):
        if isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[-1])
            names.update(a.name for a in node.names)
    assert not names & builder, names & builder


# ── (c) the generic code never stands for a dṛṣṭi operand the authority can name ────────────────────────────────────────

def test_c_every_undeterminable_operand_the_authority_names_reaches_the_window_under_that_name():
    ref = REF
    named = {}
    for agent in ("sun", "mars", "rahu", "pluto"):
        for offset in (0, 1, 2, 6, 11, 12, 13):
            out = rules_drishti.graduated_drishti(agent.title(), offset, factor_ref=ref)
            if out["value"] is None:
                named[(agent, offset)] = out["reason"]
    assert set(named.values()) == {"node_casts_no_drishti", "agent_unrecognised", "offset_not_an_inclusive_house_count_1_12", NO_RULE}
    assert GENERIC not in named.values() and set(named.values()) <= set(wv.DRISHTI_UNKNOWN_REASONS)
    for (agent, offset), reason in named.items():
        if agent in ("rahu", "pluto"):
            continue                                  # a node record never reaches a window (a); an unknown token is no record
        rec = _rec("a", path="P3", relation="aspect", kind="house_span", agent=agent, supports=((0, 10),), aspect_offset_at=lambda t, _o=offset: _o,
                   state_boundaries=lambda lo, hi: [], state_boundaries_complete=True)
        (w,), _ = _draft([rec], _rows_declared, drishti=_source())
        assert w.score is None and w.unqualified_reason == reason != GENERIC, (agent, offset, w.unqualified_reason)


# ── (b2v) the verifier's production refusal, driven through verify_window_semantics ────────────────────────────────────

def test_b2v_verify_window_semantics_refuses_a_stored_blank_that_dropped_the_dristi_reason():
    """The only production path that turns `_unknown_name_problem` into a refusal is the structural-blank branch of `verify_window_semantics`. World: Jupiter
    drifts 0.01 deg/day and leaves Aries for Taurus on day 5; the target point 180.3 deg is in Libra (sign 6), so the whole-sign offset is 7 before day 5
    (defined: full aspect) and (6 - 1) % 12 + 1 = 6 after it — an offset the bound rule (BPHS 1:16496-16502: 3-10 only) leaves undefined, which the rule
    authority names `no_aspect_rule_defined_at_offset`.
    The builder's blank (the rule's own name) is VERIFIED; the same blank stored under the generic code (the dropped name — the exact defect this lane exists to
    stop) is REFUSED, the problem naming the reason the independent derivation gives.
    Planted reversion: `window_verifier.verify_window_semantics` does not act on `_unknown_name_problem` (`name_problem = None`) -> the generic blank is
    'reproduced' and the pytest.raises below fails."""
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from .test_od1_s3_integration import GRAIN_P3, ROWS, _Cov, _d, _position, _verify

    def jup(t):
        return 29.95 + 0.01 * (t - _d(0)).total_seconds() / 86400.0
    pos = _position({"jupiter": jup})
    rec = _rec("A", path="P3", agent="jupiter", root="RA", supports=((0, 10),), relation="aspect", kind="degree_point", target="point:180.3",
               longitude_at=jup, aspect_rays=(240.0,), state_boundaries=lambda lo, hi: [c for c in (_d(5),) if lo < c < hi], state_boundaries_complete=True,
               aspect_offset_at=lambda t: 7 if t < _d(5) else 6)
    (draft,) = ws.draft_windows("marriage", [rec], ROWS, drishti=writer.DRISHTI_SOURCE, solver=ws.PRODUCTION_SOLVER)[0]
    assert draft.peak_instant is None and draft.unqualified_reason == NO_RULE
    kw = dict(grain=GRAIN_P3, ingress={"jupiter": [_d(5)]}, completed=_Cov(_d(-100), _d(100)), drishti_bound=True)
    ok = _verify([draft], [rec], ROWS("P3", "1.0.0"), pos, **kw)
    assert ok["status"] == "VERIFIED" and ok["solver_blank_windows"] == {NO_RULE: 1}
    dropped = draft.__class__(**{**draft.__dict__, "unqualified_reason": GENERIC, "unresolved": {GENERIC: 1}})
    with pytest.raises(RuntimeError, match=rf"the independent derivation names the undeterminable operand \['{NO_RULE}'\]"):
        _verify([dropped], [rec], ROWS("P3", "1.0.0"), pos, **kw)
