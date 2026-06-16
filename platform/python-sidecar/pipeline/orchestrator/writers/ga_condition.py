"""Orchestrator adapter for the L1 Gaṇita `ga_condition` writer (HEAVY).

Planetary Condition Composite — one sub-step per ayanamsha.
9 grahas × 5 ayanamshas = 45 rows per chart.
Delegates to ga_condition_writer.build_ga_condition_substep().
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep


@register('ga_condition')
class GaConditionWriter(WriterBase):
    asset_id = 'ga_condition'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_condition_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS
        return [
            SubStep(
                key=f"ayanamsha_{canonical_id}",
                label=f"GA-condition — {canonical_id}",
            )
            for canonical_id in CANONICAL_AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_condition_writer import build_ga_condition_substep

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"dry_run=True; skipped substep {step.key}",
            )

        ayanamsha_id = step.key.removeprefix("ayanamsha_")
        rows = build_ga_condition_substep(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            ayanamsha_id=ayanamsha_id,
            conn=ctx.db_conn,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
