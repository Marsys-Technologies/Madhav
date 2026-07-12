# Shard: brahma_compendium_index (FUSED 1b+5)

Grain: global L0 catalog (no chart_id). family_count=1. No reachable-surgical candidate → no curl probe.

DB-truth: `SELECT count(*) FROM brahma_compendium_index` = 9538 (matches ledger `__table_row_count__=9538`). Verified via mcp__postgres__query.

Serving path / DECLARED-BUT-NOT-LIVE mismatch: retrieval registry `coverage_matrix.ts` line 383 maps `brahma_compendium_index: ['marsys://tool/L0/query_classical_texts']` — but `query_classical_texts` is NOT in the live surgical tool set. The live classical tool is `classical_text_search`, which reads `classical_text_chunks` (verified: `platform/src/lib/tools/classical_text_search.ts` line 92 `FROM classical_text_chunks`), NOT brahma_compendium_index. So the 9538-row compendium index has a registry-declared serving tool that does not exist as a live primitive, and the live classical tool queries a different table. Table is a build-time corpus index (writer `bg_compendium_index.py`); no live tool serves it.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=9538` | served-only-by-down-pipeline | NOT directly retrievable — registry declares serving tool `marsys://tool/L0/query_classical_texts` which is not live; the live `classical_text_search` reads `classical_text_chunks` instead. The 9538-row index is a build-time corpus catalog with no live wire path of its own. | N/A — no live wire surface; declared serving tool absent. | path-grade(exemplar=`__table_row_count__=9538`) sole family; DB count 9538 confirmed = ledger. |
