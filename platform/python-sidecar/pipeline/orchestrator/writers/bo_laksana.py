"""
bo_laksana — MSR Signal Store (L2 Bodha root writer)
=====================================================
Category-agnostic projection of ALL chart_facts rows into bodha_msr_signals.

Design invariants (anti-drift spine):
- Queries chart_facts with NO category whitelist — every fact is a candidate signal.
- Infers source_l1_asset + source_subsystem from chart_facts.source_calculation prefix.
- Reads constituent_facts_array from fact_value_jsonb.constituent_facts_array when
  present (ga_structural composite facts); falls back to [fact_id] for simple facts.
- Every signal carries lel_origin=False (LEL data is L3-gated; L2 is timeless structural).
- signal_summary_text: lossless deterministic NL iterate of every config key — embedding
  input for bo_samskara.
- signal_headline_text: short deterministic sentence for display/retrieval.
- Salience = salience_formula_v1 (bodha_writers.formulas) — deterministic, never LLM.
- signature_tier assigned post-formula from salience thresholds.
- valence assigned from category heuristics — categorical, not generative.
- varga_id extracted from fact_key suffix when present (_D1, _D9, _D10, etc.)
- L3 hook columns (dasha_activation_proximity_score, active_dasha_periods_jsonb,
  activation_predicted_dates_jsonb) are written as NULL — L3 Kāla fills them.

WP-2.4 (MSR ingestion redesign — LCA-9b-1..5) hardening:
- FLOOD CAP (9b-1): per-varga aspect/matrix families (aspect_jaimini_per_varga et al.)
  are no longer 1:1-emitted. Groups over RATIFIED_FLOOD_CAP collapse to ONE aggregate
  rollup signal per (category × varga) that cites every member fact_id as a resolving
  constituent — narrows the funnel instead of flooding it.
- SALIENCE RE-TIERING (9b-2): divisional/granular signals (varga != D1, or category
  ending _per_varga) are barred from major/chart_defining via a tier ceiling. This is
  the SOURCE fix behind WP-1.2d's serving-time salience cap.
- KP HOUSE-AWARE DOMAINS (9b-3): cusp/KP-significator facts inherit the domains of the
  bhava their cusp number denotes (2nd/11th → wealth, 7th → relationship, …) so wealth
  significators can surface in a wealth query.
- CONSTITUENT REFERENTIAL INTEGRITY (9b-5, §N.5): every constituent_facts_array entry
  is filtered against the chart's real chart_facts.fact_id set and the signal's own
  (guaranteed-resolving) fact_id is always unioned in — NO signal cites a fact_id that
  resolves to nothing. Enforced permanently by
  platform/scripts/governance/msr_referential_integrity.py.

HEAVY writer: plan_substeps returns one SubStep per ayanamsha.
Each sub-step runs inside its own SAVEPOINT managed by the orchestrator.
"""
from __future__ import annotations

import json
import logging
import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS
from brahmagyan.graha_vocabulary import norm_graha, to_title
from . import WriterBase, ContextSpec, WriterResult, SubStep, register
from bodha_writers.formulas import (
    salience_formula_v2,
    SalienceInputsV2,
    VERIFICATION_RESCALE,
    DIGNITY_SCORE as _FML_DIGNITY_SCORE,
    HOUSE_WEIGHT as _FML_HOUSE_WEIGHT,
)

logger = logging.getLogger(__name__)

# ── Canonical ayanamsha IDs (from chart_facts; match DB exactly) ─────────────
CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "raman",
    "krishnamurti",
    "surya_siddhanta_classical",
    "true_chitra",
]

ENGINE_VERSION = "bo_laksana_v2.2"

# ── D-1.5b hotfix: bo_laksana's ownership allowlist for bodha_msr_signals ────
# `bodha_msr_signals` is a shared table: bo_laksana projects ALL L1
# chart_facts into it (category-agnostic), and bo_sudarshana (an independent
# top-level asset, depends_on=['ga_positions'] only) ALSO inserts directly
# into it under signal_type_class='sudarshana_agreement'. bo_laksana's
# delete-then-insert idempotency cycle must delete ONLY the signal_type_class
# values bo_laksana itself emits — never a blanket per-(chart,ayanamsha) wipe
# — or it silently destroys other writers' rows on every rebuild (see the
# D-1.5b full-rebuild post-mortem on chart 482012f1, where this wiped 45
# bo_sudarshana rows to 0 while bo_sudarshana's asset_throughput row kept
# claiming state='lit', rows_written=45).
#
# This is the complete, closed set of signal_type_class values bo_laksana can
# emit, enumerated from every "signal_type_class": <literal> assignment and
# every SIGNAL_TYPE_CLASS import in this module:
#   - _signal_type_class() below (category-agnostic L1-fact projection; its
#     fallback branch is "composite_state" — the mapping is total/closed, so
#     this list does not grow as new fact_categories appear in L1):
#     yoga, dosha, sade_sati, panchanga, karaka_alignment, tradition_specific,
#     parivartana, configuration, varga_pattern, annual, medical, vastu,
#     composite_state
#   - "varga_ratification_divergence" (CR-57 divergence signals, explicit literal)
#   - bhavat_bhavam_amplifier.SIGNAL_TYPE_CLASS = "bhavat_bhavam_amplifier"
#     (Lane B-4 in-process append hook — rows are appended to bo_laksana's OWN
#     signal_rows list before the single delete+insert, so they must be in
#     THIS allowlist too, or bo_laksana's own rebuild would delete them and
#     never reinsert-because-they-werent-reinserted... they ARE reinserted
#     every run since they're recomputed from signal_rows, but the allowlist
#     must still cover them so a *partial* future refactor can't strand them).
#
# If bo_laksana grows a new signal_type_class, add it here — the idempotency
# helper raises on an empty list rather than silently falling back to a
# blanket delete.
BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES: list[str] = [
    "yoga",
    "dosha",
    "sade_sati",
    "panchanga",
    "karaka_alignment",
    "tradition_specific",
    "parivartana",
    "configuration",
    "varga_pattern",
    "annual",
    "medical",
    "vastu",
    "composite_state",
    "varga_ratification_divergence",
    "bhavat_bhavam_amplifier",
]

# ── WP-2.4 (LCA-9b-1): flood-prone per-varga families ─────────────────────────
# These categories 1:1-emit thousands of near-identical granular signals (worst:
# aspect_jaimini_per_varga = 15,660/chart of chart-independent sign→sign rashi
# drishti). Groups larger than RATIFIED_FLOOD_CAP collapse to ONE aggregate
# rollup signal per (category × varga) that references every member fact_id.
_FLOOD_PRONE_FAMILIES = frozenset({
    "aspect_jaimini_per_varga",
    "aspect_parashari_per_varga",
    "net_argala_per_varga",
    "conjunction_per_varga",
    "lord_in_house_per_varga",
    "lord_aspects_lord_per_varga",
    "dispositor_chain_per_varga",
    "parivartana_per_varga",
    "virupa_drishti",
})
# Ratified cap: a (category × varga) group with more members than this is rolled
# up into one aggregate signal (constituents preserve full L1 traceability).
RATIFIED_FLOOD_CAP = 12

# ── L1 asset inference from source_calculation prefix ────────────────────────

def _infer_source_l1_asset(source_calculation: str) -> str:
    """Map source_calculation prefix → canonical ga_* asset_id."""
    sc = source_calculation or ""
    if sc.startswith("ga_structural"):
        return "ga_structural"
    if sc.startswith("ga_sade_sati_writer"):
        return "ga_sade_sati"
    if sc.startswith("ga_condition_writer"):
        return "ga_structural"
    if sc.startswith("ga_nakshatra"):
        return "ga_sensitive"
    if sc.startswith("panchanga_engine"):
        return "ga_panchanga"
    if sc.startswith("brahma_yoga_catalog"):
        return "ga_yoga"
    if sc.startswith("brahma_dosha_catalog"):
        return "ga_yoga"
    if sc.startswith("pyjhora_adapter.ashtakavarga"):
        return "ga_ashtakavarga"
    if sc.startswith("pyjhora_adapter.sensitive"):
        return "ga_sensitive"
    if sc.startswith("pyjhora_adapter.dosha_fires"):
        return "ga_yoga"
    if sc.startswith("pyjhora_adapter.yoga"):
        return "ga_yoga"
    if sc.startswith("pyjhora_adapter.argala") or sc.startswith("pyjhora_adapter.virodha_argala"):
        return "ga_structural"
    if sc.startswith("pyjhora_adapter"):
        return "ga_structural"
    if sc.startswith("classical_"):
        return "ga_structural"
    return "ga_structural"


_SUBSYSTEM_MAP: dict[str, str] = {
    "ga_structural":   "structural",
    "ga_sensitive":    "nakshatra",
    "ga_ashtakavarga": "strength_ashtakavarga",
    "ga_strength":     "strength_ashtakavarga",
    "ga_sade_sati":    "sade_sati",
    "ga_panchanga":    "panchanga",
    "ga_yoga":         "yoga",
    "ga_medical":      "medical",
    "ga_vastu":        "vastu",
    "ga_tajaka":       "tajaka",
    "ga_divisionals":  "varga",
}


def _infer_source_subsystem(source_l1_asset: str) -> str:
    return _SUBSYSTEM_MAP.get(source_l1_asset, "structural")


# ── fact_kind mapping from category patterns ──────────────────────────────────

_RELATIONSHIP_CATS = frozenset({
    "argala_natal_matrix", "virodha_argala_natal_matrix", "net_argala_per_varga",
    "aspect_jaimini_per_varga", "aspect_jaimini", "aspect_parashari_per_varga",
    "aspect_parashari_given", "aspect_parashari_received", "aspect_tajik",
    "aspect_matrix_summary", "aspect_received_by_special_point",
    "sambandha_grade", "bhava_significance_link", "karaka_bhava_concordance",
    "dispositor_tree", "dispositor_chain_per_varga", "graha_dispositor_chain",
    "composite_dispositor_strength", "virupa_drishti", "lord_in_house_per_varga",
    "lord_aspects_lord_per_varga", "conjunction_per_varga", "conjunction_within_orb",
    "conjunction_special_point", "parivartana_per_varga", "contradiction_pair",
    "nakshatra_lord_relationship", "significator_path", "karakatva_strength_per_significance",
})

_MAGNITUDE_CATS = frozenset({
    "graha_shadbala_total", "graha_shadbala_sthana", "graha_shadbala_dig",
    "graha_shadbala_kala", "graha_shadbala_drik", "graha_shadbala_cheshta",
    "graha_sthana_bala_per_varga", "graha_drik_bala_per_varga",
    "graha_kala_bala_per_varga", "graha_cheshta_bala_per_varga",
    "ashtakavarga_bindu", "ashtakavarga_bindu_per_varga",
    "ashtakavarga_pinda_sarva", "ashtakavarga_pinda_sarva_per_varga",
    "ashtakavarga_pinda_bhinna", "ashtakavarga_pinda_sodhita",
    "ashtakavarga_anubindu", "convergence_count", "graha_centrality",
    "graha_in_house_composite_strength", "graha_vimsopaka_shadvarga",
    "graha_vimsopaka_saptavarga", "graha_vimsopaka_dasavarga",
    "graha_vimsopaka_shodasavarga", "vimsopaka_bala_per_graha",
    "graha_saptavargaja_bala_component", "graha_vargottama_amplification_factor",
    "house_bhava_bala_subscore", "house_bhava_bala_total", "bhava_bala_total_extended",
    "bhava_bala_occupant", "bhava_bala_directional", "bhava_bala_temporal",
    "bhava_bala_lord", "bhava_bala_positional", "bhava_bala_aspectual",
    "house_strength_classification_rollup", "graha_kashta_phala", "graha_ishta_phala",
    "pranic_strength_per_graha", "graha_tri_deva_role_strength",
    "tara_bala", "tara_bala_natal_baseline", "chandra_bala_natal_baseline",
    "graha_tara_bala",
})

_BIRTH_MOMENT_CATS = frozenset({
    "panchanga_nakshatra_moon", "panchanga_tithi", "panchanga_vara",
    "panchanga_yoga", "panchanga_special_yoga_combinations",
    "panchanga_panchanka_classification", "panchanga_panchaka_classification",
    "bhadra_flag", "panchaka_flag",
})

_TIME_WINDOW_CATS = frozenset({
    "sade_sati_cycle", "sade_sati_phase", "sade_sati_phase_quarter",
    "sade_sati_modifier_overlay", "sade_sati_saturn_retrograde_subset",
    "sade_sati_cancellation_check", "sade_sati_concurrent_dasha_overlay",
    "sade_sati_downstream_cross_reference",
    "dhaiya_period", "ashtama_shani_period", "ardha_ashtama_shani_period",
    "janma_shani_period", "kantaka_shani_period", "vishakha_shani_period",
    "anumukha_shani_period", "eclipse_proximity_natal",
    "tajik_triraashipathi", "tajik_hadda_lord", "tajik_vargottama_specific",
})

_POSITION_CATS_PREFIX = (
    "graha_position", "nakshatra_", "karaka_chara_position", "karakamsa_position",
    "swamsa_position", "arudha_pada", "saham_position", "bhrigu_nadi_point",
    "upagraha_position", "special_lagna", "saturn_derived_point", "sun_derived_upagraha",
    "aprakasha_position", "midpoint", "esoteric_point_", "lal_kitab_special_point",
    "maharsi_specific_point", "sensitive_point_", "graha_pada_join",
    "graha_nakshatra_join", "cusp_kp_lords", "graha_kp_lords",
    "graha_functional_class_per_ascendant", "kp_cuspal_significators",
    "kp_ruling_planets_natal", "graha_avastha_lifetime_exposure_summary",
    "graha_sign_attributes", "graha_gandanta",
)


def _infer_fact_kind(fact_category: str) -> str:
    """Map fact_category to fact_kind enum value."""
    if fact_category in _RELATIONSHIP_CATS:
        return "relationship"
    if fact_category in _MAGNITUDE_CATS:
        return "magnitude"
    if fact_category in _BIRTH_MOMENT_CATS:
        return "birth_moment"
    if fact_category in _TIME_WINDOW_CATS:
        return "time_window"
    # Position patterns
    for prefix in _POSITION_CATS_PREFIX:
        if fact_category.startswith(prefix):
            return "position"
    # Configuration: yogas, doshas, avasthas, dignity, vargottama, cluster, composite
    cfg_keywords = (
        "yoga", "dosha", "kala_sarpa", "avastha", "dignity", "vargottama",
        "composite_state", "special_state", "chart_cluster", "chart_center",
        "nway_config", "combustion", "yuddha", "nakshatra_statistics",
        "nakshatra_cogravity", "cross_ayanamsha", "significator",
    )
    for kw in cfg_keywords:
        if kw in fact_category:
            return "configuration"
    return "configuration"


# ── Valence inference ─────────────────────────────────────────────────────────

_MALEFIC_CATEGORIES = frozenset({
    "dosha_fires", "dosha_label", "kala_sarpa_per_varga",
    "sade_sati_cycle", "sade_sati_phase", "sade_sati_phase_quarter",
    "dhaiya_period", "ashtama_shani_period", "ardha_ashtama_shani_period",
    "janma_shani_period", "kantaka_shani_period", "vishakha_shani_period",
    "anumukha_shani_period", "combustion_per_varga", "eclipse_proximity_natal",
    "contradiction_pair",
})

_BENEFIC_CATEGORIES = frozenset({
    "yoga_fires", "yoga_label", "graha_yoga_karaka_flag",
})

_MALEFIC_VALUE_SUBSTRINGS = (
    "debilitated", "neecha", "enemy", "combust", "malefic", "afflict",
    "retrograde", "cancel", "dosha", "kala_sarpa",
)
_BENEFIC_VALUE_SUBSTRINGS = (
    "exalted", "uccha", "own", "mooltrikona", "friend", "benefic",
    "yoga_karaka", "vargottama", "strong",
)


def _infer_valence(fact_category: str, fact_value_text: str | None) -> str:
    if fact_category in _MALEFIC_CATEGORIES:
        return "malefic"
    if fact_category in _BENEFIC_CATEGORIES:
        return "benefic"
    txt = (fact_value_text or "").lower()
    if txt:
        for sub in _BENEFIC_VALUE_SUBSTRINGS:
            if sub in txt:
                return "benefic"
        for sub in _MALEFIC_VALUE_SUBSTRINGS:
            if sub in txt:
                return "malefic"
    return "neutral"


# ── Night-1 Lane 4 (CR-83/CR-54-as-amended): judged valence ───────────────────
#
# _infer_valence above is NOT deleted — it is demoted to the annotated fallback
# (CR-42 class: no silent degradation). When a chart_vichara `valence_pass` row
# exists for this signal's (actor, target, varga), its judged valence wins and
# valence_source='ga_vichara_v1'; otherwise the keyword heuristic fires and
# valence_source='keyword_heuristic_v1' — always visible, never silent.

_VICHARA_TO_MSR_VALENCE: dict[str, str] = {
    "strong_benefic": "benefic", "benefic": "benefic",
    "strong_malefic": "malefic", "malefic": "malefic",
    "mixed": "mixed",   # DR-9: mixed is first-class on the served signal, not collapsed to neutral
    "neutral": "neutral",
}


def _resolve_valence(
    vichara_lookup: dict[tuple[str, str, str], dict],
    fact_cat: str,
    fact_value_text: str | None,
    tags: dict,
) -> tuple[str, str, float | None]:
    """Returns (valence, valence_source, judged_value_num_or_None).

    ga_vichara now ships (Lane 2, 2026-07-14) — vichara_lookup is populated
    from chart_vichara's valence_pass rows keyed on (actor, target, varga)
    where `actor` is the CANONICAL graha subject code (PLANET_TO_SUBJECT
    convention: 'MAR', 'SUN', …) and `target` is the composite string
    f'{varga}_HOUSE_{house}' (e.g. 'D1_HOUSE_2') — see
    ga_vichara_writer.py::build_valence_pass_rows. Both dimensions are
    normalized here to match that exact shape:
      - actor: tags['lord'] (bhava_significance_link's own jsonb key) carries
        the long form ('Mars') while tags['graha'] (when present) is already
        canonical — _canonical_graha_code() normalizes either.
      - target: built from tags['target_house'] (or the house-tag fallbacks)
        composed with varga into ga_vichara's exact key format; a bare house
        number alone never matches ga_vichara's rows.
    When vichara_lookup is empty (table/rows absent) or the specific
    (actor, target, varga) triple has no row, this legitimately falls back to
    the keyword heuristic — always visibly tagged (CR-42 class: no silent
    degradation).
    """
    raw_actor = tags.get("graha") or tags.get("primary_graha") or tags.get("lord") or tags.get("body")
    actor = _canonical_graha_code(raw_actor)
    raw_house = (tags.get("target_house") or tags.get("target") or tags.get("aspected_house")
                 or tags.get("house") or tags.get("house_number"))
    varga = str(tags.get("varga") or tags.get("varga_id") or "D1").upper()
    if actor is not None and raw_house is not None and vichara_lookup:
        try:
            house_num = int(str(raw_house).strip())
        except (TypeError, ValueError):
            house_num = None
        if house_num is not None and 1 <= house_num <= 12:
            target_key = f"{varga}_HOUSE_{house_num}"
            rec = vichara_lookup.get((actor, target_key, varga))
            if rec is not None:
                value_text = str(rec.get("value_text") or "").lower()
                mapped = _VICHARA_TO_MSR_VALENCE.get(value_text, "neutral")
                value_num = rec.get("value_num")
                return mapped, "ga_vichara_v1", (float(value_num) if value_num is not None else None)
    return _infer_valence(fact_cat, fact_value_text), "keyword_heuristic_v1", None


# ── Varga extraction ──────────────────────────────────────────────────────────

_VARGA_PATTERN = re.compile(r"\b(D\d+)\b", re.IGNORECASE)


def _extract_varga_id(fact_key: str, fact_value_jsonb: dict | None) -> str | None:
    """Extract varga (D1, D9, D10…) from fact_key or jsonb."""
    if fact_value_jsonb:
        varga = fact_value_jsonb.get("varga") or fact_value_jsonb.get("varga_id")
        if varga:
            return str(varga).upper()
    m = _VARGA_PATTERN.search(fact_key or "")
    if m:
        return m.group(1).upper()
    return None


# ── Signal type class mapping ─────────────────────────────────────────────────

