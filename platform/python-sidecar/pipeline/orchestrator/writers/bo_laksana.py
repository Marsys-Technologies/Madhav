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

from . import WriterBase, ContextSpec, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

# ── Canonical ayanamsha IDs (from chart_facts; match DB exactly) ─────────────
CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "raman",
    "krishnamurti",
    "surya_siddhanta_classical",
    "true_chitra",
]

ENGINE_VERSION = "bo_laksana_v2.0"

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

_DOMAIN_MAP: dict[str, list[str]] = {
    "yoga_label":                           ["career", "wealth", "health", "relationship", "spirituality"],
    "yoga_fires":                           ["career", "wealth", "health", "relationship", "spirituality"],
    "dosha_label":                          ["health", "relationship", "career"],
    "dosha_fires":                          ["health", "relationship"],
    "kala_sarpa_per_varga":                 ["character", "career", "wealth"],
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
    "karaka_chara_position":               ["career", "relationship", "character"],
    "karakamsa_position":                  ["career", "spirituality"],
    "swamsa_position":                     ["spirituality", "career"],
    "arudha_pada":                         ["career", "wealth", "relationship"],
    "graha_tri_deva_role_strength":        ["spirituality", "character"],
    "jaimini_tri_deva_role_per_graha":     ["spirituality", "character"],
    "sade_sati_cycle":                     ["career", "health", "relationship"],
    "sade_sati_phase":                     ["career", "health", "relationship"],
    "sade_sati_phase_quarter":             ["career", "health", "relationship"],
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
    "lord_in_house_per_varga":             ["career", "wealth", "relationship"],
    "bhava_significance_link":             ["career", "relationship", "wealth"],
    "combustion_per_varga":                ["health", "career"],
    "sambandha_grade":                     ["career", "relationship"],
    "convergence_count":                   ["career", "character"],
}

_CATEGORY_DEFAULT_DOMAINS: dict[str, list[str]] = {
    "structural":          ["character", "career"],
    "nakshatra":           ["character", "relationship"],
    "strength_ashtakavarga": ["career", "wealth"],
    "sade_sati":           ["career", "health", "relationship"],
    "panchanga":           ["character", "spirituality"],
    "yoga":                ["career", "wealth", "spirituality"],
    "medical":             ["health"],
    "vastu":               ["health", "wealth"],
    "tajaka":              ["career", "wealth"],
    "varga":               ["career", "character"],
}


def _assign_domains(fact_category: str, source_subsystem: str) -> list[str]:
    if fact_category in _DOMAIN_MAP:
        return _DOMAIN_MAP[fact_category]
    return _CATEGORY_DEFAULT_DOMAINS.get(source_subsystem, ["career", "character"])


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
                         source_l1_asset: str) -> str:
    """Short deterministic headline for display/retrieval."""
    val = fact_value_text or (f"{fact_value_num:.3g}" if fact_value_num is not None else "")
    cat_display = fact_category.replace("_", " ")
    key_display = fact_key.replace("_", " ")
    if val:
        return f"{cat_display}: {key_display} = {val} [{source_l1_asset}]"
    return f"{cat_display}: {key_display} [{source_l1_asset}]"


# ── Duration class ────────────────────────────────────────────────────────────

def _duration_class(fact_category: str) -> str:
    if fact_category in _TIME_WINDOW_CATS:
        return "transit_period"
    if fact_category in _BIRTH_MOMENT_CATS:
        return "birth_moment"
    return "natal_permanent"


# ── Signature tier from salience ──────────────────────────────────────────────

def _signature_tier(computed_salience: float) -> str:
    if computed_salience >= 3.0:
        return "chart_defining"
    if computed_salience >= 1.5:
        return "major"
    if computed_salience >= 0.8:
        return "supporting"
    return "background"


# ── Lookup builders ───────────────────────────────────────────────────────────

def _fetch_dict(conn: Any, sql: str, params: list) -> list[dict]:
    # conn uses dict_row factory; fetchall() already returns dicts — convert to plain dict.
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def _build_strength_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, float]:
    """graha → normalized shadbala (total / 390 virupas)."""
    rows = _fetch_dict(conn,
        """SELECT fact_key, fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='graha_shadbala_total'""",
        [chart_id, ayanamsha_id])
    lookup: dict[str, float] = {}
    for r in rows:
        graha = str(r["fact_key"] or "").split(":")[0]
        raw = float(r.get("fact_value_num") or 390.0)
        lookup[graha] = min(raw / 390.0, 2.0)
    return lookup


