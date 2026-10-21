"""SR-OD1 R5 — the governed subject of every P1 factor is the record's `period_anchor_lord` (fallback: its agent), on BOTH sides.

Ruling: SR-PLAN-REVIEW-RECONCILED R-5 (GPT B6: the builder judged `period_anchor_lord or agent`, the checker and the verifier's SQL judged
`agent` only, so every delivery record would have disagreed). Doctrine: ANSWERS.md v2.1 §B.1 (P1 judges the PERIOD LORD's strength) and the
Form B table §B.3; Phaladīpikā XX.34-38 (the lord's strength is judged where the lord itself stands, however the delivery reaches the native).
The oracle is a delivery record — transiting AGENT the Sun, period ANCHOR Jupiter — whose two possible subjects stand in OPPOSITE Form B
cells: the Sun in Aries is exalted (malefic EX, favourable 1.0) while Jupiter in Capricorn is debilitated (benefic DEB, adverse 1.0), and
Jupiter then enters Aquarius (benefic NEU, favourable 0.125). The expected cells are typed from the owner's table in `test_od1_d2_form_b.OWNER`
(a literal copy of ANSWERS §B.3), never read back from the code under test. No database, no personal data.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  R1 the verifier evaluates a delivery record by its ANCHOR's sky, side and value                 (revert: `subject_of` returns the agent)
  R2 the verifier's evaluation cache is keyed by the SUBJECT, so two records of one agent anchored
     at different lords never share an entry                                                      (revert: key (agent, t))
  R3 the verifier cuts the delivery record's pieces at the ANCHOR's change instants               (revert: boundaries of the agent)
  R4 the verifier's per-record prerequisite (L0 row) check is the anchor's                         (revert: problem read for the agent)
  R5 the verifier's record SQL selects the anchor (a P1 grain), and only for P1                    (revert: the column dropped from the SELECT)
  R6 the BUILDER's sources for a delivery record give the ANCHOR's side and value per instant     (revert: `attach` reads `rec.agent`)
  R7 builder and verifier reproduce one delivery window end to end (stored by the builder, refused
     when the anchor is lost)                                                                     (differential: the R5/R6 reversions fail it)
"""
from __future__ import annotations

import dataclasses

import pytest

from services.gochara_kernel import p1_operands as P
from services.gochara_kernel import p1_operands_check as chk
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import p1_inputs as p1

from .test_a53_window_sweep import _d, _draft, _rec
from .test_od1_d2_form_b import (A, AGAINST, COMB, DIG, F, FOR, GAIN, MAPPING, NAIS, OWNER, ROWS, expected_channel, l0, lon)
from .test_od1_w0_interface import _Conn, _stored

SUN_LON = lon("Aries", 10)                       # the Sun, the transiting AGENT: exalted (malefic EX, favourable 1.0)
JUP_START = lon("Capricorn", 29.0)               # Jupiter, the period ANCHOR: debilitated (benefic DEB, adverse 1.0) …
JUP_SPEED = 0.2                                  # … until it enters Aquarius (30.0 degrees) on day 5 (benefic NEU, favourable 0.125)
DELIVERY = {"agent": "sun", "anchor": "jupiter"}
OWN = {"agent": "sun", "anchor": None}           # the Sun's own transit: the lord is the agent


def sky(body, t):
    days = (t - _d(0)).total_seconds() / 86400.0
    return {"Sun": SUN_LON, "Jupiter": JUP_START + JUP_SPEED * days, "Moon": lon("Leo", 5), "Mars": lon("Gemini", 20),
            "Mercury": lon("Sagittarius", 20), "Venus": lon("Virgo", 20), "Saturn": lon("Scorpio", 20), "Rahu": lon("Pisces", 20),
            "Ketu": lon("Virgo", 25)}[body.title()] % 360.0


def check() -> chk.P1Check:
    return chk.P1Check(sky, dignity_rows=DIG, orb_rows=COMB, naisargika_rows=NAIS)


def _owner(nature, rung):
    side, value, _tag = OWNER[nature][rung]
    return side, value


