"""
bo_sudarshana — Sudarśana Chakra: tri-frame house assignment (L2 Bodha)
=========================================================================
D-1.5b Lane B-3 (CR-100). PURE L2 DERIVATION over existing L1 facts — no new
astronomical compute. For each of the 9 grahas, reads the graha's sign (and
the Lagna/Chandra/Sūrya signs) from `chart_facts` (fact_category=
'graha_position', fact_key='sign' — written by ga_positions, untouched by
this writer) and computes the house the graha occupies counted from three
concurrent reference points: Lagna, Chandra (Moon), Sūrya (Sun).

house_from(reference_sign0, graha_sign0) = ((graha_sign0 - reference_sign0) % 12) + 1

Emits one `sudarshana_agreement` MSR signal per (graha x ayanamsha) via
bodha_writers.sudarshana_emitter — a STANDALONE emitter module (does not
import or edit bo_laksana.py), per BRIEF_D1_5B.md Lane B-3 coordination note
("B-3 and B-4 both add MSR emitters — each owns its OWN new emitter module").

Salience: class_prior=1.15, subsystem='structural' — ratified DIS.016/DR-3.

LIGHT writer: loops over the 5 canonical ayanamshas in a single run() call
(mirrors bo_bimba's shape — this asset is small: 9 grahas x 5 ayanamshas =
45 rows total for a fully built chart).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register
from bodha_writers.sudarshana_emitter import (
    GRAHAS,
    sign_index,
    compute_tri_frame,
    build_signal_row,
)

logger = logging.getLogger(__name__)

CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "raman",
    "krishnamurti",
    "surya_siddhanta_classical",
    "true_chitra",
]

# Tier thresholds mirror bo_laksana's static _signature_tier (this asset is
# small enough — 9 rows/ayanamsha — that a percentile pass would be noise;
# absolute thresholds are the right grain here).
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


def _fetch_sign_facts(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    """Returns {fact_subject: {'sign': str, 'fact_id': str}} for graha_position
    sign facts (LAGNA + 9 grahas) at this (chart_id, ayanamsha_id)."""
    rows = conn.execute(
        """SELECT fact_id, fact_subject, fact_value_text
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_position' AND fact_key = 'sign'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, subject, sign = r["fact_id"], r["fact_subject"], r["fact_value_text"]
        else:
            fid, subject, sign = r[0], r[1], r[2]
        if subject and sign:
            out[str(subject).upper()] = {"sign": str(sign), "fact_id": str(fid)}
    return out


@register("bo_sudarshana")
class BoSudarshanaWriter(WriterBase):
    """bo_sudarshana: Sudarśana Chakra tri-frame MSR signal layer."""
    asset_id = "bo_sudarshana"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_msr_signals

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn = ctx.db_conn
        now = datetime.now(timezone.utc).isoformat()
        total = 0

        for aya in CANONICAL_AYANAMSHAS:
            sign_facts = _fetch_sign_facts(conn, chart_id, aya)
            if ctx.dry_run:
                logger.info("[bo_sudarshana dry_run] %s — %d sign facts found", aya, len(sign_facts))
                continue

            lagna_rec = sign_facts.get("LAGNA")
            moon_rec = sign_facts.get("MOON")
            sun_rec = sign_facts.get("SUN")
            if not (lagna_rec and moon_rec and sun_rec):
                raise RuntimeError(
                    f"[bo_sudarshana] chart_id={chart_id} ayanamsha={aya} — "
                    "missing LAGNA/MOON/SUN sign facts; ga_positions must have "
                    "failed or produced 0 rows for this ayanamsha"
                )
            lagna_i = sign_index(lagna_rec["sign"])
            moon_i = sign_index(moon_rec["sign"])
            sun_i = sign_index(sun_rec["sign"])
            if lagna_i is None or moon_i is None or sun_i is None:
                raise RuntimeError(
                    f"[bo_sudarshana] chart_id={chart_id} ayanamsha={aya} — "
                    f"unrecognized sign name (lagna={lagna_rec['sign']!r}, "
                    f"moon={moon_rec['sign']!r}, sun={sun_rec['sign']!r})"
                )

            rows: list[dict] = []
            for graha_code in GRAHAS:
                grec = sign_facts.get(graha_code)
                if not grec:
                    logger.warning(
                        "[bo_sudarshana] %s — no sign fact for %s; skipping",
                        aya, graha_code,
                    )
                    continue
                graha_i = sign_index(grec["sign"])
                if graha_i is None:
                    continue
                tri = compute_tri_frame(graha_i, lagna_i, moon_i, sun_i)
                row = build_signal_row(
                    chart_id=chart_id,
                    ayanamsha_id=aya,
                    build_id=build_id,
                    graha_code=graha_code,
                    tri_frame=tri,
                    fact_ids={
                        "graha": grec["fact_id"],
                        "lagna": lagna_rec["fact_id"],
                        "moon": moon_rec["fact_id"],
                        "sun": sun_rec["fact_id"],
                    },
                    now=now,
                )
                row["signature_tier"] = _signature_tier(row["computed_salience"])
                rows.append(row)

            if not rows:
                continue

            deleted = replace_prior_msr_signals(conn, rows)
            logger.info("[bo_sudarshana] %s — deleted %d prior, inserting %d signals",
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
