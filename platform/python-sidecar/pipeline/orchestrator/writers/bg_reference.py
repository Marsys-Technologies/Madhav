"""
bg_reference writer — populates the 5 typed reference tables.
Delegates to brahmagyan.l0_reference.seed_reference() for actual INSERT logic.
Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time

import psycopg.rows

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_reference import seed_reference

logger = logging.getLogger(__name__)


@register('bg_reference')
class ReferenceWriter(WriterBase):
    asset_id = 'bg_reference'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        # The orchestrator connection is created with row_factory=dict_row
        # (pipeline/orchestrator/db.py:26), but the delegate
        # brahmagyan.l0_reference.seed_reference indexes fetched rows
        # numerically (l0_reference.py:1418, `r[0]` on the brahma_ontology
        # FK-validation query) — the KeyError: 0 that put this asset into
        # error state in the 2026-08-02 L0 global build (run 6fd72ed9).
        # l0_reference.py is a shared brahmagyan module outside this writer
        # lane's scope, so the fix is applied at this boundary: pin tuple_row
        # for the duration of the delegate call and restore the caller's
        # factory in a finally. row_factory only affects cursors opened after
        # this point; the writer still never commits/closes the connection
        # (FROZEN contract, §N.2).
        prior_row_factory = getattr(conn, "row_factory", None)
        conn.row_factory = psycopg.rows.tuple_row
        try:
            # autocommit=False: caller (asset_runner) owns the transaction boundary
            counts = seed_reference(conn, ctx.build_id, dry_run=ctx.dry_run, autocommit=False)
        finally:
            conn.row_factory = prior_row_factory
        # counts is a dict like {'reference_planets': N, 'reference_nakshatras': N, ...}
        total_inserted = sum(counts.values()) if isinstance(counts, dict) else int(counts or 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            duration_seconds=time.time() - t0,
            notes=f'5 reference tables: {counts}',
        )
