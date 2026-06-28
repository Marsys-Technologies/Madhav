---
canonical_id: RETRIEVAL_CITATION_REPORT_LIB_RETRIEVE_RETIREMENT
version: 1.0
status: COMPLETE
created: 2026-06-28
phase: D7 Step 4 — lib/retrieve retirement + mcp/primitives_registry retirement
---

# Reverse-Citation Report — lib/retrieve + mcp/primitives_registry Retirement

## Summary

D7 Step 4 of the chat-channel migration. This report confirms that zero live
external callers of `lib/retrieve` or `lib/mcp/primitives_registry` remained
at the time of deletion. All callers were repointed prior to deletion.

---

## Citation Gate Commands and Output

### GREP 1 — External imports from lib/retrieve

```
grep -rn "from.*lib/retrieve" platform/src --include="*.ts" | grep -v node_modules | grep -v "lib/retrieve/"
```

**Output (zero live import statements; remaining hits are comments only):**
```
platform/src/lib/retrieval/registry/tool_name_bridge.ts:28: * Authoritative map from legacy lib/retrieve tool names to registry URIs.
platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts:28:// Bridge-registered tool names (D7: replaces RETRIEVAL_TOOLS from lib/retrieve)
```

Both are comment lines — not import statements. ZERO live external callers confirmed.

---

### GREP 2 — Imports from primitives_registry

```
grep -rn "from.*primitives_registry" platform/src --include="*.ts" | grep -v node_modules
```

**Output (zero live import statements; remaining hits are comments only):**
```
platform/src/app/api/mcp/primitives/[tool]/route.ts:153:  // Resolve the underlying retrieval tool name (from primitives_registry whitelist)
platform/src/lib/retrieval/registry/tool_name_bridge.ts:10: * isAllowedSurgicalTool) — moved here from `lib/mcp/primitives_registry` as part
platform/src/lib/retrieval/registry/tool_name_bridge.ts:239:// Moved here from lib/mcp/primitives_registry.ts (D7 Step 4 retirement).
platform/src/lib/retrieval/registry/tool_name_bridge.ts:290: * retrieval tool names. Moved from lib/mcp/primitives_registry (D7 Step 4).
```

All are comment/documentation lines — not import statements. ZERO live external callers confirmed.

---

### GREP 3 — msr_sql outside lib/retrieve (import statements only)

```
grep -rn "msr_sql" platform/src --include="*.ts" | grep -v node_modules | grep -v "lib/retrieve/" | grep "from "
```

**Output:**
```
(empty)
```

All `msr_sql` references are string literals (tool names), not imports. ZERO lib/retrieve import callers.

---

## Files Deleted

1. **`platform/src/lib/retrieve/`** — entire directory deleted.
   - `index.ts` — RETRIEVAL_TOOLS registry (replaced by lib/retrieval/registry)
   - `types.ts` — shared types (migrated to `lib/retrieval/shared_types.ts`)
   - `chart_facts_query.ts` — chart facts query tool
   - `classical_text_search_tool.ts` — moved to `lib/retrieval/tools/classical_text_search_tool.ts`
   - `classical_attribution_lookup_tool.ts` — moved to `lib/retrieval/tools/classical_attribution_lookup_tool.ts`
   - `classical_disclosure_filter.ts` — moved to `lib/retrieval/tools/classical_disclosure_filter.ts`
   - `tool_catalogue.ts` — `buildChatToolsFromNames` migrated to `lib/retrieval/registry/schema_utils.ts`
   - `pyhora_natal_positions.ts`, `pyhora_dasha_periods.ts`, `pyhora_special_lagnas.ts` — PyHora wrappers
   - `remedy_tools.ts`, `sutravali_tools.ts` — remedy/sutravali tools

2. **`platform/src/lib/mcp/primitives_registry.ts`** — deleted.
   - `SURGICAL_TOOLS`, `MCP_TO_RETRIEVAL_TOOL`, `SurgicalToolName`, `isAllowedSurgicalTool` migrated to
     `platform/src/lib/retrieval/registry/tool_name_bridge.ts`.

---

## Callers Repointed (pre-deletion)

