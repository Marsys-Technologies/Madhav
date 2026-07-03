---
artifact: RETRIEVAL_D7_CALLER_MAP
canonical_id: RETRIEVAL_D7_CALLER_MAP
version: 1.0
status: CURRENT
created: 2026-06-28
author: Claude Code (Caller Inventory Agent — D7 Chat-Channel Migration)
classification: Migration work-list and reverse-citation baseline
parent: CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION_v1_0 §1
scope: Read-only inventory. No files modified. All greps against live tree at HEAD.
---

# RETRIEVAL D7 CALLER MAP v1.0

Authoritative caller map for the D7 chat-channel migration (§1 deliverable).
Covers all references to `lib/retrieve` (imports), `msr_sql` (usage as tool name),
and `primitives_registry` (bridge fold target).

---

## §1 — Summary table

| # | File | Classification | Primary imports / usage | Registry replacement | Blast radius |
|---|---|---|---|---|---|
| 1 | `src/app/api/chat/consult/route.ts` | **(a) CHAT-PATH-RUNTIME** | `getTool`, `buildChatToolsFromNames`, `ToolBundle`, `ToolBundleResult` (types); uses `msr_sql` as tool name in step-type classification and B.11 injection | `getCapability(uri)` / `getCatalog()` from `@/lib/retrieval/registry`; `ToolResult` type replaces `ToolBundle`; see §2.1 | **CRITICAL** |
| 2 | `src/lib/pipelines/shared/run_adapter_dispatch.ts` | **(b) OTHER-RUNTIME** | `buildChatToolsFromNames`, `ToolBundle` (type); uses `msr_sql` as literal tool name in L2.5 classification | Same as #1 — `buildChatToolsFromNames` moves to registry-native catalog lookup; `ToolBundle` → `ToolResult` | **HIGH** |
| 3 | `src/lib/synthesis/mcp_tool_executor.ts` | **(b) OTHER-RUNTIME** | `getTool`, `QueryPlan` (type) | `getCapability(uri)` + `CapabilityContext` from `@/lib/retrieval/registry`; `QueryPlan` lives in `@/lib/router/types` (no change) | **HIGH** |
| 4 | `src/app/api/mcp/primitives/[tool]/route.ts` | **(b) OTHER-RUNTIME** | `getTool` (dispatches retrieval tool by name after MCP whitelist check); also imports `primitives_registry` | `getCapability(uri)` from `@/lib/retrieval/registry`; `primitives_registry` folds into registry — see §2.4 | **HIGH** |
| 5 | `src/lib/providers/anthropic/adapter.ts` | **(b) OTHER-RUNTIME** | `normalizeInputSchema` from `@/lib/retrieve/tool_catalogue` | `normalizeInputSchema` moves to `@/lib/retrieval/registry/tool_catalogue` (new shared util) or is inlined | **MEDIUM** |
| 6 | `src/lib/checkpoints/types.ts` | **(b) OTHER-RUNTIME** | `ToolBundle` (type-only import) | `ToolResult` from `@/lib/retrieval/registry` | **MEDIUM** |
| 7 | `src/lib/synthesis/types.ts` | **(b) OTHER-RUNTIME** | `ToolBundle` (type-only import) | `ToolResult` from `@/lib/retrieval/registry` | **MEDIUM** |
| 8 | `src/lib/audit/consumer.ts` | **(b) OTHER-RUNTIME** | `ToolBundle` (type-only import) | `ToolResult` from `@/lib/retrieval/registry` | **MEDIUM** |
| 9 | `src/lib/performance/compliance.ts` | **(b) OTHER-RUNTIME** | `ToolBundle` (type-only import) | `ToolResult` from `@/lib/retrieval/registry` | **MEDIUM** |
| 10 | `src/lib/performance/ingestion.ts` | **(b) OTHER-RUNTIME** | `ToolBundle` (type-only import) | `ToolResult` from `@/lib/retrieval/registry` | **MEDIUM** |
| 11 | `src/lib/mcp/primitives_registry.ts` | **(b) OTHER-RUNTIME (fold target)** | Self — this IS the bridge to fold. `SURGICAL_TOOLS`, `MCP_TO_RETRIEVAL_TOOL`, `isAllowedSurgicalTool` | Fold whitelist into registry capability URIs; `isAllowedSurgicalTool` becomes `hasCapability(uri)` on the registry | **HIGH** |
| 12 | `src/scripts/test/msr_sql_smoke.ts` | **(c) TEST / SCRIPT** | `getTool` (fetches `msr_sql` tool for live smoke test) | `getCapability('marsys://tool/L2/query_signals')` from registry | **LOW** |
| 13 | `src/__tests__/integration/mcp_stub_engines.integration.test.ts` | **(c) TEST** | `getTool`, `RETRIEVAL_TOOLS` | `getCapability`, `getCatalog()` from registry | **LOW** |
| 14 | `src/lib/__tests__/mcp/primitives.test.ts` | **(c) TEST** | `getTool` (mocked); imports `primitives_registry` types | Mock updated to `@/lib/retrieval/registry` after fold | **LOW** |
| 15 | `src/lib/mcp/__tests__/primitives_registry.test.ts` | **(c) TEST** | `isAllowedSurgicalTool`, `MCP_TO_RETRIEVAL_TOOL`, `SURGICAL_TOOLS` from `primitives_registry` | Tests migrate to registry URI checks after fold | **LOW** |
| 16 | `src/lib/__tests__/mcp/red_team/whitelist.test.ts` | **(c) TEST** | `isAllowedSurgicalTool`, `MCP_TO_RETRIEVAL_TOOL`, `SURGICAL_TOOLS` from `primitives_registry` | Same as #15 | **LOW** |
| 17 | `src/lib/router/__tests__/retrieval_capability_spec.test.ts` | **(c) TEST** | `RETRIEVAL_TOOLS` from `@/lib/retrieve` (validates RETRIEVAL_TOOLS vs RETRIEVAL_CAPABILITY_SPEC coverage) | After migration: test gates `getCatalog()` vs `RETRIEVAL_CAPABILITY_SPEC` | **LOW** |

