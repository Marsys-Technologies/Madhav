"""bodha_writers.bhavat_bhavam_amplifier — Lane B-4 (D-1.5b, CR-97) MSR emitter.

GATED AMPLIFIER signal class: `bhavat_bhavam_amplifier`.

Doctrinal contract (BRIEF_D1_5B.md Lane B-4 + DIS.016/DR-3 ruling — read both
before touching this file):
  1. NEVER A GENERATOR. Fires ONLY when an already-salient configuration
     (signature_tier in {"major", "chart_defining"}, OR a fired yoga from
     ga_yoga_firings) occupies/rules a bhāva that is the Bhavat-Bhavam
     DERIVED house of another already-salient configuration's house. No
     salient primary + no salient derived-house occupant => no signal, ever.
  2. NEVER OUTRANKS THE PRIMARY. DR-3's ruling is explicit: "the prior
     [bhavat_bhavam_amplifier=0.85] is a scoring input, not a hard cap" — the
     0.85 class_prior alone does NOT guarantee the amplifier's
     computed_salience stays below its primary's. This module enforces it
     with an explicit clamp + assertion (`_clamp_below_primary`), independent
     of whatever the salience formula computes.
  3. NO CHAINING. A bhavat_bhavam_amplifier signal can never itself be
     treated as an "already-salient configuration" input to a second
     application of the rule. Enforced by construction: candidate pools
     passed into this module must never include prior bhavat_bhavam_amplifier
     rows (see `SalientConfig.signal_type_class` guard in `_validate_candidates`).
  4. EVEN HOUSES RECEIVE NOTHING. Derived houses come exclusively from
     `bodha_writers.bhavat_bhavam_registry.derived_houses` — even primary
     houses return () and therefore can never anchor an amplifier.

This module is pure / DB-free (formulas.py convention): callers (bo_laksana's
run_substep) are responsible for building the `SalientConfig` candidate list
from ga_yoga_firings rows + already-tiered bodha_msr_signals rows, and for
turning the returned `AmplifierSignal` objects into full MSR row dicts.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from bodha_writers.bhavat_bhavam_registry import derived_houses

VERSION_BHAVAT_BHAVAM_AMPLIFIER = "v1.0"

SIGNAL_TYPE_CLASS = "bhavat_bhavam_amplifier"
SOURCE_SUBSYSTEM = "structural"  # DR-3 (DIS.016) ruling
CLASS_PRIOR = 0.85  # DR-3 (DIS.016) ratified constant — RATIFIED, do not change without a new DR-n

# Signature tiers counted as "already salient" for the tier>=major test.
SALIENT_TIERS = ("major", "chart_defining")

# Guard: the amplifier's computed_salience is clamped strictly below the
# primary's by at least this margin, so floating-point equality can never
# accidentally satisfy "never outranks" at the boundary.
_OUTRANK_EPSILON = 1e-6


@dataclass(frozen=True)
class SalientConfig:
    """An already-salient configuration: either a fired yoga (source="yoga_firing")
    or a tier>=major MSR signal (source="msr_tier"). `house` is the bhāva this
    configuration occupies or rules."""
    identifier: str
    house: int
    source: str  # "yoga_firing" | "msr_tier"
    salience_reference: float  # strength (yoga) or computed_salience (MSR row)
    signal_type_class: str = "configuration"
    signal_id: str | None = None  # populated only for source="msr_tier"
    ayanamsha_id: str = ""


@dataclass(frozen=True)
class AmplifierSignal:
    signal_id: str
    ayanamsha_id: str
    primary_identifier: str
    primary_house: int
    primary_salience: float
    derived_house: int
    occupant_identifier: str
    occupant_salience: float
    computed_salience: float
    class_prior: float
    signal_type_class: str
    source_subsystem: str
    configuration: dict[str, Any] = field(default_factory=dict)


def _validate_candidates(candidates: list[SalientConfig]) -> list[SalientConfig]:
    """NO-CHAINING guard: strip (defensively — the caller should never pass
    these in the first place) any candidate that is itself a prior
    bhavat_bhavam_amplifier signal. A candidate pool built correctly by the
    caller never triggers this filter; it exists so this module is safe even
    if a future caller forgets the exclusion."""
    return [c for c in candidates if c.signal_type_class != SIGNAL_TYPE_CLASS]


def _is_salient(candidate: SalientConfig) -> bool:
    if candidate.source == "yoga_firing":
        return True  # a row in ga_yoga_firings with fired=True IS the salience test
    if candidate.source == "msr_tier":
        return candidate.signal_type_class != SIGNAL_TYPE_CLASS  # no-chaining, belt+suspenders
    return False


def _clamp_below_primary(raw_salience: float, primary_salience: float) -> float:
    """NEVER-OUTRANKS-PRIMARY guard (CODE, not just the 0.85 prior).

    DR-3: "the prior is a scoring input, not a hard cap" — so this function
    is the actual hard cap. Always returns a value strictly less than
    `primary_salience` (by at least _OUTRANK_EPSILON), regardless of what the
    formula above computed.
    """
    ceiling = primary_salience - _OUTRANK_EPSILON
    if ceiling <= 0:
        # Degenerate primary (near-zero salience): still must not be <= 0 and
        # still must not reach/exceed the primary. Use a tiny fraction of the
        # primary rather than a fabricated positive constant.
        ceiling = max(primary_salience * 0.01, 0.0)
    clamped = min(raw_salience, ceiling)
    assert clamped < primary_salience, (
        "bhavat_bhavam_amplifier restraint violation: computed_salience "
        f"({clamped}) did not stay below its primary's ({primary_salience})"
    )
    return clamped


def compute_bhavat_bhavam_amplifiers(
    candidates: list[SalientConfig],
) -> list[AmplifierSignal]:
    """The core doctrinal computation.

    For every ODD primary house H that has at least one already-salient
    candidate occupying/ruling it, and for every derived house D in
    bhavat_bhavam_registry.derived_houses(H) that ALSO has at least one
    already-salient candidate, emit one AmplifierSignal per
    (primary_candidate, derived_candidate) pair, corroborating the primary —
    never generating a finding where neither leg is already salient, never
    exceeding the primary's own weight, never chaining off a prior amplifier.
    """
    candidates = _validate_candidates(candidates)
    salient = [c for c in candidates if _is_salient(c)]

    by_house: dict[int, list[SalientConfig]] = {}
    for c in salient:
        by_house.setdefault(c.house, []).append(c)

    out: list[AmplifierSignal] = []
    for primary_house, primaries in by_house.items():
        # EVEN-HOUSE GUARD: derived_houses() returns () for every even house
        # by construction (bhavat_bhavam_registry), so this loop naturally
        # never fires for an even primary. No separate branch needed — but
        # assert it explicitly so a future registry bug can't silently defeat
        # the doctrine.
        derived = derived_houses(primary_house)
        if not derived:
            assert primary_house % 2 == 0, (
                f"bhavat_bhavam: odd house {primary_house} unexpectedly has no "
                "derived houses — registry map is broken"
            )
            continue  # NEVER A GENERATOR: no derived house => nothing to amplify

        for d_house in derived:
            occupants = by_house.get(d_house)
            if not occupants:
                continue  # NEVER A GENERATOR: no salient occupant in the derived house

            for primary in primaries:
                for occupant in occupants:
                    if occupant is primary:
                        continue
                    raw = CLASS_PRIOR * min(primary.salience_reference, occupant.salience_reference)
                    amplifier_salience = _clamp_below_primary(raw, primary.salience_reference)
                    out.append(AmplifierSignal(
                        signal_id=str(uuid.uuid4()),
                        ayanamsha_id=primary.ayanamsha_id or occupant.ayanamsha_id,
                        primary_identifier=primary.identifier,
                        primary_house=primary_house,
                        primary_salience=primary.salience_reference,
                        derived_house=d_house,
                        occupant_identifier=occupant.identifier,
                        occupant_salience=occupant.salience_reference,
                        computed_salience=amplifier_salience,
                        class_prior=CLASS_PRIOR,
                        signal_type_class=SIGNAL_TYPE_CLASS,
                        source_subsystem=SOURCE_SUBSYSTEM,
                        configuration={
                            "primary_house": primary_house,
                            "primary_identifier": primary.identifier,
                            "primary_source": primary.source,
                            "derived_house": d_house,
                            "occupant_identifier": occupant.identifier,
                            "occupant_source": occupant.source,
                            "gated_amplifier": True,
                            "no_chaining": True,
                        },
                    ))
    return out


def to_msr_row(
    signal: AmplifierSignal,
    chart_id: str,
    build_id: str,
    now: str,
) -> dict[str, Any]:
    """Convert an AmplifierSignal into a bodha_msr_signals row dict, matching
    the column set + convention of bo_laksana's other synthetic emitters
    (mirrors `_load_vichara_divergence_signals`'s row shape so it can be
    appended to the same `signal_rows` list before the shared post-processing
    pipeline — top_k_salience_rank / salience_pctl_in_class /
    strength_normalized_to_chart_max / signature_tier — runs).

    NOTE (no-chaining, restated in data): `salience_conditioned_by_jsonb`
    records the amplifier as conditioning-only ("effect": "amplifies") on the
    primary — it is never itself eligible to be re-selected as a primary or
    an occupant by a second application of compute_bhavat_bhavam_amplifiers
    (enforced upstream by `_validate_candidates`).
    """
    import json as _json

    headline = (
        f"Bhavat-Bhavam: {signal.occupant_identifier} in H{signal.derived_house} "
        f"(derived from H{signal.primary_house}) corroborates {signal.primary_identifier} in H{signal.primary_house}"
    )
    return {
        "signal_id": signal.signal_id,
        "chart_id": chart_id,
        "ayanamsha_id": signal.ayanamsha_id,
        "build_id": build_id,
        "signal_type_id": (
            f"bhavat_bhavam_amplifier:H{signal.primary_house}->H{signal.derived_house}:"
            f"{signal.primary_identifier}:{signal.occupant_identifier}"
        )[:120],
        "signal_type_class": signal.signal_type_class,
        "signal_tradition": "parashari",
        "fact_kind": "configuration",
        "source_l1_asset": "ga_yoga",
        "source_subsystem": signal.source_subsystem,
        "signal_summary_text": (
            f"category=bhavat_bhavam_amplifier | primary_house=H{signal.primary_house} | "
            f"primary={signal.primary_identifier} | derived_house=H{signal.derived_house} | "
            f"occupant={signal.occupant_identifier} | gated_amplifier=true | no_chaining=true"
        ),
        "signal_headline_text": headline,
        "classical_sources_jsonb": None,
        "varga_id": None,
        "varga_provenance_jsonb": None,
        "epistemic_tier": "documented_approximation",
        "epistemic_jsonb": _json.dumps({
            "tradition_agreement_state": "single",
            "epistemic_tier": "documented_approximation",
            "computation_vs_interpretation": "computation",
            "source": "bhavat_bhavam_amplifier/ga_yoga_firings+bodha_msr_signals",
        }),
        "salience_conditioned_by_jsonb": _json.dumps([{
            "signal_id": signal.primary_identifier,
            "effect": "amplifies",
            "basis": f"bhavat_bhavam: H{signal.derived_house} is the derived house of H{signal.primary_house}",
        }]),
        "signature_tier": None,  # assigned by _assign_tiers_by_percentile
        "valence": "neutral",
        "lel_origin": False,
        "configuration_jsonb": _json.dumps(signal.configuration),
        "constituent_facts_array": None,
        "constituent_signals_array": None,
        "classical_sources_array": None,
        "source_corroboration_count_by_text": 2,
        "source_corroboration_count_by_verse": None,
        "orb_tightness": 1.0,
        "shadbala_norm": 1.0,
        "dignity_score": 0.5,
        "deterministic_strength": 1.0,
        "verification_certainty": 0.778,
        "divisional_corroboration_count": None,
        "dasha_activation_proximity_score": None,
        "house_weight_multiplier": 1.0,
        "ashtakavarga_support_multiplier": 1.0,
        "aspect_modifier": None,
        "vargottama_amplification": 0.0,
        "argala_modifier": None,
        "neechabhanga_modifier": 1.0,
        "cancellation_modifier": 1.0,
        "computed_salience": round(signal.computed_salience, 6),
        "salience_formula_version": VERSION_BHAVAT_BHAVAM_AMPLIFIER,
        "salience_confidence_interval_jsonb": None,
        "domains_affected_array": [],
        "domain_salience_jsonb": _json.dumps({}),
        "shared_factor_keys_jsonb": None,
        "cross_domain_shared_factor_count": None,
        "graph_edge_pattern_jsonb": None,
        "graph_node_strength_contribution_jsonb": None,
        "relationship_classification": None,
        "graha_weakness_indicators_jsonb": None,
        "remedy_hooks_array": None,
        "recurring_pattern_marker": None,
        "top_k_salience_rank": None,
        "system_convergence_count": None,
        "signature_class": "planetary",
        "contradicts_signals_array": None,
        "active_duration_class": "natal_permanent",
        "active_dasha_periods_jsonb": None,
        "activation_predicted_dates_jsonb": None,
        "predicted_outcome_class": None,
        "cross_ayanamsha_consistency_score": None,
        "strength_normalized_to_chart_max": None,
        "pada_precision_flag": None,
        "cross_system_consensus_count": None,
        "channel_render_priority_jsonb": None,
        "verification_pass_status": "documented_approximation",
        "verification_method": "bhavat_bhavam_amplifier_v1",
        "citation_ref": f"bhavat_bhavam/H{signal.primary_house}/H{signal.derived_house}",
        "citation_human": (
            f"Bhavat Bhavam (house of the house): H{signal.derived_house} derived from H{signal.primary_house}"
        ),
        "computed_at": now,
        "engine_version": "bo_laksana_v2.2",
        "ratification_factor": None,
        "valence_source": "bhavat_bhavam_amplifier_v1",
        "class_prior": signal.class_prior,
    }
