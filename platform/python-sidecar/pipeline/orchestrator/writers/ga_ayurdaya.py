"""Orchestrator adapter for the L1 Gaṇita `ga_ayurdaya` writer (WP-2.5 / LCA-16).

Heavy writer — one sub-step per ayanamsha. Computes ALL THREE classical longevity
methods (Pindayu / Nisargayu / Amsayu), method-attributed, plus the classical
applicability rule and maraka significators, into chart_facts under
fact_category='ayurdaya'. §7.2 BINDING: serve all three, no autonomous adjudication.

FROZEN contract (§N.2): @register WriterBase subclass; runs on ctx.db_conn and NEVER
commits/closes it; does NOT write asset_throughput.
"""
from __future__ import annotations
from ga_writers.data_plane_runtime import l1_producer_contract
from brahmagyan.ayanamsha_scope import CANONICAL_FIVE, ayanamshas_for_chart

from . import register, WriterBase, ContextSpec, WriterResult, SubStep

# Iteration order of this adapter's sub-steps (krishnamurti before true_chitra), kept exactly as before; the SET a chart
# builds comes from ayanamshas_for_chart, which returns canonical order, so it is re-ordered by this tuple.
_LOCAL_ORDER = tuple(CANONICAL_FIVE[i] for i in (0, 2, 1, 3, 4))
_AYANAMSHAS = list(_LOCAL_ORDER)   # the DEFAULT set, in the adapter's historical order


@register('ga_ayurdaya')
@l1_producer_contract
class GaAyurdayaWriter(WriterBase):
    asset_id = 'ga_ayurdaya'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_ayurdaya_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        chosen = set(ayanamshas_for_chart(ctx.db_conn, ctx.config['chart_id']))
        return [SubStep(key=f"ayanamsha_{aya}", label=f"GA-ayurdaya — {aya}")
                for aya in _LOCAL_ORDER if aya in chosen]

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
