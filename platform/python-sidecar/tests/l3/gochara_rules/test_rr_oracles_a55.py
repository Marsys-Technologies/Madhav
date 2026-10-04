"""A5.5 frozen test oracles — relationship_record (GOCHARA_DESIGN_SPECS_v1_4 §1).

O-RR-4, O-RR-5, O-RR-6, O-RR-7 with LITERAL inputs per /tmp oracles constants
(chart 482012f1-710e-4a25-994a-93821f5871aa, ayanamsha lahiri_chitrapaksha,
natal build 1c092ffb-72eb-4614-8422-552ca6eae985 [L1 chart_facts];
dasha build 75524b3e-102a-43ec-8cee-3f57fee752c3).
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
    _NEGATIVE_SENSITIVE_VALUES, _build_sensitive_degree_rows, _build_yoga_rows,
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


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.2/A5.3): the oracle's 'then' — the "
           "negative fact attaches as a GRAHA QUALIFIER on the subject's own "
           "row — is unmet by production: _build_sensitive_degree_rows "
           "DROPS the negative fact entirely (writer.py:494-495 counts it in "
           "the report, no qualifier is attached anywhere). spec §1/O-RR-4.")
def test_o_rr_4_negative_fact_lands_as_graha_qualifier():
    negative_fact = {"fact_id": "fact-moon-gandanta-neg",
                     "fact_subject": "Moon",
                     "fact_key": "gandanta",
                     "fact_value_text": "not_gandanta"}
    positive_fact = {"fact_id": "fact-jupiter-gandanta-pos",
                     "fact_subject": "Jupiter",
                     "fact_key": "gandanta",
                     "fact_value_text": "gandanta",
                     "degree": 359.5}
    rows = _build_sensitive_degree_rows("marriage",
                                        [negative_fact, positive_fact], None)
    # the negative fact must land as a qualifier on the SUBJECT GRAHA's own
    # row (Moon), not as a target object and not silently dropped
    moon_rows = [r for r in rows if r.get("_fact_subject") == "Moon"]
    assert moon_rows, "no row carries the Moon subject at all"
    assert any("not_gandanta" in str(r.get("target_qualifier") or "")
               for r in moon_rows)


# ── O-RR-5 (§1/§2; defects #22, NK-7) — yoga cancellation + strength 0.8 ────
def test_o_rr_5_yoga_admission_via_production_path():
    # natal pins (kept from the original fixture): 7L Venus 259.19° Libra,
    # Jupiter 249.79°, Saturn 202.43° Libra = the 7th from the 12.43° Aries
    # lagna; natal Mars 198.52° Libra also = the 7th — the pinned synthetic
    # yoga's cancellation condition '7th occupied by both Saturn and Mars'
    # is TRUE on the natal chart, FALSE with Mars moved to 100.0° (4th).
    chart = _chart()
    assert house_of(198.52, Frame("lagna"), chart) == 7
    assert house_of(202.43, Frame("lagna"), chart) == 7
    assert house_of(100.0, Frame("lagna"), chart) == 4

    # the REAL production yoga-admission path: _build_yoga_rows consumes a
    # LIVE ga_yoga_firings row (fired=true enforced by the upstream fetch)
    # and emits the yoga_constituent record with its own strength operand.
    firing = {"yoga_canonical_id": "7l-venus-conj-exalted-jupiter-9th",
              "constituent_fact_ids": ["f-venus-7l", "f-jupiter-exalted",
                                       "f-benefic-aspect"],
              "bhanga_active": False}
    report = {"validated_ids": set(), "constituents": {}}
    rows = _build_yoga_rows("marriage", [firing], report)

    # the record exists with the yoga_constituent target type…
    assert len(rows) == 1
    assert rows[0]["target_type"] == "yoga_constituent"
    assert rows[0]["target_ref"] == "7l-venus-conj-exalted-jupiter-9th"
    assert rows[0]["target_qualifier"] is None  # no bhaṅga carried
    # …the validation report comes from PRODUCTION (id pinned, constituents
    # counted), not from a test-side enumeration
    assert report["validated_ids"] == {"7l-venus-conj-exalted-jupiter-9th"}
    assert report["constituents"] == {"7l-venus-conj-exalted-jupiter-9th": 3}

    # the record's OWN strength factor is consumed as a named factor through
    # the production score path (the row carries the 0.7 weight operand; the
    # factor scale is declared in the registry)
    strength_factor = FACTORS[("yoga_strength", "1.0.0")]
    assert strength_factor["range"] == [0.0, 1.0]
    score = factor_product(
        [{"value": rows[0]["weight"], "null_state": "unqualified"}])
    assert score == pytest.approx(0.7)
    # mutation probe: dropping the strength operand (empty product = 1.0)
    # differs from consuming the record's own factor
    assert factor_product([]) != score


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.2/A5.3): NO production path evaluates a "
           "yoga cancellation for ADMISSION. _build_yoga_rows emits the row "
           "even when bhaṅga is active — bhanga_active=True is carried as a "
           "target_qualifier string (writer.py:683-684), never a gate; the "
           "oracle's 'cancellation fires ⇒ NO admission, and the evaluation "
           "is reported' is unmet. spec §1/O-RR-5.")
def test_o_rr_5_cancellation_blocks_admission():
    # the SAME yoga with its cancellation ACTIVE must produce NO admitted
    # record, and the cancellation evaluation must be reported by production
    firing = {"yoga_canonical_id": "7l-venus-conj-exalted-jupiter-9th",
              "constituent_fact_ids": ["f-venus-7l", "f-jupiter-exalted",
                                       "f-benefic-aspect"],
              "bhanga_active": True}
    report = {"validated_ids": set(), "constituents": {}}
    rows = _build_yoga_rows("marriage", [firing], report)
    assert rows == [], ("cancellation active ⇒ no admission; production "
                        "emitted the row anyway (qualifier-only bhaṅga)")
    assert report.get("cancellation", {}).get("evaluated") is True


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


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.2/A5.3): the oracle's 'then' — the "
           "afflicter is NAMED on the production output and the contact is "
           "enforced WITHIN THE DECLARED ORB — is unmet: records.afflicted() "
           "(records.py:108-121) returns a bare TRUE with no afflicter name "
           "and takes no longitude/orb operands at all, so a conjunction "
           "OUTSIDE the declared orb still afflicts. spec §1.2 inv 8/O-RR-6.")
def test_o_rr_6_afflicter_named_and_orb_enforced():
    # Saturn conjunct object X at orb 6.0° > the declared 5° orb must NOT
    # afflict (object X at natal Sun 291.96°; transit Saturn 297.96°;
    # Δ = 6.0° — outside the pinned 5° admission orb, literal operands).
    assert abs(297.96 - 291.96) == pytest.approx(6.0, abs=1e-9)
    wide_row = _record(agent="Saturn", relation="conjunction",
                       object_id="obj:x")
    verdict = afflicted("obj:x", [wide_row])
    # production must return evidence carrying the afflicter's name and the
    # orb verdict — not a bare TRUE that ignores the 6.0° separation
    assert isinstance(verdict, dict)
    assert verdict["afflicter"] == "Saturn"
    assert verdict["within_declared_orb"] is False
    assert verdict["afflicted"] is FALSE


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


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.2/A5.3): the oracle's second 'then' — the "
           "testimony row's ANNOTATION is present in the path breakdown with "
           "both content fields — is unmet: score.path_channel_scores "
           "(score.py:68-83) returns only the two channel totals; no "
           "per-record annotation naming the testimony row is carried in any "
           "breakdown. spec §1.2 inv 2/O-RR-7.")
def test_o_rr_7_testimony_annotation_in_breakdown():
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
    breakdown = path_channel_scores(
        [scored, maraka], "marriage",
        {scored.record_id: ev_scored, maraka.record_id: ev_testimony})
    # the breakdown must carry the testimony row's annotation with BOTH
    # content fields (both channels reported, both exactly zero)
    annotations = breakdown.get("annotations", {})
    assert maraka.record_id in annotations
    assert annotations[maraka.record_id] == {"evidence_for_occurrence": 0.0,
                                             "evidence_against_occurrence": 0.0}
