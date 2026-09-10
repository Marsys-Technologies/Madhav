"""
mi_seva — Serve-time Apply Service Handler (L5 Mīmāṃsā)
=========================================================
Service handler: applies calibration overlays at serve time for a given chart.
Reads mimamsa_multipliers and overlay tables to produce an adjusted reading bundle.
Writes a journal entry to mimamsa_journal when a prediction is surfaced to the native.

This writer creates NO build-time rows. It is invoked by the retrieval layer at
serve time, not by the orchestrator build.

GLOBAL scope (service handler — no DELETE/INSERT at build time).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)


@register("mi_seva")
class MiSevaWriter(WriterBase):
    """
    Service handler: verifies overlay infrastructure is present.
    Actual serve-time logic lives in services/mi_seva/handler.py (TypeScript retrieval layer).
    """

    asset_id = "mi_seva"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # Verify overlay infrastructure
        tables_required = [
            "mimamsa_multipliers",
            "mimamsa_signal_adjustment",
            "mimamsa_insight_units",
            "mimamsa_journal",
        ]
        missing = []
        for tbl in tables_required:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = %s AND table_schema = 'public'",
                    (tbl,),
                )
                if not cur.fetchone():
                    missing.append(tbl)

        if missing:
            # A1 (L5-W3, adjudication #1738).  This used to return a
            # WriterResult carrying "WARNING: missing tables …" in `notes`.
            # Nothing in pipeline/orchestrator/ outside writers/ ever reads
            # `notes` -- asset_runner.py reads only rows_inserted and
            # rows_updated -- and this asset has target_floor = 0, so
            # zero_rows_is_complete promoted it to 'lit'.  A dropped
            # mimamsa_journal produced a GREEN BUILD.
            #
            # This writer's entire job is verifying serve-time apply
            # infrastructure.  A missing table means the verification could not
            # RUN -- not that it passed.  Its sibling mi_vistara.py raises on
            # the identical check against mimamsa_export_log; that is the
            # correct precedent and this now matches it.
            raise RuntimeError(
                f"mi_seva: required service tables absent: {missing} — apply the "
                "L5 migrations before building. This writer verifies serve-time "
                "apply infrastructure; a missing table means the verification "
                "could not run, not that it passed."
            )

        logger.info("[mi_seva] service infrastructure verified — all tables present")
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes="serve-time apply handler verified; no build-time rows",
        )
