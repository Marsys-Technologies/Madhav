"""
Orchestrator adapter for the L1 Gaṇita `ga_dashas` writer (HEAVY — ~40 min,
~536k rows).

Sub-step grain = the 35 (system × ayanamsha) chunks that already exist as
build_system() calls, plus a final concurrency post-pass. The orchestrator drives
each as its own SAVEPOINT + last_built_at heartbeat + commit, so the asset stays
under both watchdog reapers and resumes per-chunk. See
ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md §2.B.2.
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep

_POST_PASS_KEY = '__concurrency_post_pass__'


@register('ga_dashas')
class GaDashasWriter(WriterBase):
    asset_id = 'ga_dashas'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_dashas_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        from ga_writers.ga_dashas_writer import SYSTEMS, AYANAMSHAS

        steps = [
            SubStep(key=f'{system}:{aya}', label=f'{system} × {aya}')
            for aya in AYANAMSHAS
            for system in SYSTEMS
        ]
        # Final cross-system concurrency annotation (DB-side; needs all systems).
        steps.append(SubStep(key=_POST_PASS_KEY, label='concurrency post-pass'))
        return steps

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_dashas_writer import build_system, _run_concurrency_post_pass_db

        chart_id = ctx.config['chart_id']
        if step.key == _POST_PASS_KEY:
            _run_concurrency_post_pass_db(chart_id, ctx.build_id, conn=ctx.db_conn)
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes='concurrency post-pass')

        system, aya = step.key.split(':', 1)
        res = build_system(system, aya, chart_id, ctx.build_id, conn=ctx.db_conn)
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(res.get('rows_written', 0)))
