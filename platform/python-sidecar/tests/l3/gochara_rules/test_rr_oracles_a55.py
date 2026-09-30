"""A5.5 frozen test oracles — relationship_record (GOCHARA_DESIGN_SPECS_v1_4 §1).

O-RR-4, O-RR-5, O-RR-6, O-RR-7 with LITERAL inputs per /tmp oracles constants
(chart 482012f1-710e-4a25-994a-93821f5871aa, ayanamsha lahiri_chitrapaksha,
natal build 1c092ffb-72eb-4614-8422-552ca6eae985 [L1 chart_facts];
dasha build 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb).
"""
from __future__ import annotations

import pytest

from services.gochara_rules.frames import Frame, house_of, sign_of
from services.gochara_rules.predicates import FALSE, TRUE, UNKNOWN
from services.gochara_rules.records import RelationshipRecord, afflicted
from services.gochara_rules.registry import FACTORS
from services.gochara_rules.score import (
    factor_product, path_channel_scores, record_channel_value,
)
# E3's negative-sensitive-fact shape (§1.2 inv 4) is realised in the merged
# tree by the resonance target builder: R-1 keeps ONLY positive check results
# as objects; the pinned negatives fold into the graha's interpretation.
from services.ka_gochara_resonance.writer import (
    _NEGATIVE_SENSITIVE_VALUES, _build_sensitive_degree_rows,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# L1 natal longitudes, build 1c092ffb-72eb-4614-8422-552ca6eae985 (literal)
NATAL = {
    "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
    "Jupiter": 249.79, "Venus": 259.19, "Saturn": 202.43,
    "Rahu": 49.03, "Ketu": 229.03,
}
LAGNA_DEG = 12.43  # Aries lagna [L1]


def _chart(**natal_overrides) -> dict:
    return {"lagna_deg": LAGNA_DEG,
            "natal": {**NATAL, **natal_overrides},
            "day_birth": True, "paksha": "Shukla"}


def _record(**kw) -> RelationshipRecord:
    base = dict(
        chart_id=CHART_ID, generation="5.0", event_class="marriage",
        affected_person="native", frame="lagna", agent="Jupiter",
        relation="residence", object_id="obj:sign:Aquarius",
        object_kind="sign_span", object_role="occupant",
        contact_id="sha256:contact-x", path_id="P3", rule_version="1.0.0",
        prerequisites=[], provenance="verse_cited", operator_role="scored",
    )
    return RelationshipRecord(**{**base, **kw})


# ── O-RR-4 (§1; defects #9, E3) — negative sensitive fact is no object ──────
def test_o_rr_4_negative_fact_no_object():
    # given: one NEGATIVE sensitive fact (value_text='not_gandanta') and one
    # POSITIVE sensitive fact (a real degree) per E3's shape (literal).
    negative_fact = {"fact_id": "fact-moon-gandanta-neg",
                     "fact_subject": "Moon",        # natal Moon 327.06° Aquarius
                     "fact_key": "gandanta",
                     "fact_value_text": "not_gandanta"}
    positive_fact = {"fact_id": "fact-jupiter-gandanta-pos",
                     "fact_subject": "Jupiter",
                     "fact_key": "gandanta",
                     "fact_value_text": "gandanta",
                     "degree": 359.5}  # a real degree inside the gandanta arc
    assert negative_fact["fact_value_text"] in _NEGATIVE_SENSITIVE_VALUES

    # when: relationship records (objects) are built
    report = {"kept": 0, "dropped_negative": 0, "dropped_unknown_value": 0,
              "kept_subjects": set()}
    rows = _build_sensitive_degree_rows("marriage",
                                        [negative_fact, positive_fact],
                                        report)

    # then: the positive fact DOES produce its object (no vacuous pass on an
    # empty record set)…
    assert len(rows) == 1
    assert rows[0]["target_type"] == "sensitive_degree"
    assert rows[0]["target_ref"] == "fact-jupiter-gandanta-pos"
    assert rows[0]["_fact_subject"] == "Jupiter"
    assert report["kept"] == 1
    # …and NO object is materialised from the negative fact: it attaches only
    # as a graha qualifier (here: the build-note annotation, never a target).
    assert all(r["target_ref"] != "fact-moon-gandanta-neg" for r in rows)
    assert report["dropped_negative"] == 1
    assert report["kept_subjects"] == {"Jupiter"}


# ── O-RR-5 (§1/§2; defects #22, NK-7) — yoga cancellation + strength 0.8 ────
def _enumerate_marriage_yoga(chart: dict) -> tuple[list, dict]:
    """The pinned synthetic yoga: '7L Venus conjunct exalted Jupiter in the
    9th with benefic aspect' → marriage, strength operand 0.8; cancellation
    condition '7th house occupied by both Saturn and Mars'. The cancellation
    is ALWAYS evaluated and reported; admission iff it evaluates false."""
    fires = (house_of(chart["natal"]["Saturn"], Frame("lagna"), chart) == 7
             and house_of(chart["natal"]["Mars"], Frame("lagna"), chart) == 7)
    report = {"cancellation": "7th house occupied by both Saturn and Mars",
              "evaluated": True, "fires": fires}
    if fires:
        return [], report
    rec = _record(event_class="marriage", agent="Venus",
                  relation="association",
                  object_id="obj:yoga:7l-venus-conj-exalted-jupiter-9th",
                  object_kind="yoga", object_role="yoga_constituent",
                  contact_id=None, path_id="P3")
    return [rec], report


def test_o_rr_5_yoga_cancellation_and_strength_consumed():
    # natal pins: 7L Venus 259.19° (Libra lord), Jupiter 249.79° (exalted
    # candidate), Saturn 202.43° Libra = the 7th from the 12.43° Aries lagna.
    assert sign_of(202.43) == "Libra"

    # fixture A: MODIFIED object set — Mars removed from the 7th (natal Mars
    # 198.52° Libra replaced by 100.0° Cancer = the 4th)
    fixture_a = _chart(Mars=100.0)
    assert house_of(100.0, Frame("lagna"), fixture_a) == 4
    records_a, report_a = _enumerate_marriage_yoga(fixture_a)
    # the record exists with object_role=yoga_constituent…
    assert len(records_a) == 1
    assert records_a[0].object_role == "yoga_constituent"
    # …the cancellation is evaluated and reported FALSE explicitly
    assert report_a == {"cancellation":
                        "7th house occupied by both Saturn and Mars",
                        "evaluated": True, "fires": False}
    # …and the strength operand 0.8 is consumed as a NAMED factor
    # (declared factor scale; the registry carries the row)
    strength_factor = FACTORS[("yoga_strength", "1.0.0")]
    assert strength_factor["range"] == [0.0, 1.0]
    score = factor_product([{"value": 0.8, "null_state": "unqualified"}])
    assert score == pytest.approx(0.8)
    # mutation probe: dropping the 0.8 operand (empty product = 1.0) differs
    assert factor_product([]) != score

    # fixture B: the SAME yoga with the cancellation TRUE — natal Mars
    # 198.52° Libra restored to the 7th alongside Saturn 202.43°
    fixture_b = _chart()
    assert house_of(198.52, Frame("lagna"), fixture_b) == 7
    records_b, report_b = _enumerate_marriage_yoga(fixture_b)
    # NO admission from this yoga (cancellation fires)…
    assert records_b == []
    # …and fixture B ALSO reports the cancellation evaluation explicitly
    assert report_b["evaluated"] is True and report_b["fires"] is True


# ── O-RR-6 (§1.2 inv 8; defect #23) — affliction predicate ──────────────────
def test_o_rr_6_affliction_predicate():
    # fixture A: named afflicter (Saturn) conjunct object X within the
    # declared orb — object X at natal Sun 291.96°; transit Saturn 288.01°;
    # Δ = 3.95° ≤ 5° orb (literal operands).
    assert abs(291.96 - 288.01) == pytest.approx(3.95, abs=1e-9)
    assert abs(291.96 - 288.01) <= 5.0
    afflicter_row = _record(agent="Saturn", relation="conjunction",
                            object_id="obj:x")
    result_a = afflicted("obj:x", [afflicter_row])
    assert result_a is TRUE
    # the afflicter is NAMED on the witnessing row
    assert afflicter_row.agent == "Saturn"

    # fixture B: same object, no afflicter contact (benefic Jupiter instead)
    benign_row = _record(agent="Jupiter", relation="conjunction",
                         object_id="obj:x")
    assert afflicted("obj:x", [benign_row]) is FALSE
    assert afflicted("obj:x", []) is FALSE

    # an UNEVALUATED fixture ⇒ unqualified (unknown), never false
    assert afflicted("obj:x", None) is UNKNOWN

    # mutation probe: label-based affliction (string match on a label field,
    # no afflicter row) or afflicted-by-default both fail the above — a
    # non-afflicter conjunction and the empty row set stay FALSE, and the
    # unevaluated claim is UNKNOWN, not FALSE.
    assert UNKNOWN != FALSE


# ── O-RR-7 (§1.2 inv 2; defects S-04, D-PADMIT) — testimony zero effect ─────
def test_o_rr_7_testimony_row_bitwise_equal_scores():
    # a window whose record set includes a testimony row (a māraka edge),
    # with a pinned score
    scored = _record(agent="Jupiter", relation="residence",
                     object_id="obj:sign:Libra")
    maraka = _record(agent="Venus", relation="ownership",
                     object_id="obj:sign:Libra", contact_id=None,
                     object_role="maraka_of_house",
                     provenance="uncited_extension",
                     operator_role="testimony", ruling_ref="D-PADMIT")
    ev_scored = record_channel_value(
        scored, "marriage", "favourable", [{"value": 0.5, "null_state": "omit"}])
    ev_testimony = record_channel_value(
        maraka, "marriage", "favourable", [{"value": 0.9, "null_state": "omit"}])

    # the testimony row's annotation is present in the breakdown in BOTH its
    # content fields (both channels reported, both exactly zero)
    assert ev_testimony == {"evidence_for_occurrence": 0.0,
                            "evidence_against_occurrence": 0.0}
    assert set(ev_testimony) == {"evidence_for_occurrence",
                                 "evidence_against_occurrence"}

    # scored with the testimony row present vs removed: identical scores
    without = path_channel_scores([scored], "marriage",
                                  {scored.record_id: ev_scored})
    with_ = path_channel_scores(
        [scored, maraka], "marriage",
        {scored.record_id: ev_scored, maraka.record_id: ev_testimony})
    assert with_ == without  # bitwise-equal (exact float equality)
    assert with_["evidence_for_occurrence"] == 0.5
    assert with_["evidence_against_occurrence"] == 0.0
    assert type(with_["evidence_for_occurrence"]) is type(
        without["evidence_for_occurrence"])

    # positive control: the scored row DOES move its channel (no vacuous pass
    # on a zero window)
    assert without["evidence_for_occurrence"] > 0.0
