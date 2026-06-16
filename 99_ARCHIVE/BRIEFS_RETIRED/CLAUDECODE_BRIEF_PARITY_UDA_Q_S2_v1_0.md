---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S2: Quality Backport query_ephemeris enhancements → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S2
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S2
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S2 — Quality Backport: query_ephemeris enhancements → portal

## 1. Context

The MCP version of `query_ephemeris` (`platform-mcp/src/tools/query_ephemeris.ts`) added several
enhancements not yet present in the portal version (`platform/src/lib/retrieve/query_ephemeris.ts`):

1. **`date_range` struct parameter** — a `{start, end}` object (alternative to separate `start_date`/`end_date`)
2. **`sample_step` parameter** — an integer N to return every Nth row (reduces token volume for wide ranges)
3. **`return_changes_only` parameter** — boolean; when true, only return rows where planet sign/dignity changes vs prior row
4. **1825-day span guard** — rejects ranges exceeding 5 years (1825 days) with a descriptive error

This session backports these four enhancements to the portal tool.

**Source of truth (read-only):** `platform-mcp/src/tools/query_ephemeris.ts`
**Target to modify:** `platform/src/lib/retrieve/query_ephemeris.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_ephemeris.ts`

**must_not_touch:**
- `platform-mcp/` (source reference only)
- `platform/src/lib/retrieve/index.ts`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.Q2.1: Portal `QueryEphemerisInput` includes `date_range?: { start: string; end: string }` OR the existing `start_date`/`end_date` params now accept the range struct pattern (either approach is acceptable as long as `date_range` appears in the file)
- [ ] AC.Q2.2: Portal tool accepts `sample_step?: number` parameter
- [ ] AC.Q2.3: Portal tool accepts `return_changes_only?: boolean` parameter
- [ ] AC.Q2.4: A 1825-day guard is present — the tool returns an error or empty result for ranges exceeding 1825 days
- [ ] AC.Q2.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q2.6: Commit message contains `UDA-Q-S2`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tools

```bash
cat platform-mcp/src/tools/query_ephemeris.ts
cat platform/src/lib/retrieve/query_ephemeris.ts
```

Understand the portal's existing `QueryEphemerisInput` interface shape and its DB query path.

### Step 2 — Add new parameters to QueryEphemerisInput

```typescript
/** Alternative range input: { start: 'YYYY-MM-DD', end: 'YYYY-MM-DD' }. */
date_range?: { start: string; end: string }
/** If set, return every Nth row (e.g. sample_step=7 returns weekly samples). */
sample_step?: number
/** If true, only return rows where sign or dignity changed since the prior row. */
return_changes_only?: boolean
```

### Step 3 — Merge date_range into start_date/end_date

Near the top of the execute function, normalize:
```typescript
const resolvedStart = input.date_range?.start ?? input.start_date
const resolvedEnd   = input.date_range?.end   ?? input.end_date
```

### Step 4 — Add 1825-day span guard

```typescript
if (resolvedStart && resolvedEnd) {
  const spanDays = (new Date(resolvedEnd).getTime() - new Date(resolvedStart).getTime()) / 86_400_000
  if (spanDays > 1825) {
    return { ok: false, error: `Date range exceeds 1825-day limit (requested ${Math.round(spanDays)} days). Narrow the range or use sample_step.` }
  }
}
```

### Step 5 — Implement sample_step

After fetching rows, if `sample_step` is set and > 1:
```typescript
const rows = rawRows.filter((_, i) => i % input.sample_step! === 0)
```

### Step 6 — Implement return_changes_only

After fetching (or sampling) rows, if `return_changes_only`:
```typescript
const filtered = rows.filter((row, i) => {
  if (i === 0) return true
  const prev = rows[i - 1]!
  return row.sign !== prev.sign || row.dignity !== prev.dignity
})
```

### Step 7 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 8 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_ephemeris.ts
git commit -m "feat(UDA-Q-S2): backport date_range, sample_step, return_changes_only, 1825-day guard to portal query_ephemeris

Matches MCP quality level. tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "date_range\|sample_step\|return_changes_only" platform/src/lib/retrieve/query_ephemeris.ts && echo 'GATE_UDA_Q_S2_PARAMS: PASS'
grep -q "1825\|span" platform/src/lib/retrieve/query_ephemeris.ts && echo 'GATE_UDA_Q_S2_GUARD: PASS'
git log --oneline -3 | grep -q 'UDA-Q-S2' && echo 'GATE_UDA_Q_S2_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S2_v1_0.md*
