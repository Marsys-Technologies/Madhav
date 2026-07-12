"""Orchestrator adapter for the L1 Gaṇita `ga_sensitive_degree` writer (WP-2.5 / LCA-10).

Heavy writer — one sub-step per ayanamsha. Computes the never-computed per-graha
sensitive-degree facts (mrityu-bhaga, neecha-bhanga, kartari, sarvatobhadra-vedha,
khareshwara 22nd-drekkana/64th-navamsa, pushkara, kranti, gandanta) into chart_facts
under fact_category='sensitive_degree_check'.

FROZEN contract (§N.2): @register WriterBase subclass; runs on ctx.db_conn and NEVER
commits/closes it; does NOT write asset_throughput.
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep

_AYANAMSHAS = [
    "lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman",
    "surya_siddhanta_classical",
]


@register('ga_sensitive_degree')
class GaSensitiveDegreeWriter(WriterBase):
    asset_id = 'ga_sensitive_degree'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_sensitive_degree_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [SubStep(key=f"ayanamsha_{aya}", label=f"GA-sensitive-degree — {aya}")
                for aya in _AYANAMSHAS]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_sensitive_degree_writer import build_ga_sensitive_degree_substep
        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run; skipped {step.key}")
        aya = step.key.removeprefix("ayanamsha_")
        rows = build_ga_sensitive_degree_substep(
            chart_id=ctx.config['chart_id'], build_id=ctx.build_id,
            ayanamsha_id=aya, conn=ctx.db_conn,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
