---
session_id: UDA-2-S6
phase: UDA-2
title: "MCP wrappers — query_ucn_walk + query_cdlm_lookup"
status: pending
---

# UDA-2-S6: MCP Wrappers — query_ucn_walk + query_cdlm_lookup

## Goal
Create MCP tool wrappers for the two L2.5 synthesis-document walk tools.

## Context
- `platform/src/lib/retrieve/query_ucn_walk.ts` (TOOL_NAME='query_ucn_walk') — file-based walk
  over UCN_v4_0.md. Input: { seed_signal_id?: string, depth?: number }

- `platform/src/lib/retrieve/query_cdlm_lookup.ts` (TOOL_NAME='query_cdlm_lookup') — file-based
  lookup over CDLM_v1_1.md (81 cells). Input: { domain_a?: string, domain_b?: string, signal_id?: string }

## Steps

1. Create `platform-mcp/src/tools/query_ucn_walk.ts`:
   - Input: seed_signal_id? (string e.g. 'MSR.234'), depth? (int 1–5, default 2)
   - registerQueryUcnWalk calls callPlatformPrimitive('query_ucn_walk', args, principal)

2. Create `platform-mcp/src/tools/query_cdlm_lookup.ts`:
   - Input: domain_a? (string), domain_b? (string), signal_id? (string)
   - registerQueryCdlmLookup calls callPlatformPrimitive('query_cdlm_lookup', args, principal)

3. Register both in server.ts. Update tool count +2.

4. Write tests for both.

5. Commit:
   ```bash
   git add platform-mcp/src/tools/query_ucn_walk.ts platform-mcp/src/tools/query_ucn_walk.test.ts \
     platform-mcp/src/tools/query_cdlm_lookup.ts platform-mcp/src/tools/query_cdlm_lookup.test.ts \
     platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S6 — query_ucn_walk + query_cdlm_lookup MCP wrappers"
   ```

## Acceptance criteria
- Both files exist, both registered in server.ts, tsc exits 0
