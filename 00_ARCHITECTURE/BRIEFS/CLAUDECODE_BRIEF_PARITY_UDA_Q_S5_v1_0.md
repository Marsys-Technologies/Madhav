---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S5: query_varshphal year range to MCP"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S5
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S5
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S5 — Add year range support to MCP query_varshphal

## 1. Context

The portal `platform/src/lib/retrieve/query_varshaphala.ts` (204 lines) supports range queries:
- `year`: single year
- `year_start` + `year_end`: range (returns all years from start to end inclusive)

The MCP `platform-mcp/src/tools/query_varshphal.ts` (84 lines, from TR) only supports:
- `year: z.number().int().min(1900).max(2100)` — single year only

This session adds `year_start`/`year_end` range support to the MCP tool, matching portal capability.

## 2. Scope

**may_touch:**
- `platform-mcp/src/tools/query_varshphal.ts`

**must_not_touch:**
- `platform/src/lib/retrieve/query_varshaphala.ts` (reference only)
- `platform-mcp/src/server.ts`
- `platform-mcp/src/tools/catalog.ts`
- All portal files
- Governance files

## 3. Files to read before starting

1. `platform/src/lib/retrieve/query_varshaphala.ts` — source of truth for range support
2. `platform-mcp/src/tools/query_varshphal.ts` — current MCP version

## 4. Acceptance Criteria

- [ ] AC.1: `year_start: z.number().int().min(1900).max(2100).optional()` added to input schema
- [ ] AC.2: `year_end: z.number().int().min(1900).max(2100).optional()` added to input schema
- [ ] AC.3: When `year_start` and `year_end` provided (without `year`), query returns all varshaphal records from `year_start` to `year_end` inclusive
- [ ] AC.4: When only `year` provided, single-year behavior unchanged (backward compat)
- [ ] AC.5: `year_end` must be >= `year_start`; return `{ error: "year_end must be >= year_start" }` if not
- [ ] AC.6: Range span capped at 10 years max to prevent oversized results
- [ ] AC.7: TypeScript compiles: `cd platform-mcp && npx tsc --noEmit`

## 5. Implementation Steps

### Step 1 — Read both files

```bash
cat platform/src/lib/retrieve/query_varshaphala.ts
cat platform-mcp/src/tools/query_varshphal.ts
```

### Step 2 — Update schema

```typescript
const inputSchema = z.object({
  chart_id: z.string().uuid(),
  year: z.number().int().min(1900).max(2100).optional(),
  year_start: z.number().int().min(1900).max(2100).optional(),
  year_end: z.number().int().min(1900).max(2100).optional(),
  // preserve any existing params
}).refine(d => d.year || (d.year_start && d.year_end), {
  message: 'Provide either year or both year_start and year_end'
});
```

### Step 3 — Add range validation

```typescript
if (year_start && year_end) {
  if (year_end < year_start) return { error: 'year_end must be >= year_start' };
  if (year_end - year_start > 10) return { error: 'Range exceeds 10-year maximum' };
}
```

### Step 4 — Build range query

Port from portal tool. If `year_start`/`year_end` provided:
```sql
SELECT * FROM varshaphal
WHERE chart_id = $1 AND year >= $2 AND year <= $3
ORDER BY year ASC
```

### Step 5 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform-mcp && npx tsc --noEmit 2>&1 | head -40
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform-mcp/src/tools/query_varshphal.ts
git commit -m "feat(UDA-Q-S5): add year range support to MCP query_varshphal

- year_start + year_end params for multi-year queries
- Range capped at 10 years; validated year_end >= year_start
- Single-year 'year' param behavior unchanged
- TypeScript clean

Quality gap closed: MCP query_varshphal now == portal range capability."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S5_v1_0.md*
