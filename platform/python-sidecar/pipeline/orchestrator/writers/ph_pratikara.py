"""
ph_pratikara — Mitigation Program (L4 Phala wave 4 parallel).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_mitigation.

Reads: kala_obstruction · kala_convergence (bridge: graha + window) · phala_anchors (influenceable) · bodha_rm_remedy_prescriptions (bo_upaya)
Writes: phala_mitigation (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_pratikara.engine import (
    RemedyPrescription,
    MitigationContext,
    derive_mitigation_record,
)

logger = logging.getLogger(__name__)


def _safe_float(value, default: float, *, field: str, row_id) -> float:
    """
    Coerce a possibly-TEXT numeric column to float; never raises.

    classical_strength_rating is declared TEXT on bodha_rm_remedy_prescriptions
    (bo_upaya writes it as str(confidence) or ''), not NUMERIC. A blank or
    non-numeric value must not crash the whole prescriptions load — fall back
    to the documented default and warn so the row is traceable.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning(
            "ph_pratikara: prescription %s has non-numeric %s=%r; using default %s",
            row_id, field, value, default,
        )
        return default


@register('ph_pratikara')
class PhPratikaraWriter(WriterBase):
    """
    Builds phala_mitigation: for each kala_obstruction row (bridged with kala_convergence
    for window + graha), assembles a P1-P5 managed remedy program from bodha_rm prescriptions.
    """
    asset_id = 'ph_pratikara'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_mitigation WHERE chart_id = %s", (chart_id,))

        obstructions = self._load_obstructions(conn, chart_id)
        anchors_by_domain = self._load_influenceable_anchors(conn, chart_id)
        prescriptions_by_graha = self._load_prescriptions(conn, chart_id)

        logger.info(
            "ph_pratikara: %d obstructions / %d influenceable anchors",
            len(obstructions), sum(len(v) for v in anchors_by_domain.values()),
        )

        # Map kala_obstruction severity vocab → engine's (low/medium/high) for P4 proportionality
        _SEVERITY_MAP = {'mild': 'low', 'moderate': 'medium', 'severe': 'high'}

        rows_inserted = 0
        with conn.cursor() as cur:
            for obs in obstructions:
                obs_id     = obs['id']
                # graha bridged from kala_convergence.constituent_factors->>'planet'; may be None
                graha      = str(obs.get('afflicting_graha') or '').lower() or None
                # severity from kala_obstruction.severity (mild/moderate/severe); map for engine
                raw_sev    = str(obs.get('severity') or 'mild').lower()
                severity   = _SEVERITY_MAP.get(raw_sev, 'low')
                # window bridged from kala_convergence
                obs_start  = obs.get('window_start')
                obs_end    = obs.get('window_end')
                obs_type   = str(obs.get('obstruction_type') or '')

                # Find the highest-magnitude influenceable anchor in any domain
                linked_anchor_id = None
                anchor_magnitude = None
                for domain_anchors in anchors_by_domain.values():
                    for a in domain_anchors:
                        if linked_anchor_id is None:
                            linked_anchor_id = str(a['anchor_id'])
                            anchor_magnitude = a.get('magnitude', 'moderate')

                # Prescription lookup: by graha if available; by obstruction_type if not; then jupiter generic
                prescriptions = []
                if graha:
                    prescriptions = prescriptions_by_graha.get(graha, [])
                if not prescriptions and obs_type:
                    # obstruction_type-keyed fallback (e.g. combustion, gandanta → general propitiation)
                    prescriptions = prescriptions_by_graha.get(obs_type, [])
                if not prescriptions:
                    prescriptions = prescriptions_by_graha.get('jupiter', [])

                mctx = MitigationContext(
                    obstruction_id=obs_id,
                    obstruction_severity=severity,
                    obstruction_window_start=obs_start,
                    obstruction_window_end=obs_end,
                    afflicting_graha=graha,
                    linked_anchor_id=linked_anchor_id,
                    anchor_magnitude=anchor_magnitude,
                    prescriptions=prescriptions,
                )

                rec = derive_mitigation_record(mctx)

                cur.execute(
                    """
                    INSERT INTO phala_mitigation (
                        chart_id, obstruction_id, linked_anchor_id,
                        afflicting_graha, obstruction_severity,
                        program_jsonb, tradition_options_jsonb, recommended_tier_jsonb,
                        intensity_tier, proportionality_basis,
                        initiation_muhurta_ref,
                        window_start, window_end, re_evaluation_date,
                        outcome_hook_jsonb, classical_citation,
                        cross_tradition_corroboration,
                        derivation_ledger_jsonb, source_citation
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s,
                        %s::jsonb, %s::jsonb, %s::jsonb,
                        %s, %s,
                        %s,
                        %s, %s, %s,
                        %s::jsonb, %s,
                        %s,
                        %s::jsonb, %s
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        chart_id, rec.obstruction_id, rec.linked_anchor_id,
                        rec.afflicting_graha, rec.obstruction_severity,
                        json.dumps(rec.program_jsonb),
                        json.dumps(rec.tradition_options_jsonb),
                        json.dumps(rec.recommended_tier_jsonb),
                        rec.intensity_tier, rec.proportionality_basis,
                        rec.initiation_muhurta_ref,
                        rec.window_start, rec.window_end, rec.re_evaluation_date,
                        json.dumps(rec.outcome_hook_jsonb), rec.classical_citation,
                        rec.cross_tradition_corroboration,
                        json.dumps(rec.derivation_ledger_jsonb), rec.source_citation,
                    ),
                )
                rows_inserted += 1

        logger.info("ph_pratikara: inserted %d rows into phala_mitigation for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_pratikara', rows_inserted=rows_inserted)

    def _load_obstructions(self, conn, chart_id: str) -> list:
        """
        Load kala_obstruction rows bridged with kala_convergence for window + graha.
        Graha is extracted from kala_convergence.constituent_factors->>'planet'.
        Fails loud on query errors — kala_obstruction exists; silent suppression is the bug pattern.
        """
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT
                    o.id,
                    o.convergence_id,
                    o.obstruction_type,
                    o.severity,
                    o.severity_score,
                    o.override_score,
                    o.obstruction_detail,
                    c.window_start,
                    c.window_end,
                    c.constituent_factors->>'planet' AS afflicting_graha
                FROM kala_obstruction o
                LEFT JOIN kala_convergence c ON o.convergence_id = c.convergence_id
                WHERE o.chart_id = %s
                ORDER BY o.severity_score DESC
                """,
                (chart_id,),
            )
            return cur.fetchall()

    def _load_influenceable_anchors(self, conn, chart_id: str) -> dict[str, list]:
        result: dict[str, list] = {}
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT anchor_id, domain, magnitude, malleability
                FROM phala_anchors
                WHERE chart_id = %s AND malleability = 'influenceable'
                ORDER BY CASE magnitude
                    WHEN 'pivotal' THEN 1 WHEN 'major' THEN 2
                    WHEN 'moderate' THEN 3 ELSE 4 END
                """,
                (chart_id,),
            )
            for row in cur.fetchall():
                d = row['domain']
                result.setdefault(d, []).append(row)
        return result

    def _load_prescriptions(self, conn, chart_id: str) -> dict[str, list[RemedyPrescription]]:
        """
        Load bodha_rm_remedy_prescriptions grouped by target_graha.
        Fails loud on query errors — bodha_rm_remedy_prescriptions exists (bo_upaya,
        L2 Bodha); silent suppression is the bug pattern (see _load_obstructions).
        """
        result: dict[str, list[RemedyPrescription]] = {}
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT prescription_id, tradition, sub_tradition, remedy_category,
                       classical_strength_rating, resonance_match_score, feasibility_score,
                       estimated_cost_inr_range_jsonb, requires_acharya_review_flag,
                       prerequisite_prescription_ids_array, incompatible_with_prescription_ids_array,
                       recommended_hora_lord_array, recommended_choghadiya_window_array,
                       pranapratishtha_required_flag, classical_sources_jsonb, target_graha
                FROM bodha_rm_remedy_prescriptions
                WHERE chart_id = %s
                ORDER BY resonance_match_score DESC NULLS LAST
                """,
                (chart_id,),
            )
            for row in cur.fetchall():
                graha_key = str(row.get('target_graha') or 'generic').lower()
                hora_arr = row.get('recommended_hora_lord_array') or []
                choghadiya_arr = row.get('recommended_choghadiya_window_array') or []
                # classical_sources_jsonb shape (bo_upaya writer): {"source_id": ..., "citation": ...}
                sources = row.get('classical_sources_jsonb')
                if not isinstance(sources, dict):
                    sources = {}
                p = RemedyPrescription(
                    prescription_id=str(row['prescription_id']),
                    tradition=str(row.get('tradition') or 'vedic'),
                    remedy_category=str(row.get('remedy_category') or ''),
                    classical_strength_rating=_safe_float(
                        row.get('classical_strength_rating'), 0.5,
                        field='classical_strength_rating', row_id=row.get('prescription_id'),
                    ),
                    resonance_match_score=float(row.get('resonance_match_score') or 0.5),
                    feasibility_score=float(row.get('feasibility_score') or 0.5),
                    estimated_cost_inr_range=row.get('estimated_cost_inr_range_jsonb') or {},
                    requires_acharya_review=bool(row.get('requires_acharya_review_flag')),
                    prerequisite_ids=list(row.get('prerequisite_prescription_ids_array') or []),
                    incompatible_ids=list(row.get('incompatible_with_prescription_ids_array') or []),
                    recommended_hora=(hora_arr[0] if hora_arr else None),
                    recommended_choghadiya=(choghadiya_arr[0] if choghadiya_arr else None),
                    pranapratishtha=bool(row.get('pranapratishtha_required_flag')),
                    classical_citation=str(sources.get('citation') or ''),
                )
                result.setdefault(graha_key, []).append(p)
        return result
