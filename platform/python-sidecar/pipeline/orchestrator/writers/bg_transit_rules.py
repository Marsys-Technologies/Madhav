"""
pipeline/orchestrator/writers/bg_transit_rules.py
L0 static seed writer for Transit/Gochara reference tables.
Conforms to the FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2).
"""
from __future__ import annotations

from pipeline.orchestrator.writers import WriterBase, WriterResult, register, ContextSpec


@register("bg_transit_rules")
class BgTransitRulesWriter(WriterBase):
    """
    Seeds bg_transit_engine and bg_transit_rules with classical Gochara reference data.

    L0 (Brahmagyan) writer — chart-agnostic static reference only.
    No PyJHora calls, no per-chart computation.
    Idempotency: ON CONFLICT DO UPDATE (L0 standard).
    """

    asset_id = "bg_transit_rules"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from brahmagyan.l0_transit import seed_transit_rules

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run")

        counts = seed_transit_rules(ctx.db_conn, dry_run=False)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=counts.get("total", 0),
            notes=(
                f"bg_transit_engine={counts.get('bg_transit_engine', 0)}; "
                f"bg_transit_rules={counts.get('bg_transit_rules', 0)}"
            ),
        )