| File | Old import | New import |
|---|---|---|
| `app/api/mcp/primitives/[tool]/route.ts` | `@/lib/mcp/primitives_registry` | `@/lib/retrieval/registry/tool_name_bridge` |
| `lib/mcp/__tests__/primitives_registry.test.ts` | `../primitives_registry` | `@/lib/retrieval/registry/tool_name_bridge` |
| `lib/__tests__/mcp/primitives.test.ts` | `@/lib/mcp/primitives_registry` | `@/lib/retrieval/registry/tool_name_bridge` |
| `lib/__tests__/mcp/red_team/whitelist.test.ts` | `@/lib/mcp/primitives_registry` | `@/lib/retrieval/registry/tool_name_bridge` |
| `lib/router/__tests__/retrieval_capability_spec.test.ts` | `@/lib/retrieve` (RETRIEVAL_TOOLS) | `@/lib/retrieval/registry/tool_name_bridge` (TOOL_NAME_TO_URI) |
| `app/api/chat/consult/route.ts` | `@/lib/retrieve/tool_catalogue` + `@/lib/retrieve/types` | `@/lib/retrieval/registry/schema_utils` + `@/lib/retrieval/shared_types` |
| `lib/pipelines/shared/run_adapter_dispatch.ts` | `@/lib/retrieve/tool_catalogue` + `@/lib/retrieve/types` | `@/lib/retrieval/registry/schema_utils` + `@/lib/retrieval/shared_types` |
| `lib/checkpoints/types.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `lib/synthesis/mcp_tool_executor.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `lib/synthesis/types.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `lib/audit/consumer.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `lib/performance/compliance.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `lib/performance/ingestion.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `lib/router/types.ts` | inline `@/lib/retrieve/chart_facts_query` | inlined type literal |
| `lib/retrieval/registry/tool_name_bridge.ts` | `@/lib/retrieve/types` | `@/lib/retrieval/shared_types` |
| `__tests__/integration/mcp_stub_engines.integration.test.ts` | `lib/retrieve/index` (getTool, RETRIEVAL_TOOLS) | `tool_name_bridge` (getToolByName, TOOL_NAME_TO_URI) |
| `scripts/test/msr_sql_smoke.ts` | `@/lib/retrieve/index` | `@/lib/retrieval/registry/tool_name_bridge` |
| `lib/__tests__/mcp/primitives.test.ts` | mock `@/lib/retrieve/index` | mock `@/lib/retrieval/registry/tool_name_bridge` |
| `tests/e2e/r11g-server-smoke/tool-executor-loop.test.ts` | mock `lib/retrieve/index` | mock `tool_name_bridge` |
| `tests/e2e/r11g-server-smoke/multi-tool-fan-out.test.ts` | mock `lib/retrieve/index` | mock `tool_name_bridge` |
| `tests/e2e/r11g-server-smoke/tool-error-recovery.test.ts` | mock `lib/retrieve/index` | mock `tool_name_bridge` |
| `tests/providers/agentic-loop-engine.test.ts` | mock `lib/retrieve/index` | mock `tool_name_bridge` |
| `tests/governance/sla_probe_new_tools.test.ts` | `@/lib/retrieve/index` (RETRIEVAL_TOOLS) | `tool_name_bridge` + `retrieval_capability_spec` |
| `tests/classical/classical_pipeline_integration.test.ts` | `@/lib/retrieve/classical_*` | `@/lib/retrieval/tools/classical_*` |

---

## New Files Created

| File | Purpose |
|---|---|
| `platform/src/lib/retrieval/shared_types.ts` | Canonical home for ToolBundle, QueryPlan, RetrievalTool (without audience_tier) |
| `platform/src/lib/retrieval/tools/classical_text_search_tool.ts` | Moved from lib/retrieve |
| `platform/src/lib/retrieval/tools/classical_attribution_lookup_tool.ts` | Moved from lib/retrieve |
| `platform/src/lib/retrieval/tools/classical_disclosure_filter.ts` | Moved from lib/retrieve |

---

## audience_tier Status

- `lib/retrieve/types.ts` had `audience_tier` in `QueryPlan` — **removed** in new `lib/retrieval/shared_types.ts`.
- `lib/mcp/primitives_registry.ts` did not carry `audience_tier`.
- Residual `audience_tier` in the codebase is serve-time access control (MCP auth, prompts, cache) — intentionally retained per DG1 ruling. Zero `audience_tier` remains in retrieval-layer types.

---

## Test Results (post-deletion)

```
Test Files  420 passed | 11 skipped (431)
Tests  5054 passed | 174 skipped | 1 todo (5229)
```

- `chart_agnostic_gate`: PASS — 0 violations
- `parity_check`: PASS (exit 0)

---

## Known Residuals (not test failures)

Two manual SLA probe scripts in `platform/scripts/` import from deleted `lib/retrieve/` tool files
(`sla_probe_temporal.ts`, `sla_probe_planner_blind_tools.ts`). These are NOT in the `npm test` suite
and do not cause CI failures. They import individual tool wrappers (`temporal`, `lel_query`,
`query_signal_state`, etc.) that were never committed to git HEAD. These scripts require separate
remediation when those tool implementations are built. They are documented here as known residuals.

---

*End of RETRIEVAL_CITATION_REPORT_LIB_RETRIEVE_RETIREMENT v1.0 — 2026-06-28*
