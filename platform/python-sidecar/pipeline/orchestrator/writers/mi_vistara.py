"""
mi_vistara — Export-Integrity Ledger (L5 Mīmāṃsā)
==================================================
Append-only export log: one row per calibrated export event, capturing
payload hash, included insight IDs, disclosure bundle, and calibration mode.

This writer is a service asset — it creates NO rows at build time.
Rows are inserted by the mi_seva service handler when exports are actually
delivered. This writer only verifies the table exists and is clean.

GLOBAL scope (append-only log; no per-chart DELETE).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

EXPORT_FORMULA_VERSION = "mi_vistara_v1.0"


@register("mi_vistara")
class MiVistaraWriter(WriterBase):
    """
    Service asset: no build-time rows generated.
    Verifies mimamsa_export_log exists and logs readiness.
    """

    asset_id = "mi_vistara"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # Verify table exists (should have been created by migration 355)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'mimamsa_export_log' AND table_schema = 'public'"
            )
            exists = cur.fetchone() is not None

        if not exists:
            raise RuntimeError(
                "mimamsa_export_log table not found — ensure migration 355 has been applied"
            )

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM mimamsa_export_log")
            r = cur.fetchone()
            count = r[0] if r else 0

        logger.info(
            "[mi_vistara] export ledger ready — %d existing export records "
            "(append-only; no build-time rows generated)", count
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=f"export ledger verified; {count} historical export records present",
        )
