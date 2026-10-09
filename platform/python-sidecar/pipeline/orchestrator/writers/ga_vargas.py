"""
Orchestrator adapter for the L1 Gaṇita `ga_vargas` writer (HEAVY — ~21k rows).

Sub-step grain = per ayanamsha (the writer's existing per-ayanamsha loop, exposed
via ayanamsha_subset). The orchestrator drives each ayanamsha as its own SAVEPOINT
+ last_built_at heartbeat + commit. See investigation §2.B (analogous to ga_dashas).
"""
from __future__ import annotations
from ga_writers.data_plane_runtime import l1_producer_contract
from brahmagyan.ayanamsha_scope import ayanamshas_for_chart
from panchang_engine.swiss_backend import records_swiss_backend

from . import register, WriterBase, ContextSpec, WriterResult, SubStep


@register('ga_vargas')
@l1_producer_contract
@records_swiss_backend
class GaVargasWriter(WriterBase):
    asset_id = 'ga_vargas'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_vargas_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [SubStep(key=aya, label=f'vargas × {aya}')
                for aya in ayanamshas_for_chart(ctx.db_conn, ctx.config['chart_id'])]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_vargas_writer import build_ga_vargas

        s = build_ga_vargas(
            # uuid.UUID from the real orchestrator (psycopg uuid decode); the writer's FORENSIC gate compares
            # chart_id to a str constant, so convert at the boundary.
            chart_id=str(ctx.config['chart_id']),
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
            ayanamsha_subset=[step.key],
        )
        if s.get('status') == 'FORENSIC_FAIL':
            # build_ga_vargas reports a failed native-anchored gate as a returned summary (status FORENSIC_FAIL), not a
            # raise: without this the orchestrator would record the sub-step as built with 0 rows (the gate "ran" but
            # could never fail the run). Raise so the savepoint rolls back and the asset errors.
            raise RuntimeError(
                f"ga_vargas FORENSIC gate FAILED for ayanamsha {step.key}: {s.get('forensic_results', {}).get(step.key)}")
        # rows_inserted counts rows the database actually stored, never rows
        # attempted; anything that did not land is surfaced, not absorbed (F-A2).
        not_landed = int(s.get('rows_attempted', 0)) - int(s.get('rows_landed', 0))
        notes = ''
        if not_landed > 0 or s.get('rows_collided') or s.get('rows_failed'):
            notes = (
                f"{not_landed} of {s.get('rows_attempted', 0)} rows did not land: "
                f"{s.get('rows_collided', 0)} unique-key collisions within the run, "
                f"{s.get('rows_db_skipped', 0)} skipped on conflict, "
                f"{s.get('rows_failed', 0)} rejected; "
                f"first colliding keys: {s.get('collision_samples', [])[:3]}"
            )
        return WriterResult(asset_id=self.asset_id,
                            rows_inserted=int(s.get('total_rows_written', 0)),
                            rows_skipped=max(not_landed, 0),
                            notes=notes)
