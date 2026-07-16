"""
bo_nakshatra_semantic — Nakshatra-semantic MSR signal layer (L2 Bodha)
=========================================================================
D-2 Lane V-5 (CR-26/64). PURE L2 DERIVATION over existing L1
`graha_position` / `graha_dispositor_chain` / `graha_tara_bala` facts — no
new astronomical compute. For each of the 9 grahas, emits one
`nakshatra_semantic` MSR signal per (graha x ayanamsha) combining own-star
identity, dispositor chain, tara bala, and gandanta/end-degree flagging.

Salience: class_prior=1.00, subsystem='nakshatra' — ratified DIS.019/DR-6.

Owned signal_type_classes for the idempotency delete scope (D-1.5b
`owned_signal_type_classes` allowlist discipline — a rebuild must NEVER wipe
a sibling writer's rows in the shared `bodha_msr_signals` table): this writer
owns EXACTLY `nakshatra_semantic` and nothing else.

LIGHT writer: loops over the 5 canonical ayanamshas in a single run() call
(mirrors bo_sudarshana's shape).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register
from bodha_writers.nakshatra_semantic_emitter import (
    GRAHAS,
    build_signal_row,
    _fetch_facts,
)

logger = logging.getLogger(__name__)

CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "raman",
    "krishnamurti",
    "surya_siddhanta_classical",
    "true_chitra",
]

# ── Owned signal_type_class allowlist for replace_prior_msr_for_chart ───────
BO_NAKSHATRA_SEMANTIC_OWNED_SIGNAL_TYPE_CLASSES: list[str] = ["nakshatra_semantic"]

_TIER_CHART_DEFINING = 2.0
_TIER_MAJOR = 0.8
_TIER_SUPPORTING = 0.3


def _signature_tier(computed_salience: float) -> str:
    if computed_salience >= _TIER_CHART_DEFINING:
        return "chart_defining"
    if computed_salience >= _TIER_MAJOR:
        return "major"
    if computed_salience >= _TIER_SUPPORTING:
        return "supporting"
    return "background"


@register("bo_nakshatra_semantic")
class BoNakshatraSemanticWriter(WriterBase):
    """bo_nakshatra_semantic: nakshatra-semantic MSR signal layer."""
    asset_id = "bo_nakshatra_semantic"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_msr_for_chart

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn = ctx.db_conn
        now = datetime.now(timezone.utc).isoformat()
        total = 0

        for aya in CANONICAL_AYANAMSHAS:
            facts = _fetch_facts(conn, chart_id, aya)
            if ctx.dry_run:
                logger.info("[bo_nakshatra_semantic dry_run] %s — %d fact buckets found",
                            aya, len(facts))
                continue

            rows: list[dict] = []
            for graha_code in GRAHAS:
                pos_facts = facts.get(f"graha_position:{graha_code}")
                if not pos_facts:
                    logger.warning("[bo_nakshatra_semantic] %s — no graha_position facts for %s; skipping",
                                   aya, graha_code)
                    continue
                disp_facts = facts.get(f"graha_dispositor_chain:{graha_code}")
                tara_facts = facts.get(f"graha_tara_bala:{graha_code}")
                row = build_signal_row(
                    chart_id=chart_id,
                    ayanamsha_id=aya,
                    build_id=build_id,
                    graha_code=graha_code,
                    position_facts=pos_facts,
                    dispositor_facts=disp_facts,
                    tara_facts=tara_facts,
                    now=now,
                )
                if row is None:
                    continue
                row["signature_tier"] = _signature_tier(row["computed_salience"])
                rows.append(row)

            if not rows:
                continue

            deleted = replace_prior_msr_for_chart(
                conn, chart_id, aya, BO_NAKSHATRA_SEMANTIC_OWNED_SIGNAL_TYPE_CLASSES,
            )
            logger.info("[bo_nakshatra_semantic] %s — deleted %d prior, inserting %d signals",
                        aya, deleted, len(rows))

            for row in rows:
                conn.execute(_INSERT_SQL, row)
            total += len(rows)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total)


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