def _signal_type_class(fact_category: str) -> str:
    if "yoga" in fact_category:
        return "yoga"
    if "dosha" in fact_category:
        return "dosha"
    if "sade_sati" in fact_category or "shani" in fact_category or "dhaiya" in fact_category:
        return "sade_sati"
    if "panchanga" in fact_category or "bhadra" in fact_category or "panchaka" in fact_category:
        return "panchanga"
    if "karaka" in fact_category or "karakamsa" in fact_category or "arudha" in fact_category:
        return "karaka_alignment"
    if "kp_" in fact_category:
        return "tradition_specific"
    if "parivartana" in fact_category:
        return "parivartana"
    if "kala_sarpa" in fact_category:
        return "configuration"
    if "vargottama" in fact_category:
        return "varga_pattern"
    if "tajik" in fact_category:
        return "annual"
    if "medical" in fact_category:
        return "medical"
    if "vastu" in fact_category:
        return "vastu"
    return "composite_state"


# ── Tradition inference ───────────────────────────────────────────────────────

def _infer_tradition(fact_category: str, source_calculation: str) -> str:
    if "jaimini" in fact_category or "karaka" in fact_category or "arudha" in fact_category:
        return "jaimini"
    if "kp_" in fact_category or "kp_" in source_calculation:
        return "kp"
    if "tajik" in fact_category:
        return "tajika"
    if "lal_kitab" in fact_category:
        return "lal_kitab"
    if "esoteric" in fact_category or "mahars" in fact_category:
        return "esoteric"
    return "parashari"


# ── Domain assignment ─────────────────────────────────────────────────────────

# SHABDA-SHUDDHI R7: expanded to 13-domain vocabulary. Categories that carry
# progeny/education/family/residence/travel significations are annotated with
# classical citations per B.3 derivation-ledger discipline.
_DOMAIN_MAP: dict[str, list[str]] = {
    # Yogas can signify across all major domains — BPHS ch.34-39
    "yoga_label":                           ["career", "wealth", "health", "relationship", "spirituality", "progeny", "education"],
    "yoga_fires":                           ["career", "wealth", "health", "relationship", "spirituality", "progeny", "education"],
    # Doshas affect health + relationship + transition — BPHS ch.47 (Manglik), PD ch.7
    "dosha_label":                          ["health", "relationship", "career", "transition"],
    "dosha_fires":                          ["health", "relationship", "transition"],
    "kala_sarpa_per_varga":                 ["character", "career", "wealth", "transition"],
    "graha_composite_state_classification": ["character", "career", "wealth"],
    "graha_special_state_rollup":           ["character", "career"],
    "graha_yoga_karaka_flag":               ["career", "wealth"],
    "parivartana_per_varga":                ["career", "wealth", "relationship"],
    "vargottama_per_varga":                 ["character", "career"],
    "conjunction_within_orb":              ["career", "relationship", "spirituality"],
    "conjunction_per_varga":               ["career", "relationship"],
    "graha_dispositor_chain":              ["character", "career"],
    "dispositor_chain_per_varga":          ["character", "career"],
    "composite_dispositor_strength":       ["character", "career"],
    "graha_avastha_lajjitadi":             ["character", "relationship"],
    "graha_effective_dignity_modified_by_aspects": ["career", "wealth"],
    "aspect_parashari_given":              ["career", "relationship", "wealth"],
    "aspect_parashari_per_varga":          ["career", "relationship", "wealth"],
    "aspect_jaimini_per_varga":            ["career", "relationship", "spirituality"],
    "kp_cuspal_significators":             ["career", "relationship", "wealth", "spirituality"],
    # Chara karakas: putrakaraka→progeny, matrikaraka→family — BPHS ch.32
    "karaka_chara_position":               ["career", "relationship", "character", "progeny", "family"],
    "karakamsa_position":                  ["career", "spirituality", "education"],
    "swamsa_position":                     ["spirituality", "career"],
    # Arudha padas: A4→residence, A5→progeny, A9→travel — BPHS ch.30
    "arudha_pada":                         ["career", "wealth", "relationship", "residence", "progeny", "travel"],
    "graha_tri_deva_role_strength":        ["spirituality", "character"],
    "jaimini_tri_deva_role_per_graha":     ["spirituality", "character"],
    # Sade Sati: career + health + relationships + transition — BJ ch.4
    "sade_sati_cycle":                     ["career", "health", "relationship", "transition"],
    "sade_sati_phase":                     ["career", "health", "relationship", "transition"],
    "sade_sati_phase_quarter":             ["career", "health", "relationship", "transition"],
    "panchanga_yoga":                      ["character", "spirituality"],
    "panchanga_tithi":                     ["character", "spirituality"],
    "panchanga_vara":                      ["character"],
    "panchanga_nakshatra_moon":            ["character", "relationship"],
    "panchanga_special_yoga_combinations": ["spirituality", "character"],
    "argala_natal_matrix":                 ["career", "character", "relationship"],
    "net_argala_per_varga":                ["career", "character"],
    "graha_shadbala_total":                ["career", "wealth"],
    "ashtakavarga_bindu":                  ["career", "wealth"],
    "ashtakavarga_pinda_sarva":            ["career", "wealth"],
    "graha_dignity_per_varga":             ["character", "career"],
    "nakshatra_dispositor":                ["character", "relationship"],
    "nakshatra_dispositor_chain":          ["character", "relationship"],
    # Lord-in-house: domains depend on both house and varga — BPHS ch.24
    "lord_in_house_per_varga":             ["career", "wealth", "relationship", "progeny", "education", "family"],
    # Bhava significance links: the bhava's own karyatva — BPHS ch.11
    "bhava_significance_link":             ["career", "relationship", "wealth", "progeny", "education", "family", "residence", "travel"],
    "combustion_per_varga":                ["health", "career"],
    "sambandha_grade":                     ["career", "relationship"],
    "convergence_count":                   ["career", "character"],
}

# SHABDA-SHUDDHI R7: defaults expanded to 13-domain vocabulary.
_CATEGORY_DEFAULT_DOMAINS: dict[str, list[str]] = {
    "structural":            ["character", "career", "family"],
    "nakshatra":             ["character", "relationship", "spirituality"],
    "strength_ashtakavarga": ["career", "wealth"],
    "sade_sati":             ["career", "health", "relationship", "transition"],
    "panchanga":             ["character", "spirituality"],
    "yoga":                  ["career", "wealth", "spirituality", "progeny", "relationship"],
    "medical":               ["health"],
    "vastu":                 ["health", "residence"],
    "tajaka":                ["career", "wealth"],
    "varga":                 ["career", "character"],
}


# ── WP-2.4 (LCA-9b-3): KP house-aware domain inheritance ──────────────────────
#
# KP cusp facts (cusp_kp_lords, kp_cuspal_significators, kp_ruling_planets_natal)
# were mapped to a fixed character|relationship set, so a 2nd/11th-cusp wealth
# significator could never surface in a wealth query (63% of cusp facts
# un-consumed in the wealth channel). Fix: parse the cusp/house number and
# inherit that bhava's canonical domains — the significator's karyatva follows
# the house it rules.
#
# Bhava → domain map keyed to the full canonical 13-domain vocabulary
# (SHABDA-SHUDDHI R7). Each row carries a classical citation per B.3.
#
# Citations: BPHS = Brihat Parasara Hora Shastra; BJ = Brihat Jataka (Varahamihira);
# PD = Phaladeepika (Mantreswara); JP = Jataka Parijata.
_BHAVA_DOMAINS: dict[int, list[str]] = {
    # 1st (Tanu): self, body, temperament — BPHS ch.11 v.1-2
    1:  ["character", "health"],
    # 2nd (Dhana): wealth, family, speech, food — BPHS ch.11 v.3-4; PD ch.2 v.5
    2:  ["wealth", "family", "character"],
    # 3rd (Sahaja): siblings, courage, short travel — BPHS ch.11 v.5-6
    3:  ["career", "character"],
    # 4th (Sukha): mother, property/residence, education, happiness — BPHS ch.11 v.7-8; PD ch.2 v.8
    4:  ["residence", "education", "family", "character"],
    # 5th (Putra): progeny, intelligence, past merit, romance — BPHS ch.11 v.9-10; BJ ch.17
    5:  ["progeny", "education", "character", "spirituality"],
    # 6th (Ari): enemies, disease, service, debts — BPHS ch.11 v.11-12
    6:  ["health", "career"],
    # 7th (Kalatra): spouse, partnerships, marriage — BPHS ch.11 v.13-14
    7:  ["relationship"],
    # 8th (Randhra): longevity, transformation, occult — BPHS ch.11 v.15-16
    8:  ["health", "spirituality", "transition"],
    # 9th (Dharma): father, fortune, long journeys, higher learning — BPHS ch.11 v.17-18; PD ch.2 v.13
    9:  ["spirituality", "career", "travel", "education"],
    # 10th (Karma): career, profession, status — BPHS ch.11 v.19-20
    10: ["career"],
    # 11th (Labha): gains, income, elder siblings — BPHS ch.11 v.21-22
    11: ["wealth", "career"],
    # 12th (Vyaya): losses, foreign travel/settlement, liberation — BPHS ch.11 v.23-24; JP ch.7
    12: ["spirituality", "travel", "health"],
}

_KP_HOUSE_CATS = frozenset({
    "cusp_kp_lords", "kp_cuspal_significators", "kp_ruling_planets_natal",
})

# Matches CUSP_01 / HOUSE_2 / BHAVA-11 etc. in fact_subject.
_CUSP_NUM_RE = re.compile(r"(?:CUSP|HOUSE|BHAVA)[_\-]?0*(\d{1,2})", re.IGNORECASE)


def _parse_house_number(fact_subject: str | None, fvj: dict | None) -> int | None:
    """Extract the 1..12 bhava/cusp number from jsonb keys or fact_subject."""
    if fvj:
        for k in ("house", "house_number", "bhava", "cusp", "cusp_number"):
            v = fvj.get(k)
            if v is not None:
                try:
                    n = int(v)
                except (TypeError, ValueError):
                    continue
                if 1 <= n <= 12:
                    return n
    m = _CUSP_NUM_RE.search(fact_subject or "")
    if m:
        n = int(m.group(1))
        if 1 <= n <= 12:
            return n
    return None


def _assign_kp_domains(fact_subject: str | None, fvj: dict | None) -> list[str] | None:
    """Domains inherited from the KP cusp's bhava, or None if house not parseable."""
    house = _parse_house_number(fact_subject, fvj)
    if house is not None:
        return list(_BHAVA_DOMAINS.get(house, ["general"]))
    return None


# ── D-2 Lane V-4 (CR-62): multi-varga map for the wealth/career lenses ───────
# CR-62: wealth uses {D1,D2,D9,D11}; career uses {D1,D9,D10}. Before this, a
# varga-scoped signal's 'wealth'/'career' domain tag came only from its
# fact_category (_DOMAIN_MAP / _CATEGORY_DEFAULT_DOMAINS above), regardless of
# WHICH varga the signal lived in — a D10 (career-only varga) lord-placement
# signal could still surface in a wealth query, and a D2/D11 (wealth-only
# varga) signal could surface in a career query. This gate is applied AFTER
# the base domain assignment: 'wealth' is dropped unless varga_id is one of
# CR-62's wealth vargas (or the signal is varga-agnostic, i.e. varga_id is
# None); 'career' is dropped unless varga_id is one of CR-62's career vargas
# (or varga-agnostic). Every OTHER domain (health/relationship/spirituality/
# character) is untouched — CR-62 only names the wealth/career lenses.
# SHABDA-SHUDDHI R7: varga-domain affinity gates extended per classical vargas.
# D7 (Saptamsha) → progeny (BPHS ch.6 v.11: "D7 for progeny assessment").
# D4 (Chaturthamsha) → residence (BPHS ch.6 v.7: "D4 for fortune and property").
# D24 (Chaturvimshamsha) → education (BPHS ch.6 v.25: "D24 for learning/vidya").
CR62_WEALTH_VARGAS = frozenset({"D1", "D2", "D9", "D11"})
CR62_CAREER_VARGAS = frozenset({"D1", "D9", "D10"})
CR62_PROGENY_VARGAS = frozenset({"D1", "D7", "D9"})
CR62_RESIDENCE_VARGAS = frozenset({"D1", "D4"})
CR62_EDUCATION_VARGAS = frozenset({"D1", "D24", "D9"})
CR62_TRAVEL_VARGAS = frozenset({"D1", "D9", "D12"})


def _apply_cr62_multi_varga_gate(domains: list[str], varga_id: str | None) -> list[str]:
    if not varga_id:
        return domains  # varga-agnostic signal — CR-62 does not apply
    varga = varga_id.upper()
    # SHABDA-SHUDDHI R7: extended to new domain-varga affinities.
    _VARGA_GATES: dict[str, frozenset[str]] = {
        "wealth": CR62_WEALTH_VARGAS,
        "career": CR62_CAREER_VARGAS,
        "progeny": CR62_PROGENY_VARGAS,
        "residence": CR62_RESIDENCE_VARGAS,
        "education": CR62_EDUCATION_VARGAS,
        "travel": CR62_TRAVEL_VARGAS,
    }
    out = []
    for d in domains:
        gate = _VARGA_GATES.get(d)
        if gate is not None and varga not in gate:
            continue
        out.append(d)
    # Never return an empty list from a gate — B.10 (no silent drop): if the
    # gate would empty a signal's domains entirely (e.g. a D2-only signal that
    # was ONLY ever tagged 'career'), fall back to the ungated domains rather
    # than making the signal domain-less.
    return out if out else domains


def _assign_domains(fact_category: str, source_subsystem: str,
                    fact_subject: str | None = None,
                    fvj: dict | None = None,
                    varga_id: str | None = None) -> list[str]:
    # WP-2.4 (9b-3): KP cusp facts inherit their bhava's domains house-by-house.
    if fact_category in _KP_HOUSE_CATS:
        kp = _assign_kp_domains(fact_subject, fvj)
        if kp:
            return _apply_cr62_multi_varga_gate(kp, varga_id)
    if fact_category in _DOMAIN_MAP:
        return _apply_cr62_multi_varga_gate(_DOMAIN_MAP[fact_category], varga_id)
    base = _CATEGORY_DEFAULT_DOMAINS.get(source_subsystem, ["general"])
    return _apply_cr62_multi_varga_gate(base, varga_id)


# ── Signal text builders ──────────────────────────────────────────────────────

def _build_summary_text(fact_category: str, fact_key: str,
                        fact_value_text: str | None, fact_value_num: float | None,
                        config: dict) -> str:
    """Lossless deterministic NL summary — iterates ALL config keys."""
    parts = [f"category={fact_category}", f"key={fact_key}"]
    if fact_value_text:
        parts.append(f"value_text={fact_value_text}")
    if fact_value_num is not None:
        parts.append(f"value_num={fact_value_num:.4g}")
    for k, v in sorted(config.items()):
        if k in ("fact_key", "fact_value_text", "fact_value_num"):
            continue
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return " | ".join(parts)


def _build_headline_text(fact_category: str, fact_key: str,
                         fact_value_text: str | None, fact_value_num: float | None,
                         source_l1_asset: str,
                         fact_subject: str | None = None,
                         house: int | None = None,
                         varga_id: str | None = None) -> str:
    """Short deterministic headline for display/retrieval.

    CR-45 (Night-1 Lane 4, Change 3): leads with SUBJECT (house, varga) when a
    subject is resolvable — "Headline must name subject + house + varga.
    Salience without subject is unusable evidence." Parts genuinely absent are
    omitted. Falls back to the pre-existing anonymous form only when
    fact_subject is None/empty — no regression for facts that HAVE a subject.
    """
    val = fact_value_text or (f"{fact_value_num:.3g}" if fact_value_num is not None else "")
    cat_display = fact_category.replace("_", " ")
    key_display = fact_key.replace("_", " ")
    body = f"{cat_display}: {key_display} = {val}" if val else f"{cat_display}: {key_display}"
    if fact_subject:
        loc_parts: list[str] = []
        if house is not None:
            loc_parts.append(f"H{house}")
        if varga_id:
            loc_parts.append(str(varga_id))
        loc = f" ({', '.join(loc_parts)})" if loc_parts else ""
        return f"{str(fact_subject).upper()}{loc}: {body} [{source_l1_asset}]"
    return f"{body} [{source_l1_asset}]"


# ── Duration class ────────────────────────────────────────────────────────────

def _duration_class(fact_category: str) -> str:
    if fact_category in _TIME_WINDOW_CATS:
        return "transit_period"
    if fact_category in _BIRTH_MOMENT_CATS:
        return "birth_moment"
    return "natal_permanent"


# ── Signature tier from salience ──────────────────────────────────────────────

# Tier lattice (ascending). A ceiling clamps a signal to at most that tier.
_TIER_ORDER = ("background", "supporting", "major", "chart_defining")


def _signature_tier(computed_salience: float, ceiling: str | None = None) -> str:
    # V2 thresholds — conservative placeholders recut against live v2 distribution post-rebuild.
    # V2 values differ from V1 due to class_prior × verification_rescale scaling.
    if computed_salience >= 2.0:
        tier = "chart_defining"
    elif computed_salience >= 0.8:
        tier = "major"
    elif computed_salience >= 0.3:
        tier = "supporting"
    else:
        tier = "background"
    # WP-2.4 (9b-2): divisional/granular signals are barred from the top tiers.
    if ceiling is not None and ceiling in _TIER_ORDER:
        if _TIER_ORDER.index(tier) > _TIER_ORDER.index(ceiling):
            tier = ceiling
    return tier


def _tier_ceiling_for(fact_category: str, varga_id: str | None) -> str | None:
    """CR-82→CR-65 (Night-1 Lane 4, Change 2): the flat "any non-D1/`_per_varga`
    fact capped at supporting" rule is RETIRED — it structurally forbade the
    varga layer from ever ranking chart_defining/major, which is the exact
    CR-65 defect (95.7% of the corpus stuck at 'supporting'). Replaced by
    ratification-aware weighting (_resolve_ratification_factor) + percentile
    tier assignment (_assign_tiers_by_percentile).

    ONLY the flood-rollup aggregate ceiling survives: _FLOOD_PRONE_FAMILIES
    members are genuinely one facet of a divisional matrix collapsed into a
    single aggregate row (WP-2.4 9b-1) — un-capping THOSE would recreate
    CR-65 in mirror image (15,660 rashi-drishti-class rollups flooding the
    top tiers). This is the one ceiling the brief's §10 traps says to keep.
    """
    if fact_category in _FLOOD_PRONE_FAMILIES:
        return "supporting"
    return None


# ── Night-1 Lane 4 (Change 2, CR-82→CR-65): percentile-based tier assignment ──

# design §11: "chart_defining ≈ top 1–2%" — module constant per brief §3.3
# (1–2% midpoint = 1.5%; "major" = the next 8.5%, i.e. top 10% cumulative).
_TIER_CHART_DEFINING_PCTL = 0.985
_TIER_MAJOR_PCTL = 0.90


def _assign_tiers_by_percentile(rows: list[dict]) -> None:
    """Assign signature_tier from the percentile rank of (ratification-adjusted)
    computed_salience within this (chart × ayanamsha) substep's full signal set —
    replaces the old per-row _signature_tier(computed_salience, ceiling) call.

    chart_defining = top 1.5%, major = next 8.5% (top 10% cumulative);
    below that, the pre-existing 0.3 threshold still splits supporting from
    background (unchanged behavior for the bulk of the corpus — only the top
    decile's ceiling logic changes). The flood-rollup ceiling from
    _tier_ceiling_for (stashed per-row as "_tier_ceiling" by the caller) is
    applied AFTER percentile assignment — an aggregate rollup cannot escape
    into major/chart_defining regardless of its raw percentile rank.

    §10 trap: percentiles are per-chart, per-build (here: per ayanamsha
    substep, which is the existing per-chart-per-build granularity used by
    _set_salience_pctl_in_class) — never global across charts.
    """
    if not rows:
        return
    n = len(rows)
    ordered = sorted(rows, key=lambda r: r["computed_salience"])
    rank_by_salience: dict[float, int] = {}
    for i, row in enumerate(ordered):
        sal = row["computed_salience"]
        if sal not in rank_by_salience:
            rank_by_salience[sal] = i + 1  # first occurrence — RANK() semantics (ties share min rank)
    for row in rows:
        rank = rank_by_salience[row["computed_salience"]]
        pctl = (rank - 1) / (n - 1) if n > 1 else 1.0
        if pctl >= _TIER_CHART_DEFINING_PCTL:
            tier = "chart_defining"
        elif pctl >= _TIER_MAJOR_PCTL:
            tier = "major"
        elif row["computed_salience"] >= 0.3:
            tier = "supporting"
        else:
            tier = "background"
        ceiling = row.pop("_tier_ceiling", None)
        if ceiling is not None and ceiling in _TIER_ORDER:
            if _TIER_ORDER.index(tier) > _TIER_ORDER.index(ceiling):
                tier = ceiling
        row["signature_tier"] = tier