def _build_dignity_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, str]:
    """graha → dignity state string (D1 only)."""
    rows = _fetch_dict(conn,
        """SELECT fact_key, fact_value_text FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='graha_dignity_per_varga'
             AND (fact_key LIKE '%%:D1' OR fact_key LIKE '%%_D1')""",
        [chart_id, ayanamsha_id])
    lookup: dict[str, str] = {}
    for r in rows:
        key = str(r.get("fact_key", ""))
        graha = key.split(":")[0].split("_")[0]
        state = str(r.get("fact_value_text") or "neutral").lower()
        lookup[graha] = state
    return lookup


def _build_av_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[int, int]:
    """house → sarva ashtakavarga bindus (D1)."""
    rows = _fetch_dict(conn,
        """SELECT fact_key, fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='ashtakavarga_pinda_sarva'""",
        [chart_id, ayanamsha_id])
    lookup: dict[int, int] = {}
    for r in rows:
        key = str(r.get("fact_key", ""))
        try:
            house = int(key.split(":")[-1]) if ":" in key else int(key)
        except (ValueError, TypeError):
            continue
        lookup[house] = int(r.get("fact_value_num") or 28)
    return lookup


# ── Row fetcher (ALL fact categories, no whitelist) ──────────────────────────

_FETCH_SQL = """
SELECT fact_id, fact_category, ayanamsha_id, fact_key,
       fact_value_num, fact_value_text, fact_value_jsonb, formula_id,
       source_calculation, verification_pass_status, citation_ref, citation_human
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id IN (%s, 'INVARIANT')
ORDER BY fact_category, fact_key
"""


