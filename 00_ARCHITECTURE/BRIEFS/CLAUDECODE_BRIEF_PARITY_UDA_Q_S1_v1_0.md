---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S1: Quality Backport query_dasha_periods PD/SD → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S1
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S1 — Quality Backport: query_dasha_periods PD/SD → portal

## 1. Context

The MCP version of `query_dasha_periods` (at `platform-mcp/src/tools/query_dasha_periods.ts`) has
a `level` parameter supporting `"pratyantar"` and `"sookshma"` sub-period levels (PD and SD),
computed via Vimshottari planet ratios. The portal version at
`platform/src/lib/retrieve/query_dasha_periods.ts` only supports level `"M" | "A" | "P" | "all"`
and does not compute sub-periods dynamically.

This session backports the MCP's PD/SD sub-period computation into the portal tool.

**Source of truth (read-only):** `platform-mcp/src/tools/query_dasha_periods.ts`
**Target to modify:** `platform/src/lib/retrieve/query_dasha_periods.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_dasha_periods.ts`

**must_not_touch:**
- `platform-mcp/` (source reference only — do not modify)
- `platform/src/lib/retrieve/index.ts` (no registration changes needed)
- Any governance files (`CLAUDE.md`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`)

---

## 3. Acceptance Criteria

- [ ] AC.Q1.1: Portal `query_dasha_periods.ts` accepts a `level` parameter supporting at minimum `"pratyantar"` and `"sookshma"` values
- [ ] AC.Q1.2: When `level="pratyantar"`, each MD/AD row in the response carries a `sub_periods` array of PD rows
- [ ] AC.Q1.3: When `level="sookshma"`, each MD/AD/PD row carries a `sub_periods` array of SD rows
- [ ] AC.Q1.4: Sub-period computation uses the same Vimshottari planet ratios as the MCP version (`VIMSHOTTARI_YEARS` map from the MCP tool)
- [ ] AC.Q1.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q1.6: Commit message contains `UDA-Q-S1`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tool files

```bash
cat platform-mcp/src/tools/query_dasha_periods.ts
cat platform/src/lib/retrieve/query_dasha_periods.ts
```

Understand:
- The MCP's `VIMSHOTTARI_YEARS` constant and `VIMSHOTTARI_TOTAL_YEARS = 120`
- The MCP's `computeSubPeriods` logic (or equivalent inline logic)
- The portal's existing `QueryDashaPeriodsInput` interface and response shape

### Step 2 — Add Vimshottari constants

In `platform/src/lib/retrieve/query_dasha_periods.ts`, add (or verify already present):

```typescript
const VIMSHOTTARI_TOTAL_YEARS = 120
const VIMSHOTTARI_YEARS: Record<string, number> = {
  Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16,
  Saturn: 19, Mercury: 17, Ketu: 7, Venus: 20,
}
const VIMSHOTTARI_SEQUENCE = ['Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury','Ketu','Venus']
```

### Step 3 — Extend QueryDashaPeriodsInput

Add `"pratyantar" | "sookshma"` to the existing `DashaLevel` type, or add a new field:

```typescript
/** Sub-period depth: 'pratyantar' adds PD sub_periods to each AD; 'sookshma' adds SD sub_periods to each PD. */
sub_level?: 'pratyantar' | 'sookshma'
```

(If the existing `level` field already exists and uses `'P'` semantics, add `sub_level` as a separate parameter to avoid breaking callers.)

### Step 4 — Implement sub-period computation

Port the sub-period computation from the MCP tool. Key logic:

```typescript
function computeSubPeriods(
  parentLord: string,
  parentStart: Date,
  parentEnd: Date,
): Array<{ lord: string; start_date: string; end_date: string; duration_days: number }> {
  const parentMs = parentEnd.getTime() - parentStart.getTime()
  const sequence = buildSequenceFrom(parentLord) // rotate VIMSHOTTARI_SEQUENCE to start at parentLord
  const subs = []
  let cursor = parentStart.getTime()
  for (const lord of sequence) {
    const ratio = VIMSHOTTARI_YEARS[lord]! / VIMSHOTTARI_TOTAL_YEARS
    const durationMs = parentMs * ratio
    const subStart = new Date(cursor)
    const subEnd = new Date(cursor + durationMs)
    subs.push({
      lord,
      start_date: subStart.toISOString().slice(0, 10),
      end_date: subEnd.toISOString().slice(0, 10),
      duration_days: Math.round(durationMs / 86_400_000),
    })
    cursor += durationMs
  }
  return subs
}
```

### Step 5 — Wire sub_periods into response

After the portal tool retrieves its normal rows, if `sub_level === 'pratyantar'`, decorate each row with `sub_periods` by calling `computeSubPeriods(row.ad_lord, row.start_date, row.end_date)`.

If `sub_level === 'sookshma'`, first compute PD sub_periods for each AD row, then for each PD also compute SD sub_periods.

### Step 6 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

Fix any errors before committing.

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_dasha_periods.ts
git commit -m "feat(UDA-Q-S1): backport PD/SD sub-period levels to portal query_dasha_periods

Adds sub_level param ('pratyantar'|'sookshma') to portal tool, matching
MCP quality level. Sub-periods computed via Vimshottari planet ratios.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
# Gate 1: pratyantar in file
grep -q "pratyantar" platform/src/lib/retrieve/query_dasha_periods.ts && echo 'GATE_UDA_Q_S1_PRATYANTAR: PASS'

# Gate 2: sookshma in file
grep -q "sookshma" platform/src/lib/retrieve/query_dasha_periods.ts && echo 'GATE_UDA_Q_S1_SOOKSHMA: PASS'

# Gate 3: sub_periods computation present
grep -q "computePratyantar\|sub_periods" platform/src/lib/retrieve/query_dasha_periods.ts && echo 'GATE_UDA_Q_S1_SUBPERIODS: PASS'

# Gate 4: commit present
git log --oneline -3 | grep -q 'UDA-Q-S1' && echo 'GATE_UDA_Q_S1_COMMIT: PASS'
```

All 4 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S1_v1_0.md*