# ── Signature class derivation ────────────────────────────────────────────────

def _signature_class(signal_type_class: str) -> str:
    """Derive signature_class from signal_type_class.

    signature_class is a free-text grouping field (no DB constraint).
    Derivation is categorical, deterministic, and never generative.
    """
    stc = (signal_type_class or "").lower()
    if any(kw in stc for kw in ("dignity", "shadbala", "strength", "varga_pattern")):
        return "planetary"
    if any(kw in stc for kw in ("house", "bhava")):
        return "house"
    if any(kw in stc for kw in ("dasha", "temporal", "sade_sati", "annual")):
        return "temporal"
    return "general"


# ── Lookup builders ───────────────────────────────────────────────────────────

def _fetch_dict(conn: Any, sql: str, params: list) -> list[dict]:
    # conn uses dict_row factory; fetchall() already returns dicts — convert to plain dict.
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def _build_strength_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, float]:
    """graha → L1-authoritative achieved/required shadbala ratio, clamped to 2.0.

    ŚUDDHA-VĀCA P0-5 (D1_MISSELECT) fix: the SELECT previously filtered ONLY
    on fact_category='graha_shadbala_total' — no fact_key pin, no ORDER BY.
    Under that category, chart_facts carries TWO fact_key variants scoped to
    the SAME (chart_id, ayanamsha_id, fact_subject) for every classical
    graha — 'rupa' (raw achieved shadbala, scale ~4.6-8.5) and 'ratio'
    (L1-computed achieved/required, scale ~0.8-1.7) — plus a third
    'required_rupa' row stored under ayanamsha_id='INVARIANT' (out of this
    filter's scope). With no fact_key pin and no ORDER BY, the dict-building
    loop below silently kept whichever row the DB happened to return LAST
    per graha — non-deterministic across otherwise-identical builds.

    ŚUDDHA-VĀCA P0-6 (D3_HARDCODED_DRIFT) fix: whichever row won, its value
    was normalized by a flat `raw / 1.0` constant instead of that graha's
    own L1 `required_rupa` fact — a wrapper-local constant standing in for
    an L1-derived per-graha value (forbidden by construction per CLAUDE.md
    §N.5, even though `raw` itself was already correct).

    Fix: pin fact_key='ratio'. `ga_strength_writer` (L1) already computes
    this exact ratio as `achieved_total / required_rupa` per graha
    (`ga_writers/ga_strength_writer.py::_build_shadbala_rows`, CR-18) and
    stores it under this same fact_category, ayanamsha-scoped — reading it
    directly means this function REFERENCES the L1-computed value rather
    than re-deriving it independently, per §N.5. This mirrors the sibling
    `_fetch_shadbala` in `bo_upaya.py`, which already reads this identical
    fact_key='ratio' row for the same purpose. The ORDER BY makes the
    result deterministic even if a duplicate/re-derived row set were ever
    to exist (today's data has exactly one 'ratio' row per graha).

    Rahu/Ketu carry no classical shadbala requirement (ga_strength_writer's
    `classical_grahas` list excludes them) and therefore emit no 'ratio'
    row — they are simply absent from this lookup. Callers already default
    a missing graha to a neutral 1.0 (see `shadbala_norm` call sites),
    mirroring bo_upaya.py's documented fallback for the nodes.
    """
    rows = _fetch_dict(conn,
        """SELECT fact_subject, fact_value_num, fact_id FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='graha_shadbala_total'
             AND fact_key='ratio'
           ORDER BY fact_subject ASC, fact_id ASC""",
        [chart_id, ayanamsha_id])
    lookup: dict[str, float] = {}
    for r in rows:
        # fact_subject e.g. 'SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT'
        # — use as-is (callers match via tags/dignity keys)
        graha = str(r.get("fact_subject") or "").strip()
        if not graha:
            continue
        if graha in lookup:
            continue  # deterministic first-seen-per-graha under the stable ORDER BY
        ratio = float(r.get("fact_value_num") or 0.0)
        # ratio is already actual_rupa / required_rupa, both L1 facts (§N.5);
        # clamp at 2.0 (2× classical minimum) to bound the salience multiplier.
        lookup[graha] = min(ratio, 2.0)
    return lookup


def _build_dignity_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, str]:
    """graha → dignity state string (D1 only).

    B2-fix: the old filter used fact_key LIKE '%:D1' / '%_D1' which returns
    ZERO rows.  Actual schema: fact_key = 'dignity_state', varga stored in
    fact_value_jsonb->>'varga', graha in fact_subject as 'D1_SUN', 'D1_MOON',
    'D1_MAR' etc.  Filter on jsonb varga = 'D1' and strip the 'D1_' prefix.
    """
    rows = _fetch_dict(conn,
        """SELECT fact_subject, fact_value_text FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='graha_dignity_per_varga'
             AND fact_value_jsonb->>'varga' = 'D1'""",
        [chart_id, ayanamsha_id])
    lookup: dict[str, str] = {}
    for r in rows:
        subject = str(r.get("fact_subject") or "")
        # fact_subject pattern: 'D1_SUN', 'D1_MOON', 'D1_MAR', 'D1_RAH_MEAN' …
        graha = subject.removeprefix("D1_")
        if not graha or graha == subject:
            # fallback: skip rows that don't have D1_ prefix
            continue
        state = str(r.get("fact_value_text") or "neutral").lower()
        if graha not in lookup:  # first row wins (avoid overwriting with duplicates)
            lookup[graha] = state
    return lookup


