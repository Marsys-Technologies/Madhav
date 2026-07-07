"""Orchestrator adapter for the L1 Gaṇita `ga_structural` writer (HEAVY).

GA8 Structural Enumeration Rebuild v2.0 — per GA8_STRUCTURAL_ENUMERATION_BRIEF v2.0.
16 vargas × 5 ayanamshas — uses plan_substeps + run_substep for per-ayanamsha sub-steps.
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep


@register('ga_structural')
class GaStructuralWriter(WriterBase):
    asset_id = 'ga_structural'
    has_substeps = True
    # JL-026 (2026-07-07): ga_condition edge removed (migration 419) — it existed
    # only to serialize the graha_yuddha delete-clobber, now single-writer in
    # ga_structural. The authoritative dependency set lives in asset_registry.depends_on
    # (DB), which the scheduler reads; this attr is a documentation subset.
    depends_on = ['ga_nakshatra']
    source_paths = ['platform/python-sidecar/ga_writers/ga_structural_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS
        return [
            SubStep(key=f"ayanamsha_{canonical_id}", label=f"GA8 structural — {canonical_id}")
            for canonical_id in CANONICAL_AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_structural_writer import build_ga_structural_substep

        ayanamsha_id = step.key.removeprefix("ayanamsha_")
        rows = build_ga_structural_substep(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            ayanamsha_id=ayanamsha_id,
            conn=ctx.db_conn,
            birth_params=ctx.config.get('birth_params'),
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
