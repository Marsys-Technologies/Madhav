---
session_id: UDA-2-S7
phase: UDA-2
title: "MCP wrappers — query_rm_walk + query_jaimini_drishti"
status: pending
---

# UDA-2-S7: MCP Wrappers — query_rm_walk + query_jaimini_drishti

## Goal
Create MCP tool wrappers for the Resonance Map walk and Jaimini drishti tools.

## Context
- `platform/src/lib/retrieve/query_rm_walk.ts` (TOOL_NAME='query_rm_walk') — file-based walk
  over RM_v2_0.md (35 RM element blocks). Input: { seed_signal_id?: string }

- `platform/src/lib/retrieve/query_jaimini_drishti.ts` (TOOL_NAME='query_jaimini_drishti') —
  sidecar stub (returns not_implemented). Input: { params?: Record<string, unknown> }
  NOTE: This tool is a stub — the sidecar endpoint is not yet implemented. The MCP wrapper
  should be created anyway so the capability slot exists. The handler will return an informative
  not_implemented envelope which is acceptable.

## Steps

1. Create `platform-mcp/src/tools/query_rm_walk.ts`:
   - Input: seed_signal_id? (string e.g. 'MSR.045')
   - registerQueryRmWalk calls callPlatformPrimitive('query_rm_walk', args, principal)

2. Create `platform-mcp/src/tools/query_jaimini_drishti.ts`:
   - Input: params? (z.record(z.unknown()).optional())
   - registerQueryJaiminiDrishti calls callPlatformPrimitive('query_jaimini_drishti', args, principal)
   - In the description, note: "stub — returns not_implemented until M6+ Jaimini engine is built"

3. Register both in server.ts. Update tool count +2.

4. Write tests for both.

5. Commit:
   ```bash
   git add platform-mcp/src/tools/query_rm_walk.ts platform-mcp/src/tools/query_rm_walk.test.ts \
     platform-mcp/src/tools/query_jaimini_drishti.ts platform-mcp/src/tools/query_jaimini_drishti.test.ts \
     platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S7 — query_rm_walk + query_jaimini_drishti MCP wrappers"
   ```

## Acceptance criteria
- Both files exist, both registered in server.ts, tsc exits 0
