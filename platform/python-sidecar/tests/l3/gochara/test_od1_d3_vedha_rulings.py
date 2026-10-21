"""SR-OD1 D3 — the owner-confirmed vedha rulings bound into the vedha rows (vedha_attenuation@1.3.0 / P2@1.3.0) and agreed by BOTH sides.

Rulings (owner, 2026-10-21; `DECISIONS_SURROGATE.jsonl`: VEDHA-SOURCE, ND-NODE-VEDHA, ND-VIPAREETA; text
fast/owner-doctrine-answers/ANSWERS.md v2.1 §C Q8-Q11). Each claim below has ONE oracle; the classical source is cited with it:

  D3-1 a Rāhu/Ketu in a planet's vedha house OBSTRUCTS it like any graha — Phaladīpikā XXVI.3-8 say "planets other than …" /
       "void of planets" (phaladeepika:PG322:C1, PG323:C1) and the chapter treats the nodes as grahas (XXVI.2, XXVI.24); the builder's
       provider and the verifier's own derivation return the SAME step function (revert: nodes dropped from the obstructor set);
  D3-2 a TRANSITING node's own favourable transit carries NO vedha factor (the Sun's pairs, vedha place = 7th from the favourable house,
       would be obstructed by the partner node 100 % of the time): declared not-applicable on both sides, and its window is NOT blanked
       and NOT scaled by the partner node's presence (revert: the nodes get the Sun's pairs);
  D3-3 no vipāreeta cancellation in this version — a companion planet joining the transiting planet in its favourable house does NOT lift
       the vedha (bphs:PG313:C1 is commentary-grade and stays out; XXVI.3-8 state no cancellation) (revert: a companion cancels);
  D3-4 the row declares what the derivation does (earned signal, N.8): `vedha_attenuation@1.3.0` promises exactly the unqualified reasons
       the derivation can emit and not `node_obstruction_undecided`; the sealed 1.1.0 row is untouched (revert: restore the old reason);
  D3-5 the rulings are ledger refs (B.3): the row's selector, the P2@1.3.0 path row, the build's ruling list (identity) and the provider's
       summary all carry VEDHA-SOURCE / ND-NODE-VEDHA / ND-VIPAREETA; P2@1.3.0 no longer promises "vipareeta cancellation" (revert: drop one);
  D3-6 the binding: the FINAL profile binds and selects P2@1.3.0 + vedha_attenuation@1.3.0 (1.1.0 unbound), the measuring profile is
       byte-identical, and BOTH inventory sides supersede P2@1.0.0 / 1.1.0 by 1.3.0 on the ruling VEDHA-SOURCE (revert: leave P2 at 1.1.0);
  D3-7 the trial count: with the final-profile binding no vedha-bearing P2 window carries `vedha_overlay_not_bound` (control: unbound ⇒ all do).
"""
from __future__ import annotations

import dataclasses

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import inventory_verifier as ver
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import vedha_source as vs
from services.gochara_kernel import vedha_verifier as vv
from services.gochara_kernel import window_sweep as ws
from services.gochara_rules import registry as reg
from services.gochara_rules import vedha_derive as vd

from .test_od1_c1_vedha_provider import CHART, CLS, GEN, MOON_SIGN, D, _Conn, p2 as _p2, sign_of, world
from .test_od1_c2_vedha_verifier import FakeConn

DOC = reg.DOCTRINE_VERSION
VREF = ("vedha_attenuation", DOC)
RULING_IDS = ("VEDHA-SOURCE", "ND-NODE-VEDHA", "ND-VIPAREETA")


def p2(rid, agent, house):
    """A P2 record of the owner-confirmed rule version (1.3.0): the sweep reads its factor rows from THAT version's path row."""
    return dataclasses.replace(_p2(rid, agent, house), rule_version=DOC)


@pytest.fixture
def final():
    with rr.rule_profile(final_rules=True):
        yield


