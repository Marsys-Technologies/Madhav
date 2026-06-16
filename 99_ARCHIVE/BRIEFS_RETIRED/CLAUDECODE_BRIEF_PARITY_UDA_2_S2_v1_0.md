---
session_id: UDA-2-S2
phase: UDA-2
title: "MCP wrapper — temporal"
status: pending
---

# UDA-2-S2: MCP Wrapper — temporal

## Goal
Create a fully registered MCP tool wrapper for `temporal` so Channel C can access unified
transit and ephemeris data from the Python sidecar.

## Context
- Portal source: `platform/src/lib/retrieve/temporal.ts` (TOOL_NAME = 'temporal')
- No MCP wrapper exists yet
- temporal calls the Python sidecar at PYTHON_SIDECAR_URL for transit/ephemeris endpoints

## Steps

1. Read `platform/src/lib/retrieve/temporal.ts` to extract all sidecar endpoint params
   (date_from, date_to, include_transits, include_ephemeris, include_dashas, chart_id, etc.).

2. Create `platform-mcp/src/tools/temporal.ts`:
   - Export TEMPORAL_DESCRIPTION using buildToolDescription
   - Define TemporalInputSchema: date_from? (YYYY-MM-DD), date_to? (YYYY-MM-DD),
     include_transits? (bool, default true), include_ephemeris? (bool, default false),
     include_dashas? (bool, default false), chart_id? (UUID)
   - Export function registerTemporal(server, getPrincipal)
   - Handler calls callPlatformPrimitive('temporal', args, principal)

3. Register in `platform-mcp/src/server.ts`:
   - Add import + register call in Tier 3 section
   - Update header comment tool count

4. Write test: `platform-mcp/src/tools/temporal.test.ts`

5. Commit:
   ```bash
   git add platform-mcp/src/tools/temporal.ts platform-mcp/src/tools/temporal.test.ts platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S2 — temporal MCP wrapper + registration + test"
   ```

## Acceptance criteria
- File exists, registerTemporal in server.ts, tsc --noEmit exits 0
