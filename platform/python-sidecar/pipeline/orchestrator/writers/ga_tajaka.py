"""Orchestrator adapter for the L1 Gaṇita `ga_tajaka` writer (Vārṣaphal, light)."""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult


@register('ga_tajaka')
class GaTajakaWriter(WriterBase):
    asset_id = 'ga_tajaka'
    source_paths = ['platform/python-sidecar/ga_writers/ga_tajaka_writer.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        from ga_writers.ga_tajaka_writer import build_ga_tajaka

        s = build_ga_tajaka(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(s.get('total_rows_written', 0)))
