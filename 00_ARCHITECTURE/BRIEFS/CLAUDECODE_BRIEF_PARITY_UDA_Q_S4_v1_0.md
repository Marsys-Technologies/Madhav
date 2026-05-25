---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S4: lel_query chart_state + significance enum to MCP"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S4
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S4
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S4 — Upgrade MCP lel_query to portal depth

## 1. Context

The portal `platform/src/lib/retrieve/lel_query.ts` (230 lines) is richer than the MCP version:

**Portal advantages over MCP:**
1. Selects `chart_state` column (Swiss Ephemeris snapshot per event — planetary positions at event date)
2. `min_significance` filter accepts string enum: `'major' | 'moderate' | 'minor'` (not just a float)
3. Returns `significance` as enum string in each row

**MCP `platform-mcp/src/tools/lel_query.ts`** (90 lines):
- Omits `chart_state` from SELECT and output
- `min_significance: z.number().min(0).max(1)` — float-only, no enum variant

This session upgrades the MCP lel_query to match portal depth. Both versions continue to work; MCP gains the missing fields.

## 2. Scope

**may_touch:**
- `platform-mcp/src/tools/lel_query.ts`

**must_not_touch:**
- `platform/src/lib/retrieve/lel_query.ts` (reference only — the richer source)
- `platform-mcp/src/server.ts`
- `platform-mcp/src/tools/catalog.ts`
- All portal files
- Governance files

## 3. Files to read before starting

1. `platform/src/lib/retrieve/lel_query.ts` — source of truth (richer version)
2. `platform-mcp/src/tools/lel_query.ts` — current degraded MCP version

## 4. Acceptance Criteria

- [ ] AC.1: MCP `lel_query` SELECT query includes `chart_state` column
- [ ] AC.2: `chart_state` returned in each row of the MCP response (as JSON string or object)
- [ ] AC.3: `min_significance` accepts BOTH float (backward compat) AND string enum `'major' | 'moderate' | 'minor'`
- [ ] AC.4: When string enum provided, map to float threshold: `major` → `≥0.8`, `moderate` → `≥0.5`, `minor` → `≥0.0` (or port the exact mapping from portal)
- [ ] AC.5: `significance` field in returned rows is the string enum value (not raw float), matching portal output format
- [ ] AC.6: TypeScript compiles: `cd platform-mcp && npx tsc --noEmit` (or equivalent check)
- [ ] AC.7: Existing MCP float-based `min_significance` queries still return results (no regression)

## 5. Implementation Steps

### Step 1 — Read both files

```bash
cat platform/src/lib/retrieve/lel_query.ts
cat platform-mcp/src/tools/lel_query.ts
```

### Step 2 — Upgrade SELECT in MCP tool

In the SQL query string, add `chart_state` to the SELECT columns:
```sql
SELECT event_id, event_date, category, description, significance, 
       chart_state, source_section
FROM life_event_log
WHERE chart_id = $1
```

Check the actual table column name by referencing the portal tool's query.

### Step 3 — Upgrade min_significance schema

Replace the float-only schema with a union:
```typescript
min_significance: z.union([
  z.number().min(0).max(1),
  z.enum(['major', 'moderate', 'minor'])
]).optional().default(0),
```

Add significance-to-float mapping:
```typescript
const SIG_FLOOR: Record<string, number> = {
  major: 0.8, moderate: 0.5, minor: 0.0
};
function resolveMinSig(val: number | string): number {
  if (typeof val === 'string') return SIG_FLOOR[val] ?? 0;
  return val;
}
```

### Step 4 — Map significance float → enum in output

When constructing the returned rows, map the stored float back to enum:
```typescript
function sigToEnum(val: number): string {
  if (val >= 0.8) return 'major';
  if (val >= 0.5) return 'moderate';
  return 'minor';
}
```

### Step 5 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform-mcp
npx tsc --noEmit 2>&1 | head -40
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform-mcp/src/tools/lel_query.ts
git commit -m "feat(UDA-Q-S4): upgrade MCP lel_query to portal depth

- chart_state column added to SELECT and response
- min_significance accepts string enum (major/moderate/minor) + float
- significance returned as enum string in output rows
- Backward compat: float min_significance still works
- TypeScript clean

Quality gap closed: MCP lel_query now == portal depth."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S4_v1_0.md*
