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
        # WFIX-A: report the rows PRESENT in brahma_ontology (registry count_sql: whole table), not the
        # rows this run newly inserted -- 0 on every converged rerun against 728 live rows. A dry run
        # writes nothing, so it keeps the seeder's own figure.
        present = inserted
        if not ctx.dry_run:
            from pipeline.orchestrator.writers._rows_present import present_count
            with ctx.db_conn.cursor() as cur:
                cur.execute(ROWS_PRESENT_SQL)
                present = present_count(cur.fetchone())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=present,
            rows_skipped=counts.get('skipped', 0) if isinstance(counts, dict) else 0,
            duration_seconds=time.time() - t0,
            notes=f'brahma_ontology: {counts}; newly_inserted={inserted}',
        )


# WFIX-A: the rows-present statement is a literal at the module end (resolved at call time) so no line above it shifts and
# the writer-line citations in the declarations keep pointing at the same code; the census scans it as the asset's own read.
# The declared produced-table set: registry count_sql SELECT count(*) FROM brahma_ontology.
ROWS_PRESENT_SQL = "SELECT count(*) AS n FROM brahma_ontology"
