"""ASTRA_REVIEW_A5_4 P1-7 / P1-8 — the resonance-rebuild rehearsal is a
FAILING acceptance check and the runbook's backup/rollback is verifiable.

Pure tests (no DB): the acceptance function fails on every violated R-1..R-6
property, the rerun and the rollback checks; the SQL module refuses unsafe
names/values, never uses IF NOT EXISTS for the snapshot, and the runbook
carries the module's statements verbatim (drift guard). The live disposable
run is `resonance_rebuild_disposable_rehearsal.py` itself (exit 1 on any
failure) — its output is recorded in evidence/resonance_rebuild_R1_R6_
evidence.md.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "kala_gochara_cutover"
sys.path.insert(0, str(HERE))

import resonance_rebuild_backup_sql as B  # noqa: E402


def _load_rehearsal():
    spec = importlib.util.spec_from_file_location(
        "resonance_rebuild_disposable_rehearsal_t",
        HERE / "resonance_rebuild_disposable_rehearsal.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load_rehearsal()
CH = "482012f1-710e-4a25-994a-93821f5871aa"


def _passing_ver() -> dict:
    return {
        "before": {"sensitive_total": 176, "sensitive_negative": 154},
        "after": {"total": 481, "sensitive_total": 105, "sensitive_negative": 0,
                  "by_type": {}},
        "sensitive_keyed_to_positive_facts": 105,
        "dangling_or_null_refs": 0,
        # ASTRA v1.4 amendment 1: the fact-backed refs are producer-shaped 16-hex ids
        "fact_backed_refs": 158, "fact_backed_refs_not_producer_shaped": 0,
        "non_canonical_fact_ids_referenced": 0,
        "rows_missing_or_bad_resolution_state": 0,
        "arudha_rows": 67, "arudha_all_keyed_to_sign_facts": True,
        "arudha_invalid_sign_unavailable": 10,
        "yoga_rows": 4, "yoga_refs_not_live_fired": 0,
        "lord_rows": 51, "lord_states": {"resolved": 51},
        "afflicted_qualifier_rows": 6, "expected_afflicted_rows": 6,
        "writer_notes": {
            "sensitive_degree": {"negative_dropped_zero_rows": 735},
            "yoga_constituent": {"dropped_since_prior_build": ["yoga_demo_stopped"]}},
        "rerun_digest_equal": True,
        "snapshot": {"recorded_count": 177, "full_row_matches_live_preimage": True},
        "identities": {
            "lord_rows": {"expected": ["career_setback:10L", "marriage:7L"],
                          "actual": ["career_setback:10L", "marriage:7L"]},
            "afflicted_rows": {"expected": ["career_setback:10L"], "actual": ["career_setback:10L"]},
            # class-associated (ASTRA v1.2 P1-3): "class:ref", never a global DISTINCT set
            "sensitive_rows": {"expected": ["marriage:f-pos-1", "surgery:f-pos-2"],
                               "actual": ["marriage:f-pos-1", "surgery:f-pos-2"]},
            "arudha_rows": {"expected": ["marriage:a-1", "surgery:a-2"],
                            "actual": ["marriage:a-1", "surgery:a-2"]},
            "yoga_rows": {"expected": ["career_entry:yoga_demo_bhanga", "marriage:yoga_demo_gajakesari"],
                          "actual": ["career_entry:yoga_demo_bhanga", "marriage:yoga_demo_gajakesari"]},
            "exact_row_tuples": {
                "expected": ["marriage|bhava|7|1.0|resolved|None|False|cite",
                             "marriage|sensitive_degree|f-pos-1|0.5|resolved|None|True|None"],
                "actual": ["marriage|bhava|7|1.0|resolved|None|False|cite",
                           "marriage|sensitive_degree|f-pos-1|0.5|resolved|None|True|None"]}},
        "negative_fact_ids_referenced": 0,
        "value_invariant_violations": 0,
        "r1_identity_sql": {"actual_not_expected": 0, "expected_not_actual": 0},
        "r2_identity_sql": {"actual_not_expected": 0, "expected_not_actual": 0},
        "r3_identity_sql": {"actual_not_expected": 0, "expected_not_actual": 0},
        "r4_identity_sql": {"actual_not_expected": 0, "expected_not_actual": 0},
        "mechanism_identity_sql": {"actual_not_expected": 0, "expected_not_actual": 0},
        "r5_identity_sql": {"qualified_not_in_ontology": 0, "ontology_not_qualified": 0},
        "detector_controls": {
            "clean": {"r1": [0, 0], "r2": [0, 0], "r3": [0, 0], "r4": [0, 0], "r5": [0, 0],
                      "mech": [0, 0], "value_violations": 0, "dangling": 0,
                      "state:mechanism_resolved": 0, "state:m6_operands": 0},
            **{name: {"count_preservation_expected": True, "id_set_preservation_expected": True,
                      "counts_preserved": True, "global_id_sets_preserved": True,
                      "mutation_applied": True, "detected": True}
               for name in ("sensitive_class_swap", "arudha_class_swap", "yoga_class_swap",
                            "weight_changed", "qualifier_transferred",
                            "resolution_state_flipped", "provenance_flipped", "lord_token_wrong",
                            "mechanism_weight_sign_flipped", "mechanism_state_forged",
                            "m6_operand_missing", "m6_state_forged")},
            **{name: {"count_preservation_expected": False, "id_set_preservation_expected": True,
                      "counts_preserved": False, "global_id_sets_preserved": True,
                      "mutation_applied": True, "detected": True}
               for name in ("lord_token_missing", "birth_anchor_row_injected")},
            # a re-pointed reference changes the global id set by design (v1.4 amendment 1)
            **{name: {"count_preservation_expected": True, "id_set_preservation_expected": False,
                      "counts_preserved": True, "global_id_sets_preserved": False,
                      "mutation_applied": True, "detected": True}
               for name in ("fact_ref_missing", "fact_ref_foreign_chart")},
            "restored_after_controls": True},
        "map_unchanged_after_detector_controls": True,
        # ASTRA v1.3 amendment 1: the class universe and the schema are the migrations'
        "ontology": {"birth_anchor_present_in_ontology": True, "birth_anchor_rows_in_map": 0,
                     "map_classes_equal_eligible": True, "mirror_matches_migration_seed": True,
                     "mirror_diff": [], "citations_type": "ARRAY",
                     "chart_facts_fact_id_type": "text"},
        "rollback": {"refused_on_stale_snapshot": True,
                     "partition_untouched_after_refusal": True,
                     "pre_refusal_full_certificate": [481, "b" * 32],
                     "post_refusal_full_certificate": [481, "b" * 32],
                     "restored_full_row_digest_equal": True,
                     "other_chart_untouched": True,
                     "rebuild_after_rollback_digest_equal": True},
    }


def test_passing_verification_is_accepted():
    assert R.verify_acceptance(_passing_ver()) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda v: v["after"].__setitem__("sensitive_negative", 1), "R-1"),
    (lambda v: v["after"].__setitem__("sensitive_total", 0), "R-1 control"),
    (lambda v: v.__setitem__("sensitive_keyed_to_positive_facts", 100), "not all keyed"),
    (lambda v: v["before"].__setitem__("sensitive_negative", 0), "fixture control"),
    (lambda v: v["after"].__setitem__("total", 0), "R-6 control"),
    (lambda v: v.__setitem__("dangling_or_null_refs", 2), "dangling"),
    # ASTRA v1.4 amendment 1: producer-shaped ids, chart-scoped resolution, the ayanāṃśa pin
    (lambda v: v.__setitem__("fact_backed_refs_not_producer_shaped", 1), "producer-shaped"),
    (lambda v: v.__setitem__("fact_backed_refs", 0), "refs control"),
    (lambda v: v.pop("fact_backed_refs"), "refs control"),
    (lambda v: v.__setitem__("non_canonical_fact_ids_referenced", 1), "ayanāṃśa pin"),
    (lambda v: v["detector_controls"]["fact_ref_missing"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["fact_ref_foreign_chart"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["fact_ref_missing"].__setitem__("mutation_applied", False), "not applied"),
    (lambda v: v["detector_controls"]["fact_ref_missing"].__setitem__("counts_preserved", False), "per-class counts"),
    (lambda v: v.__setitem__("rows_missing_or_bad_resolution_state", 1), "R-6"),
    (lambda v: v.__setitem__("arudha_rows", 0), "R-2"),
    (lambda v: v.__setitem__("arudha_all_keyed_to_sign_facts", False), "R-2"),
    (lambda v: v.__setitem__("arudha_invalid_sign_unavailable", 0), "R-2 control"),
    (lambda v: v.__setitem__("yoga_rows", 0), "R-3"),
    (lambda v: v.__setitem__("yoga_refs_not_live_fired", 1), "R-3"),
    (lambda v: v["writer_notes"]["yoga_constituent"].__setitem__("dropped_since_prior_build", []), "R-3 drift"),
    (lambda v: v.__setitem__("lord_states", {"resolved": 50, "unavailable": 1}), "R-4"),
    (lambda v: v.__setitem__("lord_rows", 0), "R-4"),
    (lambda v: v.__setitem__("afflicted_qualifier_rows", 5), "R-5"),
    (lambda v: v.__setitem__("expected_afflicted_rows", 0), "R-5"),
    (lambda v: v["writer_notes"]["sensitive_degree"].__setitem__("negative_dropped_zero_rows", 0), "notes"),
    (lambda v: v.__setitem__("rerun_digest_equal", False), "idempotency"),
    (lambda v: v["rollback"].__setitem__("refused_on_stale_snapshot", False), "refuse"),
    (lambda v: v["rollback"].__setitem__("partition_untouched_after_refusal", False), "refuse"),
    # ASTRA v1.2 P2-b: recorded pre- AND post-refusal certificates, never a digest compared to itself
    (lambda v: v["rollback"].__setitem__("post_refusal_full_certificate", [481, "c" * 32]), "changed across the refusal probe"),
    (lambda v: v["rollback"].__setitem__("post_refusal_full_certificate", [480, "b" * 32]), "changed across the refusal probe"),
    (lambda v: v["rollback"].pop("pre_refusal_full_certificate"), "not recorded"),
    (lambda v: v["rollback"].__setitem__("pre_refusal_full_certificate", [0, "empty"]) or v["rollback"].__setitem__("post_refusal_full_certificate", [0, "empty"]), "refuse"),
    (lambda v: v["rollback"].__setitem__("restored_full_row_digest_equal", False), "exact preimage"),
    (lambda v: v["snapshot"].__setitem__("full_row_matches_live_preimage", False), "snapshot"),
    (lambda v: v["snapshot"].__setitem__("recorded_count", 0), "snapshot"),
    # ASTRA v1.1 P1-7 — totals preserved, identities moved:
    (lambda v: v["identities"]["afflicted_rows"].__setitem__("actual", ["marriage:7L"]), "identity: afflicted_rows"),
    (lambda v: v["identities"]["sensitive_rows"].__setitem__("actual", ["marriage:f-pos-1", "surgery:f-neg-9"]), "identity: sensitive_rows"),
    (lambda v: v.__setitem__("negative_fact_ids_referenced", 1), "negative-result sensitive fact id"),
    (lambda v: v["identities"]["yoga_rows"].__setitem__("actual", ["career_entry:yoga_demo_bhanga", "marriage:yoga_demo_stopped"]), "identity: yoga_rows"),
    (lambda v: v["identities"]["lord_rows"].__setitem__("actual", ["career_setback:10L", "marriage:2L"]), "identity: lord_rows"),
    (lambda v: v["identities"]["arudha_rows"].__setitem__("actual", ["marriage:a-1", "surgery:a-3"]), "identity: arudha_rows"),
    # ASTRA v1.2 P1-3 — per-class counts AND global id sets preserved, only the class association moved:
    (lambda v: v["identities"]["sensitive_rows"].__setitem__("actual", ["marriage:f-pos-2", "surgery:f-pos-1"]), "identity: sensitive_rows"),
    (lambda v: v["identities"]["arudha_rows"].__setitem__("actual", ["marriage:a-2", "surgery:a-1"]), "identity: arudha_rows"),
    (lambda v: v["identities"]["yoga_rows"].__setitem__("actual", ["career_entry:yoga_demo_gajakesari", "marriage:yoga_demo_bhanga"]), "identity: yoga_rows"),
    # retained values changed, identity intact:
    (lambda v: v["identities"]["exact_row_tuples"].__setitem__("actual", ["marriage|bhava|7|0.9|resolved|None|False|cite", "marriage|sensitive_degree|f-pos-1|0.5|resolved|None|True|None"]), "identity: exact_row_tuples"),
    (lambda v: v["identities"]["exact_row_tuples"].__setitem__("actual", ["marriage|bhava|7|1.0|resolved|None|False|cite", "marriage|sensitive_degree|f-pos-1|0.5|unavailable|None|True|None"]), "identity: exact_row_tuples"),
    (lambda v: v["identities"]["exact_row_tuples"].__setitem__("actual", ["marriage|bhava|7|1.0|resolved|None|True|None", "marriage|sensitive_degree|f-pos-1|0.5|resolved|None|True|None"]), "identity: exact_row_tuples"),
    (lambda v: v["identities"]["exact_row_tuples"].__setitem__("actual", ["marriage|bhava|7|1.0|resolved|afflicted|False|cite", "marriage|sensitive_degree|f-pos-1|0.5|resolved|None|True|None"]), "identity: exact_row_tuples"),
    (lambda v: v.__setitem__("value_invariant_violations", 1), "values:"),
    (lambda v: v.pop("value_invariant_violations"), "values:"),
    # BOTH EXCEPT directions: an extra row AND a missing eligible row each fail
    (lambda v: v["r1_identity_sql"].__setitem__("actual_not_expected", 1), "r1_identity_sql"),
    (lambda v: v["r1_identity_sql"].__setitem__("expected_not_actual", 1), "r1_identity_sql"),
    (lambda v: v["r2_identity_sql"].__setitem__("expected_not_actual", 1), "r2_identity_sql"),
    (lambda v: v["r3_identity_sql"].__setitem__("actual_not_expected", 1), "r3_identity_sql"),
    (lambda v: v["r3_identity_sql"].__setitem__("expected_not_actual", 1), "r3_identity_sql"),
    (lambda v: v.pop("r3_identity_sql"), "r3_identity_sql"),
    # ASTRA v1.3 amendment 3: the ALL-lord identity, both directions
    (lambda v: v["r4_identity_sql"].__setitem__("actual_not_expected", 1), "r4_identity_sql"),
    (lambda v: v["r4_identity_sql"].__setitem__("expected_not_actual", 1), "r4_identity_sql"),
    (lambda v: v.pop("r4_identity_sql"), "r4_identity_sql"),
    # ASTRA v1.4 amendment 2: mechanism rows — identity pair + the sign-flip control
    (lambda v: v["mechanism_identity_sql"].__setitem__("actual_not_expected", 1), "mechanism_identity_sql"),
    (lambda v: v["mechanism_identity_sql"].__setitem__("expected_not_actual", 1), "mechanism_identity_sql"),
    (lambda v: v["detector_controls"]["mechanism_weight_sign_flipped"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["identities"]["exact_row_tuples"]["actual"].__setitem__(0, "illness_acute|mechanism_node|saturn:unfavourable:h8|1.0|resolved|None|False|Phaladeepika ch.26 (synthetic rehearsal)"), "identity: exact_row_tuples"),
    (lambda v: v["detector_controls"]["lord_token_wrong"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["lord_token_missing"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["birth_anchor_row_injected"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["lord_token_missing"].__setitem__("mutation_applied", False), "not applied"),
    (lambda v: v["detector_controls"]["lord_token_wrong"].__setitem__("counts_preserved", False), "control invalid"),
    # detector positive controls must have RUN, been VALID (count/id-set preserving) and DETECTED
    (lambda v: v["detector_controls"]["yoga_class_swap"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["weight_changed"].__setitem__("detected", False), "NOT detected"),
    (lambda v: v["detector_controls"]["sensitive_class_swap"].__setitem__("counts_preserved", False), "control invalid"),
    (lambda v: v["detector_controls"]["sensitive_class_swap"].__setitem__("global_id_sets_preserved", False), "control invalid"),
    (lambda v: v["detector_controls"].__setitem__("restored_after_controls", False), "not restored"),
    # ASTRA v1.3 P2: every named control record must be PRESENT (the reviewer's bypass:
    # all mutation entries removed, clean + restored kept, verify returned [])
    (lambda v: [v["detector_controls"].pop(n) for n in R.REQUIRED_DETECTOR_CONTROLS], "missing detector control"),
    (lambda v: v["detector_controls"].pop("yoga_class_swap"), "missing detector control record 'yoga_class_swap'"),
    (lambda v: v["detector_controls"].__setitem__("sensitive_class_swap", True), "missing detector control"),
    (lambda v: v["detector_controls"].__setitem__("bogus_control", {"detected": True, "counts_preserved": True, "global_id_sets_preserved": True}), "unexpected detector control"),
    (lambda v: v["detector_controls"].pop("clean"), "clean baseline"),
    # ASTRA v1.4 P2: the clean baseline's CONTENTS are validated (the reviewer's bypass:
    # r1=[9,9] and value_violations=99 in `clean` still returned [])
    (lambda v: v["detector_controls"]["clean"].__setitem__("r1", [9, 9]), "clean baseline r1"),
    (lambda v: v["detector_controls"]["clean"].__setitem__("value_violations", 99), "clean baseline value_violations"),
    (lambda v: v["detector_controls"]["clean"].__setitem__("dangling", 1), "clean baseline dangling"),
    (lambda v: v["detector_controls"]["clean"].__setitem__("mech", [0, 1]), "clean baseline mech"),
    (lambda v: v["detector_controls"]["clean"].pop("r4"), "clean baseline r4"),
    (lambda v: v["detector_controls"].__setitem__("clean", "ok"), "clean baseline measurement missing"),
    (lambda v: v["detector_controls"]["weight_changed"].__setitem__("mutation_applied", False), "not applied"),
    (lambda v: v["detector_controls"]["weight_changed"].pop("mutation_applied"), "not applied"),
    (lambda v: v.pop("detector_controls"), "not run"),
    (lambda v: v.__setitem__("map_unchanged_after_detector_controls", False), "post-control digest"),
    # ASTRA v1.3 amendment 1: eligible class universe + migration-faithful schema
    (lambda v: v["ontology"].__setitem__("birth_anchor_rows_in_map", 1), "N6"),
    (lambda v: v["ontology"].__setitem__("birth_anchor_present_in_ontology", False), "ontology control"),
    (lambda v: v["ontology"].__setitem__("map_classes_equal_eligible", False), "class universe"),
    (lambda v: v["ontology"].__setitem__("mirror_matches_migration_seed", False), "migration seed"),
    (lambda v: v["ontology"].__setitem__("citations_type", "jsonb"), "schema"),
    (lambda v: v["ontology"].__setitem__("chart_facts_fact_id_type", "uuid"), "schema"),
    (lambda v: v.pop("ontology"), "ontology control"),
    (lambda v: v["identities"]["lord_rows"].__setitem__("expected", []), "identity control"),
    (lambda v: v.pop("identities"), "not measured"),
    (lambda v: v["r5_identity_sql"].__setitem__("qualified_not_in_ontology", 1), "R-5 SQL identity"),
    (lambda v: v["rollback"].__setitem__("other_chart_untouched", False), "foreign chart"),
    (lambda v: v["rollback"].__setitem__("rebuild_after_rollback_digest_equal", False), "rebuild after rollback"),
])
def test_each_violated_property_fails(mutate, needle):
    v = copy.deepcopy(_passing_ver())
    mutate(v)
    failures = R.verify_acceptance(v)
    assert failures and any(needle in f for f in failures), (needle, failures)


def test_empty_output_cannot_pass():
    v = _passing_ver()
    v["after"] = {"total": 0, "sensitive_total": 0, "sensitive_negative": 0, "by_type": {}}
    v.update(sensitive_keyed_to_positive_facts=0, arudha_rows=0, yoga_rows=0,
             lord_rows=0, lord_states={})
    failures = R.verify_acceptance(v)
    assert len(failures) >= 5


def test_expected_afflicted_rows_from_signature_models():
    assert R.expected_afflicted_lord_rows() == 6  # 10L, 7L, 2L/11L ×2


def test_expected_identities_follow_the_writers_tokenisation():
    lords, afflicted = R.expected_lord_identities()
    assert afflicted == {("career_setback", "10L"), ("separation", "7L"),
                         ("major_loss", "2L"), ("major_loss", "11L"),
                         ("financial_deception", "2L"), ("financial_deception", "11L")}
    assert ("bereavement", "2L") in lords and ("bereavement", "7L") in lords  # 'maraka lords (2L/7L)'
    assert ("bereavement", "2L") not in afflicted
    assert len(lords) == sum(1 for _ in lords) and afflicted <= lords


def test_a_class_swap_preserving_counts_and_global_id_sets_is_rejected():
    """ASTRA v1.2 P1-3: swap the class association of two sensitive rows —
    every per-class count and the GLOBAL DISTINCT target_ref set are
    unchanged (a global-set identity passes), yet the class-associated
    identity fails."""
    v = copy.deepcopy(_passing_ver())
    before = v["identities"]["sensitive_rows"]["expected"]
    swapped = ["marriage:f-pos-2", "surgery:f-pos-1"]
    v["identities"]["sensitive_rows"]["actual"] = swapped
    assert sorted(x.split(":")[1] for x in swapped) == sorted(x.split(":")[1] for x in before)
    assert len(swapped) == len(before)
    failures = R.verify_acceptance(v)
    assert any("identity: sensitive_rows" in f for f in failures), failures


def test_expected_row_tuples_are_class_associated_with_retained_values():
    """The expected set is built from the writer's own eligibility rules per
    class: a fact is expected under a class only when its subject is one of
    THAT class's kārakas; arudha/bhava_arudha only for the class's houses
    (invalid sign → unavailable); yogas only where houses or kārakas
    intersect, with the bhanga qualifier; lords carry the qualifier of the
    entry that names them; bhava/lord/karaka carry the ontology citation."""
    models = {"marriage": ([7, 2], ["7L"], ["Venus"]),
              "surgery": ([6, 8], ["6L", "8L afflicted"], ["Mars"])}
    fixture = {"positive_facts": [("f-ven", "VEN"), ("f-mar", "MAR"), ("f-sat", "SAT")],
               "arudha_fact_ids_by_house": {7: "a7", 2: "a2", 6: "a6", 8: "a8"},
               "arudha_sign_by_house": {7: "Libra", 2: "Taurus", 6: "Virgo", 8: "not_a_sign"},
               "live_yogas": [("y1", [7], ["venus"], False), ("y2", [6], ["mars"], True)],
               "citation_by_class": {"marriage": "cite", "surgery": "cite"}}
    got = R.expected_row_tuples(fixture, models)
    assert ("marriage", "sensitive_degree", "f-ven", 0.5, "resolved", None, True, None) in got
    assert ("surgery", "sensitive_degree", "f-mar", 0.5, "resolved", None, True, None) in got
    assert not any(tp[1] == "sensitive_degree" and tp[2] == "f-sat" for tp in got)  # no class names Saturn
    assert not any(tp[0] == "surgery" and tp[2] == "f-ven" for tp in got)          # class association
    assert ("surgery", "arudha", "a8", 0.6, "unavailable", None, True, None) in got
    assert ("surgery", "bhava_arudha", "BHAVA_ARUDHA_A8", 0.6, "unavailable", None, True, None) in got
    assert ("marriage", "arudha", "a7", 0.6, "resolved", None, True, None) in got
    assert not any(tp[0] == "marriage" and tp[2] == "a6" for tp in got)
    assert ("surgery", "lord", "8L", 1.0, "resolved", "afflicted", False, "cite") in got
    assert ("surgery", "lord", "6L", 1.0, "resolved", None, False, "cite") in got
    assert ("surgery", "yoga_constituent", "y2", 0.7, "resolved", "bhanga_active", True, None) in got
    assert ("marriage", "yoga_constituent", "y1", 0.7, "resolved", None, True, None) in got
    assert not any(tp[0] == "marriage" and tp[2] == "y2" for tp in got)
    assert ("marriage", "bhava", "7", 1.0, "resolved", None, False, "cite") in got
    assert ("marriage", "karaka", "Venus", 1.0, "resolved", None, False, "cite") in got


def test_identity_sql_is_class_associated_pinned_and_bidirectional():
    """R-1/R-2/R-3 as (event_class, ref) identities: ayanāṃśa-pinned,
    eligibility-scoped exactly as the writer reads (kāraka→subject map and
    positive pairs for R-1; class houses for R-2; constituent_houses ∩
    houses or constituent_planets ∩ kārakas for R-3), BOTH EXCEPT
    directions, and never a global DISTINCT target_ref set."""
    for fn in (B.r1_identity_sql, B.r2_identity_sql, B.r3_identity_sql):
        fwd, rev = fn(CH)
        for q in (fwd, rev):
            assert q.startswith("-- ") and "\nEXCEPT\n" in q
            assert "ayanamsha_id = 'lahiri_chitrapaksha'" in q
            assert "SELECT DISTINCT target_ref FROM gochara_resonance_map" not in q
            assert "SELECT event_class, target_ref FROM gochara_resonance_map" in q
            assert q.count("event_class") >= 3
        # direction: forward = map rows not named by the contract; reverse = eligible rows missing
        assert fwd.index("gochara_resonance_map") < fwd.index("EXCEPT") < fwd.index("chart_facts" if fn is not B.r3_identity_sql else "ga_yoga_firings")
        assert rev.index("EXCEPT") < rev.index("SELECT event_class, target_ref FROM gochara_resonance_map")
        assert "MISSING" in rev
    r1, _ = B.r1_identity_sql(CH)
    assert "('Rahu','RAH_MEAN')" in r1 and "('kartari','shubha_kartari')" in r1
    assert "fact_category = 'sensitive_degree_check'" in r1
    r3, _ = B.r3_identity_sql(CH)
    assert "constituent_houses" in r3 and "constituent_planets" in r3 and "y.fired" in r3
    r2, _ = B.r2_identity_sql(CH)
    assert "'ARUDHA_A' || ch.house::text" in r2 and "fact_key = 'sign'" in r2


def test_all_named_detector_controls_must_be_present_the_reviewers_bypass():
    """ASTRA v1.3 P2: remove every mutation entry, keep `clean` and
    `restored_after_controls=True` — verify_acceptance returned []."""
    v = copy.deepcopy(_passing_ver())
    v["detector_controls"] = {"clean": v["detector_controls"]["clean"], "restored_after_controls": True}
    failures = R.verify_acceptance(v)
    missing = [f for f in failures if "missing detector control record" in f]
    assert len(missing) == len(R.REQUIRED_DETECTOR_CONTROLS) == 16, failures
    assert set(R.REQUIRED_DETECTOR_CONTROLS) >= {
        "sensitive_class_swap", "arudha_class_swap", "yoga_class_swap", "weight_changed",
        "qualifier_transferred", "resolution_state_flipped", "provenance_flipped",
        "mechanism_state_forged", "m6_operand_missing", "m6_state_forged"}
    # the passing report carries exactly the required names
    names = set(_passing_ver()["detector_controls"]) - {"clean", "restored_after_controls"}
    assert names == set(R.REQUIRED_DETECTOR_CONTROLS)


def test_clean_baseline_contents_and_every_controls_application_are_validated():
    """ASTRA v1.4 P2: `clean` reporting r1=[9,9] and value_violations=99
    returned []. Every pair must be [0, 0], every count 0, no unmeasured
    key; every control record must carry mutation_applied=True."""
    v = copy.deepcopy(_passing_ver())
    v["detector_controls"]["clean"] = {"r1": [9, 9], "r2": [0, 0], "r3": [0, 0], "r4": [0, 0],
                                       "r5": [0, 0], "mech": [0, 0], "value_violations": 99,
                                       "dangling": 0, "state:mechanism_resolved": 0,
                                       "state:m6_operands": 0}
    failures = R.verify_acceptance(v)
    assert any("clean baseline r1 = [9, 9]" in f for f in failures), failures
    assert any("clean baseline value_violations = 99" in f for f in failures), failures
    assert set(R.CLEAN_BASELINE_PAIRS) == {"r1", "r2", "r3", "r4", "r5", "mech"}
    assert set(R.CLEAN_BASELINE_ZERO_COUNTS) == {
        "value_violations", "dangling", "state:mechanism_resolved", "state:m6_operands"}
    v2 = copy.deepcopy(_passing_ver())
    for name in R.REQUIRED_DETECTOR_CONTROLS:
        v2["detector_controls"][name]["mutation_applied"] = False
    failures2 = R.verify_acceptance(v2)
    assert sum(1 for f in failures2 if "mutation was not applied" in f) == len(R.REQUIRED_DETECTOR_CONTROLS)


def test_r4_all_lord_identity_is_bidirectional_scoped_and_tokenised_as_the_writer_does():
    """ASTRA v1.3 amendment 3: the reviewer's replay (marriage:7L → marriage:2L,
    weight / state / citation / qualifier preserved; 51 resolved rows, six
    afflicted, identical counts and global id sets, zero value violations)
    passed the printed native predicates. The R-4 pair compares ALL
    (event_class, token) lord rows against every lords entry of the eligible
    classes in both directions."""
    fwd, rev = B.r4_lord_identity_sql(CH)
    for q in (fwd, rev):
        assert "target_type = 'lord'" in q and "\nEXCEPT\n" in q
        assert "regexp_matches(l.value, '(\\d+L)', 'g')" in q      # the writer's _LORD_TOKEN_RE
        assert "SELECT DISTINCT o.event_class_id AS event_class, m[1] AS target_ref" in q
        assert B.eligible_classes_array() in q and "afflicted" not in q
    assert fwd.index("gochara_resonance_map") < fwd.index("EXCEPT") < fwd.index("brahma_event_ontology")
    assert rev.index("brahma_event_ontology") < rev.index("EXCEPT") < rev.index("gochara_resonance_map")
    assert "MISSING" in rev
    # the reviewer's replay against the pure expectation: the wrong token is missing AND extra
    lords, _ = R.expected_lord_identities()
    actual = (lords - {("marriage", "7L")}) | {("marriage", "2L")}
    assert len(actual) == len(lords) and {t for _, t in actual} == {t for _, t in lords}
    assert lords - actual == {("marriage", "7L")} and actual - lords == {("marriage", "2L")}


def _writer_emitted_target_types() -> set:
    """The writer's emitted type set, derived from its source: the literal
    second argument of every _base_row(...) call."""
    import ast
    src = (Path(__file__).resolve().parents[2] / "services" / "ka_gochara_resonance" / "writer.py").read_text()
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_base_row" and len(node.args) >= 2:
            assert isinstance(node.args[1], ast.Constant), ast.dump(node.args[1])
            out.add(node.args[1].value)
    return out


def test_every_emitted_target_type_is_checked_and_no_weight_compares_with_itself():
    """ASTRA v1.4 amendment 2: for a type absent from EXPECTED_WEIGHTS the
    predicate degraded to `m.weight <> m.weight` — mechanism_node was absent,
    so illness_acute / saturn:unfavourable:h8 with its weight flipped
    -1.0 → +1.0 produced zero violations. Now every type the writer emits is
    enumerated (equal to the set of literal types in its _base_row calls);
    mechanism weights come from the cited rule's rule_type through the
    writer's own _MECHANISM_WEIGHTS; an unknown type is a violation."""
    from services.ka_gochara_resonance.writer import _MECHANISM_WEIGHTS
    emitted = _writer_emitted_target_types()
    assert set(B.CHECKED_TARGET_TYPES) == emitted, (set(B.CHECKED_TARGET_TYPES) ^ emitted)
    assert set(B.EXPECTED_WEIGHTS) == emitted - {"mechanism_node"}
    assert B.MECHANISM_WEIGHTS == _MECHANISM_WEIGHTS and B.MECHANISM_WEIGHTS["unfavourable"] == -1.0
    sql = B.value_invariants_sql(CH)
    assert "ELSE m.weight" not in sql and "m.weight <> m.weight" not in sql
    assert "'type:unknown'" in sql and "'weight:mechanism_rule_type'" in sql
    assert "'identity:mechanism_ref'" in sql and "'eligibility:mechanism_rule'" in sql
    assert "('unfavourable', -1.0)" in sql and "('favourable', 1.0)" in sql
    assert "JOIN mechanism_weights mw ON mw.rule_type = r.rule_type" in sql
    assert "WHERE r.id = m.source_rule_id" in sql
    assert "m.target_type <> 'mechanism_node' AND m.weight <> (CASE m.target_type" in sql
    for t in emitted:
        assert f"'{t}'" in sql, t
    # M-6 rows: ref / citation / qualifier from the grammar constants, scope to the two classes
    assert "'provenance:m6_constant'" in sql and "'class:m6_scope'" in sql
    assert "mandi_sign_distance_from_8L" in sql and "PG220:C1 śl.26" in sql and "agent:Saturn" in sql
    assert "WHEN 'gulika_mandi_distance' THEN 0.5" in sql and "WHEN 'yamakantaka_difference' THEN 0.5" in sql
    # mechanism identity pair: both directions, eligibility as the writer fetches
    fwd, rev = B.mechanism_identity_sql(CH)
    for q in (fwd, rev):
        assert "\nEXCEPT\n" in q and "target_type = 'mechanism_node'" in q
        assert "lower(btrim(r.graha)) = ck.karaka_lower AND r.primary_house = ch.house" in q
    assert "MISSING" in rev


