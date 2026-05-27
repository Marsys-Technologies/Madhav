---
session_id: R1-S1
status: PENDING
phase: GISMCP-R1
title: "server.ts de-gating — remove tier conditional, audit observability tools"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
branch: fix/gismcp-r1-r2
may_touch:
  - platform-mcp/src/server.ts
  - platform-mcp/src/tools/read_asset.ts
  - platform-mcp/src/tools/get_trace.ts
  - platform-mcp/src/tools/list_recent_queries.ts
  - platform-mcp/src/tools/tool_health.ts
  - platform-mcp/src/tools/data_coverage.ts
  - platform-mcp/src/tools/log_prediction.ts
  - platform-mcp/src/tools/record_outcome.ts
  - platform-mcp/src/tools/flag_disagreement.ts
must_not_touch:
  - platform/src/**
  - "*.yaml"
  - 00_ARCHITECTURE/**
  - supabase/**
---

# R1-S1: server.ts De-Gating

## Context

`platform-mcp/src/server.ts` conditionally registers 5 ops tools only when `tier !== 'client'`:

```typescript
if (tier !== 'client') {
  registerToolHealth(server)
  registerDataCoverage(server)
  registerLogPrediction(server)
  registerRecordOutcome(server)
  registerFlagDisagreement(server)
}
```

The native is super_admin of his own instrument. There is no reason to hide these tools from any MCP caller. Remove this gate so all 40 tools register unconditionally for every API key tier.

## Steps

### Step 1 — Read server.ts

Read the ENTIRE `platform-mcp/src/server.ts`. Locate:
1. The `if (tier !== 'client')` block (with the 5 registerX calls inside)
2. Where the `tier` variable is extracted from the API key record
3. Any other conditional registration blocks that may reference tier

### Step 2 — Remove the conditional

Replace:
```typescript
if (tier !== 'client') {
  registerToolHealth(server)
  registerDataCoverage(server)
  registerLogPrediction(server)
  registerRecordOutcome(server)
  registerFlagDisagreement(server)
}
```

With:
```typescript
// All ops tools registered unconditionally — native is super_admin of his own instrument
registerToolHealth(server)
registerDataCoverage(server)
registerLogPrediction(server)
registerRecordOutcome(server)
registerFlagDisagreement(server)
```

If the `tier` variable is ONLY used for this conditional and nowhere else, remove its extraction too (reduces dead code). If it's used elsewhere (e.g., for B.11 floor tier-conditioned rules), keep the extraction but just remove the conditional registration block.

### Step 3 — Audit observability + raw asset tool handlers

Read each of these files and check for secondary tier gates inside the tool handler itself (NOT in server.ts registration):
- `platform-mcp/src/tools/read_asset.ts`
- `platform-mcp/src/tools/get_trace.ts`
- `platform-mcp/src/tools/list_recent_queries.ts`

For each: if there is a `if tier === 'client' → return error` or equivalent pattern, remove it. These tools must execute for all tiers.

Read `platform-mcp/src/tools/tool_health.ts` and `platform-mcp/src/tools/data_coverage.ts` as well — same audit.

### Step 4 — Update the comment block at the top of server.ts

The comment that says "40 tools registered (v4.5, ...)" likely has a section noting the tier conditional. Update it to reflect that all 40 are now unconditional.

### Step 5 — Run existing server.ts tests (smoke)

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform-mcp
npx vitest run 2>&1 | tail -20
```

Expected: 0 failures. If any test asserts the OPPOSITE of what we just changed (e.g., "client tier should NOT see tool_health"), that test is wrong — update it to expect 40 tools for all tiers. Report if any such tests are found.

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
git add platform-mcp/src/server.ts platform-mcp/src/tools/
git commit -m "fix(R1): remove tier gating from server.ts — all 40 tools unconditional

- Remove if(tier !== 'client') block from server.ts
- registerToolHealth/DataCoverage/LogPrediction/RecordOutcome/FlagDisagreement now
  register for ALL API key tiers
- Audit read_asset/get_trace/list_recent_queries: no secondary tier gates found (or fixed)
- Native is super_admin; no reason to hide ops tools from any MCP caller

Closes R1-S1 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `! grep -q "tier !== 'client'" platform-mcp/src/server.ts` — conditional is gone
2. `grep -q 'registerToolHealth(server)' platform-mcp/src/server.ts` — registered unconditionally
3. `grep -q 'registerDataCoverage(server)' platform-mcp/src/server.ts`
4. `grep -q 'registerLogPrediction(server)' platform-mcp/src/server.ts`
5. No secondary tier gate in read_asset.ts, get_trace.ts, list_recent_queries.ts
6. `npx vitest run` in platform-mcp → 0 failures
