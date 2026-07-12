"""Orchestrator adapter for the L1 Gaṇita `ga_ayurdaya` writer (WP-2.5 / LCA-16).

Heavy writer — one sub-step per ayanamsha. Computes ALL THREE classical longevity
methods (Pindayu / Nisargayu / Amsayu), method-attributed, plus the classical
applicability rule and maraka significators, into chart_facts under
fact_category='ayurdaya'. §7.2 BINDING: serve all three, no autonomous adjudication.

FROZEN contract (§N.2): @register WriterBase subclass; runs on ctx.db_conn and NEVER
commits/closes it; does NOT write asset_throughput.
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep

_AYANAMSHAS = [
    "lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman",
    "surya_siddhanta_classical",
]


@register('ga_ayurdaya')
class GaAyurdayaWriter(WriterBase):
    asset_id = 'ga_ayurdaya'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_ayurdaya_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [SubStep(key=f"ayanamsha_{aya}", label=f"GA-ayurdaya — {aya}")
                for aya in _AYANAMSHAS]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_ayurdaya_writer import build_ga_ayurdaya_substep
        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run; skipped {step.key}")
        aya = step.key.removeprefix("ayanamsha_")
        rows = build_ga_ayurdaya_substep(
            chart_id=ctx.config['chart_id'], build_id=ctx.build_id,
            ayanamsha_id=aya, conn=ctx.db_conn,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
