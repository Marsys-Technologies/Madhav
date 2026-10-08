"""
bg_formula_constants writer — populates brahma_formula_constants with canonical
formula constants (combustion orbs, obstruction thresholds, dignity scores,
house weights, attention budget, calibration constants).

Source data: brahmagyan.l0_formula_constants — W1 seed package §7.

§N.3: L0 idempotency — ON CONFLICT DO UPDATE (global, not per-chart).
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_formula_constants import seed_formula_constants

logger = logging.getLogger(__name__)


@register('bg_formula_constants')
class FormulaConstantsWriter(WriterBase):
    asset_id = 'bg_formula_constants'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_formula_constants(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        total = counts.get("brahma_formula_constants", 0)
        # WFIX-A: rows_inserted is the whole table as it stands (registry count_sql), writer-owned
        # operational constants AND the migration-owned governed constants the writer preserves --
        # the seeder's figure (10) counts only the former, against 17 live rows. A dry run writes nothing.
        present = total
        if not ctx.dry_run:
            from pipeline.orchestrator.writers._rows_present import present_count
            with ctx.db_conn.cursor() as cur:
                cur.execute(ROWS_PRESENT_SQL)
                present = present_count(cur.fetchone())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=present,
            duration_seconds=time.time() - t0,
            notes=(
                f"brahma_formula_constants: {total} writer-owned operational constants seeded; "
                f"{present} rows present (migration-owned governed constants are preserved)"
            ),
        )


# WFIX-A: the rows-present statement is a literal at the module end (resolved at call time) so no line above it shifts and
# the writer-line citations in the declarations keep pointing at the same code; the census scans it as the asset's own read.
# The declared produced-table set: registry count_sql SELECT count(*) FROM brahma_formula_constants.
ROWS_PRESENT_SQL = "SELECT count(*) AS n FROM brahma_formula_constants"
