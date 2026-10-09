"""Orchestrator adapter for the L1 Gaṇita `ga_medical` writer (HEAVY).

Medical/Ayurvedic Indication Composite — one sub-step per ayanamsha.
9 grahas × 5 ayanamshas = 45 rows per chart.

Delegates to ga_writers.ga_medical_writer.build_ga_medical_substep().

MEDICAL DISCLAIMER: All rows carry indication_tier='jyotish_indication' and
not_diagnosis=TRUE — Jyotish indicators only, NOT medical diagnoses.
"""
from __future__ import annotations
from ga_writers.data_plane_runtime import l1_producer_contract
from brahmagyan.ayanamsha_scope import CANONICAL_FIVE, ayanamshas_for_chart

from . import register, WriterBase, ContextSpec, WriterResult, SubStep

# Iteration order of this adapter's sub-steps (krishnamurti before true_chitra), kept exactly as before; the SET a chart
# builds comes from ayanamshas_for_chart, which returns canonical order, so it is re-ordered by this tuple.
_LOCAL_ORDER = tuple(CANONICAL_FIVE[i] for i in (0, 2, 1, 3, 4))
_AYANAMSHAS = list(_LOCAL_ORDER)   # the DEFAULT set, in the adapter's historical order


@register('ga_medical')
@l1_producer_contract
class GaMedicalWriter(WriterBase):
    asset_id = 'ga_medical'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_medical_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        chosen = set(ayanamshas_for_chart(ctx.db_conn, ctx.config['chart_id']))
        return [
            SubStep(
                key=f"ayanamsha_{aya}",
                label=f"GA-medical — {aya}",
            )
            for aya in _LOCAL_ORDER if aya in chosen
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_medical_writer import build_ga_medical_substep

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"dry_run=True; skipped substep {step.key}",
            )

        ayanamsha_id = step.key.removeprefix("ayanamsha_")
        rows = build_ga_medical_substep(
            chart_id=ctx.config['chart_id'],
            build_id=ctx.build_id,
            ayanamsha_id=ayanamsha_id,
            conn=ctx.db_conn,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