def test_expected_tuples_cover_mechanism_and_m6_rows_with_the_writers_weights():
    models = {"illness_acute": ([6, 8], ["6L", "8L"], ["Mars", "Saturn"]),
              "marriage": ([7, 2], ["7L"], ["Venus"])}
    fixture = {"positive_facts": [], "arudha_fact_ids_by_house": {}, "arudha_sign_by_house": {},
               "live_yogas": [], "citation_by_class": {"illness_acute": "c1", "marriage": "c2"},
               "transit_rules": R.FIXTURE_TRANSIT_RULES}
    got = R.expected_row_tuples(fixture, models)
    assert ("illness_acute", "mechanism_node", "saturn:unfavourable:h8", -1.0, "resolved", None, False,
            "Phaladeepika ch.26 (synthetic rehearsal)") in got
    assert ("marriage", "mechanism_node", "venus:favourable:h7", 1.0, "resolved", None, False,
            "BPHS ch.29 (synthetic rehearsal)") in got
    assert not any(tp[0] == "marriage" and tp[2] == "saturn:unfavourable:h8" for tp in got)
    assert ("illness_acute", "gulika_mandi_distance", B.MANDI_DISTANCE_REF, 0.5, "resolved",
            f"agent:{B.MANDI_DISTANCE_AGENT}", False, B.MANDI_DISTANCE_CITATION) in got
    assert sum(1 for tp in got if tp[0] == "illness_acute" and tp[1] == "yamakantaka_difference") == 4
    assert not any(tp[0] == "marriage" and tp[1] in ("gulika_mandi_distance", "yamakantaka_difference") for tp in got)
    assert set(R.EXACT_TYPES) == _writer_emitted_target_types() - {"dasha_lord_portfolio"}