def _fetch_all_facts(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    return _fetch_dict(conn, _FETCH_SQL, [chart_id, ayanamsha_id])


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


def _compute_salience(
    fact_row: dict,
    tags: dict,
    strength_lookup: dict[str, float],
    dignity_lookup: dict[str, str],
    av_lookup: dict[int, int],
) -> dict:
    """Compute salience_formula_v1 inputs deterministically from L1 data."""
    tier = str(fact_row.get("verification_pass_status") or "documented_approximation")

    # Graha from tags
    primary_graha = (tags.get("graha") or tags.get("primary_graha")
                     or tags.get("lord") or tags.get("body"))
    house_num_raw = (tags.get("house") or tags.get("house_number")
                     or tags.get("bhava") or tags.get("house"))
    try:
        house_num = int(house_num_raw) if house_num_raw is not None else 1
    except (TypeError, ValueError):
        house_num = 1

    shadbala_norm = strength_lookup.get(primary_graha or "", 1.0) if primary_graha else 1.0
    dignity_state = dignity_lookup.get(primary_graha or "", "neutral") if primary_graha else "neutral"
    dignity_score = _DIGNITY_SCORE.get(dignity_state, 0.50)
    bindus = av_lookup.get(house_num, 4)

    orb = _safe_float(tags.get("orb_tightness"), 1.0)
    vargottama_amp = _safe_float(tags.get("vargottama_amp"), 0.0)
    neechabhanga = _safe_float(tags.get("neechabhanga"), 1.0)
    cancellation = _safe_float(tags.get("cancellation"), 1.0)

    corroboration = 5 if tier == "two_pass_verified" else 2
    verification_certainty = min(math.log(1 + corroboration) / math.log(10), 1.0)

    deterministic_strength = orb * min(shadbala_norm, 2.0) * dignity_score
    house_wt = _HOUSE_WEIGHT.get(house_num, 1.0)
    av_multiplier = _av_mult(bindus)

    computed_salience = (
        deterministic_strength
        * verification_certainty
        * house_wt
        * av_multiplier
        * (1 + vargottama_amp)
        * neechabhanga
        * cancellation
    )

    return {
        "orb_tightness":                   round(orb, 6),
        "shadbala_norm":                   round(min(shadbala_norm, 2.0), 6),
        "dignity_score":                   round(dignity_score, 6),
        "deterministic_strength":          round(deterministic_strength, 6),
        "verification_certainty":          round(verification_certainty, 6),
        "house_weight_multiplier":         round(house_wt, 6),
        "ashtakavarga_support_multiplier": round(av_multiplier, 6),
        "vargottama_amplification":        round(vargottama_amp, 6),
        "neechabhanga_modifier":           round(neechabhanga, 6),
        "cancellation_modifier":           round(cancellation, 6),
        "computed_salience":               round(computed_salience, 6),
        "salience_formula_version":        "v1.0",
    }


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

    # Constituent facts: from jsonb or fallback to self
    const_facts_raw = fvj.get("constituent_facts_array") or fvj.get("constituent_fact_ids")
    if const_facts_raw and isinstance(const_facts_raw, list):
        constituent_facts = [str(f) for f in const_facts_raw if f]
    else:
        constituent_facts = [fact_id]

    # Tags: merge fact_value_jsonb extras into config
    tags: dict = {}
    for key in ("graha", "primary_graha", "lord", "body", "house", "house_number",
                "bhava", "orb_tightness", "vargottama_amp", "neechabhanga",
                "cancellation", "varga", "varga_id"):
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
            if k in ("graha", "primary_graha", "lord", "body", "house", "house_number",
                     "bhava", "orb_tightness", "vargottama_amp", "neechabhanga",
                     "cancellation", "varga", "varga_id"):
                tags[k] = v

    # Source L1 asset + subsystem
    source_l1_asset  = _infer_source_l1_asset(sc)
    source_subsystem = _infer_source_subsystem(source_l1_asset)

    # Fact kind, valence, varga_id, tradition
    fact_kind  = _infer_fact_kind(fact_cat)
    valence    = _infer_valence(fact_cat, fact_value_text)
    varga_id   = _extract_varga_id(fact_key, fvj)
    tradition  = _infer_tradition(fact_cat, sc)

    # Domains
    domains        = _assign_domains(fact_cat, source_subsystem)
    duration_class = _duration_class(fact_cat)

    # Classical citation from fact_value_jsonb if available
    classical_sources_jsonb: dict | None = None
    citation_id = fvj.get("classical_citation_id") or fvj.get("citation_id")
    if citation_id:
        classical_sources_jsonb = {"catalog_ids": [], "rule_ids": [str(citation_id)],
                                   "text_chunk_ids": [], "citations": [str(citation_id)]}

    # Salience computation
    sal = _compute_salience(fact_row, tags, strength_lookup, dignity_lookup, av_lookup)
    computed_salience = sal["computed_salience"]

    # Text columns
    signal_summary_text = _build_summary_text(
        fact_cat, fact_key, fact_value_text,
        float(fact_value_num) if fact_value_num is not None else None,
        config,
    )
    signal_headline_text = _build_headline_text(
        fact_cat, fact_key, fact_value_text,
        float(fact_value_num) if fact_value_num is not None else None,
        source_l1_asset,
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
        "signature_tier":                           _signature_tier(computed_salience),
        "valence":                                  valence,
        "lel_origin":                               False,   # LEL data is L3-gated
        # ── Structured configuration ──────────────────────────────────────────
        "configuration_jsonb":                      json.dumps(config),
        "constituent_facts_array":                  constituent_facts,
        "constituent_signals_array":                None,
        # ── Classical sourcing ────────────────────────────────────────────────
        "classical_sources_array":                  ([str(citation_id)] if citation_id else None),
        "source_corroboration_count_by_text":       5 if vpass == "two_pass_verified" else 2,
        "source_corroboration_count_by_verse":      None,
        # ── Salience inputs ───────────────────────────────────────────────────
        "orb_tightness":                            sal["orb_tightness"],
        "shadbala_norm":                            sal["shadbala_norm"],
        "dignity_score":                            sal["dignity_score"],
        "deterministic_strength":                   sal["deterministic_strength"],
        "verification_certainty":                   sal["verification_certainty"],
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
        "signature_class":                          None,
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
  computed_salience, salience_formula_version, salience_confidence_interval_jsonb,
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
  citation_ref, citation_human, computed_at, engine_version
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
  %(computed_salience)s, %(salience_formula_version)s, %(salience_confidence_interval_jsonb)s::jsonb,
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
  %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb)
DO NOTHING
"""

_BATCH_SIZE = 200


def _batch_insert(conn: Any, rows: list[dict]) -> int:
    """Batch insert using executemany (one round-trip per batch, commit per batch)."""
    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i : i + _BATCH_SIZE]
            try:
                cur.executemany(_INSERT_SQL, batch)
            except Exception:
                # Fallback: per-row insert to skip any single bad row
                logger.warning("[bo_laksana] batch at %d failed, falling back to per-row insert", i)
                for row in batch:
                    try:
                        cur.execute("SAVEPOINT row_sp")
                        cur.execute(_INSERT_SQL, row)
                        cur.execute("RELEASE SAVEPOINT row_sp")
                    except Exception as row_exc:
                        cur.execute("ROLLBACK TO SAVEPOINT row_sp")
                        logger.warning("[bo_laksana] skipping row signal_type_id=%s: %s",
                                       row.get("signal_type_id"), row_exc)
            inserted += len(batch)
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


# ── WriterBase subclass ───────────────────────────────────────────────────────

@register("bo_laksana")
class BoLaksanaWriter(WriterBase):
    """
    bo_laksana v2.0: MSR Signal Store — category-agnostic projection of ALL L1 chart_facts.

    HEAVY writer: one sub-step per ayanamsha + INVARIANT.
    Each sub-step:
    1. Builds strength/dignity/AV lookup dicts from L1 data.
    2. Fetches ALL chart_facts rows for the ayanamsha (no category filter).
    3. Builds one bodha_msr_signals row per fact row with ALL enriched spine columns.
    4. Ranks by salience; normalizes by chart max.
    5. DELETE-then-INSERT (idempotent per replace_prior_msr_for_chart).
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

        if ctx.dry_run:
            facts = _fetch_all_facts(conn, chart_id, ayanamsha)
            logger.info("[bo_laksana dry_run] %s — would project %d facts", ayanamsha, len(facts))
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run:{ayanamsha}:{len(facts)}_facts")

        # Build L1 lookup dicts for salience inputs
        strength_lookup = _build_strength_lookup(conn, chart_id, ayanamsha)
        dignity_lookup  = _build_dignity_lookup(conn, chart_id, ayanamsha)
        av_lookup       = _build_av_lookup(conn, chart_id, ayanamsha)

        # Fetch ALL fact rows for this ayanamsha (category-agnostic)
        fact_rows = _fetch_all_facts(conn, chart_id, ayanamsha)
        logger.info("[bo_laksana] %s — fetched %d fact rows", ayanamsha, len(fact_rows))

        if not fact_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"no facts for ayanamsha={ayanamsha}")

        # Build signal rows
        signal_rows: list[dict] = []
        skipped = 0
        for fact_row in fact_rows:
            try:
                row = _build_signal_row(
                    fact_row, chart_id, build_id,
                    strength_lookup, dignity_lookup, av_lookup, now,
                    ayanamsha_override=ayanamsha,
                )
                signal_rows.append(row)
            except Exception as exc:
                logger.warning("[bo_laksana] skipping fact %s (%s): %s",
                               fact_row.get("fact_id"), fact_row.get("fact_category"), exc)
                skipped += 1

        logger.info("[bo_laksana] %s — built %d rows (%d skipped)", ayanamsha, len(signal_rows), skipped)

        if not signal_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"all facts skipped for ayanamsha={ayanamsha}")

        # Post-processing: rank + normalize
        _set_top_k_ranks(signal_rows)
        _normalize_by_chart_max(signal_rows)

        # Idempotency: wipe prior rows for (chart_id, ayanamsha_id)
        deleted = replace_prior_msr_for_chart(conn, chart_id, ayanamsha)
        logger.info("[bo_laksana] %s — deleted %d prior rows", ayanamsha, deleted)

        # Batch insert
        inserted = _batch_insert(conn, signal_rows)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            notes=f"aya={ayanamsha};facts={len(fact_rows)};skipped={skipped}",
        )
