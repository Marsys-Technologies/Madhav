---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S7: Port query_drekkana_drishti + query_remedies_prescribed to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S7
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S7
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S7 — Port drekkana drishti + prescribed remedies tools to portal

## 1. Context

- `query_drekkana_drishti` — returns Jaimini's Drekkana Drishti (aspect in the D3/Drekkana divisional). Different from Parashari rashi drishti — based on drekkana positions. Used in Jaimini analysis for sibling and co-born significations.
- `query_remedies_prescribed` — returns remedies that have been logged/prescribed for the native (from the Learning Layer or a dedicated remedies table). Returns: remedy_type, prescription, prescribed_date, compliance_status. Distinct from `query_remedial_mantras` (which is static classical guidance) — this returns the operationalized remedy log.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_drekkana_drishti.ts` (create)
- `platform/src/lib/retrieve/query_remedies_prescribed.ts` (create)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- MCP tool files (reference only)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_drekkana_drishti.ts`
2. `platform-mcp/src/tools/query_remedies_prescribed.ts`
3. `platform/src/lib/retrieve/index.ts`

## 4. Acceptance Criteria

- [ ] AC.1: `query_drekkana_drishti` in portal RETRIEVAL_TOOLS — returns D3 aspect relationships
- [ ] AC.2: `query_remedies_prescribed` in portal RETRIEVAL_TOOLS — returns remedy log rows
- [ ] AC.3: `query_remedies_prescribed` returns graceful empty result if remedies table doesn't exist in portal DB
- [ ] AC.4: Both registered in `index.ts` with exact name match to MCP
- [ ] AC.5: TypeScript compiles clean

## 5. Implementation Steps

### Step 1 — Read MCP implementations

```bash
cat platform-mcp/src/tools/query_drekkana_drishti.ts
cat platform-mcp/src/tools/query_remedies_prescribed.ts
```

Note the table names. For `query_remedies_prescribed`, check if a remedies table exists in portal DB migrations:
```bash
grep -r "remedies\|remedy" platform/supabase/migrations/ | head -10
```

### Step 2 — Port both tools

Follow UDA-1-S1 porting pattern.

For `query_drekkana_drishti`: likely queries divisional positions table with `division = 3` and computes aspect relationships. May require the same D3 position data that `divisional_query` accesses.

For `query_remedies_prescribed`: wrap in try/catch to handle missing table gracefully (same pattern as UDA-1-S4 for prediction log).

### Step 3 — Register and compile

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 4 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_drekkana_drishti.ts
git add platform/src/lib/retrieve/query_remedies_prescribed.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S7): port query_drekkana_drishti + query_remedies_prescribed to portal

Drekkana Drishti (Jaimini D3 aspects) and prescribed remedies log
now available in portal RETRIEVAL_TOOLS.
Remedies tool gracefully handles missing table.
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S7_v1_0.md*
