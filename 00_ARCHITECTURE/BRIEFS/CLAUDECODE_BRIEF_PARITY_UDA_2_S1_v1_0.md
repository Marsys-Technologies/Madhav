---
session_id: UDA-2-S1
phase: UDA-2
title: "MCP wrapper — msr_sql"
status: pending
---

# UDA-2-S1: MCP Wrapper — msr_sql

## Goal
Create a fully registered MCP tool wrapper for `msr_sql` so Channel C (MCP) can query
the MSR signals corpus directly.

## Context
- Portal source: `platform/src/lib/retrieve/msr_sql.ts` (TOOL_NAME = 'msr_sql')
- No MCP wrapper exists yet
- Pattern reference: `platform-mcp/src/tools/query_signals.ts`

## Steps

1. Read `platform/src/lib/retrieve/msr_sql.ts` to extract the input interface (domain,
   domains[], forward_looking, confidence_floor, chart_id, signal_type, limit, etc.).

2. Create `platform-mcp/src/tools/msr_sql.ts`:
   - Import: z, McpServer, callPlatformPrimitive, Principal, okResult, errorResult, buildToolDescription
   - Export MSR_SQL_DESCRIPTION using buildToolDescription
   - Define MsrSqlInputSchema (Zod) exposing: domain?, domains[]?, forward_looking?,
     confidence_floor? (0.0–1.0), chart_id? (UUID), signal_type?, limit? (1–500, default 50)
   - Export function registerMsrSql(server, getPrincipal)
   - Handler calls callPlatformPrimitive('msr_sql', args, principal)

3. Register in `platform-mcp/src/server.ts`:
   - Add: `import { registerMsrSql } from './tools/msr_sql.js'`
   - Add call in Tier 3 section: `registerMsrSql(server, getPrincipal)`
   - Update header comment: increment tool count by 1

4. Write `platform-mcp/src/tools/msr_sql.test.ts`:
   - Mock callPlatformPrimitive → {ok:true, result:{signals:[]}}
   - Assert registerMsrSql does not throw
   - Assert handler returns content array with type 'text'

5. Commit:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2
   git add platform-mcp/src/tools/msr_sql.ts platform-mcp/src/tools/msr_sql.test.ts platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S1 — msr_sql MCP wrapper + registration + test"
   ```

## Acceptance criteria
- `platform-mcp/src/tools/msr_sql.ts` exists and exports registerMsrSql
- `registerMsrSql` appears in server.ts
- `platform-mcp && npx tsc --noEmit` exits 0
