---
session_id: UDA-2-S9
phase: UDA-2
title: "UDA-2 integration — server.ts header + catalog.ts + TypeScript clean"
status: pending
---

# UDA-2-S9: Integration — server.ts header + catalog.ts + TypeScript clean

## Goal
After all 14 MCP wrappers are created (S1–S8), update the server.ts header comment,
update catalog.ts entries for the 14 new tools, and confirm the full platform-mcp
TypeScript compile is clean with zero errors.

## Steps

1. Update `platform-mcp/src/server.ts` header comment:
   - Change tool count from 26 to 40 (26 + 14 new UDA-2 tools)
   - Add a UDA-2 tier block comment listing the 14 new tools
   - Verify all 14 import lines and all 14 register calls are present

2. Update `platform-mcp/src/tools/catalog.ts`:
   - Add ToolCatalogEntry records for all 14 new tools
   - Each entry: { name, tier: 'surgical', description, surgical: true }
   - Use the DESCRIPTION constant from each tool's file

3. Run full TypeScript compile:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2/platform-mcp && npx tsc --noEmit
   ```
   Fix any errors before committing.

4. Commit:
   ```bash
   git add platform-mcp/src/server.ts platform-mcp/src/tools/catalog.ts
   git commit -m "feat(mcp): UDA-2-S9 — server.ts header 26→40 tools + catalog.ts 14 new entries"
   ```

## Acceptance criteria
- server.ts header says 40 tools (or correct count)
- catalog.ts has entries for all 14 new UDA-2 tools
- `npx tsc --noEmit` exits 0 with zero errors
