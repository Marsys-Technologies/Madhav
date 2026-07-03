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
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
            notes=f"brahma_formula_constants: {total} constants (classical + native_judgment + engineering + conflation_bug)",
        )