def test_value_invariants_check_each_retained_value_against_its_source():
    sql = B.value_invariants_sql(CH)
    for label in ("'weight'", "'provenance:ontology_citation'", "'provenance:transit_rule_citation'",
                  "'provenance:own_synthesis'", "'state:lord_chain'", "'state:bhava_lagna'",
                  "'state:graha_position'", "'state:sensitive_subject_position'", "'state:arudha_sign'",
                  "'state:bhava_arudha_sign'", "'state:yoga'", "'qualifier:lord_afflicted'",
                  "'qualifier:yoga_bhanga'"):
        assert label in sql, label
    for source in ("reference_signs", "fact_category = 'graha_position'", "brahma_event_ontology",
                   "bg_transit_rules", "ga_yoga_firings", "fact_category = 'arudha_pada'"):
        assert source in sql, source
    for t, w in B.EXPECTED_WEIGHTS.items():
        assert f"WHEN '{t}' THEN {w}" in sql
    assert sql.rstrip().endswith("ORDER BY m.event_class, m.target_type, m.target_ref;")


def test_mechanism_node_state_is_checked_against_the_writers_resolved_contract():
    """ASTRA_REVIEW_A5_4_TIER0S_v1_5 P2 (b): the writer's contract
    (writer.py _stamp_target_resolution) explicitly preserves mechanism
    resolution as 'resolved' — the operand wiring IS the cited live rule.
    The values query previously checked mechanism weight / ref / eligibility /
    citation but no state, so an otherwise-valid mechanism_node row flipped
    'resolved' → 'unavailable' produced 0 violations (the reviewer's replay).
    Now a state other than 'resolved' is a 'state:mechanism_resolved'
    violation."""
    sql = B.value_invariants_sql(CH)
    assert "'state:mechanism_resolved'" in sql
    assert ("m.target_type = 'mechanism_node' AND m.target_resolution_state "
            "IS DISTINCT FROM 'resolved'") in sql


