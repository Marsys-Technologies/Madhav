"""Orchestrator adapter for the L1 Gaṇita `ga_sensitive` writer (heavy — 5 ayanamsha sub-steps).

Sub-step grain = one ayanamsha per step. Each step computes its rows, runs the
divergent/single-pass checks, inserts via replace_prior_chart_facts, then the
orchestrator commits and updates last_built_at. This keeps the asset under both
watchdog reapers and makes a connection drop non-fatal (prior ayanamshas survive).
"""
from __future__ import annotations

from . import register, WriterBase, ContextSpec, WriterResult, SubStep


@register('ga_sensitive')
class GaSensitiveWriter(WriterBase):
    asset_id = 'ga_sensitive'
    has_substeps = True
    source_paths = ['platform/python-sidecar/ga_writers/ga_sensitive_writer.py']

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        from ga_writers.ga_sensitive_writer import CANONICAL_AYANAMSHAS
        return [
            SubStep(key=f'ayanamsha:{aya_key}', label=f'GA-sensitive — {aya_key}')
            for aya_key in CANONICAL_AYANAMSHAS.keys()
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_sensitive_writer import (
            build_ga_sensitive_for_ayanamsha,
            get_ga_sensitive_context,
            CANONICAL_AYANAMSHAS,
        )
        chart_id = ctx.config['chart_id']
        birth_params = ctx.config.get('birth_params')  # always a real dict — native has no special case
        aya_key = step.key.split(':', 1)[1]
        aya_id = CANONICAL_AYANAMSHAS[aya_key]
        prereqs, eng_ver = get_ga_sensitive_context(birth_params, conn=ctx.db_conn)
        inserted = build_ga_sensitive_for_ayanamsha(
            ayanamsha_key=aya_key,
            ayanamsha_id=aya_id,
            chart_id=chart_id,
            build_id=ctx.build_id,
            conn=ctx.db_conn,
            birth_params=birth_params,
            prereqs=prereqs,
            eng_ver=eng_ver,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=inserted)
