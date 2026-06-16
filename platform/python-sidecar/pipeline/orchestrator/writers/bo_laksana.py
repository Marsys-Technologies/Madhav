"""
bo_laksana — MSR Signal Store (L2 Bodha root writer)
=====================================================
Projects ga_structural + ga_strength + ga_sensitive L1 facts into bodha_msr_signals.

PURE PROJECTION MODEL: one MSR signal per meaningful structural fact firing.
- Inherits fact_ids from chart_facts via constituent_facts_array.
- Never re-derives a fact L1 already computed.
- Applies salience_formula_v1 deterministically.
- Carries the L1 epistemic_tier (two_pass_verified / documented_approximation).
- NO predicate registry (G52 retired). signal_type_id = fact_category[:80].
- Weak-tail kept: strength is a column, not a filter.

HEAVY writer: plan_substeps returns per-ayanamsha SubSteps.
Each sub-step processes one ayanamsha and runs inside its own SAVEPOINT.
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

# Ayanamshas bo_laksana processes (mirrors ga_structural)
CANONICAL_AYANAMSHAS = ["LAHIRI", "RAMAN", "KRISHNAMURTI", "YUKTESHWAR", "TROPICAL"]

ENGINE_VERSION = "bo_laksana_v1.0"

# ── Signal categories projected from chart_facts ─────────────────────────────

# Primary ga_structural signal categories (ordered by signal quality / priority)
STRUCTURAL_SIGNAL_CATEGORIES = [
    "yoga_label",
    "dosha_label",
    "yoga_fires",
    "dosha_fires",
    "graha_composite_state_classification",
    "graha_special_state_rollup",
    "graha_yoga_karaka_flag",
    "parivartana_per_varga",
    "vargottama_per_varga",
    "conjunction_within_orb",
    "kala_sarpa_per_varga",
    "graha_dispositor_chain",
    "composite_dispositor_strength",
    "graha_avastha_lajjitadi",
    "graha_effective_dignity_modified_by_aspects",
    "aspect_parashari_given",
]

# ga_sensitive signal categories
SENSITIVE_SIGNAL_CATEGORIES = [
    "kp_cuspal_significators",
    "karaka_chara_position",
    "karakamsa_position",
    "swamsa_position",
    "arudha_pada",
    "graha_tri_deva_role_strength",
    "jaimini_tri_deva_role_per_graha",
]

# ga_sade_sati signal categories
SADE_SATI_SIGNAL_CATEGORIES = [
    "sade_sati_cycle",
    "sade_sati_phase",
]

# ga_panchanga signal categories
PANCHANGA_SIGNAL_CATEGORIES = [
    "panchanga_yoga",
    "panchanga_tithi",
    "panchanga_vara",
    "panchanga_nakshatra_moon",
    "panchanga_special_yoga_combinations",
]

# Domain mapping: fact_category → domains_affected
CATEGORY_DOMAIN_MAP: dict[str, list[str]] = {
    "yoga_label":                           ["career", "wealth", "health", "relationship", "spirituality"],
    "dosha_label":                          ["health", "relationship", "career"],
    "yoga_fires":                           ["career", "wealth", "health", "relationship", "spirituality"],
    "dosha_fires":                          ["health", "relationship"],
    "graha_composite_state_classification": ["character", "career", "wealth"],
    "graha_special_state_rollup":           ["character", "career"],
    "graha_yoga_karaka_flag":               ["career", "wealth"],
    "parivartana_per_varga":                ["career", "wealth", "relationship"],
    "vargottama_per_varga":                 ["character", "career"],
    "conjunction_within_orb":              ["career", "relationship", "spirituality"],
    "kala_sarpa_per_varga":                ["character", "career", "wealth"],
    "graha_dispositor_chain":              ["character", "career"],
    "composite_dispositor_strength":       ["character", "career"],
    "graha_avastha_lajjitadi":             ["character", "relationship"],
    "graha_effective_dignity_modified_by_aspects": ["career", "wealth"],
    "aspect_parashari_given":              ["career", "relationship", "wealth"],
    "kp_cuspal_significators":             ["career", "relationship", "wealth", "spirituality"],
    "karaka_chara_position":               ["career", "relationship", "character"],
    "karakamsa_position":                  ["career", "spirituality"],
    "swamsa_position":                     ["spirituality", "career"],
    "arudha_pada":                         ["career", "wealth", "relationship"],
    "graha_tri_deva_role_strength":        ["spirituality", "character"],
    "jaimini_tri_deva_role_per_graha":     ["spirituality", "character"],
    "sade_sati_cycle":                     ["career", "health", "relationship"],
    "sade_sati_phase":                     ["career", "health", "relationship"],
    "panchanga_yoga":                      ["character", "spirituality"],
    "panchanga_tithi":                     ["character", "spirituality"],
    "panchanga_vara":                      ["character"],
    "panchanga_nakshatra_moon":            ["character", "relationship"],
    "panchanga_special_yoga_combinations": ["spirituality", "character"],
}

# Tradition mapping: fact_category → signal_tradition
CATEGORY_TRADITION_MAP: dict[str, str] = {
    "yoga_label": "parashari",
    "dosha_label": "parashari",
    "yoga_fires": "parashari",
    "dosha_fires": "parashari",
    "graha_composite_state_classification": "parashari",
    "graha_special_state_rollup": "parashari",
    "graha_yoga_karaka_flag": "parashari",
    "parivartana_per_varga": "parashari",
    "vargottama_per_varga": "parashari",
    "conjunction_within_orb": "parashari",
    "kala_sarpa_per_varga": "parashari",
    "graha_dispositor_chain": "parashari",
    "composite_dispositor_strength": "parashari",
    "graha_avastha_lajjitadi": "parashari",
    "graha_effective_dignity_modified_by_aspects": "parashari",
    "aspect_parashari_given": "parashari",
    "kp_cuspal_significators": "kp",
    "karaka_chara_position": "jaimini",
    "karakamsa_position": "jaimini",
    "swamsa_position": "jaimini",
    "arudha_pada": "jaimini",
    "graha_tri_deva_role_strength": "jaimini",
    "jaimini_tri_deva_role_per_graha": "jaimini",
    "sade_sati_cycle": "parashari",
    "sade_sati_phase": "parashari",
    "panchanga_yoga": "parashari",
    "panchanga_tithi": "parashari",
    "panchanga_vara": "parashari",
    "panchanga_nakshatra_moon": "parashari",
    "panchanga_special_yoga_combinations": "parashari",
}

ALL_SIGNAL_CATEGORIES = (
    STRUCTURAL_SIGNAL_CATEGORIES
    + SENSITIVE_SIGNAL_CATEGORIES
    + SADE_SATI_SIGNAL_CATEGORIES
    + PANCHANGA_SIGNAL_CATEGORIES
)


# ── Salience helpers ─────────────────────────────────────────────────────────

def _safe_float(v: Any) -> float:
    """Cast a DB value to float; return 0.5 (neutral) if None/error."""
    try:
        return float(v) if v is not None else 0.5
    except (TypeError, ValueError):
        return 0.5


def _compute_salience_inputs(
    fact_row: dict,
    strength_lookup: dict[tuple[str, str], float],
    dignity_lookup: dict[tuple[str, str], str],
    av_lookup: dict[tuple[str, int], int],
) -> dict[str, float]:
    """
    Extract salience_formula_v1 inputs from a chart_facts row + lookup dicts.
    Returns a dict ready to pass as kwargs to SalienceInputs.
    """
    from bodha_writers.formulas import (
        SalienceInputs, salience_formula_v1, DIGNITY_SCORE, HOUSE_WEIGHT,
    )

    # Extract the primary graha from fact_tags (if present)
    tags: dict = {}
    if fact_row.get("fact_tags") and isinstance(fact_row["fact_tags"], dict):
        tags = fact_row["fact_tags"]
    elif fact_row.get("fact_tags") and isinstance(fact_row["fact_tags"], str):
        try:
            tags = json.loads(fact_row["fact_tags"])
        except Exception:
            tags = {}

    primary_graha = tags.get("graha") or tags.get("primary_graha") or tags.get("lord")
    house_num = tags.get("house") or tags.get("house_number") or tags.get("bhava")
    try:
        house_num = int(house_num) if house_num is not None else 1
    except (TypeError, ValueError):
        house_num = 1

    ayanamsha = str(fact_row.get("ayanamsha_id", "LAHIRI"))

    # Shadbala (normalized to required: 1.0 means meeting requirement)
    shadbala_key = (primary_graha, ayanamsha) if primary_graha else None
    shadbala_norm = strength_lookup.get(shadbala_key, 1.0) if shadbala_key else 1.0

    # Dignity score
    dignity_key = (primary_graha, ayanamsha) if primary_graha else None
    dignity_state = dignity_lookup.get(dignity_key, "neutral") if dignity_key else "neutral"
    dignity_score = DIGNITY_SCORE.get(dignity_state, 0.50)

    # Ashtakavarga bindus for the house
    av_key = (ayanamsha, house_num)
    av_bindus = av_lookup.get(av_key, 4)

    # Epistemic tier → source corroboration count
    tier = str(fact_row.get("epistemic_tier") or "documented_approximation")
    corroboration = 5 if tier == "two_pass_verified" else 2

    inputs = SalienceInputs(
        orb_tightness=_safe_float(tags.get("orb_tightness", 1.0)),
        shadbala_norm=min(shadbala_norm, 2.0),
        dignity_score=dignity_score,
        source_corroboration_count_by_text=corroboration,
        house_number=house_num,
        ashtakavarga_bindus=av_bindus,
        vargottama_amplification=_safe_float(tags.get("vargottama_amp", 0.0)),
        neechabhanga_modifier=_safe_float(tags.get("neechabhanga", 1.0)),
        cancellation_modifier=_safe_float(tags.get("cancellation", 1.0)),
    )
    return salience_formula_v1(inputs)


# ── Lookup builders ───────────────────────────────────────────────────────────

def _build_strength_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[tuple[str, str], float]:
    """graha → normalized shadbala (total / 390 virupas as rough norm)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_numeric, ayanamsha_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_shadbala_total'""",
        [chart_id, ayanamsha_id],
    ).fetchall()
    lookup: dict[tuple[str, str], float] = {}
    for r in rows:
        key_str = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        graha = key_str.split(":")[0] if ":" in key_str else key_str
        raw = float(r[1] if isinstance(r, tuple) else r.get("fact_value_numeric") or 390.0)
        aya = str(r[2] if isinstance(r, tuple) else r.get("ayanamsha_id", ayanamsha_id))
        lookup[(graha, aya)] = min(raw / 390.0, 2.0)
    return lookup


