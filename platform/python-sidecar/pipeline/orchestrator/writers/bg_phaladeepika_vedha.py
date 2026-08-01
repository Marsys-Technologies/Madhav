"""
bg_phaladeepika_vedha writers — populate bg_vedha_malefic_scale (5 rows) and
bg_phaladeepika_latta (8 rows), the two cited L0 vedha reference tables
ADJUDICATION-11 Part 4 mandates for R-19 closure.

See brahmagyan.l0_phaladeepika_vedha for the full disclosure (verbatim
source text, citation tier, honest gaps, versioning discipline).

L0 global assets. ON CONFLICT DO UPDATE idempotency (no chart_id), per §N.3.
§N.2: Frozen orchestrator contract — run(ctx) -> WriterResult, never commits.

depends_on: [] for both — pure reference data, no upstream dependency.
Downstream: ka_vedha_gochara (L3 Kāla) depends on both assets.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_phaladeepika_vedha import seed_vedha_malefic_scale, seed_phaladeepika_latta

logger = logging.getLogger(__name__)


@register('bg_vedha_malefic_scale')
class VedhaMaleficScaleWriter(WriterBase):
    asset_id = 'bg_vedha_malefic_scale'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_vedha_malefic_scale(ctx.db_conn, dry_run=ctx.dry_run, autocommit=False)
        total = counts.get("bg_vedha_malefic_scale", 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f"bg_vedha_malefic_scale: {total} rows (Phaladeepika PG353, ADJUDICATION-11)",
        )


@register('bg_phaladeepika_latta')
class PhaladeepikaLattaWriter(WriterBase):
    asset_id = 'bg_phaladeepika_latta'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_phaladeepika_latta(ctx.db_conn, dry_run=ctx.dry_run, autocommit=False)
        total = counts.get("bg_phaladeepika_latta", 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f"bg_phaladeepika_latta: {total} rows (Phaladeepika PG338-339, ADJUDICATION-11)",
        )
