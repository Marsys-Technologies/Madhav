"""Source-to-conclusion oracles for KYD-120; no fabricated production rows."""
import copy

import pytest

from services.ka_yojaka.promise_adapter import build_bundle, EVENT_BINDINGS, EventBinding


def sources():
    facts = [dict(fact_id="f:moon", ayanamsha_id="a", fact_category="graha_position",
                  fact_subject="Moon", fact_key="longitude_sidereal", fact_value_num=0,
                  unit="degrees")]
    rule = dict(formation_rule_jsonb={"fixture": True}, classical_citations=[{"text_id": "bphs"}],
                bhanga_rules_jsonb=[])
    firings = [dict(id=1, ayanamsha_id="a", yoga_canonical_id="sunapha", fired=True,
                    constituent_fact_ids=["f:moon"], constituent_planets=["Moon"],
                    bhanga_active=False, bhanga_rule_fired=None, grounds_jsonb={}, **rule),
               dict(id=2, ayanamsha_id="a", yoga_canonical_id="neecha_bhanga_raja_yoga", fired=True,
                    constituent_fact_ids=["f:moon"], constituent_planets=["Moon"],
                    bhanga_active=True, bhanga_rule_fired="NB-1", grounds_jsonb={}, **rule)]
    return facts, firings


def test_nbry_formation_is_retained_and_never_self_defeated():
    bundle = build_bundle(*sources(), [])
    row = next(r for r in bundle if r["canonical_id"] == "neecha_bhanga_raja_yoga")
    assert row["formation_state"] == "present"
    assert row["effective_state"] == "unresolved"
    assert row["defeats"] == []


def test_sourced_defeat_changes_only_its_named_conclusion():
    facts, firings = sources()
    firings[1]["bhanga_rules_jsonb"] = [dict(rule_id="NB-1", kind="defeats",
        target_yoga_canonical_id="sunapha", target_event_class_id="major_gain",
        rule_version="fixture-v1", source_locator="fixture:source:1")]
    firings[1]["grounds_jsonb"] = {"cancellation_evidence": [{"rule_id": "NB-1", "fact_ids": ["f:moon"]}]}
    bundle = build_bundle(facts, firings, [])
    gain = next(r for r in bundle if r["canonical_id"] == "sunapha" and r["event_class_id"] == "major_gain")
    other = next(r for r in bundle if r["event_class_id"] == "achievement_recognition")
    assert gain["effective_state"] == "defeated"
    assert other["effective_state"] == "in_force"
    assert gain["formation_state"] == "present"
    assert gain["defeats"][0]["fact_ids"] == ["f:moon"]


def test_l2_removal_preserves_the_entire_admitted_graph_and_duplicate_signals_attach():
    facts, firings = sources()
    signals = [dict(signal_id=s, ayanamsha_id="a", constituent_facts_array=["f:moon"]) for s in ("s1", "s2")]
    attached = build_bundle(facts, firings, signals)
    clean = build_bundle(facts, firings, [])
    assert [{k: v for k, v in r.items() if k != "attachments"} for r in attached] == [{k: v for k, v in r.items() if k != "attachments"} for r in clean]
    assert next(r for r in attached if r["canonical_id"] == "sunapha")["attachments"] == ["s1", "s2"]


def test_missing_l1_fact_changes_state_without_erasing_formation():
    _, firings = sources()
    row = next(r for r in build_bundle([], firings, []) if r["canonical_id"] == "sunapha")
    assert row["fact_state"] == "missing_fact"
    assert row["effective_state"] == "unresolved"
    assert row["scored"] is False


def test_unbound_or_ambiguous_event_binding_cannot_score_and_retains_provenance():
    facts, firings = sources()
    ambiguous = (*EVENT_BINDINGS, next(b for b in EVENT_BINDINGS if b.canonical_id == "sunapha"))
    row = next(r for r in build_bundle(facts, firings, [], bindings=ambiguous) if r["canonical_id"] == "sunapha")
    assert row["event_class_id"] is None
    assert row["qualification"] == "ambiguous_event_binding"
    assert row["scored"] is False
    assert row["rule_version"] and row["source"]


def test_explicit_zero_degree_target_has_identity_and_missing_target_has_typed_null():
    facts, firings = sources()
    row = build_bundle(facts, firings, [])[0]
    assert row["target"]["longitude_deg"] == 0
    assert row["target"]["fact_id"] == "f:moon"
    facts[0]["fact_value_num"] = None
    assert build_bundle(facts, firings, [])[0]["target"] is None


@pytest.mark.parametrize("field", ["source_locator", "rule_version", "target_yoga_canonical_id"])
def test_unsourced_cancellation_is_never_applied(field):
    facts, firings = sources()
    spec = dict(rule_id="NB-1", kind="excepts", target_yoga_canonical_id="sunapha",
                target_event_class_id="major_gain", rule_version="v1", source_locator="fixture:1")
    spec.pop(field)
    firings[1]["bhanga_rules_jsonb"] = [spec]
    firings[1]["grounds_jsonb"] = {"cancellation_evidence": [{"rule_id": "NB-1", "fact_ids": ["f:moon"]}]}
    gain = next(r for r in build_bundle(facts, firings, []) if r["event_class_id"] == "major_gain")
    assert gain["effective_state"] == "in_force"


def test_inputs_are_not_modified():
    args = sources()
    prior = copy.deepcopy(args)
    build_bundle(*args, [])
    assert args == prior


def test_l2_grounded_proposal_is_retained_as_unscored_testimony():
    facts, _ = sources()
    signals = [dict(signal_id="proposal", ayanamsha_id="a", constituent_facts_array=["f:moon"],
                    configuration_jsonb={"event_class_id": "major_gain", "assumptions": ["interpretation"]})]
    row = build_bundle(facts, [], signals)[0]
    assert row["route"] == "testimony"
    assert row["fact_state"] == "present"
    assert row["scored"] is False
    assert row["effective_state"] == "unresolved"
    assert row["assumptions"] == ["interpretation"]


def test_defeated_adverse_conclusion_never_becomes_opposite_support():
    facts, firings = sources()
    firings[0]["yoga_canonical_id"] = "CODEX-adverse-formation"
    firings[1]["bhanga_rules_jsonb"] = [dict(rule_id="NB-1", kind="excepts",
        target_yoga_canonical_id="CODEX-adverse-formation", target_event_class_id="career_change",
        rule_version="fixture-v1", source_locator="CODEX-fixture:1")]
    firings[1]["grounds_jsonb"] = {"cancellation_evidence": [{"rule_id": "NB-1", "fact_ids": ["f:moon"]}]}
    binding = EventBinding("CODEX-adverse-formation", "career_change", "CODEX-rule", "fixture-v1", "CODEX-source:1", "lagna", "opposes")
    row = next(r for r in build_bundle(facts, firings, [], bindings=(binding,)) if r["event_class_id"])
    assert row["effective_state"] == "defeated"
    assert row["binding"]["relation"] == "opposes"
    assert row["scored"] is False
    assert row["graph_nodes"] and row["graph_edges"][0]["frame"] == "lagna"


def test_missing_l0_rule_preserves_formation_with_null_version():
    facts, firings = sources()
    firings[0]["formation_rule_jsonb"] = None
    firings[0]["classical_citations"] = None
    row = next(r for r in build_bundle(facts, firings, []) if r["canonical_id"] == "sunapha")
    assert row["formation_state"] == "present"
    assert row["qualification"] == "missing_l0_rule"
    assert row["rule_version"] is None
    assert row["scored"] is False
