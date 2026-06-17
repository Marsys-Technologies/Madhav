"""
pipeline/orchestrator/writers/bg_prashna_rules.py
L0 static seed writer for Prashna (Horary) reference tables.
Conforms to the FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2).
"""
from __future__ import annotations

from pipeline.orchestrator.writers import WriterBase, WriterResult, register, ContextSpec


@register("bg_prashna_rules")
class PrashnaRulesWriter(WriterBase):
    """
    Seeds the five bg_prashna_* reference tables with static horary rule data.

    L0 (Brahmagyan) writer — chart-agnostic static reference only.
    No PyJHora calls, no per-chart computation.
    Idempotency: ON CONFLICT DO NOTHING (L0 standard).
    """

    asset_id = "bg_prashna_rules"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from brahmagyan.l0_prashna import seed_prashna_rules

        counts = seed_prashna_rules(ctx.db_conn, dry_run=ctx.dry_run)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=counts.get("total_rules", 0),
            notes=(
                f"lagna_methods={counts.get('lagna_methods', 0)}; "
                f"tajik_yogas={counts.get('tajik_yogas', 0)}; "
                f"significators={counts.get('significators', 0)}; "
                f"fructification={counts.get('fructification', 0)}; "
                f"special_techniques={counts.get('special_techniques', 0)}"
            ),
        )
