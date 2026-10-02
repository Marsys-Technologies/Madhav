"""Codex round 6 R1 — qualification propagates through the evidence reduction (S §2.1; draft AM-17).

Closing text under test: an unresolved applicable factor propagates score qualification; an affected evidence
channel is NULL unless established independently; known partial subtotals are reported separately, never as
complete evidence; admission and admitted support are unchanged. Every assertion runs production code
(score.py / valence.py); the factor results are the real `{value, null_state, reason}` shape the evaluators emit.
"""
import pytest

from services.gochara_rules.records import RelationshipRecord
from services.gochara_rules.score import (
    CHANNELS, UNQUALIFIED, factor_product, path_channel_scores, record_channel_value,
)
from services.gochara_rules.valence import compute_valence

FOR, AGAINST = CHANNELS
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
ORB_UNRATIFIED = {"value": None, "null_state": "unqualified", "reason": "orb_not_ratified", "factor": "activity_kernel@1.1.0"}


def rec(contact="c1", role="scored", object_id="obj:sign:Aquarius", **kw):
    base = dict(chart_id=CHART, generation="5.0", event_class="marriage", affected_person="native", frame="lagna",
                agent="Jupiter", relation="residence", object_id=object_id, object_kind="sign_span",
                object_role="occupant", contact_id=contact, path_id="P3", rule_version="1.0.0",
                prerequisites=[], provenance="verse_cited", operator_role=role)
    return RelationshipRecord(**{**base, **kw})


def ev(record, factors, direction="favourable"):          # marriage is a gain class: favourable ⇒ evidence_for
    return record_channel_value(record, "marriage", direction, factors)


def reduce(*pairs):
    recs = [r for r, _ in pairs]
    return path_channel_scores(recs, "marriage", {r.record_id: e for r, e in pairs})


def test_codex_reproduction_all_records_unqualified_is_not_a_numeric_zero():
    # the exact failure: the unresolved point kernel used to reduce to evidence_for == 0 (known zero)
    a, b = rec("c1", relation="conjunction", object_kind="degree_point", object_id="obj:pt:1"), rec("c2", relation="conjunction", object_kind="degree_point", object_id="obj:pt:2")
    out = reduce((a, ev(a, [ORB_UNRATIFIED])), (b, ev(b, [ORB_UNRATIFIED])))
    assert out[FOR] is None and out[AGAINST] == 0.0          # the affected (assigned) channel is NULL; the untouched one is a real 0
    assert out["qualification"] == "unqualified" and out["unqualified_channels"] == [FOR]
    assert out["known_partial_subtotals"] == {FOR: 0.0}      # a lower bound, labelled as such — NOT the total
    assert all("orb_not_ratified" in r for r in out["unqualified_reasons"].values())
    # mutation guard: the old behaviour (skip + report 0.0) must fail
    assert out[FOR] != 0.0


def test_mixed_qualified_and_unqualified_gives_null_total_and_a_flagged_partial():
    q1, q2, u = rec("c1"), rec("c2", object_id="obj:sign:Pisces"), rec("c3", relation="conjunction", object_kind="degree_point", object_id="obj:pt:9")
    out = reduce((q1, ev(q1, [{"value": 0.5, "null_state": "unqualified"}])), (q2, ev(q2, [{"value": 0.25, "null_state": "unqualified"}])),
                 (u, ev(u, [ORB_UNRATIFIED])))
    assert out[FOR] is None and out["qualification"] == "partially_unqualified"
    assert out["known_partial_subtotals"][FOR] == pytest.approx(0.75)         # Σ over the two qualified roots
    assert out["unqualified_record_ids"] == [u.record_id]
    # all-qualified control: a complete numeric total, no flags
    ok = reduce((q1, ev(q1, [{"value": 0.5, "null_state": "unqualified"}])), (q2, ev(q2, [{"value": 0.25, "null_state": "unqualified"}])))
    assert ok[FOR] == pytest.approx(0.75) and ok["qualification"] == "qualified" and ok["known_partial_subtotals"] == {}


def test_shared_root_aliases_one_unqualified_alias_makes_the_channel_unknown():
    # two role aliases of ONE physical contact (same contact_id ⇒ one root): the root's value is max over aliases;
    # an unqualified alias could be larger, so the root — and the channel — is not established.
    a1, a2 = rec("c1", object_role="occupant"), rec("c1", object_role="karaka")
    assert a1.root_id == a2.root_id
    out = reduce((a1, ev(a1, [{"value": 0.6, "null_state": "unqualified"}])), (a2, ev(a2, [ORB_UNRATIFIED])))
    assert out[FOR] is None
    assert out["known_partial_subtotals"][FOR] == pytest.approx(0.6)          # the qualified alias is a LOWER bound only
    # both aliases qualified ⇒ max, once (the established amendment-2 behaviour is intact)
    b1, b2 = rec("c2", object_role="occupant"), rec("c2", object_role="karaka")
    ok = reduce((b1, ev(b1, [{"value": 0.6, "null_state": "unqualified"}])), (b2, ev(b2, [{"value": 0.4, "null_state": "unqualified"}])))
    assert ok[FOR] == pytest.approx(0.6)


def test_genuine_numeric_zero_is_zero_not_null():
    z = rec("c1")
    out = reduce((z, ev(z, [{"value": 0.0, "null_state": "unqualified"}])))        # e.g. a vedha-nullified record (AM-18)
    assert out[FOR] == 0.0 and out[AGAINST] == 0.0 and out["qualification"] == "qualified"