def test_m6_state_is_rederived_from_operand_presence_as_the_writer_derives_it():
    """ASTRA_REVIEW_A5_4_TIER0S_v1_5 P2 (c): the M-6 state check was enum
    membership only, so a Māndi-dependent M-6 row with Māndi MISSING from
    chart_facts and a forged stored state 'resolved' produced 0 violations.
    The writer (writer.py ~1150 _build_m6_derived_rows) derives the state
    from its operands — a missing Māndi/Yamakaṇṭaka sign or 5th-star-lord
    operand yields 'unavailable', an incomplete sign-lord table yields
    'unqualified'. The query now re-derives that state from the same
    operands; the formula roles and the Vimśottari table mirror the grammar
    module, never a hand copy."""
    from services.gochara_grammar.derived_points import (
        VIMSHOTTARI_NAKSHATRA_LORDS, YAMAKANTAKA_FORMULAS)
    sql = B.value_invariants_sql(CH)
    assert "'state:m6_operands'" in sql
    # the operand tables the writer reads
    assert "fact_category = 'sensitive_point_gulika_mandi'" in sql
    assert "'MANDI'" in sql and "'YAMAKANTAKA'" in sql
    assert "fact_category = 'panchanga_nakshatra_moon'" in sql and "NAKSHATRA_MOON_BIRTH" in sql
    # the per-formula operand roles, from the grammar constants
    assert "('mandi_sign_distance_from_8L', 'eighth_lord', 'mandi')" in sql
    for f in YAMAKANTAKA_FORMULAS:
        assert f"('{f['ref']}', '{f['minuend']}', '{f['subtrahend']}')" in sql, f["ref"]
    # the 5th-star lord: natal counts as 1, so the 5th is natal+4, Vimśottari lord
    assert "(((SELECT n FROM moon_nak) - 1 + 4) % 27) % 9" in sql
    for i, lord in enumerate(VIMSHOTTARI_NAKSHATRA_LORDS):
        assert f"({i}, '{lord}')" in sql, lord
    # the writer's _state combination: unqualified wins, then unavailable, else resolved
    assert "WHEN 'unqualified' IN (o.minuend_state, o.subtrahend_state) THEN 'unqualified'" in sql
    assert "WHEN 'unavailable' IN (o.minuend_state, o.subtrahend_state) THEN 'unavailable'" in sql
    assert "WHEN NOT (SELECT ok FROM lords_complete) THEN 'unqualified'" in sql


