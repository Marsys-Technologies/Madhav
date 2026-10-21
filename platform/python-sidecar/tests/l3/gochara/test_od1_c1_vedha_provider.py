"""SR-OD1 C1 — the builder's vedha provider, the structured sweep adapter and the named reasons.

Doctrine under test (owner-confirmed 2026-10-21; `DECISIONS_SURROGATE.jsonl` VEDHA-SOURCE, ND-NODE-VEDHA, ND-VIPAREETA; text
fast/owner-doctrine-answers/ANSWERS.md v2.1 §C), each claim with its classical source:

  C1-1 a graha in the vedha house nullifies the favourable transit and a node IS a graha for this purpose — Phaladīpikā XXVI.3-8
       "planets other than …" (phaladeepika:PG322:C1, PG323:C1), XXVI.2 / XXVI.24 treat Rāhu and Ketu as grahas (ND-NODE-VEDHA i);
  C1-2 a TRANSITING node carries no vedha factor: the six L0 node rows are UNSOURCED (ND-NODE-VEDHA ii) ⇒ declared not-applicable;
       adverse residence and an uncited (graha, house) are declared not-applicable too (XXVI.3-8 cite favourable houses only);
  C1-3 the vedha is a STEP of the sky with COMPLETE edges: the window's peak is the exact edge where the obstruction ends;
  C1-4 an obstructor whose residence is not established is UNKNOWN, never 'not obstructing' — and the sweep carries the derivation's
       NAMED reason through (`obstructor_residence_unknown`), not its generic `objective_unknown_over_component`;
  C1-5 the value of a state is the registry row's own mapping (active 0, inactive 1: XXVI.3 "nullify the good effect"); a source that
       disagrees with the row is refused;
  C1-6 the measuring profile is untouched: the overlay stays unbound there, bound only under the final (doctrine) profile.

The recording connection below answers the provider's two reads (the L0 pairs, the stored residence contacts); what only SQL does is
checked in `test_od1_c1_vedha_provider_db.py`.
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import vedha_source as vs
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.window_sweep import SweepRecord, SweepRefusal
from services.gochara_rules import registry as reg
from services.gochara_rules.vedha_derive import MOON_SCOPE

FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "gochara_rules" / "fixtures" / "l0_vedha_rows_2026_10_02.json"
PAIR_ROWS = [tuple(r) for r in json.loads(FIXTURE.read_text())]
T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
CHART, GEN, CLS = "482012f1-710e-4a25-994a-93821f5871aa", "5.0", "marriage"
MOON_SIGN = 11                                           # an Aquarius Moon: Aries is the 3rd, Libra the 9th
VREF = ("vedha_attenuation", reg.KERNEL_VERSION)


def D(day: float) -> datetime:
    return T0 + timedelta(days=day)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *_a, **_k):
        return self

    def fetchall(self):
        return self._rows


class _Conn:
    """Answers the provider's two reads and records them."""

    def __init__(self, contacts):
        self.contacts = contacts
        self.reads: list = []

    def cursor(self):
        return _Result(PAIR_ROWS)

    def execute(self, sql, params=()):
        self.reads.append((sql, params))
        return _Result(self.contacts)


def world(**overrides):
    """Residence contacts: everyone parked in Pisces (span:2) for the whole year, then `overrides` {body: [(sign, d_in, d_out)]}."""
    rows = []
    for body in vs._OBSTRUCTOR_BODIES:
        spans = overrides.get(body, [(2, -5, 400)])
        rows += [(body, f"span:{sign}", D(a), None if b is None else D(b)) for sign, a, b in spans]
    return rows


def sign_of(house: int) -> int:
    """The sign that is `house` from the Moon sign (whole-sign, inclusive count)."""
    return (house - 1 + MOON_SIGN - 1) % 12 + 1


def p2(rid, agent, house, sign=None, supports=((10, 40),)):
    sign = sign_of(house) if sign is None else sign
    return SweepRecord(record_id=rid, root_id=f"root-{rid}", path_id="P2", rule_version=reg.KERNEL_VERSION, relation="residence",
                       object_kind="sign_span", agent=agent, operator_role="scored", admission_state="admitted",
                       supports=tuple((D(a), D(b)) for a, b in supports), house_from_frame=house,
                       canonical_target=f"span:{sign}")


SUN = lambda **kw: p2("sun", "sun", 3, **kw)             # noqa: E731 - the Sun in Aries, the 3rd from the Moon: its vedha house is the 9th (Libra)


def provider(contacts, records, **kw):
    return vs.SOURCE.for_grain(_Conn(contacts), chart_id=CHART, generation=GEN, event_class=CLS, records=records, **kw)


