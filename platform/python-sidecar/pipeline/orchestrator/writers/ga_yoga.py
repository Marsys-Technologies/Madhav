"""
ga_yoga — Yoga Firings writer (L1, per-chart)
Orchestrator adapter: delegates to ga_writers.ga_yoga_writer.build_ga_yoga_substep

Asset: ga_yoga
Layer: L1 (Gaṇita)
Scope: per_chart
Pattern: HEAVY — plan_substeps + run_substep (one sub-step per ayanamsha)

FROZEN contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2):
- @register('ga_yoga') + WriterBase subclass
- plan_substeps returns list[SubStep]; run_substep executes each
- NEVER commits / closes ctx.db_conn — orchestrator owns the transaction
- NEVER writes asset_throughput — orchestrator is the sole build-state writer

Build: 2026-06-17 — Yoga Subsystem Gate-1
"""
from __future__ import annotations

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult, SubStep

# Canonical ayanamsha keys — must match ga_positions_writer.CANONICAL_AYANAMSHAS keys
CANONICAL_AYANAMSHAS: list[str] = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]


@register("ga_yoga")
class GaYogaWriter(WriterBase):
    """
    Per-chart yoga firing writer.
    One sub-step per ayanamsha; evaluates the brahma_yoga_catalog rules against
    chart_facts rows and writes results to ga_yoga_firings.
    """
    asset_id = "ga_yoga"
    has_substeps = True
    source_paths = ["platform/python-sidecar/ga_writers/ga_yoga_writer.py"]

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(
                key=f"ayanamsha_{a}",
                label=f"ga_yoga — {a}",
            )
            for a in CANONICAL_AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_yoga_writer import build_ga_yoga_substep

        ayanamsha_id = step.key.removeprefix("ayanamsha_")
        rows = build_ga_yoga_substep(
            chart_id=ctx.config["chart_id"],
            build_id=ctx.build_id,
            ayanamsha_id=ayanamsha_id,
            conn=ctx.db_conn,
            dry_run=ctx.dry_run,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
