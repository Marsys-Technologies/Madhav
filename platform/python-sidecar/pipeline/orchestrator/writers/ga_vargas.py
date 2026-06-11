"""
Orchestrator adapter for the L1 Gaṇita `ga_vargas` writer (HEAVY — ~21k rows).

Sub-step grain = per ayanamsha (the writer's existing per-ayanamsha loop, exposed
via ayanamsha_subset). The orchestrator drives each ayanamsha as its own SAVEPOINT
+ last_built_at heartbeat + commit. See investigation §2.B (analogous to ga_dashas).
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep


@register('ga_vargas')
class GaVargasWriter(WriterBase):
    asset_id = 'ga_vargas'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_vargas_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        from ga_writers.ga_vargas_writer import CANONICAL_AYANAMSHAS

        return [SubStep(key=aya, label=f'vargas × {aya}')
                for aya in CANONICAL_AYANAMSHAS.keys()]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_vargas_writer import build_ga_vargas

        s = build_ga_vargas(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
            ayanamsha_subset=[step.key],
        )
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(s.get('total_rows_written', 0)))