def _build_dignity_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[tuple[str, str], str]:
    """graha/D1 → dignity state string."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_text, ayanamsha_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_dignity_per_varga'
             AND fact_key LIKE '%:D1%'""",
        [chart_id, ayanamsha_id],
    ).fetchall()
    lookup: dict[tuple[str, str], str] = {}
    for r in rows:
        key_str = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        graha = key_str.split(":")[0] if ":" in key_str else key_str
        state = str(r[1] if isinstance(r, tuple) else r.get("fact_value_text") or "neutral")
        aya = str(r[2] if isinstance(r, tuple) else r.get("ayanamsha_id", ayanamsha_id))
        lookup[(graha, aya)] = state.lower()
    return lookup


def _build_av_lookup(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[tuple[str, int], int]:
    """(ayanamsha, house) → sarva ashtakavarga bindus."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_numeric, ayanamsha_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'ashtakavarga_pinda_sarva'""",
        [chart_id, ayanamsha_id],
    ).fetchall()
    lookup: dict[tuple[str, int], int] = {}
    for r in rows:
        key_str = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        try:
            house = int(key_str.split(":")[-1]) if ":" in key_str else int(key_str)
        except ValueError:
            continue
        val = int(r[1] if isinstance(r, tuple) else r.get("fact_value_numeric") or 28)
        aya = str(r[2] if isinstance(r, tuple) else r.get("ayanamsha_id", ayanamsha_id))
        lookup[(aya, house)] = val
    return lookup


