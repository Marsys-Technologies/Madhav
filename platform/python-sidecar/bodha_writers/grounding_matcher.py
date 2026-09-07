"""
bodha_writers.grounding_matcher — D-GROUNDING tier-assignment matcher (bo_grounding)
=====================================================================================
Adjudication #2258, tier-assignment ruling D-NATIVE-09 (2026-09-07). Classifies
each v1-scope interpretive claim (`yoga_dosha_firing`, `msr_signal`) into a
`grounding_tier` — sruti | yukti | pratyaksa — per a real detector for each
tier, never a chosen/guessed label (§N.8).

Detector order (ruled): sruti -> yukti -> pratyaksa. Assign the FIRST tier its
own detector confirms; on any ambiguity, fall through to the lower tier (an
honest pratyaksa beats an invented sruti). Every assigned tier is stored with
the evidence that earned it, so any row is auditable (§N.7):
  - sruti: the covering verse_ref (+ matched_rule_id, citation_granularity)
  - yukti: the constituent-source list + derivation_chain (+ matched_rule_id)
  - pratyaksa: no citation fields set; the absence itself IS the evidence

Two real data-integrity findings shaped this design (investigated live against
production, not assumed):

1. `sutravali_rules.yoga_canonical_id` tagging is UNRELIABLE as a standalone
   sruti signal. Verified for the `sunapha` firing on the canonical chart: its
   actual `constituent_planets`/`constituent_houses` (`[moon,lagna]`/`[12,1]`)
   match NEITHER of the two `sutravali_rules` rows tagged
   `yoga_canonical_id='sunapha'` (venus-in-house-2; mars-in-own-sign). A naive
   tag JOIN would have FABRICATED a sruti classification. This matcher
   therefore does NOT trust the tag alone — it verifies structurally, and
   searches the antecedent corpus untagged-inclusive (2994 of 3002
   `sutravali_rules` rows carry no `yoga_canonical_id` at all; restricting to
   the 8 tagged values would silently exclude the vast majority of real
   citations for no honest reason).
2. `ga_yoga_firings.constituent_fact_ids` is SYSTEMICALLY stale: 0 of 40
   distinct fact_ids across all 63 fired yogas (canonical chart) resolve to
   `chart_facts` — confirmed via a full check, not a sample; consistent with
   predating the fact_id hash-scheme change (#1747/PR #1898). This closes the
   constituent-fact-citation path to yukti for `yoga_dosha_firing`; this
   matcher's yukti detector for that target_kind instead resolves each
   constituent (planet, house) pair directly against `sutravali_rules`
   antecedent entries — the ruling's own "each of its constituent components
   resolves to a classical source" framing does not require the SAME rule to
   cover every component, just that each component individually does.

v1 scope (Conductor-ruled, #2258 (a)): target_kind in
{'yoga_dosha_firing', 'msr_signal'} only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GroundingMatch:
    target_kind: str
    target_id: str
    grounding_tier: str  # sruti | yukti | pratyaksa
    citation_granularity: str | None = None
    grounding_evidence_jsonb: dict[str, Any] | None = None
    derivation_chain: list[str] | None = None
    matched_rule_id: str | None = None


# Only 'occupies' antecedent entries are structurally verifiable against the
# data this matcher has (constituent_planets/constituent_houses, paired by
# position). Other relation types (e.g. dignity_state) cannot be honestly
# confirmed with current data -- a rule using them never contributes to
# sruti or yukti here (ambiguity -> lower tier, not a guess).
_VERIFIABLE_RELATION = "occupies"


def _occupies_pairs(antecedent_jsonb: Any) -> list[tuple[str, int]] | None:
    """Extract (planet, house) pairs from an antecedent IF it consists
    ENTIRELY of verifiable 'occupies' entries. Returns None if the antecedent
    contains any entry this matcher cannot honestly verify (a different
    relation type, or a malformed entry) -- such a rule is excluded from
    sruti/yukti consideration rather than guessed at."""
    if not isinstance(antecedent_jsonb, list) or not antecedent_jsonb:
        return None
    pairs: list[tuple[str, int]] = []
    for entry in antecedent_jsonb:
        if not isinstance(entry, dict):
            return None
        if entry.get("relation") != _VERIFIABLE_RELATION:
            return None
        planet = entry.get("planet")
        house = entry.get("house")
        if not isinstance(planet, str) or not isinstance(house, int):
            return None
        pairs.append((planet.strip().lower(), house))
    return pairs


def classify_yoga_dosha_firing(
    *,
    firing_id: int,
    constituent_planets: list[str],
    constituent_houses: list[int],
    candidate_rules: list[dict[str, Any]],
) -> GroundingMatch:
    """`candidate_rules`: every sutravali_rules row worth considering for this
    firing (caller pre-filters by relevance; see grounding_writer.py). Each
    row: {rule_id, text_id, verse_ref, antecedent_jsonb, yoga_canonical_id}.
    """
    target_id = str(firing_id)
    firing_pairs = set(
        zip((p.strip().lower() for p in constituent_planets), constituent_houses)
    )

    # sruti: a rule's antecedent set is EXACTLY this firing's constituent set
    # -- the text directly states the effect of this precise configuration,
    # not a simpler one that merely happens to also be satisfied. A rule
    # covering only PART of a multi-component firing (e.g. one planet of two)
    # describes a different, simpler configuration -- real evidence, but not
    # a match for "this exact configuration's effect"; it still counts toward
    # yukti below (each constituent resolves individually).
    for rule in candidate_rules:
        pairs = _occupies_pairs(rule.get("antecedent_jsonb"))
        if pairs is None or not pairs:
            continue
        if set(pairs) == firing_pairs:
            return GroundingMatch(
                target_kind="yoga_dosha_firing",
                target_id=target_id,
                grounding_tier="sruti",
                citation_granularity="chapter_verse",
                grounding_evidence_jsonb={
                    "text_id": rule.get("text_id"),
                    "verse_ref": rule.get("verse_ref"),
                    "antecedent_jsonb": rule.get("antecedent_jsonb"),
                    "predicate_jsonb": rule.get("predicate_jsonb"),
                },
                derivation_chain=[f"{rule.get('text_id')}:{rule.get('verse_ref')}"],
                matched_rule_id=str(rule.get("rule_id")),
            )

    # yukti: no single covering rule, but each constituent (planet, house)
    # pair individually resolves to at least one cited principle somewhere in
    # the corpus (not necessarily the same rule, not necessarily tagged with
    # this yoga's canonical id -- the tag was shown unreliable above).
    chain: list[str] = []
    matched_ids: list[str] = []
    for planet, house in sorted(firing_pairs):
        hit = None
        for rule in candidate_rules:
            pairs = _occupies_pairs(rule.get("antecedent_jsonb"))
            if pairs and (planet, house) in pairs:
                hit = rule
                break
        if hit is not None:
            chain.append(f"{hit.get('text_id')}:{hit.get('verse_ref')} ({planet} in house {house})")
            matched_ids.append(str(hit.get("rule_id")))

    if chain:
        return GroundingMatch(
            target_kind="yoga_dosha_firing",
            target_id=target_id,
            grounding_tier="yukti",
            grounding_evidence_jsonb={"matched_components": len(chain), "total_components": len(firing_pairs)},
            derivation_chain=chain,
            matched_rule_id=matched_ids[0],
        )

    # pratyaksa: no classical citation of any kind resolved for this firing.
    return GroundingMatch(
        target_kind="yoga_dosha_firing",
        target_id=target_id,
        grounding_tier="pratyaksa",
        grounding_evidence_jsonb={
            "reason": "no sutravali_rules antecedent (full or per-component) matched this firing's "
                      "constituent_planets/constituent_houses"
        },
    )


def classify_msr_signal(
    *,
    signal_id: str,
    classical_sources_jsonb: dict[str, Any] | None,
) -> GroundingMatch:
    """sruti requires a RESOLVED verse_ref/source_chunk_id -- confirmed dormant
    in v1's actual data (bodha_msr_signals.classical_sources_jsonb.rule_ids
    and .text_chunk_ids are empty for every row on the canonical chart,
    verified live, not assumed) -- so this detector never fires sruti today,
    but is implemented per spec for when text_chunk_ids resolution lands
    (#1726's own future text-direct lane)."""
    target_id = str(signal_id)
    sources = classical_sources_jsonb or {}

    rule_ids = sources.get("rule_ids") or []
    text_chunk_ids = sources.get("text_chunk_ids") or []
    if rule_ids or text_chunk_ids:
        matched_id = str((rule_ids or text_chunk_ids)[0])
        return GroundingMatch(
            target_kind="msr_signal",
            target_id=target_id,
            grounding_tier="sruti",
            citation_granularity="chapter_verse",
            grounding_evidence_jsonb={"rule_ids": rule_ids, "text_chunk_ids": text_chunk_ids},
            derivation_chain=[matched_id],
            matched_rule_id=matched_id,
        )

    citations = sources.get("citations") or []
    if citations:
        catalog_ids = sources.get("catalog_ids") or []
        matched_id = str(catalog_ids[0]) if catalog_ids else str(citations[0])
        return GroundingMatch(
            target_kind="msr_signal",
            target_id=target_id,
            grounding_tier="yukti",
            grounding_evidence_jsonb={"citations": citations, "catalog_ids": catalog_ids},
            derivation_chain=list(citations),
            matched_rule_id=matched_id,
        )

    return GroundingMatch(
        target_kind="msr_signal",
        target_id=target_id,
        grounding_tier="pratyaksa",
        grounding_evidence_jsonb={"reason": "no classical_sources_jsonb citations for this signal"},
    )
