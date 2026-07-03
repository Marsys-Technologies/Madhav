"""
bg_class_priors writer — populates brahma_class_priors (165 rows across 5 prior axes).

Source data: brahmagyan.l0_class_priors — signal_type_class, source_subsystem,
signal_tradition, varga, and graha×domain priors from W1 seed package §2–§4.

§N.3: L0 idempotency — ON CONFLICT DO UPDATE (global, not per-chart).
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_class_priors import seed_class_priors

logger = logging.getLogger(__name__)


@register('bg_class_priors')
class ClassPriorsWriter(WriterBase):
    asset_id = 'bg_class_priors'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_class_priors(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        total = counts.get("brahma_class_priors", 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f"brahma_class_priors: {total} rows (17 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha×domain)",
        )