def _build_av_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[int, int]:
    """house → sarva ashtakavarga bindus (D1).

    B2-fix: the old query used ashtakavarga_pinda_sarva with fact_key='total'
    (graha totals — no house dimension) and tried to parse a house from 'total',
    which always failed → house defaulted to 1 → every signal got the same AV
    multiplier.

    Correct source: ashtakavarga_bindu, fact_subject = 'SARVA-HOUSE_N',
    fact_key = 'bindus', fact_value_num = sarva bindus for house N.
    """
    rows = _fetch_dict(conn,
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='ashtakavarga_bindu'
             AND fact_subject LIKE 'SARVA-HOUSE_%%'""",
        [chart_id, ayanamsha_id])
    lookup: dict[int, int] = {}
    for r in rows:
        subject = str(r.get("fact_subject") or "")
        # pattern: 'SARVA-HOUSE_1' … 'SARVA-HOUSE_12'
        try:
            house = int(subject.split("_")[-1])
        except (ValueError, IndexError):
            continue
        lookup[house] = int(r.get("fact_value_num") or 28)
    return lookup


# ── Night-1 Lane 4 (Change 1, CR-81): class_prior activation ──────────────────
#
# Mirrors the established join pattern already shipped in
# mi_kula._load_registry_priors (BA-P6 C6): brahma_class_priors's sentinel
# convention is prior_version='1.0', signal_tradition='*', fact_kind='*' for
# the (signal_type_class, source_subsystem) axis pair used here. Cascading
# '*' fallback resolves partial matches before defaulting to 1.0.

def _load_class_priors(conn: Any) -> dict[tuple[str, str], float]:
    """Load brahma_class_priors once per sub-step. Returns {} on any error
    (missing table, etc.) — priors are optional-by-design (brief §2); every
    caller must still default to 1.0 on a miss, never raise."""
    try:
        rows = _fetch_dict(
            conn,
            """SELECT signal_type_class, source_subsystem, class_prior
               FROM brahma_class_priors
               WHERE prior_version = '1.0' AND signal_tradition = '*' AND fact_kind = '*'""",
            [],
        )
    except Exception as exc:
        logger.warning("[bo_laksana] brahma_class_priors load failed (%s); class_prior=1.0 for all signals", exc)
        return {}
    return {
        (str(r["signal_type_class"]), str(r["source_subsystem"])): float(r["class_prior"])
        for r in rows
    }


def _resolve_class_prior(
    priors: dict[tuple[str, str], float], signal_type_class: str, source_subsystem: str,
) -> tuple[float, bool]:
    """Cascading (stc, sub) → (stc, '*') → ('*', sub) resolution. Returns (prior, hit)
    where hit=False means no row matched at all (silent-miss default, counted for the
    CR-81 hit-rate report — brief §2: "<50% hit-rate → stop and debug, don't ship
    inert")."""
    for key in ((signal_type_class, source_subsystem), (signal_type_class, "*"), ("*", source_subsystem)):
        if key in priors:
            return priors[key], True
    return 1.0, False


# ── Night-1 Lane 4 (Change 2, CR-82→CR-65): varga_ratification loader ─────────
#
# STATUS (reconciled 2026-07-15, D-1.5a A2/CR-91): LANE2 (ga_vichara /
# chart_vichara) SHIPPED 2026-07-14 and is live — this is no longer a
# blocked/pending dependency. The comment below previously read "Lane 2 never
# landed"; that was true only through the 2026-07-14 handback and is stale.
# The try/except degradation is KEPT (not removed) as a genuine defensive
# posture for a chart whose ga_vichara build is missing/partial/mid-rebuild —
# it degrades to ({}, False) whenever chart_vichara is unavailable FOR THIS
# CHART, so every signal's ratification_factor stays NULL/neutral and every
# fallback is honestly tagged (CR-42 class: no silent guess), exactly as
# before — only the framing ("permanently blocked" vs "per-chart degraded
# path") has changed.

def _load_varga_ratification(conn: Any, chart_id: str, ayanamsha_id: str) -> tuple[dict[tuple[str, str], float], bool]:
    """(subject, domain) -> ratification_factor, from chart_vichara's
    vichara_family='varga_ratification' rows for this chart AND ayanamsha. Returns
    (lookup, table_available).

    D-1.5a wave gate finding (2026-07-15): this query was missing the ayanamsha_id
    filter (sibling defect of _load_vichara_valence's, see its docstring). Unlike
    that function, THIS one has CONFIRMED LIVE cross-ayanamsha contamination on
    482012f1: (JUP, wealth) ratification_factor is 1 in some ayanamshas and 1.4 in
    others; (SAT, career/health/wealth) is 0.8 vs 1. Without this filter, whichever
    ayanamsha Postgres returns last for a given (subject, domain) key silently wins
    the lookup dict regardless of which ayanamsha the current build_substep is
    actually for — directly corrupting the ratification_factor term of served
    wealth/career/health judgments."""
    sp = "sp_bo_laksana_vichara_ratif"
    try:
        with conn.cursor() as _c:
            _c.execute(f"SAVEPOINT {sp}")
        rows = _fetch_dict(
            conn,
            """SELECT subject, domain, ratification_factor FROM chart_vichara
               WHERE chart_id = %s AND ayanamsha_id = %s AND vichara_family = 'varga_ratification'""",
            [chart_id, ayanamsha_id],
        )
        with conn.cursor() as _c:
            _c.execute(f"RELEASE SAVEPOINT {sp}")
    except Exception as exc:
        try:
            with conn.cursor() as _c:
                _c.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        logger.warning(
            "[bo_laksana] chart_vichara varga_ratification unavailable (%s) — ga_vichara "
            "build is missing/partial for this chart; ratification_factor stays "
            "NULL/neutral for every signal this build (documented degraded path, "
            "not a silent guess — CR-82→CR-65 handoff).", exc,
        )
        return {}, False
    lookup: dict[tuple[str, str], float] = {}
    for r in rows:
        subj = str(r.get("subject") or "")
        dom = str(r.get("domain") or "")
        if subj and dom:
            lookup[(subj, dom)] = float(r.get("ratification_factor") or 1.0)
    return lookup, True


def _resolve_ratification_factor(
    ratification_lookup: dict[tuple[str, str], float],
    primary_graha: str | None,
    domains: list[str],
) -> tuple[float | None, str | None]:
    """Max-magnitude-deviation-from-1.0 ratification factor across the fact's
    affected domains (design §11, brief §3 quoted). Returns (factor, domain)
    or (None, None) when no ratification row matches — column stays NULL,
    never a fabricated 1.0-that-looks-computed."""
    if not primary_graha or not ratification_lookup:
        return None, None
    best_factor: float | None = None
    best_domain: str | None = None
    for dom in domains:
        f = ratification_lookup.get((primary_graha, dom))
        if f is None:
            continue
        if best_factor is None or abs(f - 1.0) > abs(best_factor - 1.0):
            best_factor, best_domain = f, dom
    return best_factor, best_domain


# ── Night-1 Lane 4 (Change 3, CR-83/CR-54-as-amended): judged-valence loader ──
#
# STATUS (reconciled 2026-07-15, D-1.5a A2/CR-91): ga_vichara/chart_vichara
# shipped 2026-07-14 — "Lane 2 never landed" (this comment's prior wording)
# is stale and no longer describes reality. Same posture as
# _load_varga_ratification above: returns ({}, False) whenever chart_vichara
# is unavailable FOR THIS CHART (missing/partial/mid-rebuild), so
# _resolve_valence's fallback path fires honestly
# (valence_source='keyword_heuristic_v1') rather than raising — a genuine
# per-chart defensive degradation, not a permanently-dead path.

def _load_vichara_valence(conn: Any, chart_id: str, ayanamsha_id: str) -> tuple[dict[tuple[str, str, str], dict], bool]:
    """(actor, target, varga) -> {value_text, value_num}, from chart_vichara's
    vichara_family='valence_pass' rows for this chart AND ayanamsha. Returns (lookup, table_available).

    D-1.5a wave gate finding (live gate battery, 2026-07-15): this query was missing
    the ayanamsha_id filter — chart_vichara carries rows for every ayanamsha the chart
    was built with (5 on the canonical charts), and without this filter the lookup dict
    could silently mix rows across ayanamshas keyed only on (actor, target, varga).
    VERIFIED CORRECTION (independent Opus review): for the specific live symptom that
    surfaced this investigation (Mars/H2/wealth served 'malefic' while chart_vichara
    stored 'strong_benefic'), a direct DB check across all 5 ayanamshas found EVERY
    ayanamsha stores 'strong_benefic' for this exact key — so cross-ayanamsha
    contamination could not have produced that specific 'malefic'. The real cause of
    that symptom was staleness (bo_laksana's build completed at 22:05:07 UTC, over an
    hour BEFORE ga_vichara's corrected data was ready at 23:10:50 UTC — see migration
    437, which adds the missing depends_on edge). This filter is kept anyway as
    independently-real hardening: the sibling function _load_varga_ratification (fixed
    alongside this one) had PROVEN live cross-ayanamsha contamination on this same
    chart ((JUP, wealth) ratification_factor 1 vs 1.4 across ayanamshas) — the same
    missing-filter defect class is real even though it wasn't this specific bug."""
    sp = "sp_bo_laksana_vichara_valence"
    try:
        with conn.cursor() as _c:
            _c.execute(f"SAVEPOINT {sp}")
        rows = _fetch_dict(
            conn,
            """SELECT actor, target, varga, value_text, value_num FROM chart_vichara
               WHERE chart_id = %s AND ayanamsha_id = %s AND vichara_family = 'valence_pass'""",
            [chart_id, ayanamsha_id],
        )
        with conn.cursor() as _c:
            _c.execute(f"RELEASE SAVEPOINT {sp}")
    except Exception as exc:
        try:
            with conn.cursor() as _c:
                _c.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        logger.warning(
            "[bo_laksana] chart_vichara valence_pass unavailable (%s) — ga_vichara "
            "build is missing/partial for this chart; every signal falls back "
            "to the keyword heuristic this build (documented, not silent — "
            "valence_source='keyword_heuristic_v1').", exc,
        )
        return {}, False
    lookup: dict[tuple[str, str, str], dict] = {}
    for r in rows:
        actor = str(r.get("actor") or "")
        target = str(r.get("target") or "")
        varga = str(r.get("varga") or "D1")
        if actor and target:
            lookup[(actor, target, varga)] = {
                "value_text": r.get("value_text"),
                "value_num": r.get("value_num"),
            }
    return lookup, True


def _load_vichara_divergence_signals(
    conn: Any, chart_id: str, ayanamsha_id: str, build_id: str, now: str,
) -> list[dict]:
    """CR-57: emit a first-class MSR signal per chart_vichara row with
    vichara_family='varga_ratification_divergence'. ga_vichara/LANE2 shipped
    2026-07-14 (reconciled 2026-07-15, D-1.5a A2/CR-91) — this returns []
    only as a per-chart defensive degradation whenever chart_vichara is
    unavailable for THIS chart (see _load_varga_ratification's guard note),
    not because the table is permanently absent.

    D-1.5a wave gate finding (2026-07-15): this function already RECEIVED
    ayanamsha_id but never used it in the query — sibling defect of
    _load_vichara_valence / _load_varga_ratification, discovered while fixing
    those. Without the filter, this emitted a varga_ratification_divergence
    signal per chart_vichara row across EVERY ayanamsha on each ayanamsha's own
    build_substep — 5x duplicate/cross-contaminated divergence signals."""
    sp = "sp_bo_laksana_vichara_divergence"
    try:
        with conn.cursor() as _c:
            _c.execute(f"SAVEPOINT {sp}")
        rows = _fetch_dict(
            conn,
            """SELECT subject, domain, value_text, value_num, constituent_facts_array
               FROM chart_vichara
               WHERE chart_id = %s AND ayanamsha_id = %s AND vichara_family = 'varga_ratification_divergence'""",
            [chart_id, ayanamsha_id],
        )
        with conn.cursor() as _c:
            _c.execute(f"RELEASE SAVEPOINT {sp}")
    except Exception as exc:
        try:
            with conn.cursor() as _c:
                _c.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        logger.info(
            "[bo_laksana] varga_ratification_divergence signals skipped (%s) — "
            "chart_vichara unavailable for this chart (ga_vichara build "
            "missing/partial, not permanently absent).", exc,
        )
        return []
    signals: list[dict] = []
    for r in rows:
        subj = str(r.get("subject") or "")
        dom = str(r.get("domain") or "")
        value_text = str(r.get("value_text") or "")
        value_num = r.get("value_num")
        constituents = r.get("constituent_facts_array") or []
        valence = "malefic" if (value_num is not None and float(value_num) < 0) else (
            "benefic" if (value_num is not None and float(value_num) > 0) else "neutral"
        )
        signals.append({
            "signal_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": ayanamsha_id,
            "build_id": build_id,
            "signal_type_id": f"varga_ratification_divergence:{subj}:{dom}"[:80],
            "signal_type_class": "varga_ratification_divergence",
            "signal_tradition": "parashari",
            "fact_kind": "configuration",
            "source_l1_asset": "ga_vichara",
            "source_subsystem": "structural",
            "signal_summary_text": (
                f"category=varga_ratification_divergence | subject={subj} | domain={dom} | "
                f"value_text={value_text} | value_num={value_num}"
            ),
            "signal_headline_text": value_text or f"{subj}: divergent varga ratification in {dom}",
            "classical_sources_jsonb": None,
            "varga_id": None,
            "varga_provenance_jsonb": None,
            "epistemic_tier": "documented_approximation",
            "epistemic_jsonb": json.dumps({
                "tradition_agreement_state": "single",
                "epistemic_tier": "documented_approximation",
                "computation_vs_interpretation": "computation",
                "source": "chart_vichara/varga_ratification_divergence",
            }),
            "salience_conditioned_by_jsonb": None,
            "signature_tier": None,   # assigned by _assign_tiers_by_percentile
            "_tier_ceiling": None,
            "valence": valence,
            "lel_origin": False,
            "configuration_jsonb": json.dumps({"subject": subj, "domain": dom, "value_text": value_text}),
            # CR-97 hotfix follow-up (89fe8824's residual-risk finding): the same
            # NOT NULL column must never be collapsed to None by a falsy `or` —
            # constituents == [] (a legitimate, fact-less divergence signal) must
            # stay [] here, not become NULL against bodha_msr_signals' NOT NULL
            # constraint.
            "constituent_facts_array": [str(c) for c in constituents if c],
            "constituent_signals_array": None,
            "classical_sources_array": None,
            "source_corroboration_count_by_text": 2,
            "source_corroboration_count_by_verse": None,
            "orb_tightness": 1.0,
            "shadbala_norm": 1.0,
            "dignity_score": 0.5,
            # NOT NULL column; this signal type is derived from chart_vichara
            # ratification data, not the condition-terms salience pipeline that
            # populates deterministic_strength for ordinary chart_facts-sourced
            # signals (see the "sal.get('condition_terms')" path below). No
            # equivalent per-signal deterministic-strength computation exists for
            # this signal class, so — mirroring the orb_tightness/shadbala_norm
            # neutral-placeholder convention two lines up — use a fixed neutral
            # value rather than leave it NULL (schema violation) or fabricate a
            # bespoke formula (B.10).
            "deterministic_strength": 1.0,
            # NOT NULL column. This signal is epistemic_tier="documented_approximation"
            # (set above). The now-deleted v1 verification_certainty formula (see the
            # historical note on _compute_salience_v2_inputs, ~line 1644) assigned
            # documented_approximation-tier signals a 0.778 ceiling; reusing that exact,
            # already-documented precedent here (rather than 1.0 — which would overstate
            # certainty for an approximation-tier signal — or a newly-invented number).
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
            # class_prior for this signal class: design "high salience by
            # construction" default 1.2 (brief §3.4) when the priors table has
            # no explicit row for signal_type_class='varga_ratification_divergence'.
            "computed_salience": round(1.2 * 1.0, 6),
            "salience_formula_version": "v2.0",
            "salience_confidence_interval_jsonb": None,
            "salience_inputs_complete": False,
            "present_but_enfeebled": False,
            "class_prior": 1.2,
            "verification_rescale": None,
            "bala_gate": None,
            "functional_context_score": None,
            "domains_affected_array": [dom] if dom else [],
            "domain_salience_jsonb": json.dumps({dom: 1.2} if dom else {}),
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
            "verification_method": "chart_vichara_projection",
            "citation_ref": f"chart_vichara/{subj}/{dom}",
            "citation_human": f"ga_vichara varga_ratification_divergence: {subj} in {dom}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
            "ratification_factor": None,
            "valence_source": "ga_vichara_v1",
        })
    return signals


# ── Night-1 Lane 4 (Change 5, CR-76/77 AMENDED): position-class subject resolution ──
#
# Register §I.1 (binding): special-lagna / chara-karaka / arudha / KP / tajaka
# facts are ingested-then-starved — they carry no graha/house resolution so the
# salience assembly defaults to shadbala 1.0 / dignity 0.5 / bindus 4 and sinks.
# This resolves EXISTING ingested facts only (anti-scope: no new fetch of new
# categories). Explicit jsonb keys are tried first (covers the majority of
# already-ingested facts); a sign→lord fallback covers facts that only carry a
# sign/rashi name with no explicit graha key.

_SIGN_LORD: dict[str, str] = {
    "aries": "MAR", "taurus": "VEN", "gemini": "MER", "cancer": "MOON",
    "leo": "SUN", "virgo": "MER", "libra": "VEN", "scorpio": "MAR",
    "sagittarius": "JUP", "capricorn": "SAT", "aquarius": "SAT", "pisces": "JUP",
}

_POSITION_CLASS_EXPLICIT_KEYS = (
    "graha", "primary_graha", "lord", "tenant_graha", "occupant",
    "conjunct_graha", "significator", "karaka_graha", "resolved_graha",
)


def _resolve_position_subject(
    fact_cat: str, fact_subject: str | None, fvj: dict, fact_value_text: str | None,
) -> tuple[str | None, int | None, str | None]:
    """Best-effort (graha, house, rule) resolution for position-class facts.
    Returns (None, None, None) when genuinely unresolvable — callers keep the
    existing defaults + inputs_complete=False (trap #17), per brief §6."""
    house_raw = fvj.get("house") or fvj.get("house_number") or fvj.get("bhava") or fvj.get("cusp")
    try:
        house = int(house_raw) if house_raw is not None else None
    except (TypeError, ValueError):
        house = None
    if house is not None and not (1 <= house <= 12):
        house = None

    # 1. Explicit jsonb graha-like keys (covers most already-ingested facts).
    for key in _POSITION_CLASS_EXPLICIT_KEYS:
        v = fvj.get(key)
        if v:
            return str(v), house, f"explicit_jsonb:{key}"

    # 2. Chara-karaka / karakamsa / swamsa: the karaka's holder is often
    #    carried directly as fact_value_text (e.g. AmK -> "Saturn").
    if fact_cat in ("karaka_chara_position", "karakamsa_position", "swamsa_position"):
        graha = _infer_graha_from_text(fact_value_text or "")
        if graha:
            return graha, house, "karaka_value_text"

    # 3. sign/rashi name present -> classical sign lord (deterministic classical
    #    fact, not a fabrication) for special_lagna / arudha_pada / kp_* facts.
    sign = fvj.get("sign") or fvj.get("rashi")
    if not sign and fact_value_text:
        # value_text sometimes IS the sign name (e.g. special_lagna landing sign).
        candidate = str(fact_value_text).strip().lower()
        if candidate in _SIGN_LORD:
            sign = candidate
    if sign:
        lord = _SIGN_LORD.get(str(sign).strip().lower())
        if lord:
            return lord, house, "sign_lord"

    # 4. fall back to parsing fact_subject itself (e.g. 'D1_SUN', 'SUN-HOUSE_7').
    graha = _graha_key_from_subject(str(fact_subject or ""))
    if graha and (graha in _LONG_TO_SHORT.values() or graha.upper() in _LONG_TO_SHORT):
        return graha, house, "fact_subject_parse"

    return None, house, None


# ── Classical bridge: yoga/dosha citation join (P3B CLASSICAL BRIDGE fix) ─────
#
# Root cause: L1 facts never carried fvj['classical_citation_id'] / ['citation_id']
# (the keys this writer originally checked) — but L1 DOES carry a per-fact
# fvj['classical_citations'] array (chapter/text_id/chunk_id/verse_ref), and
# fact_subject IS the brahma_yoga_catalog / brahma_dosha_catalog canonical_id.
# The bridge below is a deterministic join on that existing data — no LLM,
# no fabrication. Preloaded once per sub-step (bulk reads), not per-row.

_YOGA_DOSHA_CATS = frozenset({
    "yoga_label", "yoga_fires", "dosha_label", "dosha_fires", "graha_yoga_karaka_flag",
})


def _build_classical_catalog_lookup(conn: Any) -> tuple[set[str], set[str], dict[str, list[str]]]:
    """Bulk-preload yoga/dosha canonical_ids + rule_ids once per sub-step.

    Returns (yoga_canonical_ids, dosha_canonical_ids, yoga_canonical_id -> [rule_id]).
    """
    yoga_ids = {
        str(r["canonical_id"]) for r in _fetch_dict(
            conn, "SELECT canonical_id FROM brahma_yoga_catalog", [])
    }
    dosha_ids = {
        str(r["canonical_id"]) for r in _fetch_dict(
            conn, "SELECT canonical_id FROM brahma_dosha_catalog", [])
    }
    rule_rows = _fetch_dict(
        conn,
        """SELECT yoga_canonical_id, rule_id FROM sutravali_rules
           WHERE yoga_canonical_id IS NOT NULL""",
        [],
    )
    yoga_rule_ids: dict[str, list[str]] = {}
    for r in rule_rows:
        yid = str(r["yoga_canonical_id"])
        yoga_rule_ids.setdefault(yid, []).append(str(r["rule_id"]))
    return yoga_ids, dosha_ids, yoga_rule_ids


def _collect_referenced_chunk_ids(fact_rows: list[dict]) -> set[str]:
    """Scan fact rows for chunk_id refs inside fvj.classical_citations (pre-validation pass)."""
    chunk_ids: set[str] = set()
    for fact_row in fact_rows:
        fvj = fact_row.get("fact_value_jsonb")
        if isinstance(fvj, str):
            try:
                fvj = json.loads(fvj)
            except Exception:
                fvj = {}
        if not isinstance(fvj, dict):
            continue
        citations = fvj.get("classical_citations")
        if not isinstance(citations, list):
            continue
        for c in citations:
            if isinstance(c, dict) and c.get("chunk_id"):
                chunk_ids.add(str(c["chunk_id"]))
    return chunk_ids


def _validate_chunk_ids(conn: Any, chunk_ids: set[str]) -> set[str]:
    """One bulk query confirming which referenced chunk_ids genuinely exist (no fabrication)."""
    if not chunk_ids:
        return set()
    rows = _fetch_dict(
        conn,
        "SELECT id FROM classical_text_chunks WHERE id = ANY(%s::uuid[])",
        [list(chunk_ids)],
    )
    return {str(r["id"]) for r in rows}


def _build_classical_sources(
    fact_cat: str,
    fact_subject: str | None,
    fvj: dict,
    yoga_catalog_ids: set[str],
    dosha_catalog_ids: set[str],
    yoga_rule_ids: dict[str, list[str]],
    valid_chunk_ids: set[str],
) -> tuple[dict | None, list[str] | None]:
    """Deterministic classical-source bridge — no LLM, no fabricated citations.

    citations/text_chunk_ids come straight from the L1 fact's own fvj.classical_citations
    (already attached at L1 build time). catalog_ids/rule_ids come from joining
    fact_subject (canonical_id) against brahma_yoga_catalog/brahma_dosha_catalog and
    sutravali_rules.yoga_canonical_id.
    """
    citations_raw = fvj.get("classical_citations")
    citation_strs: list[str] = []
    text_chunk_ids: list[str] = []
    if isinstance(citations_raw, list):
        for c in citations_raw:
            if not isinstance(c, dict):
                continue
            text_id = c.get("text_id")
            chapter = c.get("chapter")
            chunk_id = c.get("chunk_id")
            if chunk_id and str(chunk_id) in valid_chunk_ids:
                text_chunk_ids.append(str(chunk_id))
            if text_id and chapter is not None:
                citation_strs.append(f"{text_id}:{chapter}")
            elif text_id:
                citation_strs.append(str(text_id))

    catalog_ids: list[str] = []
    rule_ids: list[str] = []
    canonical_id = (fact_subject or "").strip()
    if canonical_id:
        if fact_cat in ("yoga_label", "yoga_fires", "graha_yoga_karaka_flag") and canonical_id in yoga_catalog_ids:
            catalog_ids.append(canonical_id)
            rule_ids.extend(yoga_rule_ids.get(canonical_id, []))
        elif fact_cat in ("dosha_label", "dosha_fires") and canonical_id in dosha_catalog_ids:
            catalog_ids.append(canonical_id)

    if not (catalog_ids or rule_ids or text_chunk_ids or citation_strs):
        return None, None

    classical_sources_jsonb = {
        "catalog_ids": catalog_ids,
        "rule_ids": rule_ids,
        "text_chunk_ids": text_chunk_ids,
        "citations": citation_strs,
    }
    seen: set[str] = set()
    flat: list[str] = []
    for x in catalog_ids + rule_ids + text_chunk_ids + citation_strs:
        if x not in seen:
            seen.add(x)
            flat.append(x)
    return classical_sources_jsonb, (flat or None)


# ── B3: Graha inference for yoga/dosha signals ────────────────────────────────

# Maps uppercase name tokens found in fire_reason / fact_value_text → canonical graha key
# (matching the graha keys used in strength_lookup / dignity_lookup).
# The graha SSoT (brahmagyan/graha_vocabulary) tokens are derived via
# norm_graha(); _EXTRA_TEXT_ALIASES adds looser prose spellings this
# free-text extractor additionally recognizes that are not themselves
# canonical identifiers anywhere else in the codebase — ADHIṢṬHĀNA Lane A2.
_EXTRA_TEXT_ALIASES: dict[str, str] = {
    "sol": "SUN", "luna": "MOON", "mangal": "MAR", "budh": "MER",
    "brihaspati": "JUP", "sukra": "VEN", "sani": "SAT",
    "rahoo": "RAH_MEAN", "kethu": "KET_MEAN",
}
_GRAHA_NAME_MAP: dict[str, str] = {
    tok: norm_graha(tok)
    for tok in (
        "sun", "surya", "moon", "chandra", "mars", "kuja", "mangala",
        "mercury", "budha", "jupiter", "guru", "venus", "shukra",
        "saturn", "shani", "rahu", "ketu",
    )
}
_GRAHA_NAME_MAP.update(_EXTRA_TEXT_ALIASES)

# Dosha-group → primary graha (classical primary graha for each dosha type)
_DOSHA_GROUP_GRAHA: dict[str, str] = {
    "mangal": "MAR",
    "kala_sarpa": "RAH_MEAN",
    "graha_placement": "",   # too generic, parse from text
}

# Long graha name (as returned by chart_divisionals queries) → short strength_lookup key.
# Used by O3 navamsha signals so shadbala_norm resolves correctly instead of falling
# back to 1.0 when graha is e.g. "Saturn" and strength_lookup keys are "SAT".
# Values sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather than
# hardcoded literals — ADHIṢṬHĀNA Lane A2.
_LONG_TO_SHORT: dict[str, str] = {
    name: norm_graha(name)
    for name in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
        "Rahu", "Ketu",
    )
}


def _canonical_graha_code(raw: Any) -> str | None:
    """Normalize a graha token to ga_vichara's canonical subject code
    (PLANET_TO_SUBJECT convention: SUN/MOON/MAR/MER/JUP/VEN/SAT/RAH_MEAN/KET_MEAN).

    Night-1 Lane 4 fix (2026-07-14): tags['lord'] on bhava_significance_link
    facts (ga_vichara's own upstream L1 source) carries the LONG form
    ('Mars', 'Saturn', …) while ga_vichara's chart_vichara.actor/subject
    columns are already-canonical short codes. Without this normalization,
    every lookup against vichara_lookup/ratification_lookup silently misses
    for facts whose tag came from 'lord' rather than an already-canonical
    'graha' tag — the ga_vichara-sourced path degrades to the fallback with
    no signal that anything went wrong (the exact CR-42 class of bug this
    lane's own valence-fallback discipline is supposed to prevent).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s in _LONG_TO_SHORT.values():
        return s  # already canonical (e.g. 'MAR', 'RAH_MEAN')
    if s in _LONG_TO_SHORT:
        return _LONG_TO_SHORT[s]
    return _GRAHA_NAME_MAP.get(s.lower(), s)


def _infer_graha_from_text(text: str) -> str | None:
    """Extract canonical graha key from free-text (fire_reason, dosha_name, etc.).

    Uses word-boundary matching so 'Moon' in 'Jupiter in kendra from Moon'
    does not shadow 'Jupiter'.  Returns the graha whose name appears FIRST
    in the text (lowest start position wins).
    """
    if not text:
        return None
    lower = text.lower()
    best_pos: int = len(lower) + 1
    best_graha: str | None = None
    for token, graha_key in _GRAHA_NAME_MAP.items():
        # Word-boundary match: token must be preceded/followed by non-alpha
        idx = lower.find(token)
        while idx != -1:
            end = idx + len(token)
            before_ok = (idx == 0) or not lower[idx - 1].isalpha()
            after_ok  = (end == len(lower)) or not lower[end].isalpha()
            if before_ok and after_ok:
                if idx < best_pos:
                    best_pos   = idx
                    best_graha = graha_key
                break
            idx = lower.find(token, idx + 1)
    return best_graha


def _infer_graha_for_yoga_dosha(fact_cat: str, fvj: dict,
                                 fact_value_text: str | None) -> str | None:
    """B3: Infer the primary graha for yoga/dosha category facts.

    Priority:
    1. Explicit jsonb keys (graha, primary_graha, lord)
    2. dosha_group fixed mapping
    3. fire_reason text parsing
    4. fact_value_text parsing (yoga/dosha name)
    Returns canonical graha key (e.g. 'MAR', 'JUP') or None.
    """
    # 1. Explicit jsonb
    for jkey in ("graha", "primary_graha", "lord"):
        v = fvj.get(jkey)
        if v:
            return str(v)

    # 2. dosha_group fixed mapping
    dosha_group = fvj.get("dosha_group") or ""
    if dosha_group in _DOSHA_GROUP_GRAHA:
        mapped = _DOSHA_GROUP_GRAHA[dosha_group]
        if mapped:
            return mapped

    # 3. fire_reason text
    fire_reason = fvj.get("fire_reason") or ""
    graha = _infer_graha_from_text(fire_reason)
    if graha:
        return graha

    # 4. fact_value_text (yoga/dosha name)
    graha = _infer_graha_from_text(fact_value_text or "")
    if graha:
        return graha

    return None


# ── Row fetcher (ALL fact categories, no whitelist) ──────────────────────────

_FETCH_SQL = """
SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_subject,
       fact_value_num, fact_value_text, fact_value_jsonb, formula_id,
       source_calculation, verification_pass_status, citation_ref, citation_human
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
ORDER BY fact_category, fact_key
"""

# C3-fix: INVARIANT rows were previously fetched via IN (%s, 'INVARIANT') which
# caused them to be included in every ayanamsha sub-step, producing 5 identical
# signals per INVARIANT fact.  We now fetch INVARIANT rows in a separate pass
# (called once per sub-step) and process them with ayanamsha_override set to the
# current ayanamsha so the emitted signal carries the correct ayanamsha_id label.
# The separate fetch ensures each INVARIANT fact produces exactly one signal per
# ayanamsha (matching the per-ayanamsha rows), which is the intended behaviour:
# INVARIANT facts are ayanamsha-independent at source but need to be retrievable
# per-ayanamsha in downstream queries.
_FETCH_INVARIANT_SQL = """
SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_subject,
       fact_value_num, fact_value_text, fact_value_jsonb, formula_id,
       source_calculation, verification_pass_status, citation_ref, citation_human
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = 'INVARIANT'
ORDER BY fact_category, fact_key
"""


def _fetch_all_facts(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """Fetch ayanamsha-specific facts only (INVARIANT excluded — see _fetch_invariant_facts)."""
    return _fetch_dict(conn, _FETCH_SQL, [chart_id, ayanamsha_id])


def _fetch_invariant_facts(conn: Any, chart_id: str) -> list[dict]:
    """Fetch INVARIANT facts separately so they are processed exactly once per sub-step."""
    return _fetch_dict(conn, _FETCH_INVARIANT_SQL, [chart_id])


def _fetch_valid_fact_ids(conn: Any, chart_id: str) -> set[str]:
    """WP-2.4 (9b-5 / §N.5): the authoritative set of resolvable chart_facts.fact_id
    for this chart. Every constituent citation is filtered against this set so no
    signal ever cites a fact_id that resolves to nothing."""
    rows = _fetch_dict(
        conn,
        "SELECT fact_id FROM chart_facts WHERE chart_id = %s",
        [chart_id],
    )
    return {str(r["fact_id"]) for r in rows if r.get("fact_id") is not None}


# ── WP-2.4 (LCA-9b-1): per-varga flood aggregation ────────────────────────────

def _make_aggregate_fact_row(members: list[dict], varga: str | None) -> dict:
    """Collapse a large (category × varga) member group into ONE synthetic fact
    row. Fed to _build_signal_row like any real fact, it yields a single aggregate
    rollup signal whose constituent_facts_array references every member fact_id
    (full L1 traceability preserved — nothing is dropped, only de-flooded).

    The synthetic row's own fact_id is the first member's (a real chart_facts row,
    so it resolves); every member id is carried in constituent_facts_array.
    """
    first = dict(members[0])
    member_ids = [str(m["fact_id"]) for m in members if m.get("fact_id")]
    sample_keys = sorted({str(m.get("fact_key") or "") for m in members})[:8]
    varga_label = varga or "all"
    first["fact_key"] = f"aggregate_{varga_label}"
    first["fact_value_num"] = float(len(members))
    first["fact_value_text"] = (
        f"{len(members)} {first.get('fact_category')} members rolled up "
        f"(varga={varga_label})"
    )
    first["fact_value_jsonb"] = {
        "aggregated": True,
        "member_count": len(members),
        "member_sample_keys": sample_keys,
        "varga": varga_label,
        "constituent_facts_array": member_ids,
        "wp": "WP-2.4:flood_cap",
    }
    return first


def _partition_flood(fact_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split fetched fact rows into (rows_to_emit_1to1, synthetic_aggregate_rows).

    Non-flood-prone categories pass through 1:1. Flood-prone families are grouped
    by (category × varga): groups at/under RATIFIED_FLOOD_CAP still emit 1:1
    (small = not a flood); groups over the cap collapse to one aggregate row.
    """
    from collections import defaultdict

    passthrough: list[dict] = []
    flood_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for r in fact_rows:
        cat = str(r.get("fact_category") or "")
        if cat not in _FLOOD_PRONE_FAMILIES:
            passthrough.append(r)
            continue
        fvj = r.get("fact_value_jsonb")
        if isinstance(fvj, str):
            try:
                fvj = json.loads(fvj)
            except Exception:
                fvj = {}
        varga = _extract_varga_id(str(r.get("fact_key") or ""), fvj if isinstance(fvj, dict) else None) or "NA"
        flood_groups[(cat, varga)].append(r)

    aggregates: list[dict] = []
    for (cat, varga), members in flood_groups.items():
        if len(members) <= RATIFIED_FLOOD_CAP:
            passthrough.extend(members)          # small group — no flood, keep 1:1
        else:
            aggregates.append(_make_aggregate_fact_row(members, None if varga == "NA" else varga))
    return passthrough, aggregates


# ── Salience helpers ──────────────────────────────────────────────────────────

def _safe_float(v: Any, default: float = 0.5) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


_DIGNITY_SCORE: dict[str, float] = {
    "exalted": 1.00, "mooltrikona": 0.95, "own": 0.85,
    "friend": 0.65, "neutral": 0.50, "enemy": 0.35, "debilitated": 0.10,
}

_HOUSE_WEIGHT: dict[int, float] = {
    1: 1.30, 5: 1.20, 9: 1.20, 4: 1.15, 7: 1.15, 10: 1.15,
    3: 1.05, 11: 1.05, 6: 0.90, 8: 0.90, 12: 0.90, 2: 1.00,
}


def _av_mult(bindus: int) -> float:
    if bindus >= 7: return 1.15
    if bindus >= 5: return 1.05
    if bindus >= 3: return 1.00
    if bindus >= 1: return 0.85
    return 0.70


def _graha_key_from_subject(fact_subject: str) -> str | None:
    """Extract the canonical graha key from fact_subject for lookup table matching.

    fact_subject patterns observed:
      'SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN'
      'D1_SUN', 'D1_MAR', …  → strip 'D1_' prefix
      'SUN-HOUSE_1', …       → strip '-HOUSE_N' suffix
    Returns the raw graha token (e.g. 'SUN', 'MAR') or None if not parseable.
    """
    s = (fact_subject or "").strip()
    if not s:
        return None
    # Strip varga prefix like 'D1_', 'D9_', …
    if "_" in s and s.split("_")[0].startswith("D") and s.split("_")[0][1:].isdigit():
        s = "_".join(s.split("_")[1:])
    # Strip house suffix like '-HOUSE_7'
    if "-HOUSE_" in s:
        s = s.split("-HOUSE_")[0]
    return s or None


def _compute_salience(
    fact_row: dict,
    tags: dict,
    strength_lookup: dict[str, float],
    dignity_lookup: dict[str, str],
    av_lookup: dict[int, int],
    class_prior: float = 1.0,
    functional_context: float = 1.0,
    varga_id: str = "D1",
) -> dict:
    """Compute salience_formula_v2 inputs from L1 data (BA-P3B formula upgrade).

    Calls formulas.salience_formula_v2 — the ONE canonical formula site (C5 fix).
    verification_certainty deleted; verification_rescale replaces it (no 0.778 ceiling).
    bala_gate added for yoga-class signals. functional_context from ga_structural.
    inputs_complete tracks whether any field fell back to a default (trap #17).
    """
    tier = str(fact_row.get("verification_pass_status") or "documented_approximation")
    fact_cat = str(fact_row.get("fact_category") or "")

    # Graha: prefer explicit tags, then fact_subject
    primary_graha = (tags.get("graha") or tags.get("primary_graha")
                     or tags.get("lord") or tags.get("body")
                     or _graha_key_from_subject(str(fact_row.get("fact_subject") or "")))

    house_num_raw = (tags.get("house") or tags.get("house_number") or tags.get("bhava"))
    try:
        house_num = int(house_num_raw) if house_num_raw is not None else 2
    except (TypeError, ValueError):
        house_num = 2

    shadbala_raw = strength_lookup.get(primary_graha or "", None) if primary_graha else None
    shadbala_norm = shadbala_raw if shadbala_raw is not None else 1.0

    dignity_state = dignity_lookup.get(primary_graha or "", "neutral") if primary_graha else "neutral"
    dignity_score = _FML_DIGNITY_SCORE.get(dignity_state, 0.50)

    bindus_raw = av_lookup.get(house_num, None)
    bindus = bindus_raw if bindus_raw is not None else 4

    # Track completeness — any default = incomplete (trap #17)
    inputs_complete = (
        primary_graha is not None
        and house_num_raw is not None
        and shadbala_raw is not None
        and bindus_raw is not None
    )

    orb = _safe_float(tags.get("orb_tightness"), 1.0)
    vargottama_amp = _safe_float(tags.get("vargottama_amp"), 0.0)
    neechabhanga = _safe_float(tags.get("neechabhanga"), 1.0)
    cancellation = _safe_float(tags.get("cancellation"), 1.0)

    # bala_gate: yoga-class signals only
    is_yoga_class = fact_cat in (
        "yoga_label", "yoga_fires", "dosha_label", "dosha_fires", "graha_yoga_karaka_flag"
    )
    bala_gate_val: float | None = None
    if is_yoga_class:
        bala_gate_val = max(0.30, min(min(shadbala_norm, 2.0), 1.00))

    inp = SalienceInputsV2(
        orb_tightness=orb,
        shadbala_norm=min(shadbala_norm, 2.0),
        dignity_score=dignity_score,
        house_number=house_num,
        ashtakavarga_bindus=bindus,
        vargottama_amplification=vargottama_amp,
        neechabhanga_modifier=neechabhanga,
        cancellation_modifier=cancellation,
        verification_pass_status=tier,
        class_prior=class_prior,
        varga_id=varga_id,
        specificity=1.0,        # filled in second pass by percentile UPDATE
        bala_gate=bala_gate_val,
        functional_context=functional_context,
        inputs_complete=inputs_complete,
    )
    result = salience_formula_v2(inp)
    # Add legacy decomposition keys for backward compat with downstream readers
    result["orb_tightness"] = round(orb, 6)
    result["shadbala_norm"] = round(min(shadbala_norm, 2.0), 6)
    result["dignity_score"] = round(dignity_score, 6)
    result["vargottama_amplification"] = round(vargottama_amp, 6)
    result["neechabhanga_modifier"] = round(neechabhanga, 6)
    result["cancellation_modifier"] = round(cancellation, 6)
    return result


# ── Row builder ───────────────────────────────────────────────────────────────

def _build_signal_row(
    fact_row: dict,
    chart_id: str,
    build_id: str,
    strength_lookup: dict,
    dignity_lookup: dict,
    av_lookup: dict,
    now: str,
    ayanamsha_override: str | None = None,
    classical_catalog: tuple[set[str], set[str], dict[str, list[str]], set[str]] | None = None,
    valid_fact_ids: set[str] | None = None,
    class_priors: dict[tuple[str, str], float] | None = None,
    ratification_lookup: dict[tuple[str, str], float] | None = None,
    vichara_valence_lookup: dict[tuple[str, str, str], dict] | None = None,
) -> dict:
    fact_id  = str(fact_row.get("fact_id", ""))
    fact_cat = str(fact_row.get("fact_category", ""))
    fact_key = str(fact_row.get("fact_key", ""))
    # For INVARIANT facts the row carries ayanamsha_id='INVARIANT'; use the substep ayanamsha
    raw_aya  = str(fact_row.get("ayanamsha_id", ""))
    aya      = ayanamsha_override if (raw_aya == "INVARIANT" and ayanamsha_override) else raw_aya
    vpass    = str(fact_row.get("verification_pass_status") or "documented_approximation")
    sc       = str(fact_row.get("source_calculation") or "")

    fact_value_text = fact_row.get("fact_value_text")
    fact_value_num  = fact_row.get("fact_value_num")

    # Parse fact_value_jsonb
    fvj = fact_row.get("fact_value_jsonb")
    if isinstance(fvj, str):
        try:
            fvj = json.loads(fvj)
        except Exception:
            fvj = {}
    fvj = fvj or {}
    if not isinstance(fvj, dict):
        fvj = {}

    # Constituent facts (WP-2.4 9b-5 / §N.5 — referential integrity).
    # Candidates come from the L1 fact's jsonb, but L1 writers (e.g. the dosha
    # catalog) sometimes store internal reference ids that are NOT chart_facts
    # fact_ids and resolve to NOTHING. Filter every candidate against the chart's
    # real fact_id set (valid_fact_ids) and ALWAYS union the signal's own fact_id
    # (a genuine chart_facts row, guaranteed to resolve). Result: no signal ever
    # cites a constituent that fails to resolve.
    const_facts_raw = fvj.get("constituent_facts_array") or fvj.get("constituent_fact_ids")
    if const_facts_raw and isinstance(const_facts_raw, list):
        candidates = [str(f) for f in const_facts_raw if f]
    else:
        candidates = []
    if valid_fact_ids is not None:
        resolved = [f for f in candidates if f in valid_fact_ids]
    else:
        resolved = list(candidates)
    # Own fact_id is authoritative (it IS a chart_facts row) — always first.
    if fact_id and fact_id not in resolved:
        resolved.insert(0, fact_id)
    constituent_facts = resolved or ([fact_id] if fact_id else [])

    # Tags: merge fact_value_jsonb extras into config
    # Night-1 Lane 4 (Change 3 fix, 2026-07-14): "target_house" added — the
    # bhava_significance_link / aspect_parashari_per_varga facts that feed
    # ga_vichara's valence_pass rows carry the aspected/lorded house under
    # jsonb key "target_house" (NOT "house" — "house" on these facts, when
    # present at all, is the ACTOR's own house). Without this key, _resolve_valence
    # could never recover the target house and the ga_vichara-sourced path was
    # silently dead even after ga_vichara shipped (verified 2026-07-14).
    _TAG_KEYS = ("graha", "primary_graha", "lord", "body", "house", "house_number",
                 "target_house", "bhava", "orb_tightness", "vargottama_amp",
                 "neechabhanga", "cancellation", "varga", "varga_id")
    tags: dict = {}
    for key in _TAG_KEYS:
        v = fvj.get(key)
        if v is not None:
            tags[key] = v

    # Structured config (ALL keys from jsonb, minus constituent_facts_array)
    config: dict = {
        "fact_key": fact_key,
        "fact_value_text": fact_value_text,
        "fact_value_num": (float(fact_value_num) if fact_value_num is not None else None),
    }
    for k, v in fvj.items():
        if k not in ("constituent_facts_array", "constituent_fact_ids") and v is not None:
            config[k] = v
            if k in _TAG_KEYS:
                tags[k] = v

    # Source L1 asset + subsystem
    source_l1_asset  = _infer_source_l1_asset(sc)
    source_subsystem = _infer_source_subsystem(source_l1_asset)

    # Fact kind, valence, varga_id, tradition
    fact_kind  = _infer_fact_kind(fact_cat)
    varga_id   = _extract_varga_id(fact_key, fvj)
    tradition  = _infer_tradition(fact_cat, sc)

    # Night-1 Lane 4 (Change 5, CR-76/77 AMENDED): position-class subject
    # resolution — position-class facts otherwise carry no graha/house
    # resolution and default to shadbala 1.0 / dignity 0.5 / bindus 4, sinking
    # to background regardless of true significance.
    subject_resolution: dict | None = None
    if fact_cat.startswith(_POSITION_CATS_PREFIX) and "graha" not in tags:
        resolved_graha, resolved_house, rule = _resolve_position_subject(
            fact_cat, fact_row.get("fact_subject"), fvj, fact_value_text,
        )
        if resolved_graha:
            tags["graha"] = resolved_graha
            config["graha"] = resolved_graha
            if resolved_house is not None and "house" not in tags:
                tags["house"] = resolved_house
                config["house"] = resolved_house
            subject_resolution = {
                "resolved_graha": resolved_graha,
                "resolved_house": resolved_house,
                "rule": rule,
            }
        elif resolved_house is not None:
            subject_resolution = {"resolved_graha": None, "resolved_house": resolved_house, "rule": None}

    # CR-91 (A2): aspect_parashari_given / aspect_parashari_per_varga carry the
    # ASPECTING graha in fact_subject (canonical short code — bare for the D1
    # -only `_given` category, varga-prefixed e.g. "D9_MAR" for `_per_varga`),
    # never in fact_value_jsonb, and aspect_parashari_given carries no jsonb at
    # all (target house lives only in fact_key="house_{n}"). Without this
    # block, `tags` never got a 'graha' entry for this population, so
    # _resolve_valence's actor lookup was always empty and it silently fell
    # back to keyword_heuristic_v1 for every aspect fact even after ga_vichara
    # shipped (ga_vichara_writer.py's build_aspect_valence_rows() now emits
    # the corresponding valence_pass rows keyed on this exact (actor, target,
    # varga) shape). aspect_parashari_per_varga's target_house is already
    # populated into `tags` from fvj by the Change-3 fix above (jsonb key
    # "target_house") — only the graha and the D1-only `_given` category's
    # house need resolving here.
    if fact_cat in ("aspect_parashari_given", "aspect_parashari_per_varga") and "graha" not in tags:
        raw_subj = str(fact_row.get("fact_subject") or "")
        subj = raw_subj
        if varga_id and raw_subj.upper().startswith(f"{varga_id}_"):
            subj = raw_subj[len(varga_id) + 1:]
        if subj:
            tags["graha"] = subj
            config["graha"] = subj
        if "target_house" not in tags and "house" not in tags:
            m = re.match(r"house_(\d{1,2})$", fact_key or "", re.IGNORECASE)
            if m:
                h = int(m.group(1))
                if 1 <= h <= 12:
                    tags["target_house"] = h
                    config["target_house"] = h

    # Night-1 Lane 4 (Change 3, CR-83/CR-54-as-amended): judged valence — prefer
    # ga_vichara's valence_pass row over the keyword heuristic; the heuristic is
    # demoted to an explicitly-tagged fallback (CR-42 class: never silent).
    valence, valence_source, judged_value_num = _resolve_valence(
        vichara_valence_lookup or {}, fact_cat, fact_value_text, tags,
    )

    # Domains (WP-2.4 9b-3: KP cusp facts inherit their bhava's domains)
    domains        = _assign_domains(fact_cat, source_subsystem,
                                     fact_subject=str(fact_row.get("fact_subject") or ""),
                                     fvj=fvj, varga_id=varga_id)
    duration_class = _duration_class(fact_cat)

    # B3: Populate configuration_jsonb.graha for yoga/dosha signals (CONTRACT-1).
    # A2 (bo_karanajala) groups contradiction detection by config['graha'].
    # yoga/dosha facts rarely carry graha in jsonb — infer it here.
    if fact_cat in ("yoga_label", "yoga_fires", "dosha_label", "dosha_fires",
                    "graha_yoga_karaka_flag"):
        if "graha" not in config or config.get("graha") is None:
            inferred_graha = _infer_graha_for_yoga_dosha(fact_cat, fvj, fact_value_text)
            if inferred_graha:
                config["graha"] = inferred_graha
                tags["graha"] = inferred_graha

    # Classical citation bridge (P3B fix) — deterministic join, see _build_classical_sources.
    classical_sources_jsonb: dict | None = None
    classical_sources_array: list[str] | None = None
    if classical_catalog is not None:
        yoga_ids, dosha_ids, yoga_rule_ids, valid_chunk_ids = classical_catalog
        classical_sources_jsonb, classical_sources_array = _build_classical_sources(
            fact_cat, fact_row.get("fact_subject"), fvj,
            yoga_ids, dosha_ids, yoga_rule_ids, valid_chunk_ids,
        )

    # Salience computation — v2 formula (BA-P3B).
    # Night-1 Lane 4 (Change 1, CR-81): class_prior activated from brahma_class_priors
    # (was a literal 1.0). Miss (no matching row) is NOT treated as inputs_complete=False
    # (priors are optional by design) but IS counted for the hit-rate report (§2).
    stc_for_prior = _signal_type_class(fact_cat)
    class_prior_val, class_prior_hit = _resolve_class_prior(
        class_priors or {}, stc_for_prior, source_subsystem,
    )
    sal = _compute_salience(
        fact_row, tags, strength_lookup, dignity_lookup, av_lookup,
        class_prior=class_prior_val,
        functional_context=1.0,
        varga_id=varga_id or "D1",
    )
    computed_salience = sal["computed_salience"]

    # Night-1 Lane 4 (Change 2, CR-82→CR-65): ratification-aware weighting.
    # Applies only to per-varga (non-D1) facts whose subject resolves to a
    # graha/lord with a chart_vichara ratification row in one of the fact's
    # domains. ratification_lookup is {} whenever chart_vichara is absent
    # (see _load_varga_ratification); factor stays None/NULL then.
    # 2026-07-14 fix: normalize through _canonical_graha_code — tags['lord']
    # (bhava_significance_link's own jsonb key) carries the long form ('Mars'),
    # but chart_vichara.subject is always the canonical short code ('MAR');
    # without normalization this lookup silently missed for every such fact.
    primary_graha_for_ratif = _canonical_graha_code(
        tags.get("graha") or tags.get("primary_graha")
        or tags.get("lord") or tags.get("body")
        or _graha_key_from_subject(str(fact_row.get("fact_subject") or ""))
    )
    ratification_factor: float | None = None
    ratification_domain: str | None = None
    if varga_id is not None and str(varga_id).upper() not in ("D1", ""):
        ratification_factor, ratification_domain = _resolve_ratification_factor(
            ratification_lookup or {}, primary_graha_for_ratif, domains,
        )
        if ratification_factor is not None:
            computed_salience = round(computed_salience * ratification_factor, 6)

    # Text columns
    signal_summary_text = _build_summary_text(
        fact_cat, fact_key, fact_value_text,
        float(fact_value_num) if fact_value_num is not None else None,
        config,
    )
    headline_subject = tags.get("graha") or (subject_resolution or {}).get("resolved_graha")
    headline_house = tags.get("house") or tags.get("house_number") or tags.get("bhava")
    try:
        headline_house = int(headline_house) if headline_house is not None else None
    except (TypeError, ValueError):
        headline_house = None
    signal_headline_text = _build_headline_text(
        fact_cat, fact_key, fact_value_text,
        float(fact_value_num) if fact_value_num is not None else None,
        source_l1_asset,
        fact_subject=headline_subject,
        house=headline_house,
        varga_id=varga_id,
    )

    # signal_type_id = category:key[:80]
    signal_type_id = f"{fact_cat}:{fact_key}"[:80]

    # Domain salience
    n_domains = max(len(domains), 1)
    domain_salience = {d: round(computed_salience / n_domains, 6) for d in domains}

    # Epistemic jsonb
    epistemic_jsonb = {
        "tradition_agreement_state": "single",
        "epistemic_tier": vpass,
        "computation_vs_interpretation": "computation",
    }
    if judged_value_num is not None:
        epistemic_jsonb["judged_valence"] = judged_value_num
    if subject_resolution is not None:
        epistemic_jsonb["subject_resolution"] = subject_resolution
    if ratification_domain is not None:
        epistemic_jsonb["ratification_domain_applied"] = ratification_domain

    # Remedy hooks for dosha categories
    remedy_hooks: list[str] | None = None
    if "dosha" in fact_cat or "kala_sarpa" in fact_cat or "sade_sati" in fact_cat:
        remedy_hooks = [fact_cat]

    # L1 citation pass-through
    l1_citation_ref   = fact_row.get("citation_ref")   or f"chart_facts/{fact_id}"
    l1_citation_human = fact_row.get("citation_human") or f"L1 chart_facts: {fact_cat}/{fact_key}"

    return {
        # Identity
        "signal_id":                                str(uuid.uuid4()),
        "chart_id":                                 chart_id,
        "ayanamsha_id":                             aya,
        "build_id":                                 build_id,
        # Classification
        "signal_type_id":                           signal_type_id,
        "signal_type_class":                        _signal_type_class(fact_cat),
        "signal_tradition":                         tradition,
        # ── Enriched spine columns ────────────────────────────────────────────
        "fact_kind":                                fact_kind,
        "source_l1_asset":                          source_l1_asset,
        "source_subsystem":                         source_subsystem,
        "signal_summary_text":                      signal_summary_text,
        "signal_headline_text":                     signal_headline_text,
        "classical_sources_jsonb":                  (json.dumps(classical_sources_jsonb)
                                                     if classical_sources_jsonb else None),
        "varga_id":                                 varga_id,
        "varga_provenance_jsonb":                   None,
        "epistemic_tier":                           vpass,
        "epistemic_jsonb":                          json.dumps(epistemic_jsonb),
        "salience_conditioned_by_jsonb":            None,
        # Night-1 Lane 4 (Change 2, CR-82→CR-65): signature_tier is now assigned
        # post-hoc by _assign_tiers_by_percentile (percentile of post-ratification
        # salience within this ayanamsha substep); only the flood-rollup ceiling
        # survives per-row, stashed here for that second pass to apply.
        "signature_tier":                           None,
        "_tier_ceiling":                            _tier_ceiling_for(fact_cat, varga_id),
        "valence":                                  valence,
        "lel_origin":                               False,   # LEL data is L3-gated
        # ── Structured configuration ──────────────────────────────────────────
        "configuration_jsonb":                      json.dumps(config),
        "constituent_facts_array":                  constituent_facts,
        "constituent_signals_array":                None,
        # ── Classical sourcing ────────────────────────────────────────────────
        "classical_sources_array":                  classical_sources_array,
        "source_corroboration_count_by_text":       5 if vpass == "two_pass_verified" else 2,
        "source_corroboration_count_by_verse":      None,
        # ── Salience inputs (v2 — BA-P3B) ────────────────────────────────────
        "orb_tightness":                            sal["orb_tightness"],
        "shadbala_norm":                            sal["shadbala_norm"],
        "dignity_score":                            sal["dignity_score"],
        "deterministic_strength":                   sal.get("condition_terms"),   # v2 name
        "verification_certainty":                   sal.get("verification_rescale"),  # v2 replaces v1
        "divisional_corroboration_count":           None,
        "dasha_activation_proximity_score":         None,   # L3-fill hook
        "house_weight_multiplier":                  sal["house_weight_multiplier"],
        "ashtakavarga_support_multiplier":          sal["ashtakavarga_support_multiplier"],
        "aspect_modifier":                          None,
        "vargottama_amplification":                 sal["vargottama_amplification"],
        "argala_modifier":                          None,
        "neechabhanga_modifier":                    sal["neechabhanga_modifier"],
        "cancellation_modifier":                    sal["cancellation_modifier"],
        "computed_salience":                        computed_salience,
        "salience_formula_version":                 sal["salience_formula_version"],
        "salience_confidence_interval_jsonb":       None,
        # ── Salience v2 new columns (migration 393) ───────────────────────────
        "salience_inputs_complete":                 sal.get("salience_inputs_complete", True),
        "present_but_enfeebled":                    sal.get("present_but_enfeebled", False),
        "class_prior":                              sal.get("class_prior", 1.0),
        "verification_rescale":                     sal.get("verification_rescale"),
        "bala_gate":                                sal.get("bala_gate") if sal.get("bala_gate") != 1.0 else None,
        "functional_context_score":                 sal.get("functional_context"),
        # Night-1 Lane 4 (migration 367): ratification_factor NULL until a chart_vichara
        # row matches (LANE2-dependent); valence_source always populated (CR-42 class).
        "ratification_factor":                      ratification_factor,
        "valence_source":                            valence_source,
        # Internal bookkeeping consumed by run_substep's notes/hit-rate report — not a
        # DB column; harmless as an extra dict key for psycopg's named-param binding.
        "_class_prior_hit":                         class_prior_hit,
        # salience_pctl_in_class, salience_robustness, aggregation_member filled by
        # second-pass UPDATE after all signals for this (chart × ayanamsha) are inserted
        # ── Domain ────────────────────────────────────────────────────────────
        "domains_affected_array":                   domains,
        "domain_salience_jsonb":                    json.dumps(domain_salience),
        "shared_factor_keys_jsonb":                 None,
        "cross_domain_shared_factor_count":         None,
        # ── Graph hooks ───────────────────────────────────────────────────────
        "graph_edge_pattern_jsonb":                 None,
        "graph_node_strength_contribution_jsonb":   None,
        "relationship_classification":              None,
        # ── RM hooks ─────────────────────────────────────────────────────────
        "graha_weakness_indicators_jsonb":          None,
        "remedy_hooks_array":                       remedy_hooks,
        "recurring_pattern_marker":                 None,
        # ── Digest hooks ─────────────────────────────────────────────────────
        "top_k_salience_rank":                      None,   # set post-build
        "system_convergence_count":                 None,
        "signature_class":                          _signature_class(_signal_type_class(fact_cat)),
        # ── Contradictions ────────────────────────────────────────────────────
        "contradicts_signals_array":                None,
        # ── Active periods (L3-fill hooks) ────────────────────────────────────
        "active_duration_class":                    duration_class,
        "active_dasha_periods_jsonb":               None,
        "activation_predicted_dates_jsonb":         None,
        "predicted_outcome_class":                  None,
        # ── Cross-ayanamsha ───────────────────────────────────────────────────
        "cross_ayanamsha_consistency_score":        None,
        "strength_normalized_to_chart_max":         None,
        # ── Precision flags ───────────────────────────────────────────────────
        "pada_precision_flag":                      None,
        "cross_system_consensus_count":             None,
        "channel_render_priority_jsonb":            None,
        # ── Provenance ────────────────────────────────────────────────────────
        "verification_pass_status":                 vpass,
        "verification_method":                      "L1_fact_projection",
        "citation_ref":                             l1_citation_ref,
        "citation_human":                           l1_citation_human,
        "computed_at":                              now,
        "engine_version":                           ENGINE_VERSION,
    }


# ── O3: Navamsha (D9) cross-check signal builder ─────────────────────────────

# Dignity strength tier for cross-check comparisons
_DIGNITY_STRENGTH_TIER: dict[str, int] = {
    "exalted": 3, "uccha": 3,
    "own": 2, "mooltrikona": 2,
    "friend": 1, "mitra": 1,
    "neutral": 0,
    "enemy": -1, "shatru": -1,
    "debilitated": -2, "neecha": -2,
    "friend (neecha bhanga)": 1,  # pyjhora sometimes emits this
}


def _dignity_tier(text: str) -> int:
    return _DIGNITY_STRENGTH_TIER.get((text or "neutral").lower().strip(), 0)


def _build_d1_dignity_map(
    conn: Any, chart_id: str, ayanamsha_id: str
) -> dict[str, tuple[str, str | None]]:
    """graha (long name, e.g. 'Sun') → (D1 dignity text, fact_id | None).

    Uses chart_facts.graha_dignity_per_varga filtered on varga='D1'.
    fact_subject format: 'D1_SUN', 'D1_MOON' …  — we map to long names via
    a lookup so we can join with chart_divisionals.graha which uses long names.

    Returns a tuple per graha so callers can cite the L1 fact_id in
    constituent_facts_array (B2 governance mandate: every L2 signal must
    cite the L1 fact IDs it consumes).
    """
    # Values sourced from the graha SSoT (brahmagyan/graha_vocabulary.to_title)
    # rather than hardcoded literals — ADHIṢṬHĀNA Lane A2. Kept as a local
    # dict (not a direct to_title() call) so `.get()` preserves None-on-miss
    # for any unexpected fact_subject shape (to_title() never returns None).
    short_to_long = {
        code: to_title(code)
        for code in (
            "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT",
            "RAH_MEAN", "KET_MEAN",
        )
    }
    rows = _fetch_dict(conn,
        """SELECT fact_id, fact_subject, fact_value_text FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='graha_dignity_per_varga'
             AND fact_value_jsonb->>'varga' = 'D1'""",
        [chart_id, ayanamsha_id])
    d1: dict[str, tuple[str, str | None]] = {}
    for r in rows:
        subj = str(r.get("fact_subject") or "").removeprefix("D1_")
        long_name = short_to_long.get(subj)
        if long_name and long_name not in d1:
            dignity_text = str(r.get("fact_value_text") or "neutral")
            fact_id = str(r.get("fact_id")) if r.get("fact_id") is not None else None
            d1[long_name] = (dignity_text, fact_id)
    return d1


def _build_d9_dignity_map(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, str]:
    """graha (long name, e.g. 'Sun') → D9 dignity text, from chart_divisionals."""
    rows = _fetch_dict(conn,
        """SELECT graha, fact_value_text FROM chart_divisionals
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND varga = 'D9' AND fact_key = 'dignity'""",
        [chart_id, ayanamsha_id])
    d9: dict[str, str] = {}
    for r in rows:
        graha = str(r.get("graha") or "")
        if graha and graha not in d9:
            d9[graha] = str(r.get("fact_value_text") or "neutral")
    return d9


# R6A.3: salience-boost value for a classically CANCELLED debility, per the
# ratified semantics documented on bodha_writers/formulas.py SalienceInputs /
# SalienceInputsV2 ("neechabhanga_modifier: 1.0 normal / 1.3 cancelled debility").
# formulas.py is frozen — this feeds its documented value, it does not re-pick it.
_NEECHABHANGA_CANCELLED_MODIFIER = 1.3
_NEECHABHANGA_NORMAL_MODIFIER = 1.0

# Y-13 fix (R6A.3 fix-iteration): single shared classification constant used by
# BOTH the D1-context redemption path and the D9-context broken_promise
# redemption path — mandatory-test (d) asserts the two branches emit literally
# this same value (no typo'd near-duplicate; this is the exact string already
# shipped by the merged D1-context path, proven in production).
_CLASSIFICATION_NEECHA_BHANGA_REDEEMED = "neecha_bhanga_redeemed"


def _build_nbry_redemption_map(
    conn: Any, chart_id: str, ayanamsha_id: str
) -> dict[str, dict[str, str | None]]:
    """graha (long name, e.g. 'Saturn') → NBRY redemption record for grahas whose
    D1 debilitation is classically CANCELLED (neecha-bhanga) per L1.

    R6A.3 architecture rule (§N.5 — L1 is the authority over L2+ derivations):
    this writer must NOT recompute neecha-bhanga. It consults the ONE source of
    truth — the `ga_yoga_firings` row written by ga_yoga_writer's R6A.1 NBRY
    evaluator (`yoga_canonical_id='neecha_bhanga_raja_yoga'`, `bhanga_active=TRUE`).

    Redeemed grahas are parsed from `bhanga_rule_fired`, whose R6A.1 format is
    ';'-joined `<planet>@<varga_ctx>:<rule_id>` entries (varga_ctx ∈ D1, D9,
    D1->D9). Only D1-context entries (D1 or D1->D9) count here, because the O3
    cross-check classifies the graha's **D1** dignity — a pure-D9 debilitation
    redemption does not redeem the D1 side. `constituent_planets` is NOT used
    for membership: it includes supporting (canceller) planets like the Sun,
    which are not themselves debilitated.

    Returns {} when no NBRY row exists (uncancelled debilitations stay
    uncancelled — the negative-control contract).
    """
    rows = _fetch_dict(conn,
        """SELECT bhanga_rule_fired, citation_ref, citation_human
           FROM ga_yoga_firings
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND yoga_canonical_id='neecha_bhanga_raja_yoga'
             AND bhanga_active IS TRUE""",
        [chart_id, ayanamsha_id])
    lower_to_long = {k.lower(): k for k in _LONG_TO_SHORT}
    redemption: dict[str, dict[str, str | None]] = {}
    for r in rows:
        rule_fired = str(r.get("bhanga_rule_fired") or "")
        for entry in rule_fired.split(";"):
            entry = entry.strip()
            if "@" not in entry or ":" not in entry:
                continue  # defensive: malformed entry — never guess a redemption
            planet_part, rest = entry.split("@", 1)
            varga_ctx, rule_id = rest.split(":", 1)
            if not varga_ctx.startswith("D1"):
                continue  # pure-D9 finding — does not redeem the D1 dignity
            long_name = lower_to_long.get(planet_part.strip().lower())
            if not long_name:
                continue
            rec = redemption.setdefault(long_name, {
                "bhanga_rules_fired": "",
                "citation_ref": r.get("citation_ref"),
                "citation_human": r.get("citation_human"),
            })
            rec["bhanga_rules_fired"] = (
                f"{rec['bhanga_rules_fired']};{entry}".strip(";")
            )
    return redemption


def _build_nbry_d9_redemption_map(
    conn: Any, chart_id: str, ayanamsha_id: str
) -> dict[str, dict[str, str | None]]:
    """graha (long name) → NBRY redemption record for grahas whose **D9-varga**
    debilitation is classically CANCELLED per L1 (pure-`D9`-context entries in
    `ga_yoga_firings.bhanga_rule_fired`).

    Y-13 fix (R6A.3 fix-iteration) — general rule: redemption must be consulted
    IN THE VARGA WHERE THE WEAKNESS LIVES. `broken_promise` is the D1-strong ×
    D9-weak case; the weakness being judged is the **D9** debilitation, so its
    classically-relevant redemption is a pure-`D9`-context NBRY firing (the D9
    debilitation redeemed within D9 itself). Such a graha can never have a
    D1-context firing (nothing is debilitated in D1), which is why the D1-only
    map above structurally could never redeem a broken_promise candidate.

    Kept as a SEPARATE map from `_build_nbry_redemption_map` (whose D1-context
    role is unchanged): this map is consulted ONLY inside the broken_promise
    formation branch of `_build_navamsha_cross_check_signals`. Entries with
    varga_ctx `D1` or `D1->D9` are excluded here — those belong to the D1 map.

    Returns {} when no NBRY row exists (unredeemed D9 debilitations stay
    broken_promise — the negative-control contract).
    """
    rows = _fetch_dict(conn,
        """SELECT bhanga_rule_fired, citation_ref, citation_human
           FROM ga_yoga_firings
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND yoga_canonical_id='neecha_bhanga_raja_yoga'
             AND bhanga_active IS TRUE""",
        [chart_id, ayanamsha_id])
    lower_to_long = {k.lower(): k for k in _LONG_TO_SHORT}
    redemption: dict[str, dict[str, str | None]] = {}
    for r in rows:
        rule_fired = str(r.get("bhanga_rule_fired") or "")
        for entry in rule_fired.split(";"):
            entry = entry.strip()
            if "@" not in entry or ":" not in entry:
                continue  # defensive: malformed entry — never guess a redemption
            planet_part, rest = entry.split("@", 1)
            varga_ctx, rule_id = rest.split(":", 1)
            if varga_ctx.strip() != "D9":
                continue  # D1 / D1->D9 findings belong to the D1-context map
            long_name = lower_to_long.get(planet_part.strip().lower())
            if not long_name:
                continue
            rec = redemption.setdefault(long_name, {
                "bhanga_rules_fired": "",
                "citation_ref": r.get("citation_ref"),
                "citation_human": r.get("citation_human"),
            })
            rec["bhanga_rules_fired"] = (
                f"{rec['bhanga_rules_fired']};{entry}".strip(";")
            )
    return redemption


def _build_navamsha_cross_check_signals(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    now: str,
    strength_lookup: dict,
    dignity_lookup: dict,
    av_lookup: dict,
) -> list[dict]:
    """O3: Emit D1×D9 cross-check signals (~9 grahas × 1 ayanamsha = ~9 signals).

    Classical basis (Parashari Hora Shastra):
    - D1 debilitated but classically CANCELLED per the L1 NBRY evaluator
      (ga_yoga_firings, R6A.1) → 'neecha_bhanga_redeemed' (checked FIRST —
      a redeemed debility is never classified from raw dignity tiers alone)
    - D1 strong + D9 weak → 'broken_promise' (natal potential undermined by
      navamsha) — UNLESS the D9 debilitation is itself classically CANCELLED
      per a pure-D9-context NBRY firing (Y-13 fix: redemption is consulted in
      the varga where the weakness lives) → 'neecha_bhanga_redeemed'
    - D1 weak + D9 strong → 'vargottama_resilience' (neechabhanga-grade uplift)
    - Both strong / both weak → 'concordant_strong' / 'concordant_weak'
    """
    d1_map = _build_d1_dignity_map(conn, chart_id, ayanamsha_id)
    d9_map = _build_d9_dignity_map(conn, chart_id, ayanamsha_id)
    # R6A.3: L1 neecha-bhanga verdicts, loaded ONCE per (chart, ayanamsha) —
    # same build-lookup-then-loop pattern as the two dignity maps above.
    nbry_map = _build_nbry_redemption_map(conn, chart_id, ayanamsha_id)
    # Y-13 fix: pure-D9-context redemptions, consulted ONLY inside the
    # broken_promise formation branch below (varga-of-weakness rule).
    nbry_d9_map = _build_nbry_d9_redemption_map(conn, chart_id, ayanamsha_id)

    graha_names = set(d1_map.keys()) | set(d9_map.keys())
    signals: list[dict] = []

    for graha in sorted(graha_names):
        # d1_map values are (dignity_text, fact_id | None) tuples (B2-fix)
        d1_tuple = d1_map.get(graha, ("neutral", None))
        d1_text, d1_fact_id = d1_tuple
        d9_text = d9_map.get(graha, "neutral")
        d1_tier = _dignity_tier(d1_text)
        d9_tier = _dignity_tier(d9_text)

        # R6A.3: consult L1's neecha-bhanga verdict BEFORE any tier-based
        # classification. If ga_yoga_firings records an active D1-context
        # bhanga for this graha, its debilitation is classically cancelled —
        # the raw dignity tiers must not classify it as a weakness pattern.
        nbry_redemption = nbry_map.get(graha)

        # Y-13 fix bookkeeping: the redemption record (if any) that this
        # graha's classification defers to, and the varga where the redeemed
        # weakness lives. The two consults are tier-disjoint by construction:
        # the early D1-context branch handles D1-weak grahas; the D9-context
        # consult is reachable only when d1_tier >= 2 (D1-strong).
        redemption_record = nbry_redemption
        redeemed_weakness_varga: str | None = None

        # Classify
        if nbry_redemption is not None:
            classification = _CLASSIFICATION_NEECHA_BHANGA_REDEEMED
            valence = "benefic"
            salience_base = 1.6  # neechabhanga-grade uplift (parity with vargottama_resilience)
        elif d1_tier >= 2 and d9_tier <= -1:
            # Y-13 fix: broken_promise judges the D9 weakness — consult the
            # redemption IN THE VARGA WHERE THE WEAKNESS LIVES (pure-D9-context
            # NBRY firing). Behavior-gated to this branch only.
            d9_redemption = nbry_d9_map.get(graha)
            if d9_redemption is not None:
                classification = _CLASSIFICATION_NEECHA_BHANGA_REDEEMED
                valence = "benefic"
                salience_base = 1.6  # parity with the D1-context redeemed path
                redemption_record = d9_redemption
                redeemed_weakness_varga = "D9"
            else:
                classification = "broken_promise"
                valence = "malefic"
                salience_base = 1.8  # high — classically significant warning
        elif d1_tier <= -1 and d9_tier >= 1:
            classification = "vargottama_resilience"
            valence = "benefic"
            salience_base = 1.6
        elif d1_tier >= 2 and d9_tier >= 1:
            classification = "concordant_strong"
            valence = "benefic"
            salience_base = 2.0  # strongest — D9 confirms D1 strength
        elif d1_tier <= -1 and d9_tier <= -1:
            classification = "concordant_weak"
            valence = "malefic"
            salience_base = 1.2
        else:
            classification = "mixed"
            valence = "neutral"
            salience_base = 0.6

        # signal_type_id truncated to 80 chars
        signal_type_id = f"navamsha_d9_cross_check:{graha.lower()}"[:80]

        config = {
            "graha": graha,
            "d1_dignity": d1_text,
            "d9_dignity": d9_text,
            "d1_tier": d1_tier,
            "d9_tier": d9_tier,
            "classification": classification,
        }
        if redemption_record is not None:
            # Provenance of the L1 verdict this classification defers to.
            config["neecha_bhanga"] = {
                "source": "ga_yoga_firings/neecha_bhanga_raja_yoga",
                "bhanga_rules_fired": redemption_record.get("bhanga_rules_fired"),
                "citation_ref": redemption_record.get("citation_ref"),
            }
            if redeemed_weakness_varga is not None:
                # Y-13 fix: the redeemed weakness lives in D9 (broken_promise
                # path). Key added ONLY on this path — the D1-context path's
                # provenance block stays byte-identical to pre-fix output.
                config["neecha_bhanga"]["redeemed_weakness_varga"] = (
                    redeemed_weakness_varga
                )

        headline = (
            f"D9 cross-check: {graha} D1={d1_text} × D9={d9_text} "
            f"→ {classification}"
        )
        summary = (
            f"category=navamsha_d9_cross_check | key={graha.lower()} | "
            f"d1_dignity={d1_text} | d9_dignity={d9_text} | "
            f"classification={classification} | valence={valence}"
        )

        epistemic_jsonb = json.dumps({
            "tradition_agreement_state": "single",
            "epistemic_tier": "documented_approximation",
            "computation_vs_interpretation": "computation",
        })

        # Salience: base × minor house weight for house=1 default
        computed_salience = round(salience_base, 6)

        row: dict = {
            "signal_id":                                str(uuid.uuid4()),
            "chart_id":                                 chart_id,
            "ayanamsha_id":                             ayanamsha_id,
            "build_id":                                 build_id,
            "signal_type_id":                           signal_type_id,
            "signal_type_class":                        "varga_pattern",
            "signal_tradition":                         "parashari",
            "fact_kind":                                "configuration",
            "source_l1_asset":                          "ga_divisionals",
            "source_subsystem":                         "varga",
            "signal_summary_text":                      summary,
            "signal_headline_text":                     headline,
            "classical_sources_jsonb":                  None,
            "varga_id":                                 "D9",
            "varga_provenance_jsonb":                   None,
            "epistemic_tier":                           "documented_approximation",
            "epistemic_jsonb":                          epistemic_jsonb,
            "salience_conditioned_by_jsonb":            None,
            "signature_tier":                           _signature_tier(computed_salience),
            "valence":                                  valence,
            "lel_origin":                               False,
            "configuration_jsonb":                      json.dumps(config),
            # B2-fix: cite the D1 dignity fact_id from chart_facts when available.
            # D9 data comes from chart_divisionals which has no fact_id column,
            # so only the D1 side is traceable to a chart_facts row.
            "constituent_facts_array":                  ([d1_fact_id] if d1_fact_id else []),
            "constituent_signals_array":                None,
            "classical_sources_array":                  None,
            "source_corroboration_count_by_text":       2,
            "source_corroboration_count_by_verse":      None,
            "orb_tightness":                            1.0,
            "shadbala_norm":                            strength_lookup.get(_LONG_TO_SHORT.get(graha, graha), 1.0),
            "dignity_score":                            _DIGNITY_SCORE.get(d1_text.lower(), 0.5),
            "deterministic_strength":                   salience_base,
            "verification_certainty":                   round(
                min(math.log(1 + 2) / math.log(10), 1.0), 6
            ),
            "divisional_corroboration_count":           None,
            "dasha_activation_proximity_score":         None,
            "house_weight_multiplier":                  1.0,
            "ashtakavarga_support_multiplier":          1.0,
            "aspect_modifier":                          None,
            "vargottama_amplification":                 0.0,
            "argala_modifier":                          None,
            # R6A.3: real values, per formulas.py's ratified semantics
            # ("1.0 normal / 1.3 cancelled debility" — SalienceInputs/V2).
            # cancellation_modifier stays 1.0: it means "cancelled YOGA"
            # (0.1), and a redeemed debility is not a cancelled yoga.
            # Y-13 fix: keyed off redemption_record so the D9-context-redeemed
            # broken_promise path also carries the cancelled-debility value —
            # identical to nbry_redemption for every non-flipping row.
            "neechabhanga_modifier":                    (
                _NEECHABHANGA_CANCELLED_MODIFIER
                if redemption_record is not None
                else _NEECHABHANGA_NORMAL_MODIFIER
            ),
            "cancellation_modifier":                    1.0,
            "computed_salience":                        computed_salience,
            "salience_formula_version":                 "v1.0",
            "salience_confidence_interval_jsonb":       None,
            "domains_affected_array":                   ["career", "character"],
            "domain_salience_jsonb":                    json.dumps({
                "career": round(computed_salience / 2, 6),
                "character": round(computed_salience / 2, 6),
            }),
            "shared_factor_keys_jsonb":                 None,
            "cross_domain_shared_factor_count":         None,
            "graph_edge_pattern_jsonb":                 None,
            "graph_node_strength_contribution_jsonb":   None,
            "relationship_classification":              None,
            "graha_weakness_indicators_jsonb":          None,
            "remedy_hooks_array":                       (
                ["navamsha_d9_cross_check"] if valence == "malefic" else None
            ),
            "recurring_pattern_marker":                 None,
            "top_k_salience_rank":                      None,
            "system_convergence_count":                 None,
            "signature_class":                          _signature_class("varga_pattern"),
            "contradicts_signals_array":                None,
            "active_duration_class":                    "natal_permanent",
            "active_dasha_periods_jsonb":               None,
            "activation_predicted_dates_jsonb":         None,
            "predicted_outcome_class":                  None,
            "cross_ayanamsha_consistency_score":        None,
            "strength_normalized_to_chart_max":         None,
            "pada_precision_flag":                      None,
            "cross_system_consensus_count":             None,
            "channel_render_priority_jsonb":            None,
            "verification_pass_status":                 "documented_approximation",
            "verification_method":                      "L1_divisional_cross_check",
            "citation_ref":                             f"chart_divisionals/D9/{graha}",
            "citation_human":                           (
                f"Navamsha D9 cross-check: {graha} "
                f"D1={d1_text} × D9={d9_text} → {classification}"
            ),
            "computed_at":                              now,
            "engine_version":                           ENGINE_VERSION,
            # Night-1 Lane 4 (migration 367): O3 navamsha signals are not per-varga
            # aspect/lord facts in the CR-82 sense (no ratification applies) and are
            # not consulted by ga_vichara's valence_pass — keyword heuristic already
            # assigned `valence` above via classification-derived logic, so tag it
            # the same way every other keyword-derived valence is tagged.
            "ratification_factor":                      None,
            "valence_source":                            "keyword_heuristic_v1",
        }
        signals.append(row)

    return signals


# ── INSERT SQL (includes all enriched spine columns) ─────────────────────────

_INSERT_SQL = """
INSERT INTO bodha_msr_signals (
  signal_id, chart_id, ayanamsha_id, build_id,
  signal_type_id, signal_type_class, signal_tradition,
  fact_kind, source_l1_asset, source_subsystem,
  signal_summary_text, signal_headline_text,
  classical_sources_jsonb, varga_id, varga_provenance_jsonb,
  epistemic_tier, epistemic_jsonb, salience_conditioned_by_jsonb,
  signature_tier, valence, lel_origin,
  configuration_jsonb, constituent_facts_array, constituent_signals_array,
  classical_sources_array, source_corroboration_count_by_text, source_corroboration_count_by_verse,
  orb_tightness, shadbala_norm, dignity_score,
  deterministic_strength, verification_certainty,
  divisional_corroboration_count, dasha_activation_proximity_score,
  house_weight_multiplier, ashtakavarga_support_multiplier,
  aspect_modifier, vargottama_amplification, argala_modifier,
  neechabhanga_modifier, cancellation_modifier,
  computed_salience, salience_pctl_in_class, salience_formula_version, salience_confidence_interval_jsonb,
  domains_affected_array, domain_salience_jsonb,
  shared_factor_keys_jsonb, cross_domain_shared_factor_count,
  graph_edge_pattern_jsonb, graph_node_strength_contribution_jsonb, relationship_classification,
  graha_weakness_indicators_jsonb, remedy_hooks_array, recurring_pattern_marker,
  top_k_salience_rank, system_convergence_count, signature_class,
  contradicts_signals_array, active_duration_class,
  active_dasha_periods_jsonb, activation_predicted_dates_jsonb, predicted_outcome_class,
  cross_ayanamsha_consistency_score, strength_normalized_to_chart_max,
  pada_precision_flag, cross_system_consensus_count, channel_render_priority_jsonb,
  verification_pass_status, verification_method,
  citation_ref, citation_human, computed_at, engine_version,
  ratification_factor, valence_source
) VALUES (
  %(signal_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(signal_type_id)s, %(signal_type_class)s, %(signal_tradition)s,
  %(fact_kind)s, %(source_l1_asset)s, %(source_subsystem)s,
  %(signal_summary_text)s, %(signal_headline_text)s,
  %(classical_sources_jsonb)s::jsonb, %(varga_id)s, %(varga_provenance_jsonb)s::jsonb,
  %(epistemic_tier)s, %(epistemic_jsonb)s::jsonb, %(salience_conditioned_by_jsonb)s::jsonb,
  %(signature_tier)s, %(valence)s, %(lel_origin)s,
  %(configuration_jsonb)s::jsonb, %(constituent_facts_array)s, %(constituent_signals_array)s,
  %(classical_sources_array)s, %(source_corroboration_count_by_text)s, %(source_corroboration_count_by_verse)s,
  %(orb_tightness)s, %(shadbala_norm)s, %(dignity_score)s,
  %(deterministic_strength)s, %(verification_certainty)s,
  %(divisional_corroboration_count)s, %(dasha_activation_proximity_score)s,
  %(house_weight_multiplier)s, %(ashtakavarga_support_multiplier)s,
  %(aspect_modifier)s, %(vargottama_amplification)s, %(argala_modifier)s,
  %(neechabhanga_modifier)s, %(cancellation_modifier)s,
  %(computed_salience)s, %(salience_pctl_in_class)s, %(salience_formula_version)s, %(salience_confidence_interval_jsonb)s::jsonb,
  %(domains_affected_array)s, %(domain_salience_jsonb)s::jsonb,
  %(shared_factor_keys_jsonb)s, %(cross_domain_shared_factor_count)s,
  %(graph_edge_pattern_jsonb)s, %(graph_node_strength_contribution_jsonb)s, %(relationship_classification)s,
  %(graha_weakness_indicators_jsonb)s, %(remedy_hooks_array)s, %(recurring_pattern_marker)s,
  %(top_k_salience_rank)s, %(system_convergence_count)s, %(signature_class)s,
  %(contradicts_signals_array)s, %(active_duration_class)s,
  %(active_dasha_periods_jsonb)s::jsonb, %(activation_predicted_dates_jsonb)s::jsonb, %(predicted_outcome_class)s,
  %(cross_ayanamsha_consistency_score)s, %(strength_normalized_to_chart_max)s,
  %(pada_precision_flag)s, %(cross_system_consensus_count)s, %(channel_render_priority_jsonb)s::jsonb,
  %(verification_pass_status)s, %(verification_method)s,
  %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s,
  %(ratification_factor)s, %(valence_source)s
)
ON CONFLICT (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb)
DO NOTHING
"""

_BATCH_SIZE = 200


def _batch_insert(conn: Any, rows: list[dict]) -> int:
    """Batch insert using executemany (one round-trip per batch). Transaction owned by orchestrator — no commit here."""
    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i : i + _BATCH_SIZE]
            # BUGFIX (Night-1 guardian rebuild): the batch executemany() itself must run
            # inside its own SAVEPOINT. Without this, a constraint violation (e.g. a
            # NOT NULL violation on one bad row) aborts the ambient orchestrator-owned
            # transaction BEFORE the per-row fallback below ever runs — so the fallback's
            # "SAVEPOINT row_sp" call fails too (no savepoint predates the abort to roll
            # back to), surfacing a confusing "savepoint does not exist" error that masks
            # the real one. Wrapping the batch attempt in "batch_sp" first means a failure
            # cleanly rolls back to a real, already-established savepoint, leaving the
            # transaction usable for the per-row retry loop.
            try:
                cur.execute("SAVEPOINT batch_sp")
                cur.executemany(_INSERT_SQL, batch)
                # BUGFIX: capture rowcount BEFORE issuing RELEASE SAVEPOINT — rowcount
                # reflects only the LAST statement executed on the cursor, so reading it
                # after a subsequent RELEASE SAVEPOINT (a transaction-control statement,
                # not a DML statement) clobbers it to 0/-1, silently under-reporting every
                # successful batch. This under-reporting is what caused rows_written=0
                # ('dormant' asset state) despite the INSERTs themselves succeeding.
                batch_rowcount = cur.rowcount
                cur.execute("RELEASE SAVEPOINT batch_sp")
                inserted += max(0, batch_rowcount)
            except Exception as batch_exc:
                cur.execute("ROLLBACK TO SAVEPOINT batch_sp")
                cur.execute("RELEASE SAVEPOINT batch_sp")
                # Fallback: per-row insert to skip any single bad row
                logger.warning("[bo_laksana] batch at %d failed (%s), falling back to per-row insert",
                                i, batch_exc)
                for row in batch:
                    try:
                        cur.execute("SAVEPOINT row_sp")
                        cur.execute(_INSERT_SQL, row)
                        row_rowcount = cur.rowcount  # capture before RELEASE (same bugfix as above)
                        cur.execute("RELEASE SAVEPOINT row_sp")
                        inserted += max(0, row_rowcount)
                    except Exception as row_exc:
                        cur.execute("ROLLBACK TO SAVEPOINT row_sp")
                        cur.execute("RELEASE SAVEPOINT row_sp")
                        logger.warning("[bo_laksana] skipping row signal_type_id=%s: %s",
                                       row.get("signal_type_id"), row_exc)
            if inserted % 2000 == 0 or i + _BATCH_SIZE >= len(rows):
                logger.info("[bo_laksana] inserted %d/%d signals", inserted, len(rows))
    return inserted