def test_refusal_probe_is_certified_by_two_recorded_certificates_not_a_tautology():
    """ASTRA v1.2 P2-b: the rehearsal source records the FULL certificate
    before the refusal probe and again after it, and the foreign partition
    is certified by its full-row certificate too; the old self-comparison
    (one digest compared to a fresh copy of itself) is gone."""
    src = (HERE / "resonance_rebuild_disposable_rehearsal.py").read_text()
    assert 'pre_refusal_full = _full_digest(cur, "gochara_resonance_map", CHART_ID)' in src
    assert 'post_refusal_full = _full_digest(cur, "gochara_resonance_map", CHART_ID)' in src
    assert src.index("pre_refusal_full = _full_digest") < src.index('B.rollback_sql(snap, CHART_ID, snap_full[0], "0" * 32)') < src.index("post_refusal_full = _full_digest")
    assert 'rb["pre_refusal_full_certificate"] = pre_refusal_full' in src
    assert 'rb["post_refusal_full_certificate"] = post_refusal_full' in src
    assert "pre_refusal_full == post_refusal_full" in src
    assert '_full_digest(cur, "gochara_resonance_map", CHART_ID)[1] == _full_digest(cur, "gochara_resonance_map", CHART_ID)[1]' not in src
    assert 'other_before_full = _full_digest(cur, "gochara_resonance_map", OTHER_CHART_ID)' in src
    assert '== other_before_full' in src


