"""
bg_dasha_systems writer — populates brahma_dasha_systems + ontology + pointer rows.
Delegates to brahmagyan.l0_dasha_systems.seed_dasha_systems() for actual INSERT logic.
Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_dasha_systems import seed_dasha_systems

logger = logging.getLogger(__name__)


@register('bg_dasha_systems')
class DashaSystemsWriter(WriterBase):
    asset_id = 'bg_dasha_systems'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        # autocommit=False: caller (asset_runner) owns the transaction boundary
        counts = seed_dasha_systems(ctx.db_conn, ctx.build_id, dry_run=ctx.dry_run, autocommit=False)
        # counts is a dict: {brahma_dasha_systems, brahma_ontology, reference_dasha_systems}
        catalog_inserted = counts.get("brahma_dasha_systems", 0)
        total_inserted = sum(counts.values()) if isinstance(counts, dict) else int(counts or 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=catalog_inserted,  # rows_inserted = catalog rows (the asset's primary table)
            duration_seconds=time.time() - t0,
            notes=f'3 tables: {counts}',
        )
