"""
bg_reference writer — populates the 5 typed reference tables.
Delegates to brahmagyan.l0_reference.seed_reference() for actual INSERT logic.
Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_reference import seed_reference

logger = logging.getLogger(__name__)


@register('bg_reference')
class ReferenceWriter(WriterBase):
    asset_id = 'bg_reference'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        # autocommit=False: caller (asset_runner) owns the transaction boundary
        counts = seed_reference(ctx.db_conn, ctx.build_id, dry_run=ctx.dry_run, autocommit=False)
        # counts is a dict like {'reference_planets': N, 'reference_nakshatras': N, ...}
        total_inserted = sum(counts.values()) if isinstance(counts, dict) else int(counts or 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            duration_seconds=time.time() - t0,
            notes=f'5 reference tables: {counts}',
        )
