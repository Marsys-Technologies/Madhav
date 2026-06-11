"""Orchestrator adapter for the L1 Gaṇita `ga_strength` writer (light)."""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult


@register('ga_strength')
class GaStrengthWriter(WriterBase):
    asset_id = 'ga_strength'
    source_paths = ['platform/python-sidecar/ga_writers/ga_strength_writer.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        from ga_writers.ga_strength_writer import build_ga_strength

        s = build_ga_strength(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(s.get('total_chart_facts_rows', 0)))
