---
lane: F-50
tier: TIER3-EXPERIENCE
stream: S4
stage: S (SPEC)
status: DRAFT
writer_asset: none
data_delta: none
---

# F-50 — Spec: bodha_remedies_get graha-filtered lead sentence suppresses chart-wide rank context

## 1. Defect Summary

`bodha_remedies_get` called with `graha='Saturn'` returns
`narration.lead: "Your Bodha remedy layer flags Saturn as your #1 remedy-priority target —
resonance_score 0.094, priority class low."` The SQL filter at line 346
(`LOWER(graha) = LOWER($3)`) reduces `orderedResRows` to exactly one row; `topRow =
orderedResRows[0]` is trivially rank-1 of that 1-row array. The template (lines 447–460)
has no branch for this filtered-singleton case, so the `#1` superlative is emitted
identically to how it would be for a genuine chart-wide #1. Saturn is actually rank 8 of 9
chart-wide (`weakest_rank_in_chart: 8`, `remedy_priority_class: "low"` — both already
present in the row at line 359, surfaced in `resonance_ranked[0]` at line 473, but never
read into `leadSentence`).

The same defect exists in the `leverageActive` branch (line 452): `"Your highest-leverage
remedy target is Saturn"` — identical `orderedResRows[0]` construct, same filter-blind template.

## 2. Root Cause (file:line, verified against main-ro)

File: `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`

- **Line 327**: `const graha = args['graha'] as string | undefined` — caller-supplied filter param.
- **Line 346**: `if (graha) { resConds.push(\`LOWER(graha) = LOWER($${rp++})\`); resParams.push(graha) }` — collapses resonance rows to 1 when graha param is supplied.
- **Line 359**: `remedy_priority_class, is_yoga_karaka_flag, weakest_rank_in_chart,` — `weakest_rank_in_chart` is already SELECTed and present in `topRow`.
- **Lines 447–460** (`// ── U-a verdict-first lead`): Both branches use `orderedResRows[0]` with no guard for filter-singleton:
  - **Line 452–456** (leverage branch): `"Your highest-leverage remedy target is ${graha}"` — unconditional superlative.
  - **Line 457–459** (non-leverage branch): `"as your #1 remedy-priority target"` — unconditional superlative.

## 3. Fix Prescription

In `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`, lines 450–460:

Introduce a filter-active guard using the in-scope `graha` variable (line 327). When `graha`
is truthy and `orderedResRows.length === 1`, the result is a filter-singleton — not a
chart-wide ranking winner. Replace superlative framing with context-honest wording that
cites `weakest_rank_in_chart` and `remedy_priority_class` from the row.

**Replace lines 450–460 with:**

```typescript
      const leadSentence = topRow
        ? (graha
            ? `${String(topRow['graha'])}'s remedy priority is ${String(topRow['remedy_priority_class'])}` +
              (topRow['weakest_rank_in_chart'] != null
                ? ` (rank ${String(topRow['weakest_rank_in_chart'])} of 9 chart-wide)` : '') +
              ` — resonance_score ${Number(topRow['resonance_score']).toFixed(3)}.`
            : (leverageActive
                ? `Your highest-leverage remedy target is ${String(topRow['graha'])}` +
                  ` — leverage_index ${Number(levFor(topRow)?.leverage_index ?? 0).toFixed(3)}` +
                  ` (domain '${String(levFor(topRow)?.leverage_domain ?? leverageInfo?.resolvedDomain ?? 'general')}'),` +
                  ` resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
                  (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.')
                : `Your Bodha remedy layer flags ${String(topRow['graha'])} as your #1 remedy-priority target` +
                  ` — resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
                  (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.')))
        : `No resonance rows found for chart ${chart_id}${graha ? ` (graha filter: ${graha})` : ''}.`
```

**Logic**: When `graha` is truthy (filter active), emit a factual per-graha sentence using
`weakest_rank_in_chart` and `remedy_priority_class` regardless of leverage mode — both fields
are already in `topRow`. When `graha` is falsy (unfiltered call), existing behaviour is
preserved exactly (leverage or standard superlative path).

**Note on `domain` filter**: `domain` can also reduce the result set but does not force
singleton (domain matches multiple grahas typically); diagnosis reproduced and scoped this
defect to the `graha` filter only. `domain`-only calls are out of scope for this lane.

## 4. No-Change Scope

- `resonance_ranked` array (lines 463–478): unchanged — already carries `weakest_rank_in_chart` per row.
- All SQL queries (lines 336–417): unchanged.
- `bo_upaya.py` writer: unchanged — defect is serving-layer TypeScript only.
- No DB writes; no asset rebuild.

## 5. Sibling Coverage

Diagnosis sibling census (DIAGNOSIS.md lines 127–149, verified against main-ro):

- Literal `"as your #1"` / `"your #1"` grep: **one hit only** — `query_remedies.ts:457`. No other file.
- `leadSentence` / narration-lead construction repo-wide: exactly two files — `query_remedies.ts`
  (this fix) and `L1_ganita/get_dashas.ts:492`. The latter emits a factual current-state
  sentence (`"You are in X Mahadasha → Y Antardasha"`) — no caller filter reduces a ranked
  set to a singleton there; not susceptible to this defect class.
- No other L0–L5 layer constructs a superlative narration lead from `rows[0]` of a caller-filtered set.

Both branches of the `topRow` construct within `query_remedies.ts` (leverage line 452, non-leverage
line 457) are addressed by this spec's single edit.

## 6. Exit Test

**Reproduce command** (fails on current code; passes after fix):

```typescript
// platform/src/lib/retrieval/registry/layers/L2_bodha/__tests__/query_remedies_graha_filter_lead.test.ts
const result = await queryRemedies({
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  graha: 'Saturn'
})
const lead: string = result.content.narration.lead
// Must NOT use superlative #1 framing when graha filter is active
expect(lead).not.toMatch(/#1/)
// Must surface priority class context
expect(lead).toMatch(/low/i)
// Must cite chart-wide rank
expect(lead).toMatch(/rank|chart-wide|8 of 9/i)
```

**Current failure**: `lead` is `"Your Bodha remedy layer flags Saturn as your #1 remedy-priority
target — resonance_score 0.094, priority class low."` — contains `#1` → first assertion fails.

**After fix**: `lead` becomes `"Saturn's remedy priority is low (rank 8 of 9 chart-wide) —
resonance_score 0.094."` → all three assertions pass.

**Unfiltered call must be unaffected** (regression guard):

```typescript
const unfiltered = await queryRemedies({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' })
expect(unfiltered.content.narration.lead).toMatch(/#1/)
expect(unfiltered.content.narration.lead).toMatch(/Venus/)
```

## 7. Recurrence Guard

The `graha` guard is colocated with the existing `graha` variable at line 327. A regression
requires removing the guard branch while keeping the `graha` param active — caught immediately
by the exit test. No schema change, no config flag, no new abstraction.

## 8. Data Delta / Rebuild

`writer_asset: none` — no Python sidecar writer involved.
`data_delta: none` — `narration.lead` is computed at serve-time from existing
`bodha_rm_resonances` rows. No DB writes. No asset rebuild required or scheduled.
Shadow run not applicable (serving-layer TypeScript, not a writer-layer Python sidecar).
