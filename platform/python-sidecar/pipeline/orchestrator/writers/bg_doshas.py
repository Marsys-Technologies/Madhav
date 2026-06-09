"""
bg_doshas writer — populates brahma_dosha_catalog + brahma_ontology (dosha class) + reference_doshas.
Delegates to brahmagyan.l0_doshas.seed_doshas() for actual INSERT logic.
Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_doshas import seed_doshas

logger = logging.getLogger(__name__)


@register('bg_doshas')
class DoshasWriter(WriterBase):
    asset_id = 'bg_doshas'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_doshas(ctx.db_conn, ctx.build_id, dry_run=ctx.dry_run, autocommit=False)
        # counts = {catalog_inserted, ontology_inserted, ref_inserted, catalog_skipped}
        catalog_ins = counts.get('catalog_inserted', 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=catalog_ins,
            rows_skipped=counts.get('catalog_skipped', 0),
            duration_seconds=time.time() - t0,
            notes=(
                f"brahma_dosha_catalog: +{catalog_ins}; "
                f"brahma_ontology(dosha): +{counts.get('ontology_inserted', 0)}; "
                f"reference_doshas: +{counts.get('ref_inserted', 0)}"
            ),
        )