**Classifications NOT found in grep results (no-op):**
- `src/lib/retrieval/registry/**` — already on the registry; mentions of `lib/retrieve/index` in `register_d7_channel.ts` are string literals in descriptions, NOT live imports.
- `src/lib/retrieval/adapters/**` — already importing from `@/lib/retrieval/registry` directly (confirmed by reverse grep).

---

## §2 — Per-file detail

### 2.1 `src/app/api/chat/consult/route.ts` — CRITICAL

**Classification:** (a) CHAT-PATH-RUNTIME

**Imports used:**
```typescript
import { getTool } from '@/lib/retrieve/index'                          // line 76
import { buildChatToolsFromNames } from '@/lib/retrieve/tool_catalogue' // line 77
import type { ToolBundle, ToolBundleResult } from '@/lib/retrieve/index' // line 88
```

**`msr_sql` usage (non-import):**
- Line 117: `if (['msr_sql', 'query_msr_aggregate'].includes(toolName)) return 'sql'` — step-type classification
- Line 139: inclusion in L2.5 tool list for citation routing
- Lines 478–499: B.11 floor injection logic (references `msr_sql` as a literal tool name injected into planner)

**Registry replacement:**
- `getTool(name)` → `getCapability(uri)` from `@/lib/retrieval/registry/index`. The chat route currently resolves tool names through `RETRIEVAL_TOOLS` in `lib/retrieve/index.ts`. After migration it resolves capability URIs (`marsys://tool/L2/query_signals` for `msr_sql`) through `getCapability()` / `getCatalog()`.
- `buildChatToolsFromNames(names)` — this function already delegates to `@/lib/contract/registry` (not directly to `lib/retrieve`); however it is imported from `lib/retrieve/tool_catalogue`. After migration, import from the new shared location (either `@/lib/retrieval/registry/tool_catalogue` or promote directly to `@/lib/contract`).
- `ToolBundle` / `ToolBundleResult` → `ToolResult` + inline result shape from `@/lib/retrieval/registry/types`.
- `msr_sql` literal name references in B.11 injection: these stay as tool_name strings in `PlanStep` objects (the B.11 injection logic in `b11_floor_inject.ts` uses tool names, not registry URIs). No change required for those literal strings — only the `getTool()` call that resolves a name to an implementation needs updating.

