# Shard: brahma_dasha_systems (FUSED 1b+5)

Grain: global L0 catalog (no chart_id). family_count=1. No reachable-surgical candidate → no curl probe.

DB-truth: `SELECT count(*) FROM brahma_dasha_systems` = 18 (matches ledger `__table_row_count__=18`). Verified via mcp__postgres__query.

Serving path: build-time dasha-system catalog consumed by `bg_dasha_systems.py`, `l0_dasha_systems.py`, `l0_rules.py` → drives per-chart `chart_dashas` computation (reachable via query_dasha_periods). `parity_check.ts` line 35 ties each `brahma_dasha_systems.canonical_id` to `brahma_ontology` (entity_class='dasha_system'). NO surgical tool fronts the catalog itself; `grep 'FROM brahma_dasha_systems'` over retrieval tools = 0 hits.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=18` | served-only-by-down-pipeline | NOT directly retrievable — 18-system dasha catalog has no surgical tool; its systems reach the wire only as computed per-chart chart_dashas periods. | N/A — no wire surface for the global catalog. | path-grade(exemplar=`__table_row_count__=18`) sole family; DB count 18 confirmed = ledger. |
