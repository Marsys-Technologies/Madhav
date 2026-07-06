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

ENGINE_VERSION = "bo_laksana_v2.1"

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
    # V2 thresholds — conservative placeholders recut against live v2 distribution post-rebuild.
    # V2 values differ from V1 due to class_prior × verification_rescale scaling.
    if computed_salience >= 2.0:
        return "chart_defining"
    if computed_salience >= 0.8:
        return "major"
    if computed_salience >= 0.3:
        return "supporting"
    return "background"


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
    """graha → normalized shadbala (rupas clamped to 0–2.0).

    B2-fix: graha lives in fact_subject (e.g. 'SUN', 'MOON', 'MAR', …).
    The fact_key is always 'rupa' — splitting on ':' in fact_key was wrong.
    C2-verified: fact_value_num is already in rupas (observed: SUN=3.23, SAT=3.61,
    JUP=2.66, MOON=2.56, MER=2.50, VEN=2.36, MAR=3.11, RAH=0.38, KET=0.63).
    Classical minimum ≈ 1 rupa per planet; values ≥1.0 = adequate, 2.0 = 2× minimum.
    """
    rows = _fetch_dict(conn,
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='graha_shadbala_total'""",
        [chart_id, ayanamsha_id])
    lookup: dict[str, float] = {}
    for r in rows:
        # fact_subject e.g. 'SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT',
        # 'RAH_MEAN', 'KET_MEAN' — use as-is (callers match via tags/dignity keys)
        graha = str(r.get("fact_subject") or "").strip()
        if not graha:
            continue
        raw = float(r.get("fact_value_num") or 0.0)
        # C2-verified: fact_value_num is already in rupas (observed range: JUP=2.66,
        # MER=2.50, MOON=2.56, SUN=3.23, SAT=3.61, MAR=3.11, VEN=2.36, RAH=0.38,
        # KET=0.63 — all consistent with rupa scale, NOT virupas).
        # Classical minimum needed ≈ 1 rupa per planet; we normalise against that
        # floor so values ≥1.0 indicate adequate strength and 2.0 = double minimum.
        # Dividing by 1.0 is intentional (identity — the value IS already normalised
        # to rupas); we clamp at 2.0 to bound the salience multiplier.
        lookup[graha] = min(raw / 1.0, 2.0)  # clamp at 2× classical minimum
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
# (matching the graha keys used in strength_lookup / dignity_lookup)
_GRAHA_NAME_MAP: dict[str, str] = {
    "sun": "SUN", "sol": "SUN", "surya": "SUN",
    "moon": "MOON", "chandra": "MOON", "luna": "MOON",
    "mars": "MAR", "kuja": "MAR", "mangal": "MAR", "mangala": "MAR",
    "mercury": "MER", "budha": "MER", "budh": "MER",
    "jupiter": "JUP", "guru": "JUP", "brihaspati": "JUP",
    "venus": "VEN", "shukra": "VEN", "sukra": "VEN",
    "saturn": "SAT", "shani": "SAT", "sani": "SAT",
    "rahu": "RAH_MEAN", "rahoo": "RAH_MEAN",
    "ketu": "KET_MEAN", "kethu": "KET_MEAN",
}

# Dosha-group → primary graha (classical primary graha for each dosha type)
_DOSHA_GROUP_GRAHA: dict[str, str] = {
    "mangal": "MAR",
    "kala_sarpa": "RAH_MEAN",
    "graha_placement": "",   # too generic, parse from text
}

# Long graha name (as returned by chart_divisionals queries) → short strength_lookup key.
# Used by O3 navamsha signals so shadbala_norm resolves correctly instead of falling
# back to 1.0 when graha is e.g. "Saturn" and strength_lookup keys are "SAT".
_LONG_TO_SHORT: dict[str, str] = {
    "Sun":     "SUN",
    "Moon":    "MOON",
    "Mars":    "MAR",
    "Mercury": "MER",
    "Jupiter": "JUP",
    "Venus":   "VEN",
    "Saturn":  "SAT",
    "Rahu":    "RAH_MEAN",
    "Ketu":    "KET_MEAN",
}


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

    # Salience computation — v2 formula (BA-P3B); class_prior defaults to 1.0 until
    # brahma_class_priors is queried per-substep in a future optimization pass.
    sal = _compute_salience(
        fact_row, tags, strength_lookup, dignity_lookup, av_lookup,
        class_prior=1.0,
        functional_context=1.0,
        varga_id=varga_id or "D1",
    )
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
    short_to_long = {
        "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury",
        "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn",
        "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu",
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
    - D1 strong + D9 weak → 'broken_promise' (natal potential undermined by navamsha)
    - D1 weak + D9 strong → 'vargottama_resilience' (neechabhanga-grade uplift)
    - Both strong / both weak → 'concordant_strong' / 'concordant_weak'
    """
    d1_map = _build_d1_dignity_map(conn, chart_id, ayanamsha_id)
    d9_map = _build_d9_dignity_map(conn, chart_id, ayanamsha_id)

    graha_names = set(d1_map.keys()) | set(d9_map.keys())
    signals: list[dict] = []

    for graha in sorted(graha_names):
        # d1_map values are (dignity_text, fact_id | None) tuples (B2-fix)
        d1_tuple = d1_map.get(graha, ("neutral", None))
        d1_text, d1_fact_id = d1_tuple
        d9_text = d9_map.get(graha, "neutral")
        d1_tier = _dignity_tier(d1_text)
        d9_tier = _dignity_tier(d9_text)

        # Classify
        if d1_tier >= 2 and d9_tier <= -1:
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
            "neechabhanga_modifier":                    1.0,
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
  %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
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
            try:
                cur.executemany(_INSERT_SQL, batch)
                inserted += max(0, cur.rowcount)
            except Exception:
                # Fallback: per-row insert to skip any single bad row
                logger.warning("[bo_laksana] batch at %d failed, falling back to per-row insert", i)
                for row in batch:
                    try:
                        cur.execute("SAVEPOINT row_sp")
                        cur.execute(_INSERT_SQL, row)
                        cur.execute("RELEASE SAVEPOINT row_sp")
                        inserted += max(0, cur.rowcount)
                    except Exception as row_exc:
                        cur.execute("ROLLBACK TO SAVEPOINT row_sp")
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

        # Post-processing: rank + normalize + in-class percentile — all computed in
        # memory on the row dicts BEFORE the insert, so salience_pctl_in_class is
        # written in the single INSERT pass (no separate post-insert UPDATE).
        _set_top_k_ranks(signal_rows)
        _normalize_by_chart_max(signal_rows)
        _set_salience_pctl_in_class(signal_rows)

        # Idempotency: wipe prior rows for (chart_id, ayanamsha_id)
        deleted = replace_prior_msr_for_chart(conn, chart_id, ayanamsha)
        logger.info("[bo_laksana] %s — deleted %d prior rows", ayanamsha, deleted)

        # Batch insert (salience_pctl_in_class now carried on each row — no second pass)
        inserted = _batch_insert(conn, signal_rows)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            notes=f"aya={ayanamsha};facts={len(fact_rows)};skipped={skipped}",
        )
