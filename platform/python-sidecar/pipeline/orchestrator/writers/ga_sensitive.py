"""Orchestrator adapter for the L1 Gaṇita `ga_sensitive` writer (light)."""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult


@register('ga_sensitive')
class GaSensitiveWriter(WriterBase):
    asset_id = 'ga_sensitive'
    source_paths = ['platform/python-sidecar/ga_writers/ga_sensitive_writer.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        from ga_writers.ga_sensitive_writer import build_ga_sensitive

        s = build_ga_sensitive(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=int(s.get('inserted_rows', s.get('total_rows', 0))),
        )
