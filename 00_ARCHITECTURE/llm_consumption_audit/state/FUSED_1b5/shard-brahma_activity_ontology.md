# Shard: brahma_activity_ontology (FUSED 1b+5)

Grain: global L0 catalog (no chart_id). family_count=1. No reachable-surgical candidate → no curl probe.

DB-truth: `SELECT count(*) FROM brahma_activity_ontology` = 12 (matches ledger `__table_row_count__=12`). Verified via mcp__postgres__query.

Serving path: THIS ONE IS ACTIVELY SERVED downstream. Allowlisted in `platform/src/app/api/mcp/db/query/route.ts` ALLOWED_TABLES (line 60) and read by the P1-synthesis **full-pipeline** MCP tool `platform-mcp/src/tools/register_p1_synthesis.ts` (line 805: `SELECT activity_class_id, name_en, significators, fructification_rules, citations FROM brahma_activity_ontology WHERE activity_class_id = $1`) plus ph_muhurta engine. Its content thus reaches the wire, but only via a server-authored full-pipeline synthesis query — never a per-family surgical tool. This is the remediation quick-win (data + serving-code both exist).

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=12` | served-only-by-down-pipeline | Reachable only via full-pipeline P1-synthesis tool (server-authored single-row lookup by activity_class_id); the 12-row ontology cannot be enumerated on demand by a consuming LLM (no surgical tool). | N/A — full-pipeline lookup returns a synthesis-shaped result, not the raw catalog; no direct table-vs-wire diff. | path-grade(exemplar=`__table_row_count__=12`) sole family; DB count 12 confirmed = ledger. |