# ── R1: the verifier judges the anchor ─────────────────────────────────────────────────────────────────────────────────
def test_r1_the_verifier_evaluates_a_delivery_record_by_its_anchors_sky_side_and_value():
    """Day 1: Jupiter (the anchor) is debilitated in Capricorn — benefic DEB, adverse 1.0 (ANSWERS §B.3) — while the Sun (the agent) would be
    exalted, favourable 1.0. The record is the first, the Sun's own transit the second. Planted reversion: `subject_of` returns the agent
    ⇒ the delivery record reads the Sun's favourable EX."""
    bound = check().bind(ROWS, GAIN)
    delivery, own = bound.evaluate(DELIVERY, _d(1)), bound.evaluate(OWN, _d(1))
    assert (delivery.rung, delivery.nature, (delivery.side, delivery.value)) == ("DEB", "benefic", _owner("benefic", "DEB"))
    assert (own.rung, own.nature, (own.side, own.value)) == ("EX", "malefic", _owner("malefic", "EX"))
    assert delivery.side != own.side                                            # the two subjects stand on OPPOSITE sides
    assert bound.channel_at(DELIVERY, _d(1)) == "evidence_against_occurrence"   # a gain class: the adverse side feeds AGAINST
    assert bound.channel_at(OWN, _d(1)) == "evidence_for_occurrence"
    assert bound.value_at(DELIVERY, _d(1)) == pytest.approx(1.0)
    after = bound.evaluate(DELIVERY, _d(6))                                      # Jupiter in Aquarius: Saturn is its NEUTRAL
    assert (after.rung, (after.side, after.value)) == ("NEU", _owner("benefic", "NEU"))


# ── R2: the cache key ──────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("first, second", [(DELIVERY, OWN), (OWN, DELIVERY)])
def test_r2_the_evaluation_cache_is_keyed_by_the_subject_not_the_agent(first, second):
    """Both records have the agent Sun at the same instant but different governed subjects; whichever is evaluated first, the other
    must still read ITS subject. Planted reversion: the key is `(agent, t)` ⇒ the second read returns the first's cached evaluation."""
    bound = check().bind(ROWS, GAIN)
    got = {id(r): bound.evaluate(r, _d(1)) for r in (first, second)}
    assert got[id(DELIVERY)].rung == "DEB" and got[id(OWN)].rung == "EX"


# ── R3: the change instants ────────────────────────────────────────────────────────────────────────────────────────────
def test_r3_the_verifier_cuts_a_delivery_record_at_the_anchors_change_instants():
    """Jupiter's debility→Aquarius ingress is day 5 (30° at 0.2°/day from 29°); the Sun, fixed in Aries, never changes state. Planted
    reversion: the boundaries are the agent's ⇒ none, and the verifier would never cut the window where the side flips."""
    bound = check().bind(ROWS, GAIN)
    cuts = bound.channel_boundaries(DELIVERY, _d(0), _d(10))
    assert len(cuts) == 1 and abs((cuts[0] - _d(5)).total_seconds()) <= chk.PEAK_TOLERANCE_SECONDS
    assert bound.channel_boundaries(OWN, _d(0), _d(10)) == []


# ── R4: the per-record prerequisite ────────────────────────────────────────────────────────────────────────────────────
def test_r4_the_l0_prerequisite_of_a_delivery_record_is_the_anchors():
    """L0's dignity row for Jupiter is missing: Jupiter's records cannot be derived, the Sun's can. A delivery record anchored at Jupiter is
    therefore refused by name; planted reversion: the problem is read for the agent ⇒ None, and the unreadable anchor is judged anyway."""
    bound = chk.P1Check(sky, dignity_rows=[r for r in DIG if r["graha"] != "Jupiter"], orb_rows=COMB, naisargika_rows=NAIS).bind(ROWS, GAIN)
    assert bound.record_problem("dignity_of_transit_sign", DELIVERY) is not None
    assert bound.record_problem("dignity_of_transit_sign", OWN) is None


# ── R5 / R7: the verifier SQL and the end-to-end window ────────────────────────────────────────────────────────────────
class _SqlConn(_Conn):
    """`_Conn` whose relationship-record answer follows the SELECT it is asked: a row carries the anchor column only if the SQL selects
    `r.period_anchor_lord` (a database returns exactly the projected columns)."""

    def __init__(self, windows, records, links):
        super().__init__(windows, records, links)
        self.record_sql: list[str] = []

    def execute(self, sql, params=()):
        if "ka_gochara_relationship_record" in sql and "ka_gochara_eval_window_record" not in sql and "pg_attribute" not in sql \
                and "kala_gochara" not in sql:
            self.record_sql.append(sql)
            keep = 9 if "r.period_anchor_lord" in sql else 8
            return type(super().execute(sql, params))([row[:keep] for row in self.records])
        return super().execute(sql, params)


def _builder_window():
    """The BUILDER's draft of the delivery record (agent Sun, anchor Jupiter) from the registry's Form B rows, drafted by `window_sweep`."""
    ops = P.P1Operands(l0(), sky, form_b=MAPPING)
    rec = ops.attach(_rec("dlv", path="P1", agent="sun", root="R-dlv", supports=((0, 10),), state_boundaries=None,
                          state_boundaries_complete=False, period_anchor_lord="jupiter"), complete=True, stations=None, event_class=GAIN)
    (draft,), _ = _draft([rec], lambda p, v: ROWS, cls=GAIN)
    return rec, draft


