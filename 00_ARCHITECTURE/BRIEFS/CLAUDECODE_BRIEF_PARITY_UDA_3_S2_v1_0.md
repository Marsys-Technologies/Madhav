---
session_id: UDA-3-S2
phase: UDA-3
title: "Interface normalization — schema parity audit"
status: pending
---

# UDA-3-S2: Schema Parity Audit

## Goal
For each of the 14 UDA-2 tools now on both channels, compare the portal input schema
against the MCP Zod schema. Document and fix critical mismatches.

## Steps

1. For each of the 14 UDA-2 tools, read:
   - Portal: `platform/src/lib/retrieve/<tool>.ts` — input interface
   - MCP: `platform-mcp/src/tools/<tool>.ts` — Zod schema

2. For each tool, identify:
   - Extra params in portal not exposed in MCP
   - Missing params in portal that MCP exposes
   - Type mismatches (string vs enum, optional vs required)
   - Default value conflicts

3. Append schema parity results to `00_ARCHITECTURE/INTERFACE_NORMALIZATION_REGISTER_v1_0.md`
   as a new §2 section: one row per tool with columns: tool | portal_params | mcp_params | gaps | severity

4. Fix HIGH severity gaps only (params that meaningfully change what data the tool can return).
   LOW severity gaps (minor default differences) — document only.

5. Commit fixes + updated register:
   ```bash
   git add 00_ARCHITECTURE/INTERFACE_NORMALIZATION_REGISTER_v1_0.md
   git add platform-mcp/src/tools/  # any updated wrapper files
   git commit -m "governance(uda3): UDA-3-S2 — schema parity audit + high-severity gap fixes"
   ```

## Acceptance criteria
- Register has §2 schema parity section with 14 tool rows
- `platform-mcp && npx tsc --noEmit` exits 0
