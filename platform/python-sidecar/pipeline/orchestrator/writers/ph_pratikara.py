"""
ph_pratikara — Mitigation Program (L4 Phala wave 4 parallel).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_mitigation.

Reads: ka_vighnakara · phala_anchors (influenceable) · bodha_rm_remedy_prescriptions (bo_upaya)
Writes: phala_mitigation (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg2.extras

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_pratikara.engine import (
    RemedyPrescription,
    MitigationContext,
    derive_mitigation_record,
)

logger = logging.getLogger(__name__)


@register('ph_pratikara')
class PhPratikaraWriter(WriterBase):
    """
    Builds phala_mitigation: for each ka_vighnakara obstruction window,
    assembles a P1-P5 managed remedy program from bodha_rm prescriptions.
    """
    asset_id = 'ph_pratikara'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_mitigation WHERE chart_id = %s", (chart_id,))

        obstructions = self._load_obstructions(conn, chart_id)
        anchors_by_domain = self._load_influenceable_anchors(conn, chart_id)
        prescriptions_by_graha = self._load_prescriptions(conn, chart_id)

        logger.info(
            "ph_pratikara: %d obstructions / %d influenceable anchors",
            len(obstructions), sum(len(v) for v in anchors_by_domain.values()),
        )

        rows_inserted = 0
        with conn.cursor() as cur:
            for obs in obstructions:
                obs_id     = obs['id']
                graha      = str(obs.get('afflicting_graha') or '').lower()
                severity   = str(obs.get('obstruction_type') or 'medium').lower()
                obs_start  = obs.get('obstruction_start')
                obs_end    = obs.get('obstruction_end')

                # Find the highest-magnitude influenceable anchor in any domain
                linked_anchor_id = None
                anchor_magnitude = None
                for domain_anchors in anchors_by_domain.values():
                    for a in domain_anchors:
                        if linked_anchor_id is None:
                            linked_anchor_id = str(a['anchor_id'])
                            anchor_magnitude = a.get('magnitude', 'moderate')

                prescriptions = prescriptions_by_graha.get(graha, [])
                if not prescriptions:
                    # fallback to generic Jupiter prescriptions
                    prescriptions = prescriptions_by_graha.get('jupiter', [])

                mctx = MitigationContext(
                    obstruction_id=obs_id,
                    obstruction_severity=severity,
                    obstruction_window_start=obs_start,
                    obstruction_window_end=obs_end,
                    afflicting_graha=graha or None,
                    linked_anchor_id=linked_anchor_id,
                    anchor_magnitude=anchor_magnitude,
                    prescriptions=prescriptions,
                )

                rec = derive_mitigation_record(mctx)

                try:
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
                except Exception as exc:
                    logger.warning("ph_pratikara: insert failed for obstruction %s: %s", obs_id, exc)

        logger.info("ph_pratikara: inserted %d rows into phala_mitigation for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_pratikara', rows_inserted=rows_inserted)

    def _load_obstructions(self, conn, chart_id: str) -> list:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    SELECT id, afflicting_graha, obstruction_type,
                           obstruction_start, obstruction_end
                    FROM ka_vighnakara
                    WHERE chart_id = %s
                    ORDER BY obstruction_start
                    """,
                    (chart_id,),
                )
                return cur.fetchall()
            except Exception as exc:
                logger.debug("ph_pratikara: ka_vighnakara load skipped: %s", exc)
                return []

    def _load_influenceable_anchors(self, conn, chart_id: str) -> dict[str, list]:
        result: dict[str, list] = {}
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
        """Load bodha_rm_remedy_prescriptions grouped by afflicting_graha."""
        result: dict[str, list[RemedyPrescription]] = {}
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT prescription_id, tradition, sub_tradition, remedy_category,
                           classical_strength_rating, resonance_match_score, feasibility_score,
                           estimated_cost_inr_range_jsonb, requires_acharya_review,
                           prerequisite_prescription_ids_array, incompatible_with_prescription_ids_array,
                           recommended_hora, recommended_choghadiya, pranapratishtha,
                           classical_citation_text, graha
                    FROM bodha_rm_remedy_prescriptions
                    WHERE chart_id = %s
                    ORDER BY resonance_match_score DESC NULLS LAST
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    graha_key = str(row.get('graha') or 'generic').lower()
                    p = RemedyPrescription(
                        prescription_id=str(row['prescription_id']),
                        tradition=str(row.get('tradition') or 'vedic'),
                        remedy_category=str(row.get('remedy_category') or ''),
                        classical_strength_rating=float(row.get('classical_strength_rating') or 0.5),
                        resonance_match_score=float(row.get('resonance_match_score') or 0.5),
                        feasibility_score=float(row.get('feasibility_score') or 0.5),
                        estimated_cost_inr_range=row.get('estimated_cost_inr_range_jsonb') or {},
                        requires_acharya_review=bool(row.get('requires_acharya_review')),
                        prerequisite_ids=list(row.get('prerequisite_prescription_ids_array') or []),
                        incompatible_ids=list(row.get('incompatible_with_prescription_ids_array') or []),
                        recommended_hora=row.get('recommended_hora'),
                        recommended_choghadiya=row.get('recommended_choghadiya'),
                        pranapratishtha=bool(row.get('pranapratishtha')),
                        classical_citation=str(row.get('classical_citation_text') or ''),
                    )
                    result.setdefault(graha_key, []).append(p)
        except Exception as exc:
            logger.debug("ph_pratikara: prescriptions load skipped: %s", exc)
        return result
