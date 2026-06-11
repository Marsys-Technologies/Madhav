"""Orchestrator adapter for the L1 Gaṇita `ga_structural` writer (light)."""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult


@register('ga_structural')
class GaStructuralWriter(WriterBase):
    asset_id = 'ga_structural'
    source_paths = ['platform/python-sidecar/ga_writers/ga_structural_writer.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        from ga_writers.ga_structural_writer import build_ga_structural

        s = build_ga_structural(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(s.get('total_chart_facts_rows', 0)))