**Notes:**
- The route already delegates the streaming body to `runAdapterDispatch` (#2) — changes here are primarily the import lines and type references.
- `forward_looking: boolean` in the query plan is already in `@/lib/router/types` `QueryPlan`; that type does NOT move.
- `audience_tier` must be stripped from all downstream registry calls per DG1 ruling.

---

### 2.2 `src/lib/pipelines/shared/run_adapter_dispatch.ts` — HIGH

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import { buildChatToolsFromNames } from '@/lib/retrieve/tool_catalogue' // line 57
import type { ToolBundle } from '@/lib/retrieve/index'                  // line 58
```

**`msr_sql` usage (non-import):**
- Line 521: inclusion in L2.5 tool name list for classification within `runAdapterDispatch`

**Registry replacement:**
- `buildChatToolsFromNames` → same as §2.1 above.
- `ToolBundle` → `ToolResult` from `@/lib/retrieval/registry`.

**Notes:** The dispatch body received from route.ts already has all planner/bundle context. The main change is the import path for the type and the catalogue helper.

---

### 2.3 `src/lib/synthesis/mcp_tool_executor.ts` — HIGH

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import { getTool } from '@/lib/retrieve/index'          // line 19
import type { QueryPlan } from '@/lib/retrieve/types'   // line 20
```

**Usage:** `getTool(toolCall.name)` → `tool.retrieve(ctx.queryPlan, toolCall.input)`.

**Registry replacement:**
- `getTool(name)` → `getCapability(uri)` where the URI is resolved from `toolCall.name` via a name→URI map (or `listCapabilities().find(c => c.name === toolCall.name)`).
- `QueryPlan` → already exists in `@/lib/router/types` with no tie to `lib/retrieve`; update import path.
- The `tool.retrieve()` call pattern → `capability.handler(args, ctx)` — signature is different; parity test required.

**Notes:** The result shape changes from `ToolBundle` (`{ results: ToolBundleResult[] }`) to `ToolResult` (`{ content: unknown, is_error: boolean }`). The JSON serialization on line 64 must be updated accordingly.

---

### 2.4 `src/app/api/mcp/primitives/[tool]/route.ts` — HIGH

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import { getTool } from '@/lib/retrieve/index'           // line 23
import { isAllowedSurgicalTool, MCP_TO_RETRIEVAL_TOOL }  // line 33
  from '@/lib/mcp/primitives_registry'
```

**Usage:** Whitelist check via `isAllowedSurgicalTool(mcpToolName)`, then resolves `retrievalToolName = MCP_TO_RETRIEVAL_TOOL[mcpToolName]`, then `getTool(retrievalToolName)`.

**Registry replacement:**
- The whitelist + name-mapping in `primitives_registry` folds into the registry: each whitelisted MCP tool corresponds to a capability URI. `isAllowedSurgicalTool(name)` → `hasCapability(mcpUriFor(name))` where `mcpUriFor` is a simple lookup table retained as a thin shim (or the URIs are registered with `name` matching the MCP tool name).
- `getTool(name)` → `getCapability(uri)` from `@/lib/retrieval/registry`.
- `tool.retrieve(queryPlan, toolParams)` → `capability.handler(args, ctx)`.
- The `MCP_TO_RETRIEVAL_TOOL` name→name map can be replaced by a name→URI map over `getCatalog()`.

**Notes:** This route also consumes `audience_tier` from headers — per DG1, that must be stripped before passing to capability handlers (capabilities are universal-access, no tier).

---

### 2.5 `src/lib/providers/anthropic/adapter.ts` — MEDIUM

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import { normalizeInputSchema } from '@/lib/retrieve/tool_catalogue' // line 52
```

**Usage:** Normalizes a raw JSON schema for tool input (converts Zod-derived schema to `{ type: 'object', properties: … }` shape).

**Registry replacement:**
- `normalizeInputSchema` is a pure utility with no dependency on `lib/retrieve` logic itself. Move to `@/lib/retrieval/registry/tool_catalogue` (new file) or `@/lib/contract/json_schema`. Update import path only.
- URI: no registry capability URI involved — this is a schema normalization helper, not a retrieval dispatch.

---

### 2.6 `src/lib/checkpoints/types.ts` — MEDIUM

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import type { ToolBundle } from '@/lib/retrieve/types'  // line 14
```

**Registry replacement:**
- `ToolBundle` → `ToolResult` from `@/lib/retrieval/registry/types`. The `ToolResult` interface (`{ content: unknown; is_error: boolean }`) is structurally narrower than `ToolBundle` (`{ results: ToolBundleResult[]; tool_name: string; … }`). The checkpoint types that use `ToolBundle` must be updated to the new shape, or a compatibility alias defined during transition.

---

### 2.7 `src/lib/synthesis/types.ts` — MEDIUM

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import type { ToolBundle } from '@/lib/retrieve/types'  // line 8
```

**Registry replacement:** Same as §2.6 — `ToolResult` from `@/lib/retrieval/registry/types`.

---

### 2.8 `src/lib/audit/consumer.ts` — MEDIUM

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import type { ToolBundle } from '@/lib/retrieve/types'  // line 10
```

**Registry replacement:** `ToolResult` from `@/lib/retrieval/registry/types`. The `AuditConsumerContext.tool_results: ToolBundle[]` field becomes `ToolResult[]`.

---

### 2.9 `src/lib/performance/compliance.ts` — MEDIUM

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import type { ToolBundle } from '@/lib/retrieve/types'  // line 11
```

**Registry replacement:** `ToolResult` from `@/lib/retrieval/registry/types`. The `detectB11Violation` function signature takes `toolResults` as `ToolBundle[]`; update to `ToolResult[]`.

---

### 2.10 `src/lib/performance/ingestion.ts` — MEDIUM

**Classification:** (b) OTHER-RUNTIME

**Imports used:**
```typescript
import type { ToolBundle } from '@/lib/retrieve/types'  // line 6
```

**Registry replacement:** Same as §2.9.

---

### 2.11 `src/lib/mcp/primitives_registry.ts` — HIGH (fold target)

**Classification:** (b) OTHER-RUNTIME — this IS the bridge to fold.

**Exports consumed by callers:**
- `SURGICAL_TOOLS` (const array) — consumed by tests and `isAllowedSurgicalTool`
- `SurgicalToolName` (type) — type guard
- `MCP_TO_RETRIEVAL_TOOL` (Record<string, SurgicalToolName>) — MCP name → retrieval tool name map
- `isAllowedSurgicalTool(name)` — whitelist guard used by `/api/mcp/primitives/[tool]/route.ts`

**Fold target:**
- The whitelist becomes a capability URI roster derived from `getCatalog()`. `isAllowedSurgicalTool(name)` → `hasCapability(mcpToRegistryUri(name))` where `mcpToRegistryUri` is a thin static map of the 37 MCP tool names to their `marsys://…` URIs.
- `MCP_TO_RETRIEVAL_TOOL` becomes `MCP_TO_CAPABILITY_URI: Record<string, CapabilityUri>` (or is dropped if the registry name matches the MCP tool name directly).
- After fold: this file is deleted; callers repoint to `@/lib/retrieval/registry`.

**Callers of `primitives_registry`:**
- `/api/mcp/primitives/[tool]/route.ts` — runtime (see §2.4)
- `src/lib/mcp/__tests__/primitives_registry.test.ts` — test (see §2.15)
- `src/lib/__tests__/mcp/primitives.test.ts` — test (see §2.14)
- `src/lib/__tests__/mcp/red_team/whitelist.test.ts` — test (see §2.16)

---

### 2.12 `src/scripts/test/msr_sql_smoke.ts` — LOW

**Classification:** (c) TEST / SCRIPT

**Imports used:**
```typescript
import { getTool } from '@/lib/retrieve/index'  // line 6
```

**Usage:** `getTool('msr_sql')` → `tool.retrieve(plan)` — live smoke test against DB.

**Registry replacement:**
- `getCapability('marsys://tool/L2/query_signals')` from `@/lib/retrieval/registry`.
- Call `capability.handler(args, { db: … })` instead of `tool.retrieve(plan)`.
- The plan shape (including `forward_looking`) must be mapped to registry args: `domain`, `min_salience`, `top_k`, etc.

---

### 2.13 `src/__tests__/integration/mcp_stub_engines.integration.test.ts` — LOW

**Classification:** (c) TEST

**Imports used:**
```typescript
import { getTool, RETRIEVAL_TOOLS } from '../../lib/retrieve/index'  // line 26
```

**Usage:** Registry smoke — verifies that `getTool(name)` resolves for 4 previously-stubbed R2 tools.

**Registry replacement:**
- `getCapability(uri)`, `getCatalog()` from `@/lib/retrieval/registry`.
- Test verifies that the 4 stub URIs are registered in the registry.

---

### 2.14 `src/lib/__tests__/mcp/primitives.test.ts` — LOW

**Classification:** (c) TEST

**Imports used:**
```typescript
import { getTool } from '@/lib/retrieve/index'         // line 121 (mocked)
import { isAllowedSurgicalTool, MCP_TO_RETRIEVAL_TOOL, SURGICAL_TOOLS }
  from '@/lib/mcp/primitives_registry'                 // line 23
```

**Usage:** Tests the whitelist guard and the primitives route dispatch (both mocked). `getTool` is mocked via `vi.mock('@/lib/retrieve/index')`.

**Registry replacement:**
- After fold: mock `@/lib/retrieval/registry` for `getCapability`, `hasCapability`.
- Whitelist assertions (`isAllowedSurgicalTool`) migrate to `hasCapability(uri)` assertions.

---

### 2.15 `src/lib/mcp/__tests__/primitives_registry.test.ts` — LOW

**Classification:** (c) TEST

**Imports used:**
```typescript
import { isAllowedSurgicalTool, MCP_TO_RETRIEVAL_TOOL, SURGICAL_TOOLS }
  from '../primitives_registry'  // line 2
```

**Usage:** Unit tests for `primitives_registry` itself — the fold deletes the source; these tests migrate to registry URI coverage tests.

---

### 2.16 `src/lib/__tests__/mcp/red_team/whitelist.test.ts` — LOW

**Classification:** (c) TEST

**Imports used:**
```typescript
import { isAllowedSurgicalTool, MCP_TO_RETRIEVAL_TOOL, SURGICAL_TOOLS }
  from '@/lib/mcp/primitives_registry'  // line 17
```

**Usage:** Red-team security tests for whitelist enforcement. After fold: tests verify registry-based whitelist enforcement.

---

### 2.17 `src/lib/router/__tests__/retrieval_capability_spec.test.ts` — LOW

**Classification:** (c) TEST

**Imports used:**
```typescript
import { RETRIEVAL_TOOLS } from '@/lib/retrieve'  // line 16
```

**Usage:** Coverage gate — verifies every tool in `RETRIEVAL_TOOLS` has a matching `RETRIEVAL_CAPABILITY_SPEC` entry.

**Registry replacement:**
- After migration: `getCatalog()` from `@/lib/retrieval/registry` replaces `RETRIEVAL_TOOLS`.
- Test gates `getCatalog().every(cap => RETRIEVAL_CAPABILITY_SPEC has cap.name entry)`.

---

## §3 — `msr_sql` reference audit (non-import occurrences)

These files reference `msr_sql` as a **tool name string** (not a `lib/retrieve` import). They do NOT need import-path changes — only the callers that dispatch through `getTool('msr_sql')` need updating. Listed here as the reverse-citation baseline for the retirement gate.

| File | Nature of reference | Action needed |
|---|---|---|
| `app/api/chat/consult/route.ts` | B.11 injection (`tool_name: 'msr_sql'`), step-type classification | String literals stay; dispatch updated (§2.1) |
| `lib/pipelines/shared/b11_floor_inject.ts` | B.11 injection constants, `toolsAuthorized.push('msr_sql')` | String literals stay (tool name is config, not a dispatch call) |
| `lib/pipelines/shared/run_adapter_dispatch.ts` | L2.5 classification list | String literal stays |
| `lib/contract/tool_metadata.ts` | Tool contract definition (`canonical_name: 'msr_sql'`) | Stays (contract registry, not dispatch) |
| `lib/router/retrieval_capability_spec.ts` | Planner capability entry | Stays (spec entry) |
| `lib/gateway/b11_floor.ts` | B.11 floor tool list | String literal stays |
| `lib/jyotish/domain_labels.ts` | Display label mapping | String literal stays |
| `lib/trace/types.ts` | TraceStep union | String literal stays |
| `lib/pipeline/manifest_compressor.ts` | Compression tool list | String literal stays |
| `lib/config/feature_flags.ts` | Flag description comment | No change |
| `lib/gates/gate_registry.ts` | Gate description string | No change |
| `lib/consume/provenance_assembler.ts` | Provenance display label | String literal stays |
| `lib/prompts/templates/shared.ts` | System prompt instruction | String literal stays |
| `lib/performance/compliance.ts` | L2.5 tool detection list | String literal stays |
| `lib/performance/judge_prompt.ts` | Judge prompt content | No change |
| All `__tests__` / `scripts` referencing `msr_sql` | Test data, mock params | Update when parent files migrate |

**Key insight:** `msr_sql` as a **string constant** appears throughout the pipeline as a tool name in config arrays, labels, and contracts. These do NOT require changes — they are configuration references to the tool name, not dispatch calls through `lib/retrieve`. Only the three dispatch sites (`consult/route.ts`, `mcp_tool_executor.ts`, `primitives/[tool]/route.ts`) need actual code changes.

---

## §4 — Registry capability gap analysis

The `lib/retrieve/index.ts` `RETRIEVAL_TOOLS` array contains these tool names that callers depend on. Each needs a registry URI equivalent before the caller can be repointed:

| `lib/retrieve` tool name | Registry URI (D1–D8) | Status |
|---|---|---|
| `msr_sql` | `marsys://tool/L2/query_signals` | **EXISTS** — `query_signals.ts` in L2_bodha layer |
| `chart_facts_query` | L1 layer capabilities (L1_ganita) | EXISTS — `get_positions`, `get_dashas`, etc. |
| `vector_search` | L0 layer (classical text search) | EXISTS — `query_classical_texts.ts` |
| `cgm_graph_walk` | L2 layer (graph traversal) | EXISTS — `traverse_chart_graph.ts` |
| `query_dasha_periods` | L1 layer | EXISTS — `get_dashas.ts` |
| `query_panchanga` | L1 layer | EXISTS — `get_panchanga.ts` |
| `query_ephemeris` | L0 layer | EXISTS — `query_planet_position.ts` |
| `query_transit_event` | L0 layer | EXISTS — `query_planet_transit.ts` |
| `lel_query` | L2 layer (signals, lel_capable) | EXISTS via `query_signals` `lel_enabled` flag |
| `classical_text_search` | L0 layer | EXISTS — `query_classical_texts.ts` |
| `pattern_register` | L2 layer | Verify in L2_bodha index |
| `resonance_register` | L2 layer | Verify in L2_bodha index |
| `query_varshaphala` | L1 layer (tajik) | EXISTS — `get_tajik.ts` |
| `divisional_query` | L1 layer | EXISTS — `get_divisionals.ts` |
| `remedial_codex_query` | L0 layer | EXISTS — `query_remedy_corpus.ts` |
| `query_muhurat` | L0 layer | VERIFY — `query_planet_transit.ts` or separate |
| `normalizeInputSchema` helper | No URI — pure utility | Move file location only |
| `buildChatToolsFromNames` helper | No URI — contract lookup util | Move file location only |
| `ToolBundle` / `ToolBundleResult` types | `ToolResult` in registry types | EXISTS — structural mismatch; adapter needed |

**Critical type-shape gap:** `ToolBundle` (lib/retrieve) has `{ results: ToolBundleResult[], tool_name, tool_version, invocation_params, served_from_cache, latency_ms, result_hash }`. `ToolResult` (registry) has `{ content: unknown, is_error: boolean }`. A compatibility adapter or transitional type alias is required for the 5 type-only callers (#6–#10) during migration.

---

## §5 — Prioritized migration order

**Rule:** chat route first, then by blast radius descending, tests last. The reverse-citation retirement gate (§4 of the brief) must not fire until all runtime callers are repointed.

### Phase 1 — Chat path (BLOCKING — DG1 split exists here)

1. **`src/lib/synthesis/mcp_tool_executor.ts`** — smallest chat-path file; port `getTool` + `QueryPlan` import; add parity test. Unblocks chat route repoint.
2. **`src/app/api/chat/consult/route.ts`** — repoint `getTool`, `buildChatToolsFromNames`, `ToolBundle`/`ToolBundleResult` types. Parity test: ≥2 charts, verify `msr_sql` queries return equivalent results from registry vs lib/retrieve.
3. **`src/lib/pipelines/shared/run_adapter_dispatch.ts`** — repoint `buildChatToolsFromNames` + `ToolBundle`. Parity test: pipeline dispatch round-trip.

### Phase 2 — MCP primitive route (high blast, fold target dependency)

4. **`src/app/api/mcp/primitives/[tool]/route.ts`** — repoint `getTool`; fold `primitives_registry` whitelist to registry URI check. Parity test: ≥2 charts via MCP primitive calls on both channels, verify identical filter behavior.

### Phase 3 — Type-only runtime callers (MEDIUM — all are type imports, zero logic change)

5. **`src/lib/checkpoints/types.ts`** — `ToolBundle` → `ToolResult` type swap.
6. **`src/lib/synthesis/types.ts`** — same.
7. **`src/lib/audit/consumer.ts`** — same.
8. **`src/lib/performance/compliance.ts`** — same.
9. **`src/lib/performance/ingestion.ts`** — same.

### Phase 4 — Utility helper callers (MEDIUM)

10. **`src/lib/providers/anthropic/adapter.ts`** — move `normalizeInputSchema` to new shared location; update import.

### Phase 5 — Fold the bridge (requires all above complete + reverse-citation gate)

11. **`src/lib/mcp/primitives_registry.ts`** — run reverse-citation grep (zero live runtime citations expected); produce citation report; delete file.
12. **`src/lib/retrieve/`** — run reverse-citation grep (zero live citations expected); produce citation report; retire `lib/retrieve/` tree (keep `types.ts` stub or move `RetrievalTool` type to a shim until all tests pass).

### Phase 6 — Tests (LOW — update after runtime callers are clean)

13. **`src/scripts/test/msr_sql_smoke.ts`** — repoint to registry capability.
14. **`src/__tests__/integration/mcp_stub_engines.integration.test.ts`** — repoint to `getCatalog()`.
15. **`src/lib/__tests__/mcp/primitives.test.ts`** — update mocks post-fold.
16. **`src/lib/mcp/__tests__/primitives_registry.test.ts`** — migrate to registry URI coverage tests.
17. **`src/lib/__tests__/mcp/red_team/whitelist.test.ts`** — migrate to registry whitelist tests.
18. **`src/lib/router/__tests__/retrieval_capability_spec.test.ts`** — repoint `RETRIEVAL_TOOLS` to `getCatalog()`.

---

## §6 — Reverse-citation baseline (pre-migration)

Run these greps to confirm zero citations before retiring each target. Expected counts at migration start (from inventory run on 2026-06-28):

| Target | Grep pattern | Current live citation count |
|---|---|---|
| `lib/retrieve/index` (runtime) | `grep -rn "from.*lib/retrieve" src --include="*.ts" --include="*.tsx"` | 21 hits across 10 files |
| `lib/mcp/primitives_registry` (runtime) | `grep -rn "primitives_registry" src --include="*.ts"` | 7 hits across 4 files |
| `msr_sql` as dispatch call | `grep -rn "getTool.*msr_sql\|getTool('msr_sql')"` | 2 hits (smoke script + route) |

After migration completes: all three counts must be zero (runtime files only; test files migrated separately).

---

*End of RETRIEVAL_D7_CALLER_MAP v1.0.*
*Generated 2026-06-28 by Caller Inventory Agent — read-only; no files modified.*
