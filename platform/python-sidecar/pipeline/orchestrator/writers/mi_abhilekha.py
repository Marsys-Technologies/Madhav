"""
mi_abhilekha — Journal Re-sync Service Handler (L5 Mīmāṃsā)
=============================================================
Service handler: re-syncs prediction outcomes from native journal entries
(mimamsa_journal) back into mimamsa_calibration by updating lifecycle_status
on the matching predictions. Called by the retrieval layer when the native
provides an answered journal entry.

This writer creates NO build-time rows. It registers as an asset so the
orchestrator can verify its readiness state and count journal entries.

GLOBAL scope (service handler).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import logging
import time

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)


@register("mi_abhilekha")
class MiAbhilekhaWriter(WriterBase):
    """
    Service handler: counts journal entries and propagates answered outcomes
    to mimamsa_predictions.lifecycle_status. No build-time INSERT rows.
    """

    asset_id = "mi_abhilekha"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # Count pending journal entries (answered but not yet synced to calibration)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT COUNT(*) AS total, "
                "       COUNT(*) FILTER (WHERE answered_at IS NOT NULL) AS answered, "
                "       COUNT(*) FILTER (WHERE resulting_event_id IS NOT NULL) AS linked "
                "FROM mimamsa_journal"
            )
            r = cur.fetchone()
            total = r["total"] if r else 0
            answered = r["answered"] if r else 0
            linked = r["linked"] if r else 0

        # Propagate answered entries: update predictions lifecycle_status
        updated = 0
        if answered > 0:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT j.chart_id, j.prediction_id, j.resulting_event_id, j.native_answer "
                    "FROM mimamsa_journal j "
                    "WHERE j.answered_at IS NOT NULL AND j.resulting_event_id IS NOT NULL"
                )
                answered_entries = cur.fetchall()

            for entry in answered_entries:
                answer = (entry.get("native_answer") or "").lower()
                new_status = "confirmed" if "yes" in answer or "confirmed" in answer else "denied"
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mimamsa_predictions SET lifecycle_status = %s "
                        "WHERE chart_id = %s AND prediction_id = %s "
                        "AND lifecycle_status = 'pending'",
                        (new_status, entry["chart_id"], entry["prediction_id"]),
                    )
                    updated += cur.rowcount

        logger.info(
            "[mi_abhilekha] journal: total=%d answered=%d linked=%d; updated %d prediction statuses",
            total, answered, linked, updated,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=updated,
            duration_seconds=time.time() - t0,
            notes=f"journal entries: total={total} answered={answered} linked={linked}; "
                  f"{updated} predictions updated",
        )
