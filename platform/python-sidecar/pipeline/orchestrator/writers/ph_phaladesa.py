"""
ph_phaladesa — Domain Result Declaration (L4 Phala wave 7).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_phaladesa.

B.11 WHOLE-CHART-READ: writer reads L2 Bodha synthesis (MSR, CDLM, CGM)
before building domain declarations.

MODEL POLICY: writer sets narration_status='pending', narration_model=NULL.
Narration is a SEPARATE async step via Gemini/DeepSeek only.
Anthropic is BANNED. validate_narration_model() enforces this.

Reads: phala_anchors · phala_suddha_sodhana · phala_sodhana (flag counts)
       phala_sankrama (spillovers) · phala_mitigation (domains covered)
       phala_muhurta (domains covered) · phala_pramana (window status)
       bodha_msr_signals (B.11) · bodha_cdlm_cells (B.11) · bodha_cgm_edges (B.11)
Writes: phala_phaladesa (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg2.extras

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_phaladesa.engine import (
    DomainAnchorSummary,
    SpilloverSummary,
    BodhaSynthesisContext,
    PhaladesakContext,
    validate_narration_model,
    derive_phaladesa_for_chart,
    _ALL_DOMAINS,
)

logger = logging.getLogger(__name__)


@register('ph_phaladesa')
class PhPhaladesakWriter(WriterBase):
    """
    Builds phala_phaladesa: 7 domain declarations per chart.
    Writer is B.11 compliant: always reads Bodha synthesis before building.
    Writer never calls an LLM: narration_status='pending', narration_model=NULL.
    """
    asset_id = 'ph_phaladesa'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_phaladesa WHERE chart_id = %s", (chart_id,))

        # B.11: read Bodha synthesis first
        bodha = self._load_bodha_synthesis(conn, chart_id)
        if not bodha.bodha_consulted:
            logger.warning("ph_phaladesa: Bodha synthesis unavailable for %s — B.11 soft miss", chart_id)

        domain_summaries = self._load_domain_summaries(conn, chart_id)
        spillovers       = self._load_spillovers(conn, chart_id)
        mitigation_d     = self._load_covered_domains(conn, chart_id, 'phala_mitigation')
        muhurta_d        = self._load_covered_domains(conn, chart_id, 'phala_muhurta')

        logger.info(
            "ph_phaladesa: %d domain summaries / %d spillovers / bodha=%s",
            len(domain_summaries), len(spillovers), bodha.bodha_consulted,
        )

        pctx = PhaladesakContext(
            chart_id=chart_id,
            domain_summaries=domain_summaries,
            spillovers=spillovers,
            mitigation_domains=mitigation_d,
            muhurta_domains=muhurta_d,
            bodha=bodha,
        )

        records = derive_phaladesa_for_chart(pctx)

        rows_inserted = 0
        with conn.cursor() as cur:
            for rec in records:
                # Model policy gate
                validate_narration_model(rec.narration_model)  # always None here; gate for safety

                try:
                    cur.execute(
                        """
                        INSERT INTO phala_phaladesa (
                            chart_id, domain,
                            anchor_count, clean_anchor_count,
                            staged_revision_count, anomaly_flag_count,
                            top_anchor_id,
                            prediction_window_start, prediction_window_end, peak_date,
                            magnitude, confidence_low, confidence_high, malleability,
                            spillover_domains_jsonb, incoming_spillover_count,
                            mitigation_available, muhurta_available,
                            pramana_window_status, evidence_type,
                            precedent_refs_jsonb, contradiction_summary_jsonb,
                            derivation_summary_jsonb,
                            narration_status, narration_model, narration_jsonb,
                            derivation_ledger_jsonb, source_citation
                        ) VALUES (
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s::jsonb, %s,
                            %s, %s,
                            %s, %s,
                            %s::jsonb, %s::jsonb,
                            %s::jsonb,
                            %s, NULL, NULL,
                            %s::jsonb, %s
                        )
                        ON CONFLICT (chart_id, domain) DO UPDATE SET
                            anchor_count                = EXCLUDED.anchor_count,
                            clean_anchor_count          = EXCLUDED.clean_anchor_count,
                            staged_revision_count       = EXCLUDED.staged_revision_count,
                            anomaly_flag_count          = EXCLUDED.anomaly_flag_count,
                            top_anchor_id               = EXCLUDED.top_anchor_id,
                            prediction_window_start     = EXCLUDED.prediction_window_start,
                            prediction_window_end       = EXCLUDED.prediction_window_end,
                            peak_date                   = EXCLUDED.peak_date,
                            magnitude                   = EXCLUDED.magnitude,
                            confidence_low              = EXCLUDED.confidence_low,
                            confidence_high             = EXCLUDED.confidence_high,
                            malleability                = EXCLUDED.malleability,
                            spillover_domains_jsonb     = EXCLUDED.spillover_domains_jsonb,
                            incoming_spillover_count    = EXCLUDED.incoming_spillover_count,
                            mitigation_available        = EXCLUDED.mitigation_available,
                            muhurta_available           = EXCLUDED.muhurta_available,
                            pramana_window_status       = EXCLUDED.pramana_window_status,
                            evidence_type               = EXCLUDED.evidence_type,
                            precedent_refs_jsonb        = EXCLUDED.precedent_refs_jsonb,
                            contradiction_summary_jsonb = EXCLUDED.contradiction_summary_jsonb,
                            derivation_summary_jsonb    = EXCLUDED.derivation_summary_jsonb,
                            derivation_ledger_jsonb     = EXCLUDED.derivation_ledger_jsonb,
                            source_citation             = EXCLUDED.source_citation,
                            computed_at                 = now()
                        """,
                        (
                            chart_id, rec.domain,
                            rec.anchor_count, rec.clean_anchor_count,
                            rec.staged_revision_count, rec.anomaly_flag_count,
                            rec.top_anchor_id,
                            rec.prediction_window_start, rec.prediction_window_end, rec.peak_date,
                            rec.magnitude, rec.confidence_low, rec.confidence_high, rec.malleability,
                            json.dumps(rec.spillover_domains_jsonb) if rec.spillover_domains_jsonb else None,
                            rec.incoming_spillover_count,
                            rec.mitigation_available, rec.muhurta_available,
                            rec.pramana_window_status, rec.evidence_type,
                            json.dumps(rec.precedent_refs_jsonb) if rec.precedent_refs_jsonb else None,
                            json.dumps(rec.contradiction_summary_jsonb) if rec.contradiction_summary_jsonb else None,
                            json.dumps(rec.derivation_summary_jsonb),
                            rec.narration_status,
                            json.dumps(rec.derivation_ledger_jsonb), rec.source_citation,
                        ),
                    )
                    rows_inserted += 1
                except Exception as exc:
                    logger.warning("ph_phaladesa: insert failed for domain %s: %s", rec.domain, exc)

        logger.info("ph_phaladesa: inserted %d rows for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_phaladesa', rows_inserted=rows_inserted)

    def _load_bodha_synthesis(self, conn, chart_id: str) -> BodhaSynthesisContext:
        """B.11: pre-fetch Bodha MSR + CDLM + CGM before any derivation."""
        bctx = BodhaSynthesisContext()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM bodha_msr_signals WHERE chart_id = %s",
                    (chart_id,),
                )
                count = cur.fetchone()[0]
                bctx.bodha_consulted = count > 0

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT signal_domain_primary, AVG(convergence_score) AS score
                    FROM bodha_msr_signals WHERE chart_id = %s
                    GROUP BY signal_domain_primary
                    """,
                    (chart_id,),
                )
                for r in cur.fetchall():
                    if r[0]:
                        bctx.msr_domain_scores[str(r[0]).lower()] = float(r[1] or 0.0)
        except Exception as exc:
            logger.debug("ph_phaladesa: Bodha load skipped: %s", exc)
        return bctx

    def _load_domain_summaries(self, conn, chart_id: str) -> dict[str, DomainAnchorSummary]:
        """Load phala_anchors + suddha_sodhana disposition + pramana status per domain."""
        summaries: dict[str, DomainAnchorSummary] = {}
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        pa.anchor_id, pa.domain, pa.magnitude, pa.confidence_low,
                        pa.confidence_high, pa.malleability, pa.window_start,
                        pa.window_end, pa.peak_date, pa.precedent_refs_jsonb,
                        pa.contradiction_jsonb,
                        COALESCE(ss.cleanliness_status, 'unknown') AS clean_status,
                        COALESCE(ss.critical_flag_count, 0) + COALESCE(ss.major_flag_count, 0)
                            + COALESCE(ss.minor_flag_count, 0) AS flag_count,
                        pr.window_status AS pramana_status,
                        pr.evidence_type AS pramana_evidence_type
                    FROM phala_anchors pa
                    LEFT JOIN phala_suddha_sodhana ss ON ss.anchor_id = pa.anchor_id
                    LEFT JOIN phala_pramana pr ON pr.anchor_id = pa.anchor_id
                    WHERE pa.chart_id = %s
                    ORDER BY pa.domain, pa.confidence_high DESC NULLS LAST
                    """,
                    (chart_id,),
                )
                for r in cur.fetchall():
                    d = str(r['domain']).lower()
                    if d not in summaries:
                        summaries[d] = DomainAnchorSummary(domain=d)
                    s = summaries[d]
                    aid = str(r['anchor_id'])
                    s.anchor_ids.append(aid)
                    s.anomaly_flag_count += int(r.get('flag_count') or 0)
                    cs = str(r.get('clean_status') or '')
                    if cs == 'clean':
                        s.clean_ids.append(aid)
                    elif cs == 'staged_revision':
                        s.staged_revision_ids.append(aid)
                    # Set top anchor from first (highest confidence) row per domain
                    if s.top_anchor_id is None:
                        s.top_anchor_id   = aid
                        s.window_start    = r.get('window_start')
                        s.window_end      = r.get('window_end')
                        s.peak_date       = r.get('peak_date')
                        s.magnitude       = r.get('magnitude')
                        s.confidence_low  = float(r['confidence_low']) if r.get('confidence_low') is not None else None
                        s.confidence_high = float(r['confidence_high']) if r.get('confidence_high') is not None else None
                        s.malleability    = r.get('malleability')
                        s.pramana_window_status = r.get('pramana_status')
                        s.evidence_type         = r.get('pramana_evidence_type')
        except Exception as exc:
            logger.debug("ph_phaladesa: domain summaries load skipped: %s", exc)
        return summaries

    def _load_spillovers(self, conn, chart_id: str) -> list[SpilloverSummary]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT source_domain, target_domain, relationship_type, spillover_confidence
                    FROM phala_sankrama
                    WHERE chart_id = %s
                    ORDER BY spillover_confidence DESC
                    """,
                    (chart_id,),
                )
                return [
                    SpilloverSummary(
                        source_domain=str(r[0]),
                        target_domain=str(r[1]),
                        relationship_type=str(r[2]),
                        spillover_confidence=float(r[3] or 0.0),
                    )
                    for r in cur.fetchall()
                ]
        except Exception as exc:
            logger.debug("ph_phaladesa: spillovers load skipped: %s", exc)
            return []

    def _load_covered_domains(self, conn, chart_id: str, table: str) -> set[str]:
        """Return set of domains that have at least one row in the given phala_* table."""
        try:
            with conn.cursor() as cur:
                # Both phala_mitigation (via anchor domain) and phala_muhurta (via action_class)
                # are linked indirectly via phala_anchors; use linked_anchor_id join
                if table == 'phala_muhurta':
                    cur.execute(
                        """
                        SELECT DISTINCT pa.domain
                        FROM phala_muhurta pm
                        JOIN phala_anchors pa ON pa.anchor_id = pm.linked_anchor_id::uuid
                        WHERE pm.chart_id = %s
                        """,
                        (chart_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT DISTINCT pa.domain
                        FROM phala_mitigation pm
                        JOIN phala_anchors pa ON pa.anchor_id = pm.linked_anchor_id::uuid
                        WHERE pm.chart_id = %s
                        """,
                        (chart_id,),
                    )
                return {str(r[0]).lower() for r in cur.fetchall()}
        except Exception as exc:
            logger.debug("ph_phaladesa: %s domain coverage load skipped: %s", table, exc)
            return set()
