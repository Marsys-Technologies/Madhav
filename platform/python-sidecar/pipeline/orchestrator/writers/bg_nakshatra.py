"""
bg_nakshatra writer — populates the 3 nakshatra reference tables.

L0 global asset. ON CONFLICT idempotency (no chart_id).
Delegates to brahmagyan.l0_nakshatra.seed_nakshatra() for all INSERT logic.

§N.3: L0 idempotency — ON CONFLICT DO NOTHING.
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.
"""
from __future__ import annotations
import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_nakshatra import seed_nakshatra

logger = logging.getLogger(__name__)


@register('bg_nakshatra')
class NakshatraReferenceWriter(WriterBase):
    asset_id = 'bg_nakshatra'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_nakshatra(
            ctx.db_conn,
            ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        total = sum(counts.values())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f"3 nakshatra tables: {counts}",
        )
