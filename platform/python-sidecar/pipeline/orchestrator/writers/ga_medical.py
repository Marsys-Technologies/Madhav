"""Orchestrator adapter for the L1 Gaṇita `ga_medical` writer (HEAVY).

Medical/Ayurvedic Indication Composite — one sub-step per ayanamsha.
9 grahas × 5 ayanamshas = 45 rows per chart.

Delegates to ga_writers.ga_medical_writer.build_ga_medical_substep().

MEDICAL DISCLAIMER: All rows carry indication_tier='jyotish_indication' and
not_diagnosis=TRUE — Jyotish indicators only, NOT medical diagnoses.
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep

_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "kp",
    "true_chitra",
    "raman",
    "yukteshwar",
]


@register('ga_medical')
class GaMedicalWriter(WriterBase):
    asset_id = 'ga_medical'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_medical_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(
                key=f"ayanamsha_{aya}",
                label=f"GA-medical — {aya}",
            )
            for aya in _AYANAMSHAS
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