def _provider(contacts, records):
    return vs.SOURCE.for_grain(_Conn(contacts), chart_id=CHART, generation=GEN, event_class=CLS, records=records)


# ── one world, two sides ─────────────────────────────────────────────────────────────────────────────────────────────────
def _both(records, contacts):
    """(builder overlays by record id, verifier overlay) over the SAME stored world. `records`: SweepRecords of path P2."""
    conn_rows = [(r.record_id, r.agent, r.house_from_frame, r.canonical_target, lo, hi) for r in records for lo, hi in r.supports]
    builder = _provider(contacts, records)
    verifier = vv.derive_overlay(FakeConn(records=conn_rows, residence=contacts), chart_id=CHART, generation=GEN, event_class=CLS,
                                 path_id="P2", rule_version=DOC, moon_sign=MOON_SIGN)
    return {r.record_id: builder.overlay(r, VREF) for r in records}, verifier, builder


def _shape(applicable, segments):
    """The comparable form of one record's answer, builder or verifier alike."""
    return applicable, [(s.t_in, s.t_out, s.state, s.value, s.reason, s.scope) for s in segments]


def _agree(records, contacts):
    built, verified, builder = _both(records, contacts)
    for r in records:
        b, v = built[r.record_id], verified(r.record_id)
        assert _shape(b.applicable, b.segments) == _shape(v.applicable, v.segments), r.record_id
    return built, verified, builder


SUN3 = lambda: p2("sun", "sun", 3)                      # noqa: E731 - the Sun in the 3rd from the Moon (Aries); its vedha place is the 9th (Libra)
V9 = sign_of(9)


# ── D3-1 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("node", ["rahu", "ketu"])
def test_d3_1_a_node_in_the_vedha_house_obstructs_and_builder_and_verifier_agree(node):
    rec = SUN3()
    built, verified, _ = _agree([rec], world(**{node: [(2, -5, 20), (7, 20, 25), (2, 25, 400)]}))
    assert built["sun"].value_at(D(22)) == 0.0 and built["sun"].value_at(D(30)) == 1.0
    assert [(s.t_in, s.t_out) for s in built["sun"].segments if s.state == "active"] == [(D(20), D(25))]
    assert verified("sun").value_at(D(22)) == 0.0 and verified("sun").unknown_reason_at(D(22)) is None     # an obstruction, never "undecided"


# ── D3-2 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_d3_2_a_transiting_nodes_own_transit_carries_no_vedha_factor_on_either_side():
    # Rāhu in the 3rd with Ketu — always its 7th — sitting in the Sun-pattern vedha place (the 9th) for the whole year
    rahu3, ketu6 = p2("rahu3", "rahu", 3), p2("ketu6", "ketu", 6)
    contacts = world(rahu=[(sign_of(3), -5, 400)], ketu=[(V9, -5, 400)])
    built, verified, _ = _agree([rahu3, ketu6], contacts)
    for rid in ("rahu3", "ketu6"):
        assert not built[rid].applicable and built[rid].segments == () and not verified(rid).applicable
        assert built[rid].not_applicable_reason == verified(rid).not_applicable_reason == "no_cited_vedha_pair_for_this_house"
    # in the window: the factor takes no part — the partner node's presence neither zeroes nor blanks it
    (w,) = ws.draft_windows(CLS, [rahu3], ws.registry_factor_rows, vedha=_provider(contacts, [rahu3]), allow_dynamic=True)[0]
    assert w.score == 1.0 and w.unresolved == {}


# ── D3-3 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_d3_3_a_companion_in_the_favourable_house_does_not_cancel_the_vedha_on_either_side():
    """bphs:PG313:C1 (translator's commentary): 'The moment another planet joins the Sun in the 3rd from the Moon, the Vedha in the 9th …
    is off'. The owner ruled it OUT of this version (ND-VIPAREETA); Venus is in the Sun's sign (the 3rd) the whole time while Mars sits in
    the 9th: the Sun is still nullified."""
    rec = SUN3()
    contacts = world(venus=[(sign_of(3), -5, 400)], mars=[(2, -5, 20), (V9, 20, 30), (2, 30, 400)])
    built, verified, _ = _agree([rec], contacts)
    assert built["sun"].value_at(D(25)) == 0.0 and verified("sun").value_at(D(25)) == 0.0
    states = {s.state for s in built["sun"].segments} | {s.state for s in verified("sun").segments}
    assert states <= {"active", "inactive", "unqualified"} and "cancelled_vipareeta" not in states