def test_testimony_never_moves_or_qualifies_a_total():
    scored, testimony, bad_testimony = rec("c1"), rec("c2", role="testimony", object_id="obj:sign:Aries"), rec("c3", role="testimony", object_id="obj:sign:Taurus")
    base = reduce((scored, ev(scored, [{"value": 0.5, "null_state": "unqualified"}])))
    with_t = path_channel_scores([scored, testimony, bad_testimony], "marriage",
                                 {scored.record_id: ev(scored, [{"value": 0.5, "null_state": "unqualified"}]),
                                  testimony.record_id: ev(testimony, [{"value": 0.9, "null_state": "unqualified"}]),
                                  # a testimony record whose factors are unresolved must NOT qualify the path either
                                  bad_testimony.record_id: ev(bad_testimony, [ORB_UNRATIFIED])})
    assert with_t == base and with_t[FOR] == 0.5 and with_t["qualification"] == "qualified"
    # …and a testimony record with NO evaluation at all (never computed) does not qualify the path either
    no_eval = path_channel_scores([scored, testimony], "marriage", {scored.record_id: ev(scored, [{"value": 0.5, "null_state": "unqualified"}])})
    assert no_eval == base


def test_declared_non_applicability_is_omitted_but_a_missing_operand_is_not():
    drishti_na = {"not_applicable": True, "factor": "graduated_drishti@1.1.0", "value": None}   # a residence record: the factor declares it does not apply
    r = rec("c1")
    assert factor_product([{"value": 0.5, "null_state": "unqualified"}, drishti_na]) == 0.5
    assert record_channel_value(r, "marriage", "favourable", [drishti_na])[FOR] == 1.0          # empty product over applicable factors = 1.0 (NK-4 base)
    # an unflagged None (a MISSING operand) still propagates — N/A needs the declaration AND a factor ref
    assert factor_product([{"value": None, "null_state": "unqualified"}]) == UNQUALIFIED
    assert factor_product([{"not_applicable": True, "value": None, "null_state": "unqualified"}]) == UNQUALIFIED
    assert factor_product([{"not_applicable": False, "factor": "x", "value": None, "null_state": "unqualified"}]) == UNQUALIFIED


def test_a_record_with_no_evaluation_qualifies_both_channels():
    r = rec("c1")
    out = path_channel_scores([r], "marriage", {})
    assert out[FOR] is None and out[AGAINST] is None and out["unqualified_reasons"][r.record_id] == ["not_evaluated"]


def test_the_against_channel_is_affected_only_when_the_record_feeds_it():
    r = rec("c1")
    adverse_on_gain = record_channel_value(r, "marriage", "adverse", [ORB_UNRATIFIED])     # adverse direction ⇒ AGAINST a gain class
    out = path_channel_scores([r], "marriage", {r.record_id: adverse_on_gain})
    assert out[AGAINST] is None and out[FOR] == 0.0 and out["unqualified_channels"] == [AGAINST]


def test_valence_follows_the_unresolved_branch_for_a_null_evidence_channel():
    for f, a in ((None, 0.0), (0.4, None), (None, None)):
        v = compute_valence("marriage", f, a)
        assert v.outcome_valence_for_native == "unqualified" and v.occurrence == "unqualified"
        assert v.unresolved_operand == "evidence_channel_unqualified"
        assert v.evidence_for_occurrence == f and v.evidence_against_occurrence == a        # NULL stays NULL, never 0
    known = compute_valence("marriage", 0.0, 0.0)                    # a KNOWN zero is not unqualified
    assert known.outcome_valence_for_native == "favourable" and known.occurrence == "plain"


# ── Codex round 7 [1] — an unknown competing path qualifies the cross-path result ─────────────────────────
from services.gochara_rules.score import aggregate_paths, aggregate_paths_detail


def test_codex_round7_unknown_competing_path_is_not_ignored():
    # the exact reproduction: aggregate_paths([0.2, 'unqualified']) used to return 0.2
    assert aggregate_paths([0.2, UNQUALIFIED]) == UNQUALIFIED
    d = aggregate_paths_detail([0.2, UNQUALIFIED])
    assert d["qualification"] == "unqualified" and d["known_lower_bound"] == 0.2 and d["unknown_paths"] == 1
    assert d["reason"] == "competing_path_unqualified"


def test_a_maximum_proved_independent_of_the_unknown_stays_qualified():
    # a known 1.0 cannot be exceeded by anything in [0,1], so the unknown path cannot change the answer
    assert aggregate_paths([1.0, UNQUALIFIED, 0.3]) == 1.0
    assert aggregate_paths_detail([1.0, None])["qualification"] == "qualified"
    # but 0.999… is NOT proof
    assert aggregate_paths([0.999999, UNQUALIFIED]) == UNQUALIFIED


def test_all_unknown_is_unqualified_with_no_lower_bound_and_empty_is_a_real_zero():
    d = aggregate_paths_detail([UNQUALIFIED, UNQUALIFIED])
    assert d["value"] == UNQUALIFIED and d["known_lower_bound"] is None and d["unknown_paths"] == 2
    assert aggregate_paths([]) == 0.0                                  # no admitted path: a computed zero, unchanged
    assert aggregate_paths([0.0, 0.0]) == 0.0                          # genuine computed zeros stay numeric
    assert aggregate_paths([0.0, UNQUALIFIED]) == UNQUALIFIED          # zero is not proof either


def test_known_paths_unchanged_and_malformed_scores_refused():
    assert aggregate_paths([0.7, 0.4]) == pytest.approx(0.7)
    for bad in ([1.2], [-0.1], [float("nan")], [True], ["high"]):
        with pytest.raises(ValueError):
            aggregate_paths(bad)
