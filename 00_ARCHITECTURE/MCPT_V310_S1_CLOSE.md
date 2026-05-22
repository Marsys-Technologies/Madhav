---
artifact: MCPT_V310_S1_CLOSE.md
status: CLOSED
version: 1.0
session_id: v3.1.0-S1
worktree: A (MadhavMCPT-FDN)
branch: feature/mcpt-foundation
authored_by: Claude Code sub-agent (Sonnet 4.6)
authored_on: 2026-05-22
parent_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCPT_V310_S1_v1_0.md
---

# v3.1.0-S1 — Code-Level Fixes — Session Close

All 6 scope items (F.1, F.2, F.3, F.4, F.5, F.7) delivered. F.6 not touched (explicitly out of scope).

## Commits

| Fix | SHA | Subject |
|-----|-----|---------|
| F.1 | 9ac54011 | prefer params.text/query_text over surgical_primitive placeholder |
| F.2 | 2edf825f | params.domain and params.limit fallback in msr_sql; dynamic LIMIT via $10 |
| F.3 | 5af0c7fe | enum-derived description for query_chart_facts via description_builder |
| F.4 | c50e210f | bind MCP_INTERNAL_TOKEN from Secret Manager in cloudbuild.yaml |
| F.5 | 8c48fd44 | 60s SHA-256-keyed in-memory cache for Bearer token validation |
| F.7 | 504b7a05 | remove token-budget allocation call from MCP execute path |

## Per-Fix Evidence

### F.1 — vector_search placeholder-query fix

File: `platform/src/lib/retrieve/vector_search.ts` (line ~235)

Change: replaced `const queryText = plan.query_text` with a three-level fallback:
1. `params?.text` (MCP surgical primitive passthrough)
2. `params?.query_text` (alternate field name)
3. `plan?.query_text` when it does NOT start with `surgical_primitive:` (otherwise empty string)
4. Throws `Error('vector_search: no query text resolved')` if all sources are empty.

Gate check: `grep -q "params?.text" platform/src/lib/retrieve/vector_search.ts` → PASS

### F.2 — params vs plan smuggling audit

Primary file: `platform/src/lib/retrieve/msr_sql.ts`

Changes:
- Added `paramsDomain` / `paramsDomains` extraction from `params.domain` (supports string or string[]).
- `effectiveDomains` = `paramsDomains` (if non-empty) else `plan.domains`.
- Added `DEFAULT_LIMIT = 100` constant.
- SQL changed from `LIMIT 100` to `LIMIT $10` (dynamic parameter).
- `queryLimit` = `paramsLimit` (if > 0) else `DEFAULT_LIMIT`.
- Both primary query and fallback query pass `queryLimit` as $10.

Audit of other `retrieve/*.ts` files for `plan.domain/limit/karakas`:
- `manifest_query.ts`: `plan.query_text` used only as fallback after `params.question` → acceptable
- `multi_school_signal_lookup_tool.ts`: `plan.query_text` used only as fallback after `params.topic/signal_ids` → acceptable
- `classical_text_search_tool.ts`: `params.query` ?? `plan.query_text` → acceptable (params wins)
- No other files had bare `plan.domain`, `plan.limit`, or `plan.karakas` reads without params fallback.

### F.3 — Enum-derived tool descriptions

New file: `platform-mcp/src/tools/description_builder.ts`
- `buildToolDescription({ baseDescription, enumSource, coverageHint })` generates description including all enum values.

Modified file: `platform-mcp/src/tools/query_chart_facts.ts`
- `CHART_FACTS_CATEGORIES` constant: exhaustive list mirroring `ChartFactsCategory` enum from `platform/src/lib/retrieve/chart_facts_query.ts:21–30` (37 values).
- `CHART_FACTS_TOOL_DESCRIPTION` built via `buildToolDescription` at module load time.
- `server.tool()` registration uses `CHART_FACTS_TOOL_DESCRIPTION` (no more hand-authored fake categories).
- Schema `category` field description now lists all 37 real categories.

Test: `platform-mcp/test/tool_descriptions.test.ts` (4 tests, all PASS)
- Asserts `CHART_FACTS_CATEGORIES` matches `PLATFORM_ENUM_CATEGORIES` set exactly (no extras, no omissions)
- Asserts no duplicates in `CHART_FACTS_CATEGORIES`
- Asserts `buildToolDescription` includes all enumSource items in output
- Asserts `buildToolDescription` works without `coverageHint`

