# FUSED 1b+5 shard — brahma_yoga_catalog (1 family)

DB truth: `SELECT count(*) FROM brahma_yoga_catalog` = 175 rows.
Serving code EXISTS: `query_yoga_catalog` (L0_brahmagyan/query_yoga_catalog.ts,
`SELECT * FROM brahma_yoga_catalog`). BUT NOT in the surgical whitelist.
Wire call: POST /api/mcp/primitives/query_yoga_catalog {"params":{}} →
  ok:false, error.class=validation, "Tool not in surgical whitelist: query_yoga_catalog",
  remediation="Use ask_madhav for full-pipeline queries."
Partial name-level reachability: `list_entities` (entity_class=yoga) surfaces the 175 yoga
canonical_id/names via brahma_ontology, but NOT the rich catalog fields (formation rules, effects,
strength) held in brahma_yoga_catalog. Catalog surface itself = full-pipeline only. No surgical
fidelity diff possible.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| __table_row_count__=175 | served-only-by-down-pipeline | UNREACHABLE-SURGICALLY (query_yoga_catalog excluded from whitelist; names-only via list_entities; catalog fields full-pipeline only) | N/A (no wire reachable) | path-grade(exemplar=__table_row_count__=175) sole family |
