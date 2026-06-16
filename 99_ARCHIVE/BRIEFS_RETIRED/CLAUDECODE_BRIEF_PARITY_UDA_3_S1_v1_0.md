---
session_id: UDA-3-S1
phase: UDA-3
title: "Interface normalization — naming audit + register"
status: pending
---

# UDA-3-S1: Interface Normalization — Naming Audit + Register

## Goal
Produce the INTERFACE_NORMALIZATION_REGISTER document listing every canonical tool name pair
(portal name → MCP name) and fix the most critical naming mismatches.

## Steps

1. Enumerate all portal RETRIEVAL_TOOLS from `platform/src/lib/retrieve/index.ts` (read the
   RETRIEVAL_TOOLS array — each tool has a `name` field).

2. Enumerate all MCP tools from `platform-mcp/src/server.ts` (read import list).

3. For each tool that exists on both channels, compare names. Document mismatches.
   Known mismatches to resolve:
   - Portal: `chart_facts_query` → MCP: `query_chart_facts` → canonical: `query_chart_facts`
   - Portal: `query_varshaphala` → MCP: `query_varshphal` → canonical: `query_varshphal`
   - Portal: `classical_text_search_tool` → MCP: `read_classical_text` → declared asymmetry (search vs read)

4. Write `00_ARCHITECTURE/INTERFACE_NORMALIZATION_REGISTER_v1_0.md`:
   ```markdown
   # Interface Normalization Register v1.0
   For each shared tool: canonical_name | portal_name | mcp_name | status | asymmetry_note
   ```

5. Fix the two hard renames in portal retrieve/index.ts if they differ from canonical:
   - If portal key is `chart_facts_query`, add alias key `query_chart_facts` pointing to same tool
   - If portal key is `query_varshaphala`, add alias key `query_varshphal` pointing to same tool
   Do NOT rename the file or function — only add the alias key in the RETRIEVAL_TOOLS map.

6. Commit:
   ```bash
   git add 00_ARCHITECTURE/INTERFACE_NORMALIZATION_REGISTER_v1_0.md platform/src/lib/retrieve/index.ts
   git commit -m "governance(uda3): UDA-3-S1 — interface normalization register + portal alias keys"
   ```

## Acceptance criteria
- INTERFACE_NORMALIZATION_REGISTER_v1_0.md exists with ≥10 tool entries
- `platform && npx tsc --noEmit` exits 0
