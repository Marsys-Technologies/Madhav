"""
pipeline/orchestrator/writers/bg_transit_rules.py
L0 static seed writer for Transit/Gochara reference tables.
Conforms to the FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2).
"""
from __future__ import annotations

from pipeline.orchestrator.writers import WriterBase, WriterResult, register, ContextSpec


@register("bg_transit_rules")
@register("bg_transit_engine")
class BgTransitRulesWriter(WriterBase):
    """
    Seeds bg_transit_engine and bg_transit_rules with classical Gochara reference data.

    L0 (Brahmagyan) writer — chart-agnostic static reference only.
    No PyJHora calls, no per-chart computation.
    Idempotency: ON CONFLICT DO UPDATE (L0 standard).

    Note: bg_transit_engine (asset_registry catalog_status=CURRENT, sort_order=61) is a
    sub-table seeded by this writer via seed_transit_rules(). The second @register decorator
    above routes "Rebuild bg_transit_engine" requests through this writer so both asset_ids
    resolve correctly. asset_id remains "bg_transit_rules" (the primary).
    """

    asset_id = "bg_transit_rules"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from brahmagyan.l0_transit import seed_transit_rules

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run")

        counts = seed_transit_rules(ctx.db_conn, dry_run=False)

        # WFIX-A: rows PRESENT in the built asset's own table after the seed. The seeder's total
        # (bg_transit_engine + bg_transit_rules + bg_transit_moorti rows it processed = 105) was
        # recorded for bg_transit_rules, whose own table holds 76.
        from pipeline.orchestrator.writers._rows_present import present_count
        with ctx.db_conn.cursor() as cur:
            if ctx.asset_id == "bg_transit_engine":
                cur.execute(ROWS_PRESENT_SQL_ENGINE)
            else:
                cur.execute(ROWS_PRESENT_SQL_RULES)
            present = present_count(cur.fetchone())
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=present,
            notes=(
                f"bg_transit_engine={counts.get('bg_transit_engine', 0)}; "
                f"bg_transit_rules={counts.get('bg_transit_rules', 0)}"
            ),
        )


# WFIX-A: the rows-present statement is a literal at the module end (resolved at call time) so no line above it shifts and
# the writer-line citations in the declarations keep pointing at the same code; the census scans it as the asset's own read.
ROWS_PRESENT_SQL_RULES = "SELECT count(*) AS n FROM bg_transit_rules"
ROWS_PRESENT_SQL_ENGINE = "SELECT count(*) AS n FROM bg_transit_engine"
