"""
bodha_writers.sudarshana_emitter — Sudarśana Chakra tri-frame MSR emitter
==========================================================================
D-1.5b Lane B-3 (CR-100). Pure L2 derivation over existing L1
`graha_position` sign facts — NO new astronomical compute.

Doctrine: the Sudarśana Chakra reads a graha's house placement from THREE
concurrent reference points — Lagna (ascendant), Chandra (Moon), Sūrya (Sun).
When a graha lands in the SAME classical quadrant category (kendra / trikoṇa
/ dusthāna / upachaya / maraka) from all three frames, the placement is
"tri-lagna confirmed" — a strong corroboration classical commentators treat
as amplifying the judgment. When the three frames disagree, the placement is
"contradicted" and must be read with more caution (never silently averaged
away — B.10 discipline: divergence is itself the signal).

house_from(reference_sign0, target_sign0) = ((target_sign0 - reference_sign0) % 12) + 1
— the standard sign-count formula (0-based sign indices, Aries=0).

This module is a STANDALONE emitter (does not import or edit bo_laksana.py)
per BRIEF_D1_5B.md Lane B-3 coordination note: B-3 and B-4 each own their own
new MSR emitter module; no shared-emitter-file edits. It is called by the
`bo_sudarshana` writer (pipeline/orchestrator/writers/bo_sudarshana.py).

Salience: class_prior=1.15, subsystem='structural' — ratified DIS.016 / DR-3
(00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md), formalized by the D-1.5b
conductor 2026-07-15. These are HARD-CODED here as the ratified constants —
do not invent new values; a change requires a new DR-n.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from bodha_writers.formulas import (
    salience_formula_v2,
    SalienceInputsV2,
)
from brahmagyan.graha_vocabulary import to_title

ENGINE_VERSION = "bo_sudarshana_v1.0"

# ── DR-3 / DIS.016 ratified constants — do not edit without a new DR-n ───────
SUDARSHANA_CLASS_PRIOR = 1.15
SUDARSHANA_SUBSYSTEM = "structural"
SIGNAL_TYPE_CLASS = "sudarshana_agreement"

# ── Sign order (0-based, Aries=0) — matches ephemeris.py / _names.py canon ──
SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_INDEX: dict[str, int] = {s: i for i, s in enumerate(SIGNS)}

# ── Canonical graha set (KP/Vedic 9-graha Sudarshana scope; Rahu/Ketu included
# per standard practice — Sudarshana is applied to all 9 chara/graha bodies) ──
GRAHAS: list[str] = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"]

# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2. Kept as a local dict so `.get(code, code)` preserves its
# fall-back-to-raw-input-unchanged behavior for unrecognized codes.
_GRAHA_DISPLAY: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

# ── Classical quadrant/category classification (priority order matters: a
# house can belong to more than one category — e.g. H1 is both kendra and
# trikoṇa; H10 is both kendra and upachaya. Priority: trikoṇa > kendra >
# dusthāna > upachaya > maraka > neutral, matching the classical strength
# hierarchy (BPHS: trikoṇa and kendra are the two auspicious pillars;
# dusthāna is inauspicious; upachaya is growth-only; maraka is death-inflicting
# but only activated by dasha, not a natal category in the same sense). ──
_TRIKONA = frozenset({1, 5, 9})
_KENDRA = frozenset({1, 4, 7, 10})
_DUSTHANA = frozenset({6, 8, 12})
_UPACHAYA = frozenset({3, 6, 10, 11})
_MARAKA = frozenset({2, 7})


def house_from(reference_sign0: int, target_sign0: int) -> int:
    """Sign-count house formula. Both args 0-based (Aries=0). Returns 1..12.

    house_from(X, graha) = ((graha_sign0 - X_sign0) % 12) + 1
    """
    return ((target_sign0 - reference_sign0) % 12) + 1


def classify_house(house: int) -> str:
    """Single-label classical quadrant category for a 1..12 house number.

    Priority: trikona > kendra > dusthana > upachaya > maraka > neutral.
    (A house can satisfy more than one predicate — e.g. H1: trikona+kendra,
    H10: kendra+upachaya, H6: dusthana+upachaya — the priority order picks
    the classically-dominant single label so tri-frame comparison is exact.)
    """
    if house in _TRIKONA:
        return "trikona"
    if house in _KENDRA:
        return "kendra"
    if house in _DUSTHANA:
        return "dusthana"
    if house in _UPACHAYA:
        return "upachaya"
    if house in _MARAKA:
        return "maraka"
    return "neutral"


def sign_index(sign_name: str | None) -> int | None:
    if not sign_name:
        return None
    return SIGN_INDEX.get(str(sign_name).strip())


def compute_tri_frame(
    graha_sign0: int, lagna_sign0: int, moon_sign0: int, sun_sign0: int,
) -> dict[str, Any]:
    """Compute the tri-frame (Lagna/Chandra/Sūrya) house assignment for one
    graha and classify each frame's classical category. Returns a dict with
    per-frame houses/classes and an `agreement` verdict:
      - 'confirmed_3frame': all three frames' classical category match
      - 'partial_2frame':   exactly two of the three frames match
      - 'contradicted':     all three frames disagree
    """
    h_lagna = house_from(lagna_sign0, graha_sign0)
    h_moon = house_from(moon_sign0, graha_sign0)
    h_sun = house_from(sun_sign0, graha_sign0)

    c_lagna = classify_house(h_lagna)
    c_moon = classify_house(h_moon)
    c_sun = classify_house(h_sun)

    classes = [c_lagna, c_moon, c_sun]
    if c_lagna == c_moon == c_sun:
        agreement = "confirmed_3frame"
        matching_class = c_lagna
    elif len(set(classes)) == 2:
        agreement = "partial_2frame"
        # The class shared by exactly two of the three frames.
        matching_class = max(set(classes), key=classes.count)
    else:
        agreement = "contradicted"
        matching_class = None

    return {
        "house_from_lagna": h_lagna,
        "house_from_moon": h_moon,
        "house_from_sun": h_sun,
        "class_from_lagna": c_lagna,
        "class_from_moon": c_moon,
        "class_from_sun": c_sun,
        "agreement": agreement,
        "matching_class": matching_class,
    }


# ── Specificity (formula-input, not a new column): reflects the corroboration
# extremity, exactly as SalienceInputsV2.specificity is documented to do
# ("1 + 0.5×extremity_pctl"). confirmed_3frame is maximal corroboration (1.5,
# the formula's own ceiling); partial_2frame is moderate (1.2); contradicted
# gets the baseline (1.0) — divergence is FLAGGED via valence/config, never
# amplified, per CLAUDE.md B.10 (no fabricated confidence). ──
_SPECIFICITY_BY_AGREEMENT: dict[str, float] = {
    "confirmed_3frame": 1.5,
    "partial_2frame": 1.2,
    "contradicted": 1.0,
}

# ── Valence (P0-7 / D4_GRADE_INVERSION fix): keyed on `matching_class` — the
# classical quadrant a signal falls into — NEVER on `agreement` (the tri-
# frame corroboration tier, above). Agreement answers "how sure are we this
# fired"; matching_class answers "is this auspicious or not" — conflating
# them let a signal confirmed by all 3 frames (maximal corroboration) but
# landing in a dusthāna (inauspicious) quadrant read as "benefic". This
# mapping is a direct restatement of the classical characterization already
# in this module's own docstring (line ~68 above, BPHS): trikoṇa and kendra
# are "the two auspicious pillars" -> benefic; dusthāna is "inauspicious" ->
# malefic; upachaya is "growth-only" (a distinct, non-auspicious-pillar
# category) and maraka is "death-inflicting but only activated by dasha, not
# a natal category in the same sense" — neither upachaya nor maraka is a
# clean natal benefic/malefic call without dasha timing this emitter does
# not have, so both stay neutral rather than fabricate a judgment (B.10).
# `contradicted` has matching_class=None (no single quadrant to restate) ->
# honest neutral. Do not key this off `agreement` again — that is the bug.
_VALENCE_BY_MATCHING_CLASS: dict[str | None, str] = {
    "trikona": "benefic",
    "kendra": "benefic",
    "dusthana": "malefic",
    "upachaya": "neutral",
    "maraka": "neutral",
    "neutral": "neutral",
    None: "neutral",
}


def build_signal_row(
    *,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    graha_code: str,
    tri_frame: dict[str, Any],
    fact_ids: dict[str, str | None],
    now: str,
) -> dict[str, Any]:
    """Build one bodha_msr_signals row dict (all NOT NULL columns populated;
    others explicit None) for a graha's tri-frame Sudarshana result.

    fact_ids: {'graha': <fact_id of the graha's own sign fact>,
               'lagna': <fact_id of the Lagna sign fact>,
               'moon': <fact_id of the Moon sign fact>,
               'sun': <fact_id of the Sun sign fact>}
    """
    agreement = tri_frame["agreement"]
    graha_display = _GRAHA_DISPLAY.get(graha_code, graha_code)

    config = {
        "graha": graha_display,
        "graha_code": graha_code,
        "house_from_lagna": tri_frame["house_from_lagna"],
        "house_from_moon": tri_frame["house_from_moon"],
        "house_from_sun": tri_frame["house_from_sun"],
        "class_from_lagna": tri_frame["class_from_lagna"],
        "class_from_moon": tri_frame["class_from_moon"],
        "class_from_sun": tri_frame["class_from_sun"],
        "agreement": agreement,
        "matching_class": tri_frame["matching_class"],
    }

    constituent_facts = [f for f in (
        fact_ids.get("graha"), fact_ids.get("lagna"),
        fact_ids.get("moon"), fact_ids.get("sun"),
    ) if f]

    specificity = _SPECIFICITY_BY_AGREEMENT[agreement]
    valence = _VALENCE_BY_MATCHING_CLASS[tri_frame["matching_class"]]

    inputs = SalienceInputsV2(
        orb_tightness=1.0,
        shadbala_norm=1.0,
        dignity_score=0.50,
        house_number=tri_frame["house_from_lagna"],
        ashtakavarga_bindus=4,
        vargottama_amplification=0.0,
        neechabhanga_modifier=1.0,
        cancellation_modifier=1.0,
        verification_pass_status="documented_approximation",  # M-22: status is earned by a verifier pass, never a literal at the emit site — deterministic sign-count arithmetic, but honestly labeled per the L2 convention (bo_laksana.py, bhavat_bhavam_amplifier.py)
        class_prior=SUDARSHANA_CLASS_PRIOR,
        varga_id="D1",
        specificity=specificity,
        bala_gate=None,
        functional_context=1.0,
        inputs_complete=True,
    )
    sal = salience_formula_v2(inputs)
    computed_salience = sal["computed_salience"]

    if agreement == "confirmed_3frame":
        headline = (
            f"{graha_display}: tri-frame confirmed {tri_frame['matching_class']} "
            f"(H{tri_frame['house_from_lagna']} Lagna / H{tri_frame['house_from_moon']} Moon / "
            f"H{tri_frame['house_from_sun']} Sun)"
        )
    elif agreement == "partial_2frame":
        headline = (
            f"{graha_display}: tri-frame partial ({tri_frame['matching_class']} 2-of-3) — "
            f"H{tri_frame['house_from_lagna']}({tri_frame['class_from_lagna']}) Lagna / "
            f"H{tri_frame['house_from_moon']}({tri_frame['class_from_moon']}) Moon / "
            f"H{tri_frame['house_from_sun']}({tri_frame['class_from_sun']}) Sun"
        )
    else:
        headline = (
            f"{graha_display}: tri-frame CONTRADICTED — "
            f"H{tri_frame['house_from_lagna']}({tri_frame['class_from_lagna']}) from Lagna vs "
            f"H{tri_frame['house_from_moon']}({tri_frame['class_from_moon']}) from Moon vs "
            f"H{tri_frame['house_from_sun']}({tri_frame['class_from_sun']}) from Sun"
        )

    summary = (
        f"category=sudarshana_agreement | graha={graha_display} | "
        f"house_from_lagna={tri_frame['house_from_lagna']} | "
        f"house_from_moon={tri_frame['house_from_moon']} | "
        f"house_from_sun={tri_frame['house_from_sun']} | "
        f"class_from_lagna={tri_frame['class_from_lagna']} | "
        f"class_from_moon={tri_frame['class_from_moon']} | "
        f"class_from_sun={tri_frame['class_from_sun']} | "
        f"agreement={agreement} | matching_class={tri_frame['matching_class']}"
    )

    return {
        "signal_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "signal_type_id": f"sudarshana_agreement:{graha_code}",
        "signal_type_class": SIGNAL_TYPE_CLASS,
        "signal_tradition": "parashari",
        "fact_kind": "relationship",
        "source_l1_asset": "ga_positions",
        "source_subsystem": SUDARSHANA_SUBSYSTEM,
        "signal_summary_text": summary,
        "signal_headline_text": headline,
        "classical_sources_jsonb": json.dumps({
            "catalog_ids": [], "rule_ids": [], "text_chunk_ids": [],
            "citations": ["Sudarshana Chakra (tri-lagna concurrent judgment); "
                          "BPHS quadrant classification (kendra/trikona/dusthana/upachaya)"],
        }),
        "varga_id": "D1",
        "varga_provenance_jsonb": None,
        "epistemic_tier": "documented_approximation",
        "epistemic_jsonb": json.dumps({
            "tradition_agreement_state": "single_tradition",
            "ayanamsha_fragility": "per_ayanamsha_computed",
            "computation_vs_interpretation": "computation",
            "calibration_hook": None,
        }),
        "salience_conditioned_by_jsonb": None,
        "signature_tier": None,  # assigned by the writer's percentile pass over the substep's rows
        "valence": valence,
        "lel_origin": False,
        "configuration_jsonb": json.dumps(config),
        "constituent_facts_array": constituent_facts,
        "constituent_signals_array": None,
        "classical_sources_array": None,
        "source_corroboration_count_by_text": None,
        "source_corroboration_count_by_verse": None,
        "orb_tightness": inputs.orb_tightness,
        "shadbala_norm": inputs.shadbala_norm,
        "dignity_score": inputs.dignity_score,
        "deterministic_strength": 1.0,  # sign-count arithmetic is exact — no measurement uncertainty
        "verification_certainty": 1.0,
        "divisional_corroboration_count": None,
        "dasha_activation_proximity_score": None,  # L3-fill hook
        "house_weight_multiplier": None,
        "ashtakavarga_support_multiplier": None,
        "aspect_modifier": None,
        "vargottama_amplification": inputs.vargottama_amplification,
        "argala_modifier": None,
        "neechabhanga_modifier": inputs.neechabhanga_modifier,
        "cancellation_modifier": inputs.cancellation_modifier,
        "computed_salience": computed_salience,
        "salience_pctl_in_class": None,  # assigned by the writer's percentile pass
        "salience_formula_version": "v2",
        "salience_confidence_interval_jsonb": None,
        "domains_affected_array": ["character", "career"],
        "domain_salience_jsonb": json.dumps({"character": computed_salience, "career": computed_salience}),
        "shared_factor_keys_jsonb": None,
        "cross_domain_shared_factor_count": None,
        "graph_edge_pattern_jsonb": None,
        "graph_node_strength_contribution_jsonb": None,
        "relationship_classification": agreement,
        "graha_weakness_indicators_jsonb": None,
        "remedy_hooks_array": None,
        "recurring_pattern_marker": None,
        "top_k_salience_rank": None,
        "system_convergence_count": None,
        "signature_class": "planetary",
        "contradicts_signals_array": None,
        "active_duration_class": "natal_permanent",
        "active_dasha_periods_jsonb": None,  # L3-fill hook
        "activation_predicted_dates_jsonb": None,  # L3-fill hook
        "predicted_outcome_class": None,
        "cross_ayanamsha_consistency_score": None,
        "strength_normalized_to_chart_max": None,
        "pada_precision_flag": None,
        "cross_system_consensus_count": None,
        "channel_render_priority_jsonb": None,
        "verification_pass_status": "documented_approximation",
        "verification_method": "sign_count_arithmetic_deterministic",
        "citation_ref": f"bo_sudarshana/{graha_code}",
        "citation_human": f"Sudarshana Chakra tri-frame: {graha_display}",
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
        "ratification_factor": None,
        "valence_source": "categorical_deterministic_v1",
    }
