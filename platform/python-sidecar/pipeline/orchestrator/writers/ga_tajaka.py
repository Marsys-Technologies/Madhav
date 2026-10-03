"""Orchestrator adapter for the L1 Gaṇita `ga_tajaka` writer (Vārṣaphal, light)."""
from __future__ import annotations
from ga_writers.data_plane_runtime import l1_producer_contract
from panchang_engine.swiss_backend import records_swiss_backend

from . import register, WriterBase, ContextSpec, WriterResult


@register('ga_tajaka')
@l1_producer_contract
@records_swiss_backend
class GaTajakaWriter(WriterBase):
    asset_id = 'ga_tajaka'
    source_paths = ['platform/python-sidecar/ga_writers/ga_tajaka_writer.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        from ga_writers.ga_tajaka_writer import build_ga_tajaka

        s = build_ga_tajaka(
            # uuid.UUID from the real orchestrator (psycopg uuid decode); build_ga_tajaka feeds
            # chart_id into stable_uuid (canonical JSON rejects a UUID): convert at the boundary.
            chart_id=str(ctx.config['chart_id']),
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(s.get('total_rows_written', 0)))