def _set_top_k_ranks(rows: list[dict]) -> None:
    """Rank rows by computed_salience DESC in place — all rows get a rank."""
    for rank, row in enumerate(
        sorted(rows, key=lambda r: r["computed_salience"], reverse=True), start=1
    ):
        row["top_k_salience_rank"] = rank


def _normalize_by_chart_max(rows: list[dict]) -> None:
    """Set strength_normalized_to_chart_max in place."""
    if not rows:
        return
    max_sal = max(r["computed_salience"] for r in rows) or 1.0
    for row in rows:
        row["strength_normalized_to_chart_max"] = round(row["computed_salience"] / max_sal, 6)


def _set_salience_pctl_in_class(rows: list[dict]) -> None:
    """Set salience_pctl_in_class in place — the in-memory equivalent of
    PERCENT_RANK() OVER (PARTITION BY chart_id, ayanamsha_id, signal_type_class
    ORDER BY computed_salience). Rows here are already scoped to a single
    (chart_id, ayanamsha_id) — the writer processes one ayanamsha per substep —
    so partitioning by signal_type_class alone is equivalent.

    BA-P3 (2026-07-06): replaces a post-insert `UPDATE bodha_msr_signals SET
    salience_pctl_in_class = ...` that ran pathologically long (600s+, CPU/IO
    bound, no lock) because updating one scalar column on ~28K freshly-inserted
    rows forces a full-row rewrite against this table's 20 indexes (incl. 3 GIN
    on jsonb arrays). Computing it here from the rows already in memory writes
    the value in the single INSERT pass — zero extra DB work. PERCENT_RANK uses
    RANK() (ties share the minimum rank); a single-row partition is 0.0.
    """
    from collections import defaultdict
    by_class: dict[Any, list[dict]] = defaultdict(list)
    for row in rows:
        by_class[row.get("signal_type_class")].append(row)
    for cls_rows in by_class.values():
        n = len(cls_rows)
        if n <= 1:
            for row in cls_rows:
                row["salience_pctl_in_class"] = 0.0
            continue
        # RANK with ties sharing the minimum rank: in ascending order, the rank of
        # a value is 1 + (count of rows with strictly smaller computed_salience),
        # i.e. the 1-based index of that value's first occurrence.
        ordered = sorted(cls_rows, key=lambda r: r["computed_salience"])
        rank_by_salience: dict[Any, int] = {}
        for i, row in enumerate(ordered):
            sal = row["computed_salience"]
            if sal not in rank_by_salience:
                rank_by_salience[sal] = i + 1
        for row in cls_rows:
            rank = rank_by_salience[row["computed_salience"]]
            row["salience_pctl_in_class"] = round((rank - 1) / (n - 1), 6)


