# Shard: brahma_class_priors (FUSED 1b+5)

Grain: global L0 catalog (no chart_id). family_count=1. No reachable-surgical candidate → no curl probe.

DB-truth: `SELECT count(*) FROM brahma_class_priors` = 164 (matches ledger `__table_row_count__=164`). Verified via mcp__postgres__query.

Serving path: build-time priors consumed by `bo_laksana.py`, `mi_kula.py`, `bodha_writers/formulas.py` → baked into per-chart `bodha_msr_signals` (reachable via msr_sql) and mimamsa insight units. NO surgical tool fronts the priors catalog itself; `grep 'FROM brahma_class_priors'` over retrieval tools = 0 hits.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=164` | served-only-by-down-pipeline | NOT directly retrievable — 164 calibration priors have no surgical tool; their effect reaches the wire only after bo_laksana/mi_kula transform them into per-chart signals. | N/A — no wire surface for the global catalog. | path-grade(exemplar=`__table_row_count__=164`) sole family; DB count 164 confirmed = ledger. |
