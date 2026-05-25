---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S6: Quality Backport msr_sql filter enrichment → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S6
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S6
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S6 — Quality Backport: msr_sql filter enrichment → portal

## 1. Context

The MCP version of the MSR signal query (`platform-mcp/src/tools/query_signals.ts`) exposes
three filter parameters not present in the portal `msr_sql.ts`:

1. **`dasha_lord`** — filter signals whose `dasha_activations` JSON array contains a specific planet lord
2. **`valence`** — filter to `"positive" | "negative" | "mixed"` valence
3. **`temporal_activation`** — filter to `"natal" | "transit" | "dasha"` activation mode

The portal `msr_sql.ts` already has rich filtering (domain, confidence floor, LL.1 weights,
Pancha-MP clique dedup) but lacks these three MCP-added dimensions.

This session adds all three filter parameters to `platform/src/lib/retrieve/msr_sql.ts`.

**Source of truth (read-only):** `platform-mcp/src/tools/query_signals.ts`
**Target to modify:** `platform/src/lib/retrieve/msr_sql.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/msr_sql.ts`
- `platform/src/lib/retrieve/types.ts` (if `MsrSqlInput` is defined there)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- `platform/src/lib/retrieve/index.ts`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.Q6.1: `MsrSqlInput` (in `msr_sql.ts` or `types.ts`) includes `dasha_lord?: string`
- [ ] AC.Q6.2: `MsrSqlInput` includes `valence?: "positive" | "negative" | "mixed"`
- [ ] AC.Q6.3: `MsrSqlInput` includes `temporal_activation?: "natal" | "transit" | "dasha"`
- [ ] AC.Q6.4: Each new filter is actually applied in the SQL query or post-filter logic
- [ ] AC.Q6.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q6.6: Commit message contains `UDA-Q-S6`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tools

```bash
cat platform-mcp/src/tools/query_signals.ts
cat platform/src/lib/retrieve/msr_sql.ts
grep -n "MsrSqlInput" platform/src/lib/retrieve/types.ts
```

Identify where `MsrSqlInput` is defined and how the SQL query is constructed.

### Step 2 — Add three new fields to MsrSqlInput

Find the `MsrSqlInput` interface (either in `types.ts` or inline in `msr_sql.ts`) and add:

```typescript
/** Filter to signals where dasha_activations JSON array contains this planet lord. */
dasha_lord?: string
/** Filter to signals by valence. */
valence?: 'positive' | 'negative' | 'mixed'
/** Filter to signals by temporal activation mode. */
temporal_activation?: 'natal' | 'transit' | 'dasha'
```

### Step 3 — Apply dasha_lord filter

The `msr_signals` table has a `dasha_activations` column (likely JSONB array of planet names).
Add a WHERE clause condition:

```typescript
if (input.dasha_lord) {
  conditions.push(`dasha_activations @> $${params.length + 1}::jsonb`)
  params.push(JSON.stringify([input.dasha_lord]))
}
```

Or if post-filtering from rows:
```typescript
.filter(row => !input.dasha_lord ||
  (row.dasha_activations as string[] | null)?.includes(input.dasha_lord))
```

### Step 4 — Apply valence filter

```typescript
if (input.valence) {
  conditions.push(`valence = $${params.length + 1}`)
  params.push(input.valence)
}
```

### Step 5 — Apply temporal_activation filter

```typescript
if (input.temporal_activation) {
  conditions.push(`temporal_activation = $${params.length + 1}`)
  params.push(input.temporal_activation)
}
```

### Step 6 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/msr_sql.ts platform/src/lib/retrieve/types.ts
git commit -m "feat(UDA-Q-S6): add dasha_lord, valence, temporal_activation filters to portal msr_sql

Backports MCP query_signals filter dimensions. tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "dasha_lord" platform/src/lib/retrieve/msr_sql.ts && echo 'GATE_UDA_Q_S6_DASHA_LORD: PASS'
grep -q "valence\|temporal_activation" platform/src/lib/retrieve/msr_sql.ts && echo 'GATE_UDA_Q_S6_FILTERS: PASS'
git log --oneline -3 | grep -q 'UDA-Q-S6' && echo 'GATE_UDA_Q_S6_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S6_v1_0.md*