# ── WriterBase subclass ───────────────────────────────────────────────────────

@register("bo_laksana")
class BoLaksanaWriter(WriterBase):
    """
    bo_laksana v2.1: MSR Signal Store — category-agnostic projection of ALL L1 chart_facts.

    B2-fix: lookup builders now use fact_subject (not fact_key) for graha resolution,
    correct varga='D1' filter for dignity, and ashtakavarga_bindu SARVA-HOUSE_N for AV.
    B3-fix: yoga/dosha signals get configuration_jsonb.graha populated (CONTRACT-1 with A2).
    O3: emits Navamsha D9 cross-check signals per ayanamsha.

    HEAVY writer: one sub-step per ayanamsha.
    Each sub-step:
    1. Builds strength/dignity/AV lookup dicts from L1 data (fixed to use fact_subject).
    2. Fetches ALL chart_facts rows for the ayanamsha (no category filter).
    3. Builds one bodha_msr_signals row per fact row with ALL enriched spine columns.
    4. Appends Navamsha D9 cross-check signals (O3).
    5. Ranks by salience; normalizes by chart max.
    6. DELETE-then-INSERT (idempotent per replace_prior_msr_for_chart).
    """
    asset_id     = "bo_laksana"
    has_substeps = True

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(key=f"aya_{aya}", label=f"bo_laksana — {aya}")
            for aya in CANONICAL_AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_msr_for_chart

        chart_id  = ctx.config["chart_id"]
        build_id  = ctx.build_id
        ayanamsha = step.key.removeprefix("aya_")
        conn      = ctx.db_conn
        now       = datetime.now(timezone.utc).isoformat()

        # Role-default statement_timeout=30s is sized for OLTP queries; the full
        # category-agnostic chart_facts scan below (_fetch_all_facts, ~27k rows)
        # can exceed it under concurrent multi-asset load (observed live:
        # QueryCanceled on this exact substep during a wave-parallel rebuild,
        # 2026-07-10). SET LOCAL scopes to this transaction/savepoint only and
        # reverts automatically on commit/rollback — the same pattern already
        # used by every other heavy per-chart writer in this codebase
        # (ka_taranga, ph_pramana, ka_yojaka, etc.); bo_laksana was simply
        # missing it despite being the heaviest L2 Bodha root writer.
        with conn.cursor() as _timeout_cur:
            _timeout_cur.execute("SET LOCAL statement_timeout = 0")

        if ctx.dry_run:
            facts = _fetch_all_facts(conn, chart_id, ayanamsha)
            invariant = _fetch_invariant_facts(conn, chart_id)
            total = len(facts) + len(invariant)
            logger.info("[bo_laksana dry_run] %s — would project %d facts (%d INVARIANT)",
                        ayanamsha, total, len(invariant))
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run:{ayanamsha}:{total}_facts")

        # Build L1 lookup dicts for salience inputs
        strength_lookup = _build_strength_lookup(conn, chart_id, ayanamsha)
        dignity_lookup  = _build_dignity_lookup(conn, chart_id, ayanamsha)
        av_lookup       = _build_av_lookup(conn, chart_id, ayanamsha)

        # Night-1 Lane 4 — Change 1 (CR-81): activated class priors.
        class_priors = _load_class_priors(conn)
        # Night-1 Lane 4 — Change 2/3 (CR-82→CR-65, CR-83): ga_vichara-backed
        # lookups (ga_vichara/chart_vichara shipped 2026-07-14; reconciled
        # 2026-07-15, D-1.5a A2/CR-91). Both degrade to ({}, False) whenever
        # chart_vichara is unavailable for THIS chart (per-chart defensive
        # degradation, not a permanent block); every downstream consumer
        # already handles the empty-lookup case honestly.
        ratification_lookup, ratification_available = _load_varga_ratification(conn, chart_id, ayanamsha)
        vichara_valence_lookup, vichara_valence_available = _load_vichara_valence(conn, chart_id, ayanamsha)

        # Fetch ALL fact rows for this ayanamsha (category-agnostic).
        # C3-fix: INVARIANT rows are fetched separately and appended so each
        # ayanamsha sub-step processes them exactly once (previously they were
        # included via IN (%s, 'INVARIANT') → 5× duplicate signals).
        fact_rows = _fetch_all_facts(conn, chart_id, ayanamsha)
        invariant_rows = _fetch_invariant_facts(conn, chart_id)
        fact_rows = fact_rows + invariant_rows
        logger.info("[bo_laksana] %s — fetched %d fact rows (%d INVARIANT)",
                    ayanamsha, len(fact_rows), len(invariant_rows))

        if not fact_rows:
            raise RuntimeError(
                f"[bo_laksana] G3: chart_id={chart_id} ayanamsha={ayanamsha} — "
                "chart_facts is empty; L1 (Gaṇita) must be built before Bodha"
            )

        # WP-2.4 (9b-5 / §N.5): authoritative resolvable fact_id set for this chart.
        valid_fact_ids = _fetch_valid_fact_ids(conn, chart_id)

        # WP-2.4 (9b-1): de-flood per-varga families BEFORE per-row emission.
        # Passthrough rows emit 1:1; oversized (category × varga) groups collapse
        # to one aggregate row each (constituents preserve full traceability).
        pre_flood = len(fact_rows)
        fact_rows, aggregate_rows = _partition_flood(fact_rows)
        fact_rows = fact_rows + aggregate_rows
        logger.info(
            "[bo_laksana] %s — flood cap: %d fact rows → %d after de-flood "
            "(%d aggregate rollups)",
            ayanamsha, pre_flood, len(fact_rows), len(aggregate_rows),
        )

        # Classical bridge (P3B fix): bulk-preload catalog/rule lookups + validate
        # referenced chunk_ids once per sub-step — no per-row query storm.
        yoga_ids, dosha_ids, yoga_rule_ids = _build_classical_catalog_lookup(conn)
        referenced_chunk_ids = _collect_referenced_chunk_ids(fact_rows)
        valid_chunk_ids = _validate_chunk_ids(conn, referenced_chunk_ids)
        classical_catalog = (yoga_ids, dosha_ids, yoga_rule_ids, valid_chunk_ids)

        # Build signal rows
        signal_rows: list[dict] = []
        skipped = 0
        for fact_row in fact_rows:
            try:
                row = _build_signal_row(
                    fact_row, chart_id, build_id,
                    strength_lookup, dignity_lookup, av_lookup, now,
                    ayanamsha_override=ayanamsha,
                    classical_catalog=classical_catalog,
                    valid_fact_ids=valid_fact_ids,
                    class_priors=class_priors,
                    ratification_lookup=ratification_lookup,
                    vichara_valence_lookup=vichara_valence_lookup,
                )
                signal_rows.append(row)
            except Exception as exc:
                logger.warning("[bo_laksana] skipping fact %s (%s): %s",
                               fact_row.get("fact_id"), fact_row.get("fact_category"), exc)
                skipped += 1

        logger.info("[bo_laksana] %s — built %d rows (%d skipped)", ayanamsha, len(signal_rows), skipped)

        if not signal_rows:
            raise RuntimeError(
                f"[bo_laksana] G3: chart_id={chart_id} ayanamsha={ayanamsha} — "
                f"all {len(fact_rows)} facts were skipped; no MSR signals produced"
            )

        # O3: Append Navamsha D9 cross-check signals
        # SAVEPOINT-guarded (same fix as salience_pctl_in_class below): a DB error inside
        # this best-effort lookup would otherwise leave the connection in Postgres's
        # aborted-transaction state with no ROLLBACK, poisoning every statement after it.
        sp_nav = "sp_bo_laksana_navamsha"
        try:
            with conn.cursor() as _sp_cur:
                _sp_cur.execute(f"SAVEPOINT {sp_nav}")
            navamsha_signals = _build_navamsha_cross_check_signals(
                conn, chart_id, ayanamsha, build_id, now,
                strength_lookup, dignity_lookup, av_lookup,
            )
            signal_rows.extend(navamsha_signals)
            with conn.cursor() as _sp_cur:
                _sp_cur.execute(f"RELEASE SAVEPOINT {sp_nav}")
            logger.info("[bo_laksana] %s — O3 navamsha cross-check: %d signals",
                        ayanamsha, len(navamsha_signals))
        except Exception as exc:
            logger.warning("[bo_laksana] %s — O3 navamsha cross-check skipped: %s",
                           ayanamsha, exc)
            try:
                with conn.cursor() as _sp_cur:
                    _sp_cur.execute(f"ROLLBACK TO SAVEPOINT {sp_nav}")
            except Exception:
                pass

        # Night-1 Lane 4 — Change 2.4 (CR-57): varga_ratification_divergence
        # signals. ga_vichara-backed — [] only when chart_vichara is
        # unavailable for this chart (per-chart degradation, table itself
        # is live since 2026-07-14).
        divergence_signals = _load_vichara_divergence_signals(conn, chart_id, ayanamsha, build_id, now)
        if divergence_signals:
            signal_rows.extend(divergence_signals)
            logger.info("[bo_laksana] %s — CR-57 divergence signals: %d",
                        ayanamsha, len(divergence_signals))

        # Post-processing: rank + normalize + in-class percentile — all computed in
        # memory on the row dicts BEFORE the insert, so salience_pctl_in_class is
        # written in the single INSERT pass (no separate post-insert UPDATE).
        _set_top_k_ranks(signal_rows)
        _normalize_by_chart_max(signal_rows)
        _set_salience_pctl_in_class(signal_rows)

        # Night-1 Lane 4 — Change 2 (CR-82→CR-65): percentile-based signature_tier,
        # replacing the old per-row varga ceiling (flood-rollup ceiling still applies,
        # stashed per-row as "_tier_ceiling" and consumed/popped here).
        _assign_tiers_by_percentile(signal_rows)

        # ── D-1.5b Lane B-4 (CR-97): bhavat_bhavam_amplifier — GATED AMPLIFIER ──
        # Append-only hook; owns its own module (bodha_writers/bhavat_bhavam_amplifier.py,
        # bodha_writers/bhavat_bhavam_registry.py — the 12-cell doctrinal map). Runs AFTER
        # _assign_tiers_by_percentile (needs signature_tier to find already-salient
        # occupants) and re-runs the cheap post-processing passes on the augmented set
        # so the new rows carry a consistent top_k_salience_rank / salience_pctl_in_class /
        # strength_normalized_to_chart_max / signature_tier, same as every other row.
        # SAVEPOINT-guarded (same defensive posture as the other best-effort blocks above):
        # never a generator, never outranks its primary, never chains — see the module
        # docstring for the code-enforced restraint guards.
        sp_bb = "sp_bo_laksana_bhavat_bhavam"
        try:
            with conn.cursor() as _sp_cur:
                _sp_cur.execute(f"SAVEPOINT {sp_bb}")
            from bodha_writers.bhavat_bhavam_amplifier import (
                SalientConfig,
                compute_bhavat_bhavam_amplifiers,
                to_msr_row as _bb_to_msr_row,
                SALIENT_TIERS as _BB_SALIENT_TIERS,
                SIGNAL_TYPE_CLASS as _BB_SIGNAL_TYPE_CLASS,
            )
            bb_yoga_rows = _fetch_dict(
                conn,
                """SELECT yoga_canonical_id, constituent_houses, strength, constituent_fact_ids
                   FROM ga_yoga_firings
                   WHERE chart_id = %s AND ayanamsha_id = %s AND fired = true""",
                [chart_id, ayanamsha],
            )
            bb_candidates: list[SalientConfig] = []
            for yr in bb_yoga_rows:
                houses = yr.get("constituent_houses") or []
                if isinstance(houses, str):
                    try:
                        houses = json.loads(houses)
                    except Exception:
                        houses = []
                try:
                    strength = float(yr.get("strength") or 1.0)
                except (TypeError, ValueError):
                    strength = 1.0
                # CR-97 Bug-1 fix: real L1 derivation ledger for a yoga-sourced
                # candidate is ga_yoga_firings.constituent_fact_ids — thread it
                # through so the emitted amplifier row's constituent_facts_array
                # is a real ledger, not a fabricated NULL/empty one.
                yoga_facts = yr.get("constituent_fact_ids") or []
                if isinstance(yoga_facts, str):
                    try:
                        yoga_facts = json.loads(yoga_facts)
                    except Exception:
                        yoga_facts = []
                yoga_facts = tuple(str(f) for f in (yoga_facts or []) if f)
                for h in (houses or []):
                    try:
                        h_int = int(h)
                    except (TypeError, ValueError):
                        continue
                    if 1 <= h_int <= 12:
                        bb_candidates.append(SalientConfig(
                            identifier=str(yr.get("yoga_canonical_id")),
                            house=h_int,
                            source="yoga_firing",
                            salience_reference=strength,
                            signal_type_class="configuration",
                            ayanamsha_id=ayanamsha,
                            constituent_facts=yoga_facts,
                        ))
            for row in signal_rows:
                if row.get("signature_tier") not in _BB_SALIENT_TIERS:
                    continue
                if row.get("signal_type_class") == _BB_SIGNAL_TYPE_CLASS:
                    continue  # NO CHAINING: a prior amplifier can never itself be a candidate
                try:
                    cfg = json.loads(row.get("configuration_jsonb") or "{}")
                except Exception:
                    cfg = {}
                house_num = _parse_house_number(None, cfg)
                if house_num is None or not (1 <= house_num <= 12):
                    continue
                # CR-97 Bug-1 fix: an msr_tier candidate's own derivation ledger
                # (already resolved to L1 fact_ids by its original emitter) is the
                # real ledger for this amplifier row — thread it through rather
                # than emitting a null one.
                row_facts = row.get("constituent_facts_array") or []
                row_facts = tuple(str(f) for f in row_facts if f)
                bb_candidates.append(SalientConfig(
                    identifier=str(row.get("signal_type_id") or row.get("signal_id")),
                    house=house_num,
                    source="msr_tier",
                    salience_reference=float(row.get("computed_salience") or 0.0),
                    signal_type_class=str(row.get("signal_type_class") or "configuration"),
                    signal_id=row.get("signal_id"),
                    ayanamsha_id=ayanamsha,
                    constituent_facts=row_facts,
                ))
            bb_amplifiers = compute_bhavat_bhavam_amplifiers(bb_candidates)
            if bb_amplifiers:
                bb_rows = [_bb_to_msr_row(sig, chart_id, build_id, now) for sig in bb_amplifiers]
                signal_rows.extend(bb_rows)
                # Re-run the cheap post-processing passes on the augmented set so the
                # new rows (and, negligibly, everyone else) reflect the true full-set
                # ranks/percentiles rather than being left with placeholder None values.
                _set_top_k_ranks(signal_rows)
                _normalize_by_chart_max(signal_rows)
                _set_salience_pctl_in_class(signal_rows)
                _assign_tiers_by_percentile(signal_rows)
                logger.info("[bo_laksana] %s — CR-97 bhavat_bhavam_amplifier signals: %d",
                            ayanamsha, len(bb_rows))
            with conn.cursor() as _sp_cur:
                _sp_cur.execute(f"RELEASE SAVEPOINT {sp_bb}")
        except Exception as exc:
            logger.warning("[bo_laksana] %s — CR-97 bhavat_bhavam_amplifier skipped: %s",
                           ayanamsha, exc)
            try:
                with conn.cursor() as _sp_cur:
                    _sp_cur.execute(f"ROLLBACK TO SAVEPOINT {sp_bb}")
            except Exception:
                pass

        # Night-1 Lane 4 — Change 1 (CR-81) hit-rate report: count signals whose
        # class_prior resolved to a real brahma_class_priors row (vs. the 1.0
        # miss-default). "_class_prior_hit" is bookkeeping only — not a DB column;
        # popped here so it never reaches _batch_insert's named-param binding.
        prior_hits = 0
        distinct_nondefault_priors: set[float] = set()
        for row in signal_rows:
            if row.pop("_class_prior_hit", False):
                prior_hits += 1
            cp = row.get("class_prior")
            if cp is not None and cp != 1.0:
                distinct_nondefault_priors.add(round(float(cp), 4))
        prior_hit_rate = (prior_hits / len(signal_rows)) if signal_rows else 0.0
        if prior_hit_rate < 0.5:
            logger.warning(
                "[bo_laksana] %s — CR-81 class_prior hit-rate %.1f%% (<50%%) — "
                "the (signal_type_class, source_subsystem) join likely doesn't match "
                "brahma_class_priors' key convention; investigate before trusting "
                "class_prior as live (see bg_class_priors seed for the real key set).",
                ayanamsha, prior_hit_rate * 100,
            )

        # Idempotency: wipe prior rows for (chart_id, ayanamsha_id) that bo_laksana
        # itself owns (D-1.5b hotfix — see BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES
        # docstring: bodha_msr_signals is a shared table; a blanket delete here
        # would destroy other writers' rows, e.g. bo_sudarshana's
        # 'sudarshana_agreement' signals).
        deleted = replace_prior_msr_for_chart(
            conn, chart_id, ayanamsha, BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES,
        )
        logger.info("[bo_laksana] %s — deleted %d prior rows", ayanamsha, deleted)

        # Batch insert (salience_pctl_in_class now carried on each row — no second pass)
        inserted = _batch_insert(conn, signal_rows)

        lane4_notes = (
            f";class_prior_hit_rate={prior_hit_rate:.3f}"
            f";class_prior_distinct_nondefault={len(distinct_nondefault_priors)}"
            f";ratification_available={ratification_available}"
            f";vichara_valence_available={vichara_valence_available}"
            f";divergence_signals={len(divergence_signals)}"
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            notes=f"aya={ayanamsha};facts={len(fact_rows)};skipped={skipped}{lane4_notes}",
        )