def _verify(conn):
    return wv.verify_window_semantics(conn, factor_rows=ROWS, policy=wv.POLICY_VERSION, p1_check=check(), dynamic_enabled=True, chart_id="c",
                                      generation="g", event_class=GAIN, path_id="P1", rule_version="1.3.0")


def _conn(rec, draft, anchor="jupiter"):
    return _SqlConn([_stored(draft)], [(rec.record_id, rec.root_id, "residence", "sign_span", "sun", None, *rec.supports[0], anchor)],
                    [("w", rec.record_id)])


def test_r5_the_verifiers_record_sql_selects_the_anchor_for_a_p1_grain_and_only_for_p1():
    """A delivery window stored by the builder is reproduced only if the verifier's record query hands it the anchor: the fake database
    returns the anchor column iff the SELECT names `r.period_anchor_lord`. Planted reversion: the column is dropped from the SELECT ⇒ the
    verifier judges the Sun and refuses the builder's peak. For another path the SELECT must not touch the (P1-only) column."""
    rec, draft = _builder_window()
    conn = _conn(rec, draft)
    assert _verify(conn)["status"] == "VERIFIED"
    assert "r.period_anchor_lord" in conn.record_sql[0]
    # not P1: the column is not selected (a P2-P4 row carries no anchor, CHECK path_id = 'P1' ⇔ anchor IS NOT NULL, migration 1233)
    other = _SqlConn([_stored(draft)], conn.records, [("w", rec.record_id)])
    try:
        wv.verify_window_semantics(other, factor_rows=ROWS, policy=wv.POLICY_VERSION, p1_check=check(), dynamic_enabled=True, chart_id="c",
                                   generation="g", event_class=GAIN, path_id="P3", rule_version="1.0.0")
    except RuntimeError:
        pass                                                        # the P3 verdict on a P1 window is not the claim; the SELECT is
    assert other.record_sql and "r.period_anchor_lord" not in other.record_sql[0]


def test_r6_the_builders_sources_for_a_delivery_record_are_the_anchors_side_and_value_per_instant():
    """The same two subjects through the BUILDER (`P1Operands.attach`, Form B): day 1 the anchor Jupiter is DEB — adverse 1.0, the AGAINST
    channel for a gain class — and the Sun's own transit is EX, the FOR channel; from day 5 Jupiter is NEU favourable 0.125. Planted
    reversion: `attach` reads `rec.agent` ⇒ the delivery record gets the Sun's favourable 1.0."""
    ops = P.P1Operands(l0(), sky, form_b=MAPPING)
    base = _rec("r", path="P1", agent="sun", supports=((0, 10),))
    delivery = ops.attach(dataclasses.replace(base, period_anchor_lord="jupiter"), complete=True, event_class=GAIN).operand_sources
    own = ops.attach(base, complete=True, event_class=GAIN).operand_sources
    side, value = _owner("benefic", "DEB")
    assert delivery["agent_nature"].channel_at(_d(1)) == expected_channel(side, GAIN) == AGAINST
    assert delivery["dignity_of_transit_sign"].value_at(_d(1)) == pytest.approx(value)
    side, value = _owner("malefic", "EX")
    assert own["agent_nature"].channel_at(_d(1)) == expected_channel(side, GAIN) == FOR
    assert own["dignity_of_transit_sign"].value_at(_d(1)) == pytest.approx(value)
    side, value = _owner("benefic", "NEU")
    assert delivery["agent_nature"].channel_at(_d(6)) == expected_channel(side, GAIN) == FOR
    assert delivery["dignity_of_transit_sign"].value_at(_d(6)) == pytest.approx(value) and side == F and A != F


def test_r7_builder_and_verifier_reproduce_one_delivery_window_and_refuse_it_without_the_anchor():
    """The builder's window for the delivery record: the side flips at Jupiter's ingress (day 5) and the peak is that instant with the
    NEU value 0.125 in the FOR channel (the Sun alone would peak at day 0 with 1.0). The verifier, handed only the stored window and the
    record row WITH its anchor, reproduces it; with the anchor lost (the pre-R5 row) it judges the Sun and refuses the peak."""
    rec, draft = _builder_window()
    assert draft.unqualified_reason is None, draft.unqualified_reason
    assert abs((draft.peak_instant - _d(5)).total_seconds()) <= 1.0
    assert draft.evidence_for == pytest.approx(_owner("benefic", "NEU")[1])
    assert _verify(_conn(rec, draft))["numeric_reproduced"] == 1
    with pytest.raises(RuntimeError, match="peak"):
        _verify(_conn(rec, draft, anchor=None))
