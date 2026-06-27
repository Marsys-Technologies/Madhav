"""
Orchestrator adapter for the L1 Gaṇita `ga_positions` writer.

Thin @register(WriterBase) wrapper over ga_writers.ga_positions_writer. The
heavy lifting (PyJHora compute, FORENSIC gate, atomic-row build, idempotent
upsert) stays in ga_writers/; this adapter only conforms it to the frozen
orchestrator contract: run on ctx.db_conn, never commit, never write
asset_throughput. See ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md §2.A.
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult


@register('ga_positions')
class GaPositionsWriter(WriterBase):
    asset_id = 'ga_positions'
    # git-hash provenance points at the real writer logic, not this adapter.
    source_paths = ['platform/python-sidecar/ga_writers/ga_positions_writer.py']

    def run(self, ctx: ContextSpec) -> WriterResult:
        from ga_writers.ga_positions_writer import build_ga_positions

        # Pass the per-chart birth params the orchestrator pre-fetched from
        # public.charts (asset_runner → fetch_birth_params → ctx.config['birth_params']).
        # Every chart including the native now goes through this path — no NATIVE_BIRTH
        # fallback exists anywhere in the stack.
        s = build_ga_positions(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=int(s.get('total_chart_facts_rows', 0)),
            notes=f"chart_facts={s.get('total_chart_facts_rows', 0)}",
        )
