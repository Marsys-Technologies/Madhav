# Shard: bg_vastu_directions (FUSED 1b+5)

Grain: global L0 catalog (no chart_id). family_count=1. No reachable-surgical candidate → no curl probe.

DB-truth: `SELECT count(*) FROM bg_vastu_directions` = 8 (matches ledger `__table_row_count__=8`). Verified via mcp__postgres__query.

Serving path: build-time input to ga_vastu (writers `bg_vastu_directions.py`, `l0_vastu_directions.py`) → per-chart `chart_facts` (chart_facts_query). NO surgical tool fronts the catalog itself.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=8` | served-only-by-down-pipeline | NOT directly retrievable — 8-direction global catalog has no surgical tool; content reaches wire only as downstream ga_vastu chart_facts. | N/A — no wire surface. | path-grade(exemplar=`__table_row_count__=8`) sole family; DB count 8 confirmed = ledger. |
