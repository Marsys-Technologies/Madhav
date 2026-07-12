# Shard: bg_vastu_direction_remedials (FUSED 1b+5)

Grain: global L0 catalog (no chart_id). family_count=1. No reachable-surgical candidate → no curl probe (no wire surface for a global catalog; surgical tools all require chart_id).

DB-truth: `SELECT count(*) FROM bg_vastu_direction_remedials` = 24 (matches ledger family_key `__table_row_count__=24`). Verified via mcp__postgres__query.

Serving path: consumed at build-time by `bg_vastu_directions.py` / `l0_vastu_directions.py` / ga_vastu writer → content lands in per-chart `chart_facts` (reachable via chart_facts_query as derived vastu facts). NO surgical tool fronts the global catalog itself; `grep 'FROM bg_vastu'` over retrieval tools = 0 hits.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=24` | served-only-by-down-pipeline | NOT directly retrievable — global L0 vastu-remedial catalog has no surgical tool; its 24 rows reach the wire only after ga_vastu transforms them into per-chart chart_facts. | N/A — no wire surface for the global catalog (nothing to diff table-vs-wire). | path-grade(exemplar=`__table_row_count__=24`) sole family; DB count 24 confirmed = ledger. |
