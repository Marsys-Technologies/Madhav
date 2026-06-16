---
session_id: UDA-2-S3
phase: UDA-2
title: "MCP wrappers — kp_query + query_kp_ruling_planets"
status: pending
---

# UDA-2-S3: MCP Wrappers — kp_query + query_kp_ruling_planets

## Goal
Create MCP tool wrappers for both KP system tools.

## Context
- `platform/src/lib/retrieve/kp_query.ts` (TOOL_NAME='kp_query') — queries chart_facts for
  KP data: cusp significators, planet significators, star/sub lord chains.
  Input interface: { cusp?: number, planet?: string, query_type?: 'significators'|'star_lord'|'sub_lord'|'sub_sub_lord'|'all' }

- `platform/src/lib/retrieve/query_kp_ruling_planets.ts` (TOOL_NAME='query_kp_ruling_planets') —
  reads kp_sublords table. Input: { chart_id?: string }

## Steps

1. Create `platform-mcp/src/tools/kp_query.ts`:
   - KpQueryInputSchema: cusp? (1–12 int), planet? (string), query_type? (enum above)
   - registerKpQuery calls callPlatformPrimitive('kp_query', args, principal)

2. Create `platform-mcp/src/tools/query_kp_ruling_planets.ts`:
   - QueryKpRulingPlanetsInputSchema: chart_id? (UUID string)
   - registerQueryKpRulingPlanets calls callPlatformPrimitive('query_kp_ruling_planets', args, principal)

3. Register both in server.ts (Tier 3 section). Update tool count +2.

4. Write tests for both.

5. Commit:
   ```bash
   git add platform-mcp/src/tools/kp_query.ts platform-mcp/src/tools/kp_query.test.ts \
     platform-mcp/src/tools/query_kp_ruling_planets.ts platform-mcp/src/tools/query_kp_ruling_planets.test.ts \
     platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S3 — kp_query + query_kp_ruling_planets MCP wrappers"
   ```

## Acceptance criteria
- Both files exist, both registered in server.ts, tsc exits 0
