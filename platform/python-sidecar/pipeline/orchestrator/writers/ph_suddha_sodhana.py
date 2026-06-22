"""
ph_suddha_sodhana — Cleansed Anchor Disposition (L4 Phala wave 5).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_suddha_sodhana.

Reads: phala_anchors · phala_sodhana (flags for each anchor)
Writes: phala_suddha_sodhana (delete-then-insert per chart_id)

D43 SAFETY RAIL: revision_approved_by and revision_applied_at are NEVER inserted.
Any code that attempts to set them here is a critical bug.
"""
from __future__ import annotations

import json
import logging

import psycopg2.extras

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_suddha_sodhana.engine import (
    FlagSummary,
    SuddhaContext,
    derive_suddha_record,
)

logger = logging.getLogger(__name__)


@register('ph_suddha_sodhana')
class PhSuddhaSodhanaWriter(WriterBase):
    """
    Builds phala_suddha_sodhana: one row per phala_anchors entry, classified
    as clean / flagged / staged_revision based on phala_sodhana flags.
    D43 safety rail: revision_approved_by + revision_applied_at always NULL.
    """
    asset_id = 'ph_suddha_sodhana'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_suddha_sodhana WHERE chart_id = %s", (chart_id,))

        anchor_ids = self._load_anchor_ids(conn, chart_id)
        flags_by_anchor = self._load_flags_grouped(conn, chart_id)

        logger.info(
            "ph_suddha_sodhana: %d anchors / %d flagged anchors",
            len(anchor_ids), len(flags_by_anchor),
        )

        sctx = SuddhaContext(chart_id=chart_id)
        rows_inserted = 0

        with conn.cursor() as cur:
            for anchor_id in anchor_ids:
                fs = flags_by_anchor.get(anchor_id) or FlagSummary(anchor_id=anchor_id)
                rec = derive_suddha_record(sctx, fs)

                # D43 SAFETY RAIL: explicitly verify engine never set these
                assert rec.revision_approved_by is None, "D43 VIOLATED: engine set revision_approved_by"
                assert rec.revision_applied_at is None,  "D43 VIOLATED: engine set revision_applied_at"

                try:
                    cur.execute(
                        """
                        INSERT INTO phala_suddha_sodhana (
                            chart_id, anchor_id,
                            cleanliness_status,
                            critical_flag_count, major_flag_count, minor_flag_count,
                            flag_ids_jsonb,
                            staged_revision_jsonb,
                            revision_approved_by, revision_applied_at,
                            confidence_delta_if_applied, magnitude_delta_if_applied,
                            derivation_ledger_jsonb, source_citation
                        ) VALUES (
                            %s, %s,
                            %s,
                            %s, %s, %s,
                            %s::jsonb,
                            %s::jsonb,
                            NULL, NULL,
                            %s, %s,
                            %s::jsonb, %s
                        )
                        ON CONFLICT (chart_id, anchor_id) DO UPDATE SET
                            cleanliness_status          = EXCLUDED.cleanliness_status,
                            critical_flag_count         = EXCLUDED.critical_flag_count,
                            major_flag_count            = EXCLUDED.major_flag_count,
                            minor_flag_count            = EXCLUDED.minor_flag_count,
                            flag_ids_jsonb              = EXCLUDED.flag_ids_jsonb,
                            staged_revision_jsonb       = EXCLUDED.staged_revision_jsonb,
                            confidence_delta_if_applied = EXCLUDED.confidence_delta_if_applied,
                            magnitude_delta_if_applied  = EXCLUDED.magnitude_delta_if_applied,
                            derivation_ledger_jsonb     = EXCLUDED.derivation_ledger_jsonb,
                            source_citation             = EXCLUDED.source_citation,
                            computed_at                 = now()
                        """,
                        (
                            chart_id, rec.anchor_id,
                            rec.cleanliness_status,
                            rec.critical_flag_count, rec.major_flag_count, rec.minor_flag_count,
                            json.dumps(rec.flag_ids_jsonb) if rec.flag_ids_jsonb else None,
                            json.dumps(rec.staged_revision_jsonb) if rec.staged_revision_jsonb else None,
                            rec.confidence_delta_if_applied, rec.magnitude_delta_if_applied,
                            json.dumps(rec.derivation_ledger_jsonb), rec.source_citation,
                        ),
                    )
                    rows_inserted += 1
                except Exception as exc:
                    logger.warning("ph_suddha_sodhana: insert failed for anchor %s: %s", anchor_id, exc)

        logger.info(
            "ph_suddha_sodhana: inserted %d rows into phala_suddha_sodhana for %s",
            rows_inserted, chart_id,
        )
        return WriterResult(asset_id='ph_suddha_sodhana', rows_inserted=rows_inserted)

    def _load_anchor_ids(self, conn, chart_id: str) -> list[str]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT anchor_id FROM phala_anchors WHERE chart_id = %s ORDER BY anchor_id",
                (chart_id,),
            )
            return [str(row[0]) for row in cur.fetchall()]

    def _load_flags_grouped(self, conn, chart_id: str) -> dict[str, FlagSummary]:
        """Load phala_sodhana rows grouped by anchor_id."""
        result: dict[str, FlagSummary] = {}
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT sodhana_id, anchor_id, anomaly_type, anomaly_severity,
                           detected_field, expected_value_text, observed_value_text,
                           recommendation_text
                    FROM phala_sodhana
                    WHERE chart_id = %s
                    ORDER BY anchor_id, anomaly_severity
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    aid = str(row['anchor_id'])
                    if aid not in result:
                        result[aid] = FlagSummary(anchor_id=aid)
                    fs = result[aid]
                    sev = str(row.get('anomaly_severity') or '')
                    fs.sodhana_ids.append(str(row['sodhana_id']))
                    fs.flag_details.append({
                        'sodhana_id':       str(row['sodhana_id']),
                        'anomaly_type':     row.get('anomaly_type'),
                        'severity':         sev,
                        'detected_field':   row.get('detected_field'),
                        'expected':         row.get('expected_value_text'),
                        'observed':         row.get('observed_value_text'),
                        'recommendation':   row.get('recommendation_text'),
                    })
                    if sev == 'critical':
                        fs.critical_count += 1
                    elif sev == 'major':
                        fs.major_count += 1
                    elif sev == 'minor':
                        fs.minor_count += 1
                    else:
                        fs.informational_count += 1
        except Exception as exc:
            logger.debug("ph_suddha_sodhana: flags load skipped: %s", exc)
        return result