# ═══════════════════════════════════════════════════════════════════════════
# D-2 Lane V-4 — BoLaksanaRerankWriter (CR-84 + PARK-#4 pickup)
# ═══════════════════════════════════════════════════════════════════════════
#
# Registered as a SEPARATE asset_id ('bo_laksana_rerank', migration 446) in
# THIS file (bo_laksana.py — V-4's EXCLUSIVE re-rank-pass file per
# BRIEF_D2.md Lane V-4) rather than folded into BoLaksanaWriter's own
# depends_on, because bo_karanajala already depends_on bo_laksana — adding the
# reverse edge onto bo_laksana itself would create a DAG cycle (a FROZEN-
# orchestrator-contract-class change; CLAUDE.md §N.2 says STOP and raise with
# the native rather than force it). A second @register'd WriterBase in the
# same file, scheduled strictly after bo_karanajala in the DAG via its own
# depends_on, is the extension-not-modification path §N.2 already sanctions.
#
# UPDATE-only (never delete-then-insert): it never touches row identity or
# ownership — only enriches two already-existing, previously-always-NULL
# columns (graph_node_strength_contribution_jsonb, valence/valence_source for
# the PARK-#4 subset). It is therefore safe against the bo_laksana/
# bo_sudarshana shared-table class of defect (F2 / PR#574): it can never
# delete any bodha_msr_signals row, of bo_laksana's own classes or any
# sibling's.