# ── C1-1 / C1-3: the derivation over stored contacts ─────────────────────────────────────────────────────────────────────
def test_c1_1_a_node_in_the_vedha_house_nullifies_like_any_graha_and_the_overlay_is_a_tiled_step():
    rec = SUN()
    prov = provider(world(mars=[(2, -5, 20), (7, 20, 25), (2, 25, 400)], ketu=[(2, -5, 30), (7, 30, 35), (2, 35, 400)]), [rec])
    ov = prov.overlay(rec, VREF)
    assert ov.applicable and ov.complete
    assert [(s.t_in, s.t_out, s.state, s.value, s.obstructors) for s in ov.segments] == [
        (D(10), D(20), "inactive", 1.0, ()), (D(20), D(25), "active", 0.0, ("Mars",)), (D(25), D(30), "inactive", 1.0, ()),
        (D(30), D(35), "active", 0.0, ("Ketu",)), (D(35), D(40), "inactive", 1.0, ())]
    assert ov.boundaries(D(10), D(40)) == [D(20), D(25), D(30), D(35)]          # every edge strictly inside the support, none missing
    assert ov.value_at(D(22)) == 0.0 and ov.value_at(D(27)) == 1.0 and ov.value_at(D(40)) is None
    assert {s.scope for s in ov.segments if s.value == 1.0} == {MOON_SCOPE} and ov.scopes == [MOON_SCOPE]     # the Moon label stays (Q11 a)


def test_c1_2_adverse_residence_uncited_house_and_a_transiting_node_are_declared_not_applicable():
    recs = [p2("sat8", "saturn", 8), p2("sun9", "sun", 9), p2("rahu3", "rahu", 3), p2("ketu6", "ketu", 6)]
    prov = provider(world(), recs)
    for rec in recs:
        ov = prov.overlay(rec, VREF)
        assert not ov.applicable and ov.not_applicable_reason == "no_cited_vedha_pair_for_this_house" and ov.segments == ()
    assert prov.summary()["applicable"] == 0 and prov.summary()["not_applicable"] == 4


def test_c1_4_an_open_contact_with_no_horizon_is_missing_data_never_inactivity():
    rec = SUN()
    prov = provider(world(mars=[(2, -5, 20), (7, 20, None)]), [rec])      # Mars' last contact is stored with no end and no horizon closed it
    ov = prov.overlay(rec, VREF)
    assert [(s.t_in, s.t_out, s.state, s.reason) for s in ov.segments] == [
        (D(10), D(20), "inactive", None), (D(20), D(40), "unqualified", "obstructor_residence_unknown")]
    assert prov.summary()["open_contacts_without_horizon"] == 1 and ov.value_at(D(30)) is None
    assert ov.unknown_reason_at(D(30)) == "obstructor_residence_unknown" and ov.unknown_reason_at(D(15)) is None


def test_c1_provider_reads_lazily_and_only_the_obstructor_bodies_residence_of_the_grain():
    conn = _Conn(world())
    prov = vs.SOURCE.for_grain(conn, chart_id=CHART, generation=GEN, event_class=CLS, records=[SUN()])
    assert conn.reads == []                                                  # nothing read until a record needs it
    prov.overlay(SUN(), VREF)
    ((sql, params),) = conn.reads
    assert "relation_kind = 'residence'" in sql and params == (CLS, CHART, GEN, list(vs._OBSTRUCTOR_BODIES))
    assert "rahu" in params[3] and "ketu" in params[3] and "moon" not in params[3]       # nodes are obstructors; the Moon is never stored


def test_c1_the_moon_sign_is_the_one_the_stored_records_imply_and_a_disagreement_is_refused():
    rec = SUN()
    assert provider(world(), [rec]).overlay(rec, VREF).applicable
    with pytest.raises(vs.VedhaSourceError, match="imply"):
        provider(world(), [rec, p2("clash", "mars", 4, 1)]).overlay(rec, VREF)
    with pytest.raises(vs.VedhaSourceError, match="not the supplied"):
        provider(world(), [rec], moon_sign=5).overlay(rec, VREF)
    assert provider(world(), [rec], moon_sign=MOON_SIGN).overlay(rec, VREF).applicable


def test_c1_overlapping_stored_residence_of_one_graha_is_refused():
    rec = SUN()
    with pytest.raises(vs.VedhaSourceError, match="overlap"):
        provider(world(mars=[(2, -5, 30), (7, 20, 400)]), [rec]).overlay(rec, VREF)


# ── the structured adapter in the sweep ─────────────────────────────────────────────────────────────────────────────────────
def draft(records, contacts, rows_for=None, **kw):
    prov = provider(contacts, records)
    return ws.draft_windows(CLS, records, rows_for or ws.registry_factor_rows, vedha=prov, allow_dynamic=True, **kw)[0]