# ── Row fetcher ────────────────────────────────────────────────────────────────

def _fetch_signal_facts(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """Fetch all chart_facts rows that map to MSR signals for this ayanamsha."""
    rows = conn.execute(
        """SELECT fact_id, fact_category, ayanamsha_id, fact_key,
                  fact_value_numeric, fact_value_text, fact_tags, epistemic_tier,
                  source_asset_id
           FROM chart_facts
           WHERE chart_id = %s
             AND ayanamsha_id = %s
             AND fact_category = ANY(%s)
           ORDER BY fact_category, fact_key""",
        [chart_id, ayanamsha_id, ALL_SIGNAL_CATEGORIES],
    ).fetchall()

    # Normalize to dicts regardless of cursor row type
    keys = ["fact_id", "fact_category", "ayanamsha_id", "fact_key",
            "fact_value_numeric", "fact_value_text", "fact_tags", "epistemic_tier",
            "source_asset_id"]
    result = []
    for r in rows:
        if isinstance(r, dict):
            result.append(r)
        else:
            result.append(dict(zip(keys, r)))
    return result


# ── Row builder ────────────────────────────────────────────────────────────────

def _build_signal_row(
    fact_row: dict,
    chart_id: str,
    build_id: str,
    strength_lookup: dict,
    dignity_lookup: dict,
    av_lookup: dict,
    now: str,
) -> dict:
    """Convert one chart_facts row to one bodha_msr_signals row."""
    fact_cat = str(fact_row.get("fact_category", ""))
    fact_key = str(fact_row.get("fact_key", ""))
    fact_id  = str(fact_row.get("fact_id", ""))
    aya      = str(fact_row.get("ayanamsha_id", "LAHIRI"))
    tier     = str(fact_row.get("epistemic_tier") or "documented_approximation")

    # signal_type_id: category + key prefix (truncated to 80 chars)
    signal_type_id = f"{fact_cat}:{fact_key}"[:80]

    # Structured configuration
    config: dict = {
        "fact_key": fact_key,
        "fact_value_text": fact_row.get("fact_value_text"),
        "fact_value_numeric": float(fact_row["fact_value_numeric"])
                               if fact_row.get("fact_value_numeric") is not None else None,
    }

    # Parse fact_tags into config
    tags: dict = {}
    if fact_row.get("fact_tags"):
        if isinstance(fact_row["fact_tags"], dict):
            tags = fact_row["fact_tags"]
        elif isinstance(fact_row["fact_tags"], str):
            try:
                tags = json.loads(fact_row["fact_tags"])
            except Exception:
                pass
        config.update(tags)

    # Salience
    salience_result = _compute_salience_inputs(
        fact_row, strength_lookup, dignity_lookup, av_lookup
    )
    computed_salience = float(salience_result["computed_salience"])
    deterministic_strength = float(salience_result["deterministic_strength"])
    verification_certainty = float(salience_result["verification_certainty"])
    house_wt = float(salience_result["house_weight_multiplier"])
    av_mult  = float(salience_result["ashtakavarga_support_multiplier"])

    # Domains
    domains = CATEGORY_DOMAIN_MAP.get(fact_cat, ["general"])
    domain_salience = {d: round(computed_salience * (1.0 / len(domains)), 6) for d in domains}

    # Tradition
    tradition = CATEGORY_TRADITION_MAP.get(fact_cat, "parashari")

    # Duration class (nominal — structural facts are natal)
    duration_class = "natal_permanent"
    if "sade_sati" in fact_cat or "shani_period" in fact_cat:
        duration_class = "transit_period"
    elif "panchanga" in fact_cat:
        duration_class = "birth_moment"

    # Citation
    citation_ref   = f"chart_facts/{fact_id}"
    citation_human = f"L1 chart_facts: {fact_cat} / {fact_key}"

    return {
        "signal_id":                            str(uuid.uuid4()),
        "chart_id":                             chart_id,
        "ayanamsha_id":                         aya,
        "build_id":                             build_id,
        "signal_type_id":                       signal_type_id,
        "signal_type_class":                    _signal_class(fact_cat),
        "signal_tradition":                     tradition,
        "configuration_jsonb":                  json.dumps(config),
        "constituent_facts_array":              [fact_id],
        "constituent_signals_array":            None,
        "classical_sources_array":              None,
        "source_corroboration_count_by_text":   5 if tier == "two_pass_verified" else 2,
        "source_corroboration_count_by_verse":  None,
        "orb_tightness":                        float(tags.get("orb_tightness", 1.0)) if tags.get("orb_tightness") is not None else None,
        "shadbala_norm":                        None,
        "dignity_score":                        None,
        "deterministic_strength":               deterministic_strength,
        "verification_certainty":               verification_certainty,
        "divisional_corroboration_count":       None,
        "dasha_activation_proximity_score":     None,
        "house_weight_multiplier":              house_wt,
        "ashtakavarga_support_multiplier":      av_mult,
        "aspect_modifier":                      None,
        "vargottama_amplification":             float(tags.get("vargottama_amp", 0.0)) if tags.get("vargottama_amp") is not None else None,
        "argala_modifier":                      None,
        "neechabhanga_modifier":                float(tags.get("neechabhanga", 1.0)) if tags.get("neechabhanga") is not None else None,
        "cancellation_modifier":                float(tags.get("cancellation", 1.0)) if tags.get("cancellation") is not None else None,
        "computed_salience":                    computed_salience,
        "salience_formula_version":             salience_result["salience_formula_version"],
        "salience_confidence_interval_jsonb":   None,
        "domains_affected_array":               domains,
        "domain_salience_jsonb":                json.dumps(domain_salience),
        "shared_factor_keys_jsonb":             None,
        "cross_domain_shared_factor_count":     None,
        "graph_edge_pattern_jsonb":             None,
        "graph_node_strength_contribution_jsonb": None,
        "relationship_classification":          None,
        "graha_weakness_indicators_jsonb":      None,
        "remedy_hooks_array":                   [fact_cat] if fact_cat.startswith("dosha") else None,
        "recurring_pattern_marker":             None,
        "top_k_salience_rank":                  None,  # set in post-processing
        "system_convergence_count":             None,
        "signature_class":                      None,
        "contradicts_signals_array":            None,
        "active_duration_class":                duration_class,
        "active_dasha_periods_jsonb":           None,
        "activation_predicted_dates_jsonb":     None,
        "predicted_outcome_class":              None,
        "cross_ayanamsha_consistency_score":    None,
        "strength_normalized_to_chart_max":     None,
        "pada_precision_flag":                  None,
        "cross_system_consensus_count":         None,
        "channel_render_priority_jsonb":        None,
        "verification_pass_status":             tier,
        "verification_method":                  "L1_fact_projection",
        "citation_ref":                         citation_ref,
        "citation_human":                       citation_human,
        "computed_at":                          now,
        "engine_version":                       ENGINE_VERSION,
    }


def _signal_class(fact_cat: str) -> str:
    """Map fact_category to signal_type_class."""
    if fact_cat in ("yoga_fires", "yoga_label"):
        return "yoga"
    if fact_cat in ("dosha_fires", "dosha_label"):
        return "dosha"
    if "sade_sati" in fact_cat or "shani_period" in fact_cat:
        return "sade_sati"
    if "panchanga" in fact_cat:
        return "panchanga"
    if "karaka" in fact_cat or "karakamsa" in fact_cat or "swamsa" in fact_cat or "arudha" in fact_cat:
        return "karaka_alignment"
    if "kp_" in fact_cat:
        return "tradition_specific"
    if "parivartana" in fact_cat:
        return "parivartana"
    if "conjunction" in fact_cat:
        return "composite_state"
    if "kala_sarpa" in fact_cat:
        return "composite_state"
    if "vargottama" in fact_cat:
        return "varga_pattern"
    if "aspect" in fact_cat:
        return "composite_state"
    return "composite_state"


# ── INSERT helper ──────────────────────────────────────────────────────────────

_INSERT_SQL = """
INSERT INTO bodha_msr_signals (
  signal_id, chart_id, ayanamsha_id, build_id,
  signal_type_id, signal_type_class, signal_tradition,
  configuration_jsonb, constituent_facts_array, constituent_signals_array,
  classical_sources_array, source_corroboration_count_by_text, source_corroboration_count_by_verse,
  orb_tightness, shadbala_norm, dignity_score,
  deterministic_strength, verification_certainty,
  divisional_corroboration_count, dasha_activation_proximity_score,
  house_weight_multiplier, ashtakavarga_support_multiplier,
  aspect_modifier, vargottama_amplification, argala_modifier,
  neechabhanga_modifier, cancellation_modifier,
  computed_salience, salience_formula_version,
  salience_confidence_interval_jsonb,
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
  %(configuration_jsonb)s::jsonb, %(constituent_facts_array)s, %(constituent_signals_array)s,
  %(classical_sources_array)s, %(source_corroboration_count_by_text)s, %(source_corroboration_count_by_verse)s,
  %(orb_tightness)s, %(shadbala_norm)s, %(dignity_score)s,
  %(deterministic_strength)s, %(verification_certainty)s,
  %(divisional_corroboration_count)s, %(dasha_activation_proximity_score)s,
  %(house_weight_multiplier)s, %(ashtakavarga_support_multiplier)s,
  %(aspect_modifier)s, %(vargottama_amplification)s, %(argala_modifier)s,
  %(neechabhanga_modifier)s, %(cancellation_modifier)s,
  %(computed_salience)s, %(salience_formula_version)s,
  %(salience_confidence_interval_jsonb)s::jsonb,
  %(domains_affected_array)s, %(domain_salience_jsonb)s::jsonb,
  %(shared_factor_keys_jsonb)s, %(cross_domain_shared_factor_count)s,
  %(graph_edge_pattern_jsonb)s, %(graph_node_strength_contribution_jsonb)s, %(relationship_classification)s,
  %(graha_weakness_indicators_jsonb)s, %(remedy_hooks_array)s, %(recurring_pattern_marker)s,
  %(top_k_salience_rank)s, %(system_convergence_count)s, %(signature_class)s,
  %(contradicts_signals_array)s, %(active_duration_class)s,
  %(active_dasha_periods_jsonb)s, %(activation_predicted_dates_jsonb)s, %(predicted_outcome_class)s,
  %(cross_ayanamsha_consistency_score)s, %(strength_normalized_to_chart_max)s,
  %(pada_precision_flag)s, %(cross_system_consensus_count)s, %(channel_render_priority_jsonb)s::jsonb,
  %(verification_pass_status)s, %(verification_method)s,
  %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
"""

_BATCH_SIZE = 100


def _batch_insert(conn: Any, rows: list[dict]) -> int:
    """Insert rows in batches; return count inserted."""
    inserted = 0
    for i in range(0, len(rows), _BATCH_SIZE):
        batch = rows[i : i + _BATCH_SIZE]
        for row in batch:
            conn.execute(_INSERT_SQL, row)
        inserted += len(batch)
        if inserted % 500 == 0 or i + _BATCH_SIZE >= len(rows):
            logger.info("[bo_laksana] inserted %d/%d signals", inserted, len(rows))
    return inserted


def _set_top_k_ranks(rows: list[dict]) -> None:
    """Rank rows by computed_salience DESC within (chart_id, ayanamsha_id) — in place."""
    sorted_rows = sorted(rows, key=lambda r: r["computed_salience"], reverse=True)
    for rank, row in enumerate(sorted_rows, start=1):
        row["top_k_salience_rank"] = rank


# ── WriterBase subclass ────────────────────────────────────────────────────────

@register("bo_laksana")
class BoLaksanaWriter(WriterBase):
    """
    bo_laksana: MSR Signal Store — the L2 Bodha root writer.

    HEAVY writer: one sub-step per ayanamsha. Each sub-step:
    1. Builds lookup dicts (shadbala, dignity, ashtakavarga) for the ayanamsha.
    2. Fetches all structural fact rows.
    3. Builds one bodha_msr_signals row per fact row.
    4. Ranks by salience within the ayanamsha.
    5. DELETE-then-INSERT (idempotent via replace_prior_msr_for_chart).
    """
    asset_id   = "bo_laksana"
    has_substeps = True

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(key=f"aya_{aya}", label=f"bo_laksana — {aya}")
            for aya in CANONICAL_AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_msr_for_chart

        chart_id    = ctx.config["chart_id"]
        build_id    = ctx.build_id
        ayanamsha   = step.key.removeprefix("aya_")
        conn        = ctx.db_conn
        now         = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            facts = _fetch_signal_facts(conn, chart_id, ayanamsha)
            logger.info("[bo_laksana dry_run] %s — would insert %d signals", ayanamsha, len(facts))
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run:{ayanamsha}:{len(facts)}_facts")

        # Build lookup dicts
        strength_lookup = _build_strength_lookup(conn, chart_id, ayanamsha)
        dignity_lookup  = _build_dignity_lookup(conn, chart_id, ayanamsha)
        av_lookup       = _build_av_lookup(conn, chart_id, ayanamsha)

        # Fetch all structural facts for this ayanamsha
        fact_rows = _fetch_signal_facts(conn, chart_id, ayanamsha)
        logger.info("[bo_laksana] %s — fetched %d fact rows", ayanamsha, len(fact_rows))

        if not fact_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"no facts for {ayanamsha}")

        # Build signal rows
        signal_rows = []
        for fact_row in fact_rows:
            try:
                row = _build_signal_row(
                    fact_row, chart_id, build_id,
                    strength_lookup, dignity_lookup, av_lookup, now,
                )
                signal_rows.append(row)
            except Exception as e:
                logger.warning("[bo_laksana] skipping fact %s: %s",
                               fact_row.get("fact_id"), e)

        logger.info("[bo_laksana] %s — built %d signal rows", ayanamsha, len(signal_rows))

        # Rank by salience
        _set_top_k_ranks(signal_rows)

        # Idempotency: delete prior rows for this (chart_id, ayanamsha_id)
        deleted = replace_prior_msr_for_chart(conn, chart_id, ayanamsha)
        logger.info("[bo_laksana] %s — deleted %d prior rows", ayanamsha, deleted)

        # Insert
        inserted = _batch_insert(conn, signal_rows)
        return WriterResult(asset_id=self.asset_id, rows_inserted=inserted,
                            notes=f"aya={ayanamsha}")
