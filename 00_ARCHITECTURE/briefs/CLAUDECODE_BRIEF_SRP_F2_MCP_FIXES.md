---
canonical_id: CLAUDECODE_BRIEF_SRP_F2
version: 1.0
status: CURRENT
phase: SRP-F-2
session_type: fix
authored: 2026-05-25
worktree: MadhavSRP-F2
branch: fix/srp-f2-mcp-fixes
deploy_target: amjis-mcp
may_touch:
  - platform-mcp/src/tools/query_signals.ts
  - platform-mcp/src/tools/query_ephemeris.ts
  - platform-mcp/src/tools/lel_query.ts
must_not_touch:
  - platform-mcp/src/server.ts
  - platform/src/**
  - 00_ARCHITECTURE/**
---

# CLAUDECODE BRIEF: SRP-F-2 — MCP Sidecar Fixes

## Context

You are executing fixes for the MARSYS-JIS System Repair Plan (SRP). This session addresses
three bugs in the **MCP sidecar** (`amjis-mcp`, service `platform-mcp/`). All bugs are
param-translation bugs: the MCP tool sends a value in the wrong type or vocabulary, causing
the platform retrieval layer to silently ignore the filter.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-F2`
Branch: `fix/srp-f2-mcp-fixes`

**Before starting**: read the relevant sections of each tool file. Do not edit blindly —
understand the full param-building block first.

---

## Fix 1 — FIX-3: Fix valence vocabulary in query_signals.ts

**File**: `platform-mcp/src/tools/query_signals.ts`

**Root cause**: The MCP schema defines:
```typescript
valence: z.enum(['positive', 'negative', 'neutral'])
```
But the platform DB column `msr_signals.valence` stores:
`'benefic' | 'malefic' | 'context-dependent'`

The SQL is: `AND ($8::text[] IS NULL OR valence = ANY($8::text[]))`

When `valence: "positive"` is sent, the SQL `= ANY('{positive}')` finds zero rows because
no row has `valence = 'positive'`. The filter silently returns empty.

**Vocabulary mapping**:
| MCP (wrong) | DB (correct) |
|-------------|--------------|
| `positive`  | `benefic`    |
| `negative`  | `malefic`    |
| `neutral`   | `context-dependent` |

**Fix option A (preferred)**: Change the Zod enum to use the correct DB vocabulary directly.
```typescript
valence: z.enum(['benefic', 'malefic', 'context-dependent']).optional()
  .describe('Filter signals by valence: benefic (helpful), malefic (challenging), or context-dependent')
```
This is the cleanest fix. MCP callers get the correct vocabulary in the schema.

**Fix option B** (if you determine changing the schema would break existing callers in
`platform-mcp/src/server.ts` registered tool descriptions): Map the old enum to new values
in the translation block:
```typescript
const VALENCE_MAP: Record<string, string> = {
  positive: 'benefic',
  negative: 'malefic',
  neutral: 'context-dependent',
}
// In the callPlatformPrimitive args block:
...(args.valence !== undefined ? { valence: [VALENCE_MAP[args.valence] ?? args.valence] } : {})
```

**Recommendation**: Use Fix A. The schema vocabulary was simply wrong; there are no
backward-compat concerns at the MCP API layer (callers are Claude agents, not external
API consumers with SLA).

**Verify**: After the fix, grep the file and confirm the `z.enum` and the value sent to
`callPlatformPrimitive` both use `'benefic'/'malefic'/'context-dependent'`.

---

## Fix 2 — FIX-4: Fix sample_step type mismatch in query_ephemeris.ts

**File**: `platform-mcp/src/tools/query_ephemeris.ts`

**Root cause**: The MCP schema defines:
```typescript
sample_step: z.enum(['1d', '7d', '30d'])
```
And the tool sends:
```typescript
sample_step: args.sample_step ?? '1d'
```
So it sends the string `"7d"` to the platform.

The platform's `QueryEphemerisInput` type at `platform/src/lib/retrieve/query_ephemeris.ts`
defines `sample_step?: number`. The downsampling check at lines 218-220 is:
```typescript
if (input.sample_step !== undefined && input.sample_step > 1) {
  rows = rows.filter((_, i) => i % input.sample_step! === 0)
}
```
`"7d" > 1` evaluates to `false` in JavaScript (NaN comparison). Filter is silently skipped.
`"7d" % N` is `NaN`. The rows array is never downsampled.

**Fix**: Convert the string enum to the appropriate integer number of days before calling
the platform:

```typescript
const SAMPLE_STEP_DAYS: Record<string, number> = {
  '1d': 1,
  '7d': 7,
  '30d': 30,
}

// In the callPlatformPrimitive args block, replace:
//   sample_step: args.sample_step ?? '1d'
// with:
sample_step: SAMPLE_STEP_DAYS[args.sample_step ?? '1d'] ?? 1
```

This sends `7` (number) when the caller specifies `"7d"`. The platform check
`7 > 1` is `true`, and `i % 7 === 0` correctly keeps every 7th row.

**Also update**: The tool description / schema description to clarify:
- `'1d'` = daily (all rows), `'7d'` = weekly, `'30d'` = monthly

**Verify**:
```typescript
// Inline assertion (add to test file in T-2 brief):
const SAMPLE_STEP_DAYS = { '1d': 1, '7d': 7, '30d': 30 }
console.assert(SAMPLE_STEP_DAYS['7d'] === 7)
console.assert(typeof SAMPLE_STEP_DAYS['7d'] === 'number')
```

---

## Fix 3 — FIX-5: Fix significance field name in lel_query.ts

**File**: `platform-mcp/src/tools/lel_query.ts`

**Root cause**: The MCP tool maps `significance_tier` → a float and sends:
```typescript
{ min_significance: resolvedMinSignificance }  // e.g., 0.8 for tier_1
```
to `callPlatformPrimitive`.

The platform's `platform/src/lib/retrieve/lel_query.ts` reads:
```typescript
significance: params?.significance as LelQueryInput['significance']
```
`LelQueryInput['significance']` is a **string enum** (e.g., `'tier_1' | 'tier_2' | 'tier_3'`),
not a float. The SQL uses:
```typescript
if (p.significance) { conditions.push(`significance = $${idx}`) }
```
(exact string match, not numeric comparison).

There is a **field name mismatch** (`min_significance` vs `significance`) AND a
**type mismatch** (float vs string enum). The filter never fires.

**Fix — two options**:

**Option A (fix the MCP side — preferred)**: Instead of sending a float, send the string tier
directly. The platform expects the tier string.

```typescript
// In lel_query.ts MCP tool — replace the significance block:
// OLD:
//   if (args.significance_tier) {
//     resolvedMinSignificance = SIGNIFICANCE_TIER_MAP[args.significance_tier]  // → float
//   }
//   // ...later:
//   ...(resolvedMinSignificance ? { min_significance: resolvedMinSignificance } : {})

// NEW:
...(args.significance_tier !== undefined ? { significance: args.significance_tier } : {})
```

This sends `{ significance: "tier_1" }` (string), which the platform reads correctly from
`params?.significance`.

**Option B (fix both sides)**: Keep the float approach on the MCP side, but add a
`min_significance` handling path in the platform retrieval layer (`lel_query.ts`):
```typescript
// In platform/src/lib/retrieve/lel_query.ts:
const minSig = (params as Record<string, unknown>)?.min_significance as number | undefined
if (minSig !== undefined) {
  conditions.push(`significance_score >= $${idx}`)
  values.push(minSig)
  idx++
}
```
This requires touching `platform/src/lib/retrieve/lel_query.ts` which is a different file.

**Recommendation**: Use Option A. It's one file, one line change, and doesn't require a
schema migration. The `significance_tier` → string mapping is already intuitive.

**Verify**:
After the fix, the `callPlatformPrimitive` call for `significance_tier: "tier_1"` must
include `{ significance: "tier_1" }` in the params block. Grep the file to confirm
no `min_significance` key remains in the outbound params.

---

## Acceptance Criteria

- [ ] `query_signals` with `valence: "benefic"` returns non-empty results (verify via unit
      test mocking the DB response or by tracing the param translation).
- [ ] `query_signals` Zod schema uses `'benefic'/'malefic'/'context-dependent'` vocabulary.
- [ ] `query_ephemeris` with `sample_step: "7d"` sends `sample_step: 7` (number) to platform.
- [ ] `lel_query` with `significance_tier: "tier_1"` sends `{ significance: "tier_1" }` to
      `callPlatformPrimitive` (not `{ min_significance: 0.8 }`).
- [ ] No `min_significance` key in `lel_query` outbound params.
- [ ] `npx vitest run` inside `platform-mcp/` shows 0 failures, 0 regressions.
- [ ] PR opened against `main` from `fix/srp-f2-mcp-fixes`.

## Session Close

Commit message format:
```
fix(srp-f2): MCP sidecar fixes — valence enum, sample_step type, lel significance field

FIX-3: query_signals.ts — valence enum vocabulary: positive/negative/neutral → benefic/malefic/context-dependent
FIX-4: query_ephemeris.ts — sample_step string enum converted to number of days before platform call
FIX-5: lel_query.ts — significance: send tier string instead of min_significance float
```

After commit, open PR and **stop** — do not merge. Human gates the merge and `amjis-mcp` deploy.
