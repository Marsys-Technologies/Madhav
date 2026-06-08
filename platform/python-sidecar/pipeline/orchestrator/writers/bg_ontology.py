"""
bg_ontology writer — populates brahma_ontology with canonical entity vocabulary.
Delegates to brahmagyan.l0_ontology.seed_ontology() for actual INSERT logic.
Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_ontology import seed_ontology

logger = logging.getLogger(__name__)


@register('bg_ontology')
class OntologyWriter(WriterBase):
    asset_id = 'bg_ontology'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        # autocommit=False: caller (asset_runner / smoke test) owns the transaction boundary
        counts = seed_ontology(ctx.db_conn, ctx.build_id, dry_run=ctx.dry_run, autocommit=False)
        # counts is {'total': N, 'inserted': N, 'skipped': N, 'by_class': {...}}
        inserted = counts.get('inserted', 0) if isinstance(counts, dict) else int(counts or 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            rows_skipped=counts.get('skipped', 0) if isinstance(counts, dict) else 0,
            duration_seconds=time.time() - t0,
            notes=f'brahma_ontology: {counts}',
        )
