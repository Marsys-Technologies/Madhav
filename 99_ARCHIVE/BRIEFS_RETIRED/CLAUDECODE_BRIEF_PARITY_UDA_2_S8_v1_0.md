---
session_id: UDA-2-S8
phase: UDA-2
title: "MCP wrappers — timeline_query + query_signal_state"
status: pending
---

# UDA-2-S8: MCP Wrappers — timeline_query + query_signal_state

## Goal
Create MCP tool wrappers for the L5 timeline and signal-state tools.

## Context
- `platform/src/lib/retrieve/timeline_query.ts` (TOOL_NAME='timeline_query') — queries
  rag_chunks where doc_type='l5_timeline'. Input: { dasha_name?: string, keyword?: string, limit?: number }
  IMPORTANT: KETU MD follows Mercury MD (2027-08-21). Never suggest Saturn MD as upcoming.

- `platform/src/lib/retrieve/query_signal_state.ts` (TOOL_NAME='query_signal_state') — reads
  signal_states table (migration 023). Input: { chart_id?: string, date?: string (YYYY-MM-DD),
  state_filter?: 'lit'|'dormant'|'ripening', limit?: number }

## Steps

1. Create `platform-mcp/src/tools/timeline_query.ts`:
   - Input: dasha_name? (string e.g. 'Mercury MD'), keyword? (string), limit? (1–50, default 8)
   - Include dasha sequence note in description
   - registerTimelineQuery calls callPlatformPrimitive('timeline_query', args, principal)

2. Create `platform-mcp/src/tools/query_signal_state.ts`:
   - Input: chart_id? (UUID), date? (YYYY-MM-DD string), state_filter? (enum: lit|dormant|ripening),
     limit? (1–200, default 50)
   - registerQuerySignalState calls callPlatformPrimitive('query_signal_state', args, principal)

3. Register both in server.ts. Update tool count +2.

4. Write tests for both.

5. Commit:
   ```bash
   git add platform-mcp/src/tools/timeline_query.ts platform-mcp/src/tools/timeline_query.test.ts \
     platform-mcp/src/tools/query_signal_state.ts platform-mcp/src/tools/query_signal_state.test.ts \
     platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S8 — timeline_query + query_signal_state MCP wrappers"
   ```

## Acceptance criteria
- Both files exist, both registered in server.ts, tsc exits 0