# ── ASTRA v1.3 amendment 1: oracle faithful to the production schema + class universe ──

def test_oracle_reads_the_migrations_citation_type_and_the_writers_class_universe():
    """Migration 388 declares brahma_event_ontology.citations TEXT[]; the
    previous value query called jsonb_array_elements_text on it (masked by
    a JSONB stub). The writer enumerates TARGET_EVENT_CLASSES (26; the
    retained birth_anchor row is never eligible — N6); the previous CTE read
    every ontology row and expected (birth_anchor, A1) pairs."""
    from services.ka_gochara_resonance.writer import TARGET_EVENT_CLASSES
    assert B.ELIGIBLE_EVENT_CLASSES == tuple(TARGET_EVENT_CLASSES)
    assert len(B.ELIGIBLE_EVENT_CLASSES) == 26 and "birth_anchor" not in B.ELIGIBLE_EVENT_CLASSES
    values = B.value_invariants_sql(CH)
    assert "jsonb_array_elements_text(o.citations)" not in values
    assert "array_to_string(o.citations, '; ')" in values and "cardinality(o.citations) = 0" in values
    assert "'class:not_eligible'" in values
    arr = B.eligible_classes_array()
    assert arr.startswith("ARRAY['marriage'") and arr.endswith("]::text[]") and "birth_anchor" not in arr
    for fn in (B.r1_identity_sql, B.r2_identity_sql, B.r3_identity_sql, B.r5_qualifier_identity_sql):
        for q in fn(CH):
            assert arr in q, fn.__name__
    r1, _ = B.r1_identity_sql(CH)
    assert "btrim(h.value) ~ '^[0-9]+$'" in r1          # _parse_house_ints: digits only
    assert "('Sun','SUN')" in r1 and "('sun','SUN')" not in r1  # _KARAKA_FACT_SUBJECT: exact title-case
    r3, _ = B.r3_identity_sql(CH)
    assert "ck.karaka_lower = e" in r3                    # the yoga fetch lower-cases


def test_rehearsal_schema_is_derived_from_the_checked_in_migrations():
    """The rehearsal no longer hand-declares any table the writer reads: the
    ontology is migrations 388 + 456 verbatim (real 27-class seed, TEXT[]
    citations, birth_anchor retained), the map is 459 + 550 (event_class FK)
    + 1080 verbatim, and every other input table's DDL is extracted from
    every migration that creates or alters it, in migration order, from
    BOTH runner roots."""
    assert "CREATE TABLE IF NOT EXISTS asset_registry" in R.STUB_DDL
    for tname in ("brahma_event_ontology", "chart_facts", "chart_dashas", "ga_yoga_firings",
                  "reference_signs", "bg_transit_rules", "gochara_resonance_map"):
        assert tname not in R.STUB_DDL, tname
    assert R.VERBATIM_MIGRATIONS == ("388_brahma_ghatana_ontology.sql",
                                     "456_brahma_event_ontology_dr13_shapes.sql")
    assert "550_gochara_resonance_map_event_class_fk.sql" in R.VERBATIM_MAP_MIGRATIONS
    m388 = R.find_migration("388_brahma_ghatana_ontology.sql").read_text()
    assert "citations           TEXT[]" in m388
    m456 = R.find_migration("456_brahma_event_ontology_dr13_shapes.sql").read_text()
    assert "('birth_anchor', " in m456
    plan = R.rehearsal_schema_plan()
    assert set(plan) == set(R.DERIVED_TABLES)
    for tname, entries in plan.items():
        assert entries and all(stmts for _, stmts in entries), tname
        assert any(st.upper().startswith("CREATE TABLE") for _, stmts in entries for st in stmts), tname
    create_cf = next(st for st in plan["chart_facts"][0][1] if st.upper().startswith("CREATE TABLE"))
    assert "fact_id                  TEXT PRIMARY KEY" in create_cf
    names = [f for f, _ in plan["chart_facts"]]
    assert names == sorted(names, key=lambda n: int(n.split("_")[0]))
    assert "539_chart_facts_verification_pass_status_check.sql" in names
    do_block = next(st for f, stmts in plan["chart_facts"] if f.startswith("539_") for st in stmts)
    assert do_block.startswith("DO $$") and "ALTER TABLE chart_facts" in do_block
    # the splitter never cuts inside a dollar-quoted block or a string
    assert R.split_sql_statements("DO $$ BEGIN PERFORM 1; END $$; SELECT ';';") == \
        ["DO $$ BEGIN PERFORM 1; END $$", "SELECT ';'"]
    # nothing but the table's own DDL is extracted (no seeds, no bookkeeping)
    for _, stmts in plan["ga_yoga_firings"]:
        for st in stmts:
            assert "asset_registry" not in st and not st.upper().startswith("INSERT")