# ── D3-4 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _emitted_reasons(scenarios):
    out = set()
    for records, contacts in scenarios:
        built, verified, _ = _both(records, contacts)
        for r in records:
            out |= {s.reason for s in built[r.record_id].segments if s.reason}
            out |= {s.reason for s in verified(r.record_id).segments if s.reason}
    return out


def test_d3_4_the_1_3_0_row_promises_exactly_the_reasons_the_derivation_can_emit():
    scenarios = [
        ([SUN3()], world(mars=[(2, -5, 30)])),                                   # Mars' residence is established only to day 30 ⇒ unknown
        ([SUN3()], world(rahu=[], ketu=[])),                                     # node residence absent ⇒ unknown
        ([SUN3()], world(rahu=[(2, -5, 22), (7, 22, 400)])),                     # a node in the vedha house ⇒ an obstruction, not a reason
        ([SUN3()], world()),                                                     # quiet sky ⇒ inactive
    ]
    emitted = _emitted_reasons(scenarios)
    row = reg.FACTORS[VREF]
    declared = set(row["operand_selector"]["unqualified_reasons"])
    assert declared == set(row["applicability"]["unqualified_reasons"]) == emitted == {"obstructor_residence_unknown", "node_residence_unknown"}
    assert "node_obstruction_undecided" not in declared | emitted
    # the sealed 1.1.0 row is untouched (never an edit of a sealed row): it still promises the pre-ruling reason
    old = reg.FACTORS[("vedha_attenuation", reg.KERNEL_VERSION)]["operand_selector"]
    assert old["unqualified_reasons"] == ["obstructor_residence_unknown", "node_obstruction_undecided", "node_residence_unknown"]
    assert old["vipareeta_state"] == "not_produced_no_served_citation" and "ruling_refs" not in old


def test_d3_4_the_row_declares_the_three_choices_and_the_cited_step_mapping():
    sel = reg.FACTORS[VREF]["operand_selector"]
    assert (sel["map_active"], sel["map_inactive"]) == (0, 1)                    # XXVI.3 "nullify the good effect": a step, not a calibration
    assert sel["vedha_source"] == "phaladeepika_xxvi_3_8_house_vedha_only"       # VEDHA-SOURCE (Q8 a)
    assert sel["inactive_scope"] == "excluding_on_demand_moon_obstruction" and sel["scope_exempt_primaries"] == ["mercury"]   # Q11 a; XXVI.6
    assert (sel["node_as_obstructor"], sel["node_as_transiting_body"]) == ("obstructs_like_any_graha", "no_vedha_factor")    # ND-NODE-VEDHA i, ii
    assert sel["vipareeta_state"] == "not_produced_owner_ruled"                  # ND-VIPAREETA
    assert reg.FACTORS[VREF]["applicability"]["mapping"] == {"active": 0.0, "inactive": 1.0}


# ── D3-5 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_d3_5_the_rulings_are_ledger_refs_on_the_row_the_path_the_build_and_the_provider(final):
    assert reg.VEDHA_RULINGS == RULING_IDS and tuple(vs.RULINGS) == RULING_IDS
    assert reg.FACTORS[VREF]["operand_selector"]["ruling_refs"] == [r.lower().replace("-", "_") for r in RULING_IDS]
    path = reg.RULE_PATHS[reg.composite_ref("P2", DOC)]
    assert all(r in path["score_rule"] for r in RULING_IDS)
    assert "vipareeta cancellation per" not in path["note"] and "NO vipāreeta cancellation" in path["note"]
    assert reg.RULE_PATHS[reg.composite_ref("P2", reg.KERNEL_VERSION)]["note"].count("vipareeta cancellation per §5") == 1   # the sealed 1.1.0 row is untouched
    # the build identity: the three ids are in the ruling list whenever the vedha source is bound (final profile), and only then
    assert {r["id"] for r in writer._applicable_rulings()} >= set(RULING_IDS)
    prov = _provider(world(), [SUN3()])
    assert prov.summary()["rulings"] == sorted(RULING_IDS)                                  # the provider's notes carry them too


