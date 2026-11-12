"""
bg_reference writer — populates the typed reference tables.
Delegates to brahmagyan.l0_reference.seed_reference_borrowed() for INSERT logic.
Per holistic design v1.1: ZERO LLM use.
"""
from __future__ import annotations
import logging
import time

import psycopg.rows

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_reference import seed_reference_borrowed

logger = logging.getLogger(__name__)


@register('bg_reference')
class ReferenceWriter(WriterBase):
    asset_id = 'bg_reference'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        # The orchestrator uses dict_row. The reference seed reads the
        # ontology check by tuple position, so scope tuple_row to that call.
        prior_row_factory = getattr(conn, "row_factory", None)
        conn.row_factory = psycopg.rows.tuple_row
        try:
            counts = seed_reference_borrowed(conn, ctx.build_id, dry_run=ctx.dry_run)
        finally:
            conn.row_factory = prior_row_factory
        # counts is a dict like {'reference_planets': N, 'reference_nakshatras': N, ...}
        total_inserted = sum(counts.values()) if isinstance(counts, dict) else int(counts or 0)
        # WFIX-A: rows PRESENT across the eleven reference tables after the seed, not the seeder's
        # newly-inserted sum (0 on a converged rerun against 1,242 live rows). A dry run writes nothing.
        present = total_inserted
        if not ctx.dry_run:
            from pipeline.orchestrator.writers._rows_present import present_count
            with conn.cursor() as cur:
                cur.execute(ROWS_PRESENT_SQL)
                present = present_count(cur.fetchone())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=present,
            duration_seconds=time.time() - t0,
            notes=f'reference tables: {counts}; newly_inserted={total_inserted}',
        )


# WFIX-A: the rows-present statement is a literal at the module end (resolved at call time) so no line above it shifts and
# the writer-line citations in the declarations keep pointing at the same code; the census scans it as the asset's own read.
# The declared produced-table set: the eleven tables of the registry count_sql.
ROWS_PRESENT_SQL = (
    "SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs)"
    " + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas)"
    " + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems)"
    " + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas)"
    " + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags)"
    " + (SELECT count(*) FROM reference_glossary) AS n"
)
