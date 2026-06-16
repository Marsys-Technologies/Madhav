---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S5: Quality Backport query_varshphal year range support → MCP"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S5
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S5
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S5 — Quality Backport: query_varshphal year range support → MCP

## 1. Context

The portal version of `query_varshaphala` (`platform/src/lib/retrieve/query_varshaphala.ts`)
supports a `year_start` / `year_end` range query — returning multiple annual charts at once.
The MCP version (`platform-mcp/src/tools/query_varshphal.ts`) accepts only a single `year`
parameter and returns exactly one annual chart.

This session adds `year_start` / `year_end` range support to the MCP tool so that callers
can request, for example, "Varshphal for years 2025 through 2030" in a single tool call.

**Source of truth (read-only):** `platform/src/lib/retrieve/query_varshaphala.ts`
**Target to modify:** `platform-mcp/src/tools/query_varshphal.ts`

---

## 2. Scope

**may_touch:**
- `platform-mcp/src/tools/query_varshphal.ts`

**must_not_touch:**
- `platform/src/lib/retrieve/query_varshaphala.ts` (source reference only)
- `platform-mcp/src/server.ts`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.Q5.1: `platform-mcp/src/tools/query_varshphal.ts` Zod schema includes `year_start?: number` and `year_end?: number`
- [ ] AC.Q5.2: When `year_start` and `year_end` are provided, the tool returns an array of annual charts for each year in the range (inclusive)
- [ ] AC.Q5.3: Range is capped at a maximum of 20 years to prevent runaway queries
- [ ] AC.Q5.4: Single `year` mode still works as before (backward compatible)
- [ ] AC.Q5.5: `cd platform-mcp && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q5.6: Commit message contains `UDA-Q-S5`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tools

```bash
cat platform/src/lib/retrieve/query_varshaphala.ts
cat platform-mcp/src/tools/query_varshphal.ts
```

Understand how the platform primitive is called and how the response is shaped.

### Step 2 — Add year_start / year_end to Zod schema

```typescript
year_start: z.number().int().min(1900).max(2100).optional().describe(
  'Start year for range query (inclusive). Use with year_end for multi-year retrieval.'
),
year_end: z.number().int().min(1900).max(2100).optional().describe(
  'End year for range query (inclusive, max 20 years from year_start).'
),
```

### Step 3 — Implement range logic

```typescript
if (args.year_start && args.year_end) {
  const start = args.year_start
  const end = Math.min(args.year_end, start + 19) // cap at 20 years
  const years = Array.from({ length: end - start + 1 }, (_, i) => start + i)
  const results = await Promise.all(
    years.map(y => callPlatformPrimitive('query_varshaphala', { chart_id, year: y }, principal))
  )
  return okResult({ mode: 'range', year_start: start, year_end: end, charts: results.map(r => r.result) })
}
// single year mode (existing path)
```

### Step 4 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform-mcp && npx tsc --noEmit
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform-mcp/src/tools/query_varshphal.ts
git commit -m "feat(UDA-Q-S5): add year_start/year_end range support to MCP query_varshphal

Backports portal year range capability. Max 20 years. Backward compatible.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "year_start\|year_end" platform-mcp/src/tools/query_varshphal.ts && echo 'GATE_UDA_Q_S5_RANGE: PASS'
git log --oneline -3 | grep -q 'UDA-Q-S5' && echo 'GATE_UDA_Q_S5_COMMIT: PASS'
```

All 2 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S5_v1_0.md*
