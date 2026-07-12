# FUSED 1b+5 shard — brahma_dosha_catalog (1 family)

DB truth: `SELECT count(*) FROM brahma_dosha_catalog` = 79 rows.
Serving code EXISTS: `query_dosha_catalog` (src/lib/retrieval/.../L0_brahmagyan/query_dosha_catalog.ts,
`SELECT * FROM brahma_dosha_catalog`). BUT NOT in the surgical whitelist.
Wire call: POST /api/mcp/primitives/query_dosha_catalog {"params":{}} →
  ok:false, error.class=validation, "Tool not in surgical whitelist: query_dosha_catalog",
  remediation="Use ask_madhav for full-pipeline queries."
=> Data + serving code exist; only reachable via full-pipeline (ask_madhav), not surgically. This is
the remediation quick-win class (whitelist-add). No surgical wire probe possible → no fidelity diff.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| __table_row_count__=79 | served-only-by-down-pipeline | UNREACHABLE-SURGICALLY (query_dosha_catalog excluded from whitelist; full-pipeline only) | N/A (no wire reachable) | path-grade(exemplar=__table_row_count__=79) sole family |
