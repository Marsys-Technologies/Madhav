"""Golden-value fidelity test for bo_grounding narration (derivation_chain, grounding_evidence_jsonb.reason).

bodha_grounding_matches.derivation_chain holds, for a yukti firing, one cited-principle string per
constituent pair, composed as "<text_id>:<verse_ref> (<planet> in house <house>)" over the pairs in
sorted (planet, house) order; for a sruti firing the single string "<text_id>:<verse_ref>".
grounding_evidence_jsonb.reason is a constant sentence written only for a pratyaksa row, one wording
for a yoga/dosha firing and one for an MSR signal. Every expected string below is stated by hand
from that template, never read from the builder.
"""
from __future__ import annotations

import json

from bodha_writers.grounding_matcher import classify_msr_signal, classify_yoga_dosha_firing
from pipeline.orchestrator.writers.bo_grounding import _match_to_row

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
BUILD = "00000000-0000-4000-8000-000000000001"
NOW = "2026-01-01T00:00:00+00:00"


def _rule(rule_id: str, text_id: str, verse_ref: str, planet: str, house: int) -> dict:
    return {
        "rule_id": rule_id,
        "text_id": text_id,
        "verse_ref": verse_ref,
        "antecedent_jsonb": [{"relation": "occupies", "planet": planet, "house": house}],
        "predicate_jsonb": {},
    }


def test_yukti_derivation_chain_names_each_constituent_with_its_rule_citation() -> None:
    rules = [
        _rule("R-MOON", "BPHS", "PG94:C1", "moon", 12),
        _rule("R-LAGNA", "BPHS", "PG10:C2", "lagna", 1),
    ]
    match = classify_yoga_dosha_firing(
        firing_id=7,
        constituent_planets=["moon", "lagna"],
        constituent_houses=[12, 1],
        candidate_rules=rules,
    )
    row = _match_to_row(match, CHART, AYA, BUILD, NOW)
    assert row["derivation_chain"] == [
        "BPHS:PG10:C2 (lagna in house 1)",
        "BPHS:PG94:C1 (moon in house 12)",
    ]


def test_pratyaksa_reason_states_that_no_citation_resolved() -> None:
    firing = classify_yoga_dosha_firing(
        firing_id=8,
        constituent_planets=["mars"],
        constituent_houses=[3],
        candidate_rules=[],
    )
    firing_row = _match_to_row(firing, CHART, AYA, BUILD, NOW)
    reason = json.loads(firing_row["grounding_evidence_jsonb"])["reason"]
    assert reason == (
        "no sutravali_rules antecedent (full or per-component) matched this firing's "
        "constituent_planets/constituent_houses"
    )

    signal = classify_msr_signal(signal_id="sig-1", classical_sources_jsonb={})
    signal_row = _match_to_row(signal, CHART, AYA, BUILD, NOW)
    signal_reason = json.loads(signal_row["grounding_evidence_jsonb"])["reason"]
    assert signal_reason == "no classical_sources_jsonb citations for this signal"