_SHORT_TO_LONG: dict[str, str] = {v: k for k, v in _LONG_TO_SHORT.items()}


def _extract_primary_graha_for_rerank(config: dict) -> str | None:
    """Best-effort primary-graha extraction from a signal's configuration_jsonb
    — mirrors the tag keys _resolve_valence already treats as authoritative
    (graha / primary_graha / lord / body), normalized via the SAME
    _canonical_graha_code() the rest of this file uses (no new normalization
    logic introduced)."""
    if not isinstance(config, dict):
        return None
    raw = config.get("graha") or config.get("primary_graha") or config.get("lord") or config.get("body")
    return _canonical_graha_code(raw)


def _structural_role_from_centrality(c: dict) -> float:
    """Composite structural-role multiplier from real CGM centrality metrics
    (CR-84/CR-25: closes the MSR structural_role dead link at the data layer —
    the serving-side composite_ranker.ts fallback this closes is OUT of V-4's
    may_touch glob; see migration 446's header for the full rationale).
    Blend: 40% pagerank + 25% eigenvector + 20% betweenness + 15% harmonic,
    each already normalized [0,1] by bo_karanajala, mapped onto a [0.8, 1.5]
    multiplier band (the same order of magnitude as composite_ranker.ts's
    existing class-based fallback range) so a hub graha structurally
    outweighs a peripheral one, never zeroes one out (B.10 — no fabricated
    zero)."""
    pr  = float(c.get("pagerank_score") or 0.0)
    eig = float(c.get("eigenvector_centrality") or 0.0)
    bet = float(c.get("betweenness_centrality") or 0.0)
    harm = float(c.get("harmonic_centrality") or 0.0)
    composite = 0.40 * pr + 0.25 * eig + 0.20 * bet + 0.15 * harm
    return round(0.8 + composite * 0.7, 6)  # composite ∈ [0,1] -> role ∈ [0.8, 1.5]


def _fetch_graha_centrality(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, dict]:
    """{graha_title: {pagerank_score, eigenvector_centrality,
    betweenness_centrality, harmonic_centrality}} from bodha_cgm_nodes
    (post-bo_karanajala — this writer's own depends_on)."""
    rows = _fetch_dict(
        conn,
        """SELECT node_subject, pagerank_score, eigenvector_centrality,
                  betweenness_centrality, harmonic_centrality
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND node_type = 'graha'""",
        [chart_id, ayanamsha_id],
    )
    return {str(r["node_subject"]): r for r in rows}


@register("bo_laksana_rerank")
class BoLaksanaRerankWriter(WriterBase):
    """Post-CGM structural re-rank pass (CR-84) + PARK-#4 valence pickup.
    UPDATE-only; never deletes or re-inserts bodha_msr_signals rows."""
    asset_id = "bo_laksana_rerank"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                 notes="dry_run — would UPDATE structural_role + attempt PARK-#4 valence re-resolution")

        total_rerank = 0
        total_park4_reclaimed = 0
        total_park4_remaining = 0

        for ayanamsha in CANONICAL_AYANAMSHAS:
            centrality_by_graha = _fetch_graha_centrality(conn, chart_id, ayanamsha)

            # ── CR-84: structural_role from real CGM centrality ──────────────
            signal_rows = _fetch_dict(
                conn,
                """SELECT signal_id, configuration_jsonb FROM bodha_msr_signals
                   WHERE chart_id = %s AND ayanamsha_id = %s""",
                [chart_id, ayanamsha],
            )
            with conn.cursor() as cur:
                for sig in signal_rows:
                    cfg = sig.get("configuration_jsonb")
                    if isinstance(cfg, str):
                        try:
                            cfg = json.loads(cfg)
                        except Exception:
                            cfg = {}
                    code = _extract_primary_graha_for_rerank(cfg or {})
                    graha_title = _SHORT_TO_LONG.get(code) if code else None
                    c = centrality_by_graha.get(graha_title) if graha_title else None
                    if not c:
                        continue
                    payload = {
                        "structural_role_score": _structural_role_from_centrality(c),
                        "primary_graha": graha_title,
                        # bodha_cgm_nodes' centrality columns are NUMERIC in
                        # Postgres, so psycopg returns Decimal — cast to float
                        # before json.dumps (Decimal is not JSON-serializable).
                        "pagerank_score": float(c["pagerank_score"]) if c.get("pagerank_score") is not None else None,
                        "eigenvector_centrality": float(c["eigenvector_centrality"]) if c.get("eigenvector_centrality") is not None else None,
                        "betweenness_centrality": float(c["betweenness_centrality"]) if c.get("betweenness_centrality") is not None else None,
                        "harmonic_centrality": float(c["harmonic_centrality"]) if c.get("harmonic_centrality") is not None else None,
                        "formula_version": "structural_role_rerank_v1",
                        "computed_at": now,
                    }
                    cur.execute(
                        """UPDATE bodha_msr_signals
                           SET graph_node_strength_contribution_jsonb = %s::jsonb
                           WHERE signal_id = %s""",
                        [json.dumps(payload), sig["signal_id"]],
                    )
                    total_rerank += 1

            # ── PARK-#4: widened valence re-resolution for keyword_heuristic_v1
            # rows. Original PARK scoped "5 rows"; live population is
            # 43,408/49,360 chart-wide (BIND_D-2.md §B.4 scoping finding) — this
            # pass works the FULL population reachable by configuration_jsonb,
            # not a narrow 5-row slice, and reports the real before/after count.
            # Widening over bo_laksana's original _resolve_valence: (a) tries
            # the row's OWN varga_id (ga_vichara ships all 29 vargas, not just
            # D1 — the original call hardcoded varga='D1'); (b) tries the
            # additional tag keys _extract_primary_graha_for_rerank already
            # recognizes (lord/body) when 'graha'/'primary_graha' are absent.
            # A row that still cannot resolve (no graha subject at all — e.g.
            # panchanga/sade_sati-class signals with no natal graha anchor) is
            # left honestly as keyword_heuristic_v1 — not forced, per B.10.
            kw_rows = _fetch_dict(
                conn,
                """SELECT signal_id, configuration_jsonb, varga_id, fact_kind
                   FROM bodha_msr_signals
                   WHERE chart_id = %s AND ayanamsha_id = %s AND valence_source = 'keyword_heuristic_v1'""",
                [chart_id, ayanamsha],
            )
            if kw_rows:
                # varga-aware valence_pass lookup: (actor, target_house, varga) -> value_text
                try:
                    vrows = _fetch_dict(
                        conn,
                        """SELECT actor, target, varga, value_text FROM chart_vichara
                           WHERE chart_id = %s AND ayanamsha_id = %s AND vichara_family = 'valence_pass'""",
                        [chart_id, ayanamsha],
                    )
                except Exception:
                    vrows = []
                widened_lookup: dict[tuple, dict] = {}
                for r in vrows:
                    actor, target, varga = r.get("actor"), r.get("target"), r.get("varga")
                    if actor and target and varga:
                        widened_lookup[(str(actor), str(target), str(varga))] = {
                            "value_text": r.get("value_text"), "value_num": None,
                        }

                with conn.cursor() as cur:
                    for row in kw_rows:
                        cfg = row.get("configuration_jsonb")
                        if isinstance(cfg, str):
                            try:
                                cfg = json.loads(cfg)
                            except Exception:
                                cfg = {}
                        cfg = cfg or {}
                        row_varga = str(row.get("varga_id") or "D1").upper()
                        new_valence, new_source, _judged = _resolve_valence(
                            widened_lookup, "", None,
                            {**cfg, "varga": row_varga},
                        )
                        if new_source == "ga_vichara_v1":
                            cur.execute(
                                """UPDATE bodha_msr_signals
                                   SET valence = %s, valence_source = %s
                                   WHERE signal_id = %s""",
                                [new_valence, new_source, row["signal_id"]],
                            )
                            total_park4_reclaimed += 1
                        else:
                            total_park4_remaining += 1

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_rerank,
            notes=(
                f"structural_role_updated={total_rerank};"
                f"park4_reclaimed={total_park4_reclaimed};"
                f"park4_still_keyword_heuristic={total_park4_remaining}"
            ),
        )
