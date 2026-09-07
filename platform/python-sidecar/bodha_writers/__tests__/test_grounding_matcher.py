"""bo_grounding matcher must earn every tier via a real detector, never guess.

Adjudication #2258 / D-NATIVE-09. See grounding_matcher.py's own module
docstring for the two live data findings (sutravali_rules mistagging;
ga_yoga_firings.constituent_fact_ids staleness) that shaped this design.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from bodha_writers.grounding_matcher import classify_msr_signal, classify_yoga_dosha_firing


# ── yoga_dosha_firing ────────────────────────────────────────────────────────

def test_exact_antecedent_match_is_sruti():
    rule = {
        "rule_id": "r1", "text_id": "bphs", "verse_ref": "1:1",
        "antecedent_jsonb": [{"relation": "occupies", "planet": "venus", "house": 2}],
        "predicate_jsonb": {"description": "wealth"},
    }
    match = classify_yoga_dosha_firing(
        firing_id=1,
        constituent_planets=["venus"],
        constituent_houses=[2],
        candidate_rules=[rule],
    )
    assert match.grounding_tier == "sruti"
    assert match.matched_rule_id == "r1"
    assert match.citation_granularity == "chapter_verse"
    assert match.derivation_chain == ["bphs:1:1"]


def test_rule_covering_only_part_of_a_multi_component_firing_is_yukti_not_sruti():
    # The rule's antecedent (venus@2 alone) is a real citation, but this
    # firing's actual configuration also requires jupiter@5 -- the rule
    # doesn't state the effect of THIS exact configuration, only a simpler
    # one. Partial coverage is yukti-level (each component resolves
    # individually), never sruti.
    rule = {
        "rule_id": "r1", "text_id": "bphs", "verse_ref": "1:1",
        "antecedent_jsonb": [{"relation": "occupies", "planet": "venus", "house": 2}],
    }
    match = classify_yoga_dosha_firing(
        firing_id=1,
        constituent_planets=["venus", "jupiter"],
        constituent_houses=[2, 5],
        candidate_rules=[rule],
    )
    assert match.grounding_tier == "yukti"
    assert match.matched_rule_id == "r1"


def test_mistagged_yoga_canonical_id_does_not_fabricate_a_sruti_match():
    # The real sunapha case: constituents are [moon@12, lagna@1], but the only
    # candidate rules (however tagged) describe venus@2 and mars-own-sign --
    # neither is a subset of the firing's actual placements. Must NOT match.
    venus_rule = {
        "rule_id": "a5d58ce9", "text_id": "jataka_parijata", "verse_ref": "PG450:C1",
        "antecedent_jsonb": [{"relation": "occupies", "planet": "venus", "house": 2}],
    }
    mars_dignity_rule = {
        "rule_id": "7ede2ed9", "text_id": "saravali", "verse_ref": "PG144:C1",
        "antecedent_jsonb": [{"relation": "dignity_state", "planet": "mars", "dignity": "own sign"}],
    }
    match = classify_yoga_dosha_firing(
        firing_id=2735,
        constituent_planets=["moon", "lagna"],
        constituent_houses=[12, 1],
        candidate_rules=[venus_rule, mars_dignity_rule],
    )
    assert match.grounding_tier == "pratyaksa"
    assert match.matched_rule_id is None
    assert "reason" in match.grounding_evidence_jsonb


def test_dignity_relation_antecedents_never_verify_even_if_they_would_technically_apply():
    # Not structurally verifiable with current data -- must never be trusted
    # even when it happens to describe a true condition for this firing.
    rule = {
        "rule_id": "r9", "text_id": "saravali", "verse_ref": "9:9",
        "antecedent_jsonb": [{"relation": "dignity_state", "planet": "mars", "dignity": "own sign"}],
    }
    match = classify_yoga_dosha_firing(
        firing_id=3, constituent_planets=["mars"], constituent_houses=[7],
        candidate_rules=[rule],
    )
    assert match.grounding_tier == "pratyaksa"


def test_per_component_resolution_without_full_coverage_is_yukti():
    rule_a = {
        "rule_id": "ra", "text_id": "bphs", "verse_ref": "2:1",
        "antecedent_jsonb": [{"relation": "occupies", "planet": "moon", "house": 12}],
    }
    # No rule covers lagna@1 -- only one of the two components resolves.
    match = classify_yoga_dosha_firing(
        firing_id=2735,
        constituent_planets=["moon", "lagna"],
        constituent_houses=[12, 1],
        candidate_rules=[rule_a],
    )
    assert match.grounding_tier == "yukti"
    assert match.matched_rule_id == "ra"
    assert len(match.derivation_chain) == 1
    assert match.grounding_evidence_jsonb == {"matched_components": 1, "total_components": 2}


def test_no_candidate_rules_at_all_is_honest_pratyaksa():
    match = classify_yoga_dosha_firing(
        firing_id=4, constituent_planets=["sun"], constituent_houses=[3], candidate_rules=[],
    )
    assert match.grounding_tier == "pratyaksa"


def test_malformed_antecedent_entry_is_never_trusted():
    rule = {
        "rule_id": "rbad", "text_id": "bphs", "verse_ref": "3:3",
        "antecedent_jsonb": [{"relation": "occupies", "planet": "moon"}],  # missing house
    }
    match = classify_yoga_dosha_firing(
        firing_id=5, constituent_planets=["moon"], constituent_houses=[12], candidate_rules=[rule],
    )
    assert match.grounding_tier == "pratyaksa"


def test_partial_full_match_rule_with_extra_condition_not_present_fails_sruti_but_can_still_yukti():
    # Rule requires BOTH venus@2 AND moon@12 -- firing only has moon@12, so
    # the rule's full antecedent is not a subset (no sruti), but moon@12
    # alone is separately checked against candidates for yukti.
    rule = {
        "rule_id": "rc", "text_id": "bphs", "verse_ref": "4:4",
        "antecedent_jsonb": [
            {"relation": "occupies", "planet": "venus", "house": 2},
            {"relation": "occupies", "planet": "moon", "house": 12},
        ],
    }
    match = classify_yoga_dosha_firing(
        firing_id=6, constituent_planets=["moon"], constituent_houses=[12], candidate_rules=[rule],
    )
    # The rule's own per-entry pairs include moon@12, so per-component lookup
    # against THIS rule's antecedent entries still finds it (yukti).
    assert match.grounding_tier == "yukti"
    assert match.matched_rule_id == "rc"


# ── msr_signal ────────────────────────────────────────────────────────────────

def test_msr_signal_with_resolved_chunk_id_is_sruti():
    match = classify_msr_signal(
        signal_id="s1",
        classical_sources_jsonb={"rule_ids": [], "text_chunk_ids": ["chunk-abc"], "citations": [], "catalog_ids": []},
    )
    assert match.grounding_tier == "sruti"
    assert match.matched_rule_id == "chunk-abc"


def test_msr_signal_with_only_a_citation_string_is_yukti_not_sruti():
    match = classify_msr_signal(
        signal_id="s2",
        classical_sources_jsonb={"rule_ids": [], "text_chunk_ids": [], "citations": ["bphs:35"], "catalog_ids": ["gola"]},
    )
    assert match.grounding_tier == "yukti"
    assert match.matched_rule_id == "gola"
    assert match.derivation_chain == ["bphs:35"]


def test_msr_signal_with_citation_but_no_catalog_id_falls_back_to_citation_as_matched_id():
    match = classify_msr_signal(
        signal_id="s3",
        classical_sources_jsonb={"rule_ids": [], "text_chunk_ids": [], "citations": ["bphs:35"], "catalog_ids": []},
    )
    assert match.grounding_tier == "yukti"
    assert match.matched_rule_id == "bphs:35"


def test_msr_signal_with_no_sources_at_all_is_pratyaksa():
    match = classify_msr_signal(signal_id="s4", classical_sources_jsonb=None)
    assert match.grounding_tier == "pratyaksa"
    assert match.matched_rule_id is None


def test_msr_signal_with_empty_sources_dict_is_pratyaksa():
    match = classify_msr_signal(signal_id="s5", classical_sources_jsonb={})
    assert match.grounding_tier == "pratyaksa"


def test_every_yukti_match_satisfies_the_db_check_constraint_shape():
    # Mirrors migration 897's CHECK: yukti requires non-null matched_rule_id
    # AND non-empty derivation_chain.
    match = classify_msr_signal(
        signal_id="s6",
        classical_sources_jsonb={"rule_ids": [], "text_chunk_ids": [], "citations": ["saravali:9"], "catalog_ids": []},
    )
    assert match.grounding_tier == "yukti"
    assert match.matched_rule_id is not None
    assert match.derivation_chain and len(match.derivation_chain) > 0


def test_every_sruti_match_satisfies_the_db_check_constraint_shape():
    # Mirrors migration 897's CHECK: sruti requires non-null citation_granularity.
    rule = {
        "rule_id": "rs", "text_id": "bphs", "verse_ref": "5:5",
        "antecedent_jsonb": [{"relation": "occupies", "planet": "sun", "house": 10}],
    }
    match = classify_yoga_dosha_firing(
        firing_id=7, constituent_planets=["sun"], constituent_houses=[10], candidate_rules=[rule],
    )
    assert match.grounding_tier == "sruti"
    assert match.citation_granularity is not None