def test_expected_tuples_carry_each_classs_own_migration_citation():
    models = {"marriage": ([7, 2], ["7L"], ["Venus"]),
              "surgery": ([6, 8], ["6L", "8L afflicted"], ["Mars"])}
    fixture = {"positive_facts": [("f-ven", "VEN")], "arudha_fact_ids_by_house": {},
               "arudha_sign_by_house": {}, "live_yogas": [],
               "citation_by_class": {"marriage": "BPHS ch.18; Phaladeepika ch.12",
                                     "surgery": None}}
    got = R.expected_row_tuples(fixture, models)
    assert ("marriage", "bhava", "7", 1.0, "resolved", None, False, "BPHS ch.18; Phaladeepika ch.12") in got
    assert ("surgery", "lord", "8L", 1.0, "resolved", "afflicted", False, None) in got
    # kārakas are matched by EXACT title-case name, as the writer keys them
    fixture2 = dict(fixture, positive_facts=[("f-ven", "VEN")],
                    citation_by_class={"m": None})
    got2 = R.expected_row_tuples(fixture2, {"m": ([7], [], ["venus"])})
    assert not any(tp[1] == "sensitive_degree" for tp in got2)
    got3 = R.expected_row_tuples(fixture2, {"m": ([7], [], ["Venus"])})
    assert ("m", "sensitive_degree", "f-ven", 0.5, "resolved", None, True, None) in got3


def test_signature_models_mirror_carries_the_migration_seeds_exact_lord_entries():
    assert R.SIGNATURE_MODELS["major_loss"][1] == ["2L/11L afflicted", "12L active"]
    assert R.SIGNATURE_MODELS["financial_deception"][1] == ["2L/11L afflicted", "12L active"]
    assert "birth_anchor" not in R.SIGNATURE_MODELS and len(R.SIGNATURE_MODELS) == 26
    assert set(R.SIGNATURE_MODELS) == set(B.ELIGIBLE_EVENT_CLASSES)


def test_a_transferred_qualifier_with_the_same_count_is_rejected():
    """The reviewer's mutation: move 'afflicted' from career_setback/10L to
    marriage/7L — count six preserved — must fail."""
    v = copy.deepcopy(_passing_ver())
    v["identities"]["afflicted_rows"]["actual"] = ["marriage:7L"]
    assert v["afflicted_qualifier_rows"] == v["expected_afflicted_rows"]  # totals equal
    failures = R.verify_acceptance(v)
    assert any("afflicted_rows" in f for f in failures)


def test_cluster_identity_is_asserted_before_any_create_database(monkeypatch):
    executed = []

    class _M:
        def __init__(self, ident):
            self._ident = ident

        def execute(self, sql, *a):
            executed.append(sql)
            ident = self._ident

            class _X:
                def fetchone(self_inner):
                    if ident is None:
                        raise RuntimeError("permission denied for function pg_control_system")
                    return (ident,)
            return _X()
    assert R.assert_cluster_identity(_M("123"), "123") == {"system_identifier": "123"}
    with pytest.raises(SystemExit, match="not the expected disposable cluster"):
        R.assert_cluster_identity(_M("999"), "123")
    with pytest.raises(SystemExit, match="cannot read the cluster identifier"):
        R.assert_cluster_identity(_M(None), "123")
    # establish_disposable_database asserts BEFORE CREATE DATABASE
    import types

    class _Ctx:
        def __init__(self, conn):
            self._c = conn

        def __enter__(self):
            return self._c

        def __exit__(self, *a):
            return False
    fake = types.SimpleNamespace(connect=lambda *a, **k: _Ctx(_M("999")))
    # monkeypatch restores the ORIGINAL module object afterwards (a manual
    # set/pop re-imported a bare `psycopg` without its `rows` submodule and
    # broke a later test in the same session)
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    with pytest.raises(SystemExit, match="not the expected"):
        R.establish_disposable_database("postgresql://u:p@127.0.0.1:1/postgres", "x", "123")
    assert not any("CREATE DATABASE" in q for q in executed)
    with pytest.raises(SystemExit, match="--expect-cluster-id is required"):
        R.establish_disposable_database("postgresql://u:p@127.0.0.1:1/postgres", "x", None)


def test_main_returns_failure_when_acceptance_fails(monkeypatch, capsys):
    """The run must EXIT NON-ZERO on a violated invariant (the pre-rework
    script printed the block and returned 0)."""
    import types
    fake_report = {"acceptance": {"passed": False, "failures": ["R-1: 3 remain"]}}
    monkeypatch.setattr(R, "establish_disposable_database", lambda dsn, p, c=None: ("dsn", "rehearsal_a54_20260930000000_abcdef"))
    monkeypatch.setattr(R, "drop_disposable_database", lambda dsn, n: None)

    class _Conn:
        def cursor(self):
            raise RuntimeError("stop before any DDL")
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(
        connect=lambda *a, **k: _Conn(), Error=Exception))
    with pytest.raises(RuntimeError, match="stop before any DDL"):
        R.main(["--maintenance-dsn", "postgresql://u:p@127.0.0.1:1/postgres",
                "--expect-cluster-id", "1"])
    # and the verify path itself
    assert R.verify_acceptance(copy.deepcopy(_passing_ver())) == []


def test_disposable_identity_refuses_wrong_or_non_empty_database():
    class _C:
        def __init__(self, db, addr, tables):
            self._r = [(db,), (addr,), (tables,)]

        def execute(self, sql):
            r = self._r.pop(0)

            class _X:
                def fetchone(self_inner):
                    return r
            return _X()
    name = "rehearsal_a54_20260930000000_abcdef"
    ok = R.assert_disposable_identity(_C(name, "127.0.0.1", 0), name)
    assert ok["database"] == name
    with pytest.raises(SystemExit, match="not the created database"):
        R.assert_disposable_identity(_C("madhav", "127.0.0.1", 0), name)
    with pytest.raises(SystemExit, match="not fresh"):
        R.assert_disposable_identity(_C(name, "127.0.0.1", 3), name)
    # a containerised server reports its container address — diagnostic only
    assert R.assert_disposable_identity(_C(name, "172.17.0.5", 0), name)["server_addr_diagnostic"] == "172.17.0.5"
    with pytest.raises(SystemExit, match="not loopback"):
        R.establish_disposable_database("postgresql://u:p@db.example.com:5432/postgres", "x")


# ── the SQL module ──────────────────────────────────────────────────────────

def test_full_row_certificate_and_content_digest_are_typed_and_separate():
    """ASTRA v1.1 P1-6: the preimage certificate covers every column (ids,
    computed_at) as typed JSON ordered by id; the content digest is a
    separate, ID-independent typed serialisation; neither maps SQL NULL to
    a string."""
    full = B.full_row_digest_sql("gochara_resonance_map", CH)
    assert "row_to_json(t)::text" in full and "ORDER BY t.id" in full
    content = B.partition_digest_sql("gochara_resonance_map", CH)
    assert "json_build_object(" in content and "'<null>'" not in content
    assert "coalesce(" not in content.lower().replace("coalesce(md5", "")
    assert full != content


def test_rollback_refuses_empty_snapshots_in_the_generator_and_in_sql():
    t = B.snapshot_table_name(CH, "20260930120000")
    with pytest.raises(ValueError, match="positive"):
        B.rollback_sql(t, CH, 0, "a" * 32)
    with pytest.raises(ValueError, match="md5 hex"):
        B.rollback_sql(t, CH, 5, "empty")
    sql = B.rollback_sql(t, CH, 177, "a" * 32)
    before_delete = sql.split("DELETE FROM gochara_resonance_map")[0]
    assert "is EMPTY" in before_delete
    assert "row_to_json(t)::text" in before_delete       # full-row certificate
    assert "ORDER BY t.id" in before_delete
    assert "json_build_object" not in sql                # never the content digest