def test_c1_3_the_peak_is_the_exact_edge_where_the_obstruction_ends():
    rec = SUN()
    (w,) = draft([rec], world(mars=[(2, -5, 10), (7, 10, 25), (2, 25, 400)]))
    assert w.score == 1.0 and w.evidence_for == 1.0 and w.peak_instant == D(25)       # earliest instant of the max: the vedha's own edge
    (clear,) = draft([rec], world())
    assert clear.score == 1.0 and clear.peak_instant == D(10)                         # nothing obstructs: the maximum is at the start
    # an island of clearness far narrower than any sampling grid (1.2 h in 30 days) is found only because the edges are SUPPLIED
    (island,) = draft([rec], world(mars=[(7, -5, 20.1), (2, 20.1, 20.15), (7, 20.15, 400)]))
    assert island.score == 1.0 and island.peak_instant == D(20.1)


def test_c1_1_a_node_obstruction_moves_the_window_exactly_like_a_graha_would():
    rec = SUN()
    (by_node,) = draft([rec], world(rahu=[(2, -5, 10), (7, 10, 25), (2, 25, 400)]))
    (by_mars,) = draft([rec], world(mars=[(2, -5, 10), (7, 10, 25), (2, 25, 400)]))
    assert by_node.peak_instant == D(25) and by_node.score == 1.0
    assert (by_node.peak_instant, by_node.score, by_node.evidence_for) == (by_mars.peak_instant, by_mars.score, by_mars.evidence_for)


def test_c1_4_an_unknown_stretch_carries_the_derivations_named_reason_not_the_generic_one():
    rec = SUN()
    (w,) = draft([rec], world(mars=[(2, -5, 30)]))                                    # Mars' residence is established only until day 30
    assert w.score is None and w.unqualified_reason == "obstructor_residence_unknown"
    assert "obstructor_residence_unknown" in w.unresolved and ws.UNKNOWN_OVER_COMPONENT not in w.unresolved


def test_c1_a_record_the_factor_does_not_apply_to_takes_no_part_in_the_product():
    sat = p2("sat8", "saturn", 8)
    (w,) = draft([sat], world())
    assert w.unresolved == {} and w.score == 1.0                                       # adverse residence: no vedha reason, never a silent 1 or a blank


def test_c1_the_1_0_0_row_declares_no_mapping_so_a_derived_state_has_nothing_to_map_to():
    rows = lambda p, v: ws.registry_factor_rows("P2", "1.0.0")           # noqa: E731
    (w,) = draft([SUN()], world(), rows_for=rows)
    assert w.score is None and w.unresolved == {"applicability_undeclared": 1}


def test_c1_5_a_source_whose_value_disagrees_with_the_rows_mapping_is_refused():
    class Liar:
        def overlay(self, rec, ref):
            seg = vs.Segment(D(10), D(40), "active", 0.5, None, None, ("Mars",))           # XXVI.3: an obstruction NULLIFIES (0.0)
            return vs.RecordOverlay(applicable=True, segments=(seg,), complete=True)
    with pytest.raises(SweepRefusal, match="maps 'active'"):
        ws.draft_windows(CLS, [SUN()], ws.registry_factor_rows, vedha=Liar(), allow_dynamic=True)


def test_c1_incomplete_boundaries_from_a_source_make_the_record_unqualified_not_assumed_whole():
    class Partial:
        def overlay(self, rec, ref):
            return vs.RecordOverlay(applicable=True, segments=(vs.Segment(D(10), D(40), "inactive", 1.0, None, MOON_SCOPE),), complete=False)
    (w,) = ws.draft_windows(CLS, [SUN()], ws.registry_factor_rows, vedha=Partial(), allow_dynamic=True)[0]
    assert w.score is None and w.unresolved == {ws.STATE_BOUNDARIES_REASON: 1}


# ── C1-6: the binding follows the rule profile ──────────────────────────────────────────────────────────────────────────────
def test_c1_6_the_overlay_is_bound_only_under_the_final_profile_and_an_explicit_binding_wins(monkeypatch):
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from services.gochara_kernel import rule_registry as rr
    assert writer.VEDHA_SOURCE is None
    assert writer.vedha_source() is None and writer._l0_consumed() == ()                       # the measuring profile, byte for byte
    with rr.rule_profile(final_rules=True):
        assert writer.vedha_source() is vs.SOURCE and writer._l0_consumed() == (
            "bg_transit_rules", "bg_combustion_orbs", "bg_dignity_reference", "bg_graha_naisargika_friendship")
        monkeypatch.setattr(writer, "VEDHA_SOURCE", lambda rec, t: 0.5)
        assert writer.vedha_source() is writer.VEDHA_SOURCE
    assert writer.vedha_source() is writer.VEDHA_SOURCE                                         # explicit binding, any profile
