"""
ph_sodhana — Predictive Anchor Anomaly Detection (L4 Phala wave 5).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_sodhana.

Reads: phala_anchors
Writes: phala_sodhana (delete-then-insert per chart_id)
Raises: LeakageFirewallError → build halt (D43a)
"""
from __future__ import annotations

import json
import logging

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_sodhana.engine import (
    AnchorRow,
    SodhanaContext,
    LeakageFirewallError,
    derive_sodhana_flags,
)

logger = logging.getLogger(__name__)


@register('ph_sodhana')
class PhSodhanaWriter(WriterBase):
    """
    Builds phala_sodhana: scans every phala_anchors row for anomalies.
    LEAKAGE-FIREWALL: if any anchor has L5 calibration contamination,
    derive_sodhana_flags raises LeakageFirewallError and the build halts.
    """
    asset_id = 'ph_sodhana'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_sodhana WHERE chart_id = %s", (chart_id,))

        anchors = self._load_anchors(conn, chart_id)
        logger.info("ph_sodhana: scanning %d anchors for anomalies", len(anchors))

        sctx = SodhanaContext(chart_id=chart_id, anchors=anchors)

        # derive_sodhana_flags raises LeakageFirewallError if L5 contamination found
        flags = derive_sodhana_flags(sctx)

        logger.info("ph_sodhana: %d anomaly flags detected", len(flags))

        rows_inserted = 0
        with conn.cursor() as cur:
            for rec in flags:
                try:
                    cur.execute(
                        """
                        INSERT INTO phala_sodhana (
                            chart_id, anchor_id,
                            anomaly_type, anomaly_severity, detected_field,
                            expected_value_text, observed_value_text,
                            leakage_class, recommendation_text,
                            auto_action,
                            derivation_ledger_jsonb, source_citation
                        ) VALUES (
                            %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s,
                            %s::jsonb, %s
                        )
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            chart_id, rec.anchor_id,
                            rec.anomaly_type, rec.anomaly_severity, rec.detected_field,
                            rec.expected_value_text, rec.observed_value_text,
                            rec.leakage_class, rec.recommendation_text,
                            rec.auto_action,
                            json.dumps(rec.derivation_ledger_jsonb), rec.source_citation,
                        ),
                    )
                    rows_inserted += 1
                except Exception as exc:
                    logger.warning("ph_sodhana: insert failed for anchor %s: %s", rec.anchor_id, exc)

        logger.info("ph_sodhana: inserted %d rows into phala_sodhana for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_sodhana', rows_inserted=rows_inserted)

    def _load_anchors(self, conn, chart_id: str) -> list[AnchorRow]:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT anchor_id, anchor_source, domain,
                       confidence_low, confidence_high, confidence_basis,
                       magnitude, falsifier, derivation_ledger_jsonb,
                       dasha_consensus_count, ayanamsha_robustness, convergence_id
                FROM phala_anchors
                WHERE chart_id = %s
                ORDER BY anchor_id
                """,
                (chart_id,),
            )
            rows: list[AnchorRow] = []
            for r in cur.fetchall():
                ledger = r.get('derivation_ledger_jsonb') or {}
                if isinstance(ledger, str):
                    try:
                        import json as _j
                        ledger = _j.loads(ledger)
                    except Exception:
                        ledger = {}
                rows.append(AnchorRow(
                    anchor_id=str(r['anchor_id']),
                    anchor_source=str(r.get('anchor_source') or ''),
                    domain=str(r.get('domain') or ''),
                    confidence_low=float(r['confidence_low']) if r.get('confidence_low') is not None else None,
                    confidence_high=float(r['confidence_high']) if r.get('confidence_high') is not None else None,
                    confidence_basis=str(r.get('confidence_basis') or '') or None,
                    magnitude=str(r.get('magnitude') or '') or None,
                    falsifier=str(r.get('falsifier') or '') or None,
                    derivation_ledger_jsonb=ledger if isinstance(ledger, dict) else {},
                    dasha_consensus_count=int(r['dasha_consensus_count']) if r.get('dasha_consensus_count') is not None else None,
                    ayanamsha_robustness=int(r['ayanamsha_robustness']) if r.get('ayanamsha_robustness') is not None else None,
                    convergence_id=r.get('convergence_id'),
                ))
            return rows
