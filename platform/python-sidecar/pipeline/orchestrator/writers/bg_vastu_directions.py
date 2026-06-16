"""
bg_vastu_directions writer — seeds Astrovastu Gate-1 L0 direction reference tables.

Populates:
  bg_vastu_directions           (8 rows — compass directions with ruling graha)
  bg_vastu_direction_remedials  (~22 rows — 2–3 remedies per direction)

Delegates to brahmagyan.l0_vastu_directions.seed_vastu_directions().
L0 idempotency: ON CONFLICT (direction) DO UPDATE / ON CONFLICT DO NOTHING.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_vastu_directions import seed_vastu_directions

logger = logging.getLogger(__name__)


@register('bg_vastu_directions')
class BgVastuDirectionsWriter(WriterBase):
    asset_id = 'bg_vastu_directions'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        # autocommit=False: caller (asset_runner / orchestrator) owns the transaction boundary
        counts = seed_vastu_directions(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        total_inserted = sum(counts.values()) if isinstance(counts, dict) else int(counts or 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            duration_seconds=time.time() - t0,
            notes=f'2 vastu direction tables: {counts}',
        )