def test_d3_5_the_measuring_profile_carries_none_of_it():
    assert not {r["id"] for r in writer._applicable_rulings()} & set(RULING_IDS)


# ── D3-6 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_d3_6_the_final_profile_binds_and_selects_the_1_3_0_vedha_rows_and_the_measuring_profile_does_not(final):
    assert ("P2", DOC) in rr.bound_path_refs() and ("P2", reg.KERNEL_VERSION) not in rr.bound_path_refs()
    assert VREF in rr.bound_factor_refs() and ("vedha_attenuation", reg.KERNEL_VERSION) not in rr.bound_factor_refs()
    assert rr.selected_versions_for("marriage")["P2"] == DOC
    assert reg.RULE_PATHS[reg.composite_ref("P2", DOC)]["soft_factors"] == [VREF]
    assert not {r for r in rr.bound_path_refs() + rr.bound_factor_refs() if r[1] == DOC and r[0] in ("P2", "vedha_attenuation")} - {("P2", DOC), VREF}
    assert "h_table_version" not in reg.RULE_PATHS[reg.composite_ref("P2", DOC)]        # the Moon-frame residence path reads no H table


def test_d3_6_the_measuring_profile_still_binds_only_1_0_0():
    assert ("P2", DOC) not in rr.bound_path_refs() and ("vedha_attenuation", DOC) not in rr.bound_factor_refs()
    assert rr.selected_versions_for("marriage")["P2"] == "1.0.0"


def test_d3_6_both_inventory_sides_supersede_p2_1_0_0_and_1_1_0_by_1_3_0_on_the_vedha_ruling():
    for older in ("1.0.0", "1.1.0"):
        assert reg.DOCTRINE_SUPERSEDED_PATHS[("P2", older)] == {
            "superseded_by": ("P2", DOC), "ruling_ref": "VEDHA-SOURCE", "reason": "soft factors moved to the owner-confirmed 1.3.0 doctrine rows"}
        assert ver._DOCTRINE_SUPERSEDED[("p2", older)] == DOC
    assert inv.supersession_basis("P2", "1.0.0", DOC) == "ruling:VEDHA-SOURCE" == ver._supersession_basis("p2", "1.0.0", DOC)


# ── D3-7 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _trial_records():
    return [SUN3(), p2("sat8", "saturn", 8), p2("rahu3", "rahu", 3), p2("ketu6", "ketu", 6), p2("jup5", "jupiter", 5), p2("mars6", "mars", 6)]


def _not_bound_count(records, vedha):
    """`vedha_overlay_not_bound` over one window per record (each drafted alone, so the count is per vedha-bearing record)."""
    return sum(ws.draft_windows(CLS, [r], ws.registry_factor_rows, vedha=vedha, allow_dynamic=True)[0][0].unresolved
               .get("vedha_overlay_not_bound", 0) for r in records)


def test_d3_7_no_vedha_bearing_window_is_blank_vedha_overlay_not_bound_under_the_final_binding(final):
    recs = _trial_records()
    src = writer.vedha_source()
    assert src is vs.SOURCE
    bound = src.for_grain(_Conn(world(rahu=[(V9, -5, 400)])), chart_id=CHART, generation=GEN, event_class=CLS, records=recs)
    assert _not_bound_count(recs, bound) == 0
    # control: with no source (the measuring profile) every one of them is blank for exactly that reason
    assert _not_bound_count(recs, None) == len(recs)
