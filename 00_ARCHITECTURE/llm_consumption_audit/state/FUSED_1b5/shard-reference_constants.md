# FUSED 1b+5 shard — reference_constants

path: reference_constants  |  families_total: 1  |  channel: truly-UNREACHABLE  |  ledger_row: VF-3039

## Channel confirmation
- DB-truth: SELECT count(*) FROM reference_constants = 203 rows (matches ledger family_key __table_row_count__=203).
- Serving-path check: grep -rniE 'FROM reference_constants' platform/src -> ZERO hits. No MCP surgical tool and no full-pipeline/registry retrieval handler reads this table.
- Only non-writer touchpoint: platform/scripts/seed/asset_registry_seed.ts count_sql aggregates row COUNT for the cockpit — serves a number, never the catalog CONTENT.
- Similarly-named registry handlers (get_karakas -> FROM chart_facts; get_yoga_dosha -> FROM chart_facts) serve CHART-SCOPED data, NOT this global definitional catalog.
- No wire probe possible (no tool to call) -> fidelity not gradeable (no wire value to diff).

## Family row (one row per family; family_count=1)
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=203 | truly-UNREACHABLE | UNREACHABLE (class 1 — no serving tool; global L0 reference-catalog content reaches no consuming-LLM path) | N/A — no wire path exists to diff against DB truth | full per-family (family_count=1; DB-truth count SELECTed=203 confirms table populated; serving-path grep confirms nonexistence of any serving tool) |

## Finding (lane 1b — retrievability, class 1 UNREACHABLE, UNREACHABLE-by-nonexistence per Charter §2.1)
- exact call (DB-truth): SELECT count(*) FROM reference_constants -> 203
- exact call (serving check): grep -rniE 'FROM reference_constants' platform/src -> (no output)
- evidence: 203 rows of definitional/reference content; no MCP tool (surgical or full-pipeline) exposes it.
- suspected layer: retrieval-plane / MCP-contract (serving handler absent entirely).
- severity: medium