Run timestamp: 2026-05-22 ~14:14 IST — 9/9 pass.

### F.4 — cloudbuild.yaml MCP_INTERNAL_TOKEN binding

File: `platform-mcp/cloudbuild.yaml`

Added `'--update-secrets=MCP_INTERNAL_TOKEN=mcp-internal-token:latest'` to the `gcloud run deploy` step args.

Gate check: `grep -q "update-secrets=MCP_INTERNAL_TOKEN" platform-mcp/cloudbuild.yaml` → PASS

### F.5 — Bearer validation cache

File: `platform-mcp/src/auth.ts`

Changes:
- Module-scoped `Map<string, {principal: Principal, expiresAt: number}>`.
- `CACHE_TTL_MS = 60_000`.
- Cache key = `createHash('sha256').update(authHeader).digest('hex')` (raw token never stored in map).
- `evictExpired()` called on each lookup (lazy eviction, prevents unbounded growth).
- `validateMcpKeyFromHeader()`: checks cache before platform fetch; writes on success; does NOT cache failures.
- Two test-only exports: `_testClearCache()` and `_testGetCacheSize()`.

Gate check: `grep -q "Map<string" platform-mcp/src/auth.ts` → PASS

Test: `platform-mcp/test/auth_cache.test.ts` (5 tests, all PASS)
- 100 sequential validations with same key → 1 fetch, 99% cache hit rate ≥ 95% threshold
- Cache returns identical principal on repeated calls
- Different tokens get separate cache entries
- null header → no cache entry, no fetch
- Failed validation → no cache entry, next call re-hits platform

Run timestamp: 2026-05-22 ~14:14 IST — 9/9 pass (combined with F.3 run).

### F.7 — arbitrateBudgets call-site removal

Files modified:
- `platform/src/app/api/mcp/execute/route.ts`
  - Removed `import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'`
  - Removed `import { DEFAULT_STACK_ID, getModelMeta, DEFAULT_MODEL_ID }` → kept only `DEFAULT_STACK_ID`
  - Removed the `arbitrateBudgets(...)` call + its surrounding model-meta lookup
  - Retained `const modelId = await getEffectiveModel(...)` (still needed for `orchestrator.synthesize`)
  - Token budgets pass through unchanged from planner plan (correct for v3.1 zero-LLM architecture)
- `platform/src/app/api/mcp/__tests__/execute.integration.test.ts`
  - Removed `vi.mock('@/lib/pipeline/budget_arbiter', ...)` mock block
  - Replaced with clarifying comment referencing F.7

Verification: `! grep -rn "arbitrateBudgets\|budget_arbiter" platform/src/app/api/mcp/` → PASS (empty output)

Note: `platform/src/lib/pipeline/budget_arbiter.ts` is untouched. The `/consume` web path continues to use it.

## Test Results

### platform-mcp

```
Test Files  2 passed (2)
Tests  9 passed (9)
```
Run: 2026-05-22 14:14 IST

### platform

```
Test Files  4 failed | 361 passed (365)
Tests  6 failed | 3715 passed | 22 skipped (3743)
```
Run: 2026-05-22 14:20 IST

The 6 platform failures are **pre-existing residuals** confirmed against main HEAD (identical failure set):
- `tests/integration/test_muhurat_finder_e2e.test.ts` — live sidecar test, requires running sidecar
- `src/app/panchang/__tests__/MuhuratFinderModal.test.tsx` — pre-existing UI test gap
- `src/lib/router/__tests__/retrieval_capability_spec.test.ts` — pre-existing spec coverage gap
- `src/lib/__tests__/mcp/red_team/plan_escalation.test.ts` — pre-existing schema expectation mismatch

Zero new test failures introduced by S1 changes.

## Gate Command Verification

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  ! grep -rn "arbitrateBudgets\|budget_arbiter" platform/src/app/api/mcp/ && \
  grep -q "params?.text" platform/src/lib/retrieve/vector_search.ts && \
  grep -q "update-secrets=MCP_INTERNAL_TOKEN" platform-mcp/cloudbuild.yaml && \
  grep -q "Map<string" platform-mcp/src/auth.ts
```
All conditions: PASS (no output = no grep matches for F.7; positive matches for F.1, F.4, F.5)

## Residuals

None. F.6 (`marsys_methodology_block` removal) remains explicitly deferred per brief §1.

---

*End of MCPT_V310_S1_CLOSE.md. Sealed 2026-05-22.*
