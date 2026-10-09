"""
pipeline/orchestrator/writers/ga_prashna.py
Heavy writer adapter for ga_prashna.
Delegates computation to ga_writers/ga_prashna_writer.py.

FROZEN WriterBase contract:
  - @register('ga_prashna')
  - has_substeps = True (one per ayanamsha)
  - plan_substeps(ctx) → 5 SubSteps
  - run_substep(ctx, step) → WriterResult
  - NEVER calls conn.commit() or conn.close()
  - NEVER writes asset_throughput
  - Early-returns WriterResult(rows_inserted=0) if not a prashna chart
"""
from __future__ import annotations
from ga_writers.data_plane_runtime import l1_producer_contract
from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register
from brahmagyan.ayanamsha_scope import ayanamshas_for_chart
from ga_writers.ga_prashna_writer import CANONICAL_AYANAMSHAS  # noqa: F401  (re-export: the default set)


@register("ga_prashna")
@l1_producer_contract
class GaPrashnaWriter(WriterBase):
    asset_id = "ga_prashna"
    has_substeps = True

    def plan_substeps(self, ctx) -> list[SubStep]:
        return [
            SubStep(
                key=f"ayanamsha_{ayanamsha_id}",
                label=f"Prashna judgment — {ayanamsha_id}",
            )
            for ayanamsha_id in ayanamshas_for_chart(ctx.db_conn, ctx.config["chart_id"])
        ]

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        from ga_writers.ga_prashna_writer import seed_prashna_judgment

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
            )

        ayanamsha_id = step.key.replace("ayanamsha_", "")
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id

        rows = seed_prashna_judgment(
            ctx.db_conn,
            chart_id,
            ayanamsha_id,
            build_id,
            dry_run=False,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows,
            notes=f"ayanamsha={ayanamsha_id} rows={rows}",
        )