def test_snapshot_is_uniquely_named_and_never_if_not_exists():
    t = B.snapshot_table_name(CH, "20260930120000")
    assert t == "gochara_resonance_map_snap_482012f1_20260930120000"
    sql = B.create_snapshot_sql(t, CH)
    assert sql.startswith("CREATE TABLE gochara_resonance_map_snap_")
    assert "IF NOT EXISTS" not in sql
    with pytest.raises(ValueError):
        B.snapshot_table_name(CH, "bad")
    with pytest.raises(ValueError):
        B.create_snapshot_sql("gochara_resonance_map_pre_r1r6_backup", CH)
    with pytest.raises(ValueError):
        B.rollback_sql(t, "not-a-uuid", 1, "0" * 32)
    with pytest.raises(ValueError):
        B.rollback_sql(t, CH, 1, "DROP TABLE x")


def test_rollback_block_refuses_before_deleting_and_verifies_after():
    t = B.snapshot_table_name(CH, "20260930120000")
    sql = B.rollback_sql(t, CH, 177, "a" * 32)
    body = sql.split("DELETE FROM gochara_resonance_map")[0]
    assert "ROLLBACK REFUSED: snapshot table" in body
    assert "carries % rows of another chart" in body
    assert "stale or incomplete" in body
    assert "ROLLBACK FAILED VERIFICATION" in sql.split("INSERT INTO gochara_resonance_map")[1]
    assert sql.strip().startswith("BEGIN;") and sql.strip().endswith("COMMIT;")


def test_reference_checks_use_not_exists_not_not_in():
    sql = B.dangling_fact_refs_sql(CH)
    assert "NOT EXISTS" in sql and "NOT IN (" not in sql
    assert "f.fact_value_text IS NULL" in B.negative_sensitive_targets_sql(CH)


def test_fact_refs_resolve_as_chart_scoped_text_identities_not_uuids():
    """ASTRA v1.4 amendment 1: chart_facts.fact_id is TEXT and the producers
    mint 16-hex semantic ids; the previous predicate counted every non-UUID
    fact-backed ref as dangling (the reviewer's replay: two valid
    producer-generated ids, 2 'violations'). Resolution is now a chart-scoped
    NOT EXISTS on the text identity — no UUID shape test anywhere."""
    sql = B.dangling_fact_refs_sql(CH)
    assert "f.fact_id = m.target_ref" in sql and "f.chart_id = m.chart_id" in sql
    assert "[0-9a-f]{8}-" not in sql and "!~" not in sql and "~ '" not in sql
    assert "m.target_type IN ('sensitive_degree', 'arudha')" in sql
    assert "btrim(m.target_ref) = ''" in sql
    assert B.FACT_BACKED_TARGET_TYPES == ("sensitive_degree", "arudha")


def test_fixture_fact_ids_are_minted_by_the_producers_own_functions():
    """The rehearsal seeds every chart_facts row with the id its PRODUCER
    mints (ga_writers/*._fact_id), never uuid4(): the reference check is
    proven on the ids production carries. Existing ids pass (live run:
    0 dangling of 158 fact-backed refs); a producer-shaped id no fact carries
    and the same id minted for ANOTHER chart are the fact_ref_missing /
    fact_ref_foreign_chart controls (live: dangling 1 each)."""
    from ga_writers.ga_sensitive_degree_writer import _fact_id as sensitive_degree_id, FACT_CATEGORY
    from ga_writers.ga_structural_writer import _fact_id as structural_id
    assert FACT_CATEGORY == "sensitive_degree_check"  # the actual producer of these rows
    sd = R.PRODUCER_FACT_ID["sensitive_degree_check"][1](
        "sensitive_degree_check", "VEN", "pushkara", CH, "lahiri_chitrapaksha", "build-x")
    assert sd == sensitive_degree_id("VEN", "pushkara", CH, "lahiri_chitrapaksha", "build-x",
                                     "sensitive_degree_check")
    a7 = R.PRODUCER_FACT_ID["arudha_pada"][1]("arudha_pada", "ARUDHA_A7", "sign", CH,
                                             "lahiri_chitrapaksha", "build-x")
    assert a7 == structural_id("arudha_pada", "ARUDHA_A7", "sign", CH, "lahiri_chitrapaksha", "build-x")
    assert a7 == "795c47dd1b8acc07"  # the reviewer's replay id for the A7 sign fact
    for fid in (sd, a7):
        assert R.FACT_ID_RE.match(fid) and len(fid) == 16
    # identity is semantic: another chart or ayanāṃśa mints a different id; the build does not
    assert R.PRODUCER_FACT_ID["sensitive_degree_check"][1](
        "sensitive_degree_check", "VEN", "pushkara", R.OTHER_CHART_ID, "lahiri_chitrapaksha", "build-x") != sd
    assert R.PRODUCER_FACT_ID["sensitive_degree_check"][1](
        "sensitive_degree_check", "VEN", "pushkara", CH, "fixture_ayanamsha_a", "build-x") != sd
    assert R.PRODUCER_FACT_ID["sensitive_degree_check"][1](
        "sensitive_degree_check", "VEN", "pushkara", CH, "lahiri_chitrapaksha", "build-y") == sd
    src = (HERE / "resonance_rebuild_disposable_rehearsal.py").read_text()
    assert "fid = uuid.uuid4()" not in src
    assert "PRODUCER_FACT_ID[category][1](category, subject, key, chart, ayanamsha, build_id)" in src
    assert set(R.PRODUCER_FACT_ID) == {"sensitive_degree_check", "arudha_pada", "graha_position",
                                       "graha_sign_attributes", "sensitive_point_gulika_mandi",
                                       "panchanga_nakshatra_moon"}
    assert R.FIXTURE_AYANAMSHAS[-1] == R.AYANAMSHA and len(set(R.FIXTURE_AYANAMSHAS)) == 5


def test_runbook_carries_the_module_statements_verbatim():
    """Drift guard: the production runbook's SQL IS the module's rendering
    (example stamp 20260930000000, count 177, digest 32 zeros)."""
    text = (HERE / "resonance_rebuild_R1_R6_runbook.md").read_text()
    t = B.snapshot_table_name(CH, "20260930000000")
    for block in (B.create_snapshot_sql(t, CH),
                  B.full_row_digest_sql("gochara_resonance_map", CH),
                  B.full_row_digest_sql(t, CH),
                  B.partition_digest_sql("gochara_resonance_map", CH),
                  B.negative_sensitive_targets_sql(CH),
                  B.dangling_fact_refs_sql(CH),
                  B.rollback_sql(t, CH, 177, "0" * 32),
                  *B.r5_qualifier_identity_sql(CH),
                  *B.r1_identity_sql(CH), *B.r2_identity_sql(CH), *B.r3_identity_sql(CH),
                  *B.r4_lord_identity_sql(CH), *B.mechanism_identity_sql(CH),
                  B.value_invariants_sql(CH)):
        assert block in text, block[:80]
    # ASTRA v1.2 P1-3: the global-DISTINCT R-1/R-3 identities are gone
    assert "EXCEPT SELECT DISTINCT target_ref" not in text
    assert "EXCEPT SELECT yoga_canonical_id FROM ga_yoga_firings" not in text
    assert "EXCEPT SELECT f.fact_id::text FROM chart_facts" not in text
    assert "STOP: the rebuild" in text  # the pre-destructive gate is in the runbook
    assert "IF NOT EXISTS gochara_resonance_map_pre_r1r6_backup" not in text
    assert "negative_dropped_zero_rows = 154" not in text
    assert "NOT IN (SELECT" not in text
    assert "MUST BE > 0" in text  # positive controls present
