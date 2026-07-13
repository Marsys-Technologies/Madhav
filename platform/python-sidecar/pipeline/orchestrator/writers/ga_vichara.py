"""
ga_vichara — Vichāra ("judged structure") writer (L1, per-chart)
Orchestrator adapter: delegates to ga_writers.ga_vichara_writer.build_ga_vichara_substep

Asset: ga_vichara
Layer: L1 (Gaṇita)
Scope: per_chart
Pattern: HEAVY — plan_substeps + run_substep (one sub-step per ayanamsha)

FROZEN contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2):
- @register('ga_vichara') + WriterBase subclass
- plan_substeps returns list[SubStep]; run_substep executes each
- NEVER commits / closes ctx.db_conn — orchestrator owns the transaction
- NEVER writes asset_throughput — orchestrator is the sole build-state writer

Doctrine Campaign D-1 / Night-1, Lane 2 (LANE2_GA_VICHARA.md).
DAG: depends_on = ['ga_structural', 'ga_strength', 'ga_dashas', 'ga_yoga']
(also declared authoritatively in asset_registry.depends_on, migration 435).
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


@register("ga_vichara")
class GaVicharaWriter(WriterBase):
    """
    Per-chart "judged structure" writer. One sub-step per ayanamsha; derives
    valence_pass / varga_ratification / varga_ratification_divergence /
    varga_consistency / leverage_index rows from already-stored ga_structural /
    ga_strength / ga_dashas / ga_yoga facts and writes them to chart_vichara.
    """
    asset_id = "ga_vichara"
    has_substeps = True
    depends_on = ["ga_structural", "ga_strength", "ga_dashas", "ga_yoga"]
    source_paths = ["platform/python-sidecar/ga_writers/ga_vichara_writer.py"]

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(
                key=f"ayanamsha_{a}",
                label=f"ga_vichara — {a}",
            )
            for a in CANONICAL_AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        from ga_writers.ga_vichara_writer import build_ga_vichara_substep

        ayanamsha_id = step.key.removeprefix("ayanamsha_")
        rows = build_ga_vichara_substep(
            chart_id=ctx.config["chart_id"],
            build_id=ctx.build_id,
            ayanamsha_id=ayanamsha_id,
            conn=ctx.db_conn,
            dry_run=ctx.dry_run,
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows)
