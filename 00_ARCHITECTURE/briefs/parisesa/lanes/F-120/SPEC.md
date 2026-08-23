# F-120 SPEC — ganita_dasha_periods_get: extend narration to finest running level + sandhi at all levels

---
lane: F-120
spec_version: 1.0
status: DRAFT
---

## 1. Root-Cause Statement

The narration builder in `get_dashas.ts` caps `byLevel` at `lvl <= 3` (line 464), unconditionally pins the "current" label to the level-3 (Pratyantardaśā) row, and checks `sandhi_flag` only at level 1 (Mahādaśā) — so when `all_levels=true` returns a level_n=4 Sūkṣmadaśā row as the actually-running period, the narration silently omits it, mislabels the Pratyantardaśā as "current", and never surfaces a finer-level sandhi warning.

## 2. Files to Change

| File | Change | Why |
|------|--------|-----|
| `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` | **(a)** Line 464: remove `lvl > 3` cap — collect all levels `1..N` present in `enrichedRows` into `byLevel`. **(b)** After building `byLevel`, compute `finestLevel = Math.max(...Object.keys(byLevel).map(Number))` and label only that row "current" in the narration chain. **(c)** Replace the hardcoded 3-row template (lines 492–495) with a dynamic chain built from a `LEVEL_NAMES` map `{1:'Mahadasha', 2:'Antardasha', 3:'Pratyantardasha', 4:'Sukshmadasha', 5:'Prana', 6:'Anu'}` iterating levels 1 through `finestLevel`. **(d)** Lines 511–515: check `sandhi_flag` for **every** level in the chain (not only level 1), appending one sandhi sentence per level whose flag is `true`, naming the level explicitly (e.g. "the Sukshmadasha is in its sandhi window"). **(e)** Extract the narration logic into an **exported** `buildDashaNarration(byLevel: Record<number, Record<string, unknown>>, birthDate: string \| null): string` function to enable unit testing without DB mocking. The outer handler passes the already-populated `byLevel` map into it unchanged. | All four diagnosis claims (b)–(d) and the sibling census (a) are caused by the hardcoded 3-level assumption in this single function; no other file is implicated. |

## 3. Exit Test

**File:** `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_dashas_narration_F120.test.ts`

**Command:** `npx jest --testPathPattern="get_dashas_narration_F120" --no-coverage`

**Fails on today's code** because `buildDashaNarration` is not exported (import fails) AND because the embedded logic filters level-4 out before the narration string is built — the test assertions for level-4 inclusion and sandhi would never pass even if the function were accessible.

**Passes after fix** because the extracted export is importable and all five assertions hold.

```typescript
import { buildDashaNarration } from '../get_dashas'

const BIRTH_DATE = '1984-06-10'

const allFourLevels: Record<number, Record<string, unknown>> = {
  1: { level_n: 1, lord_graha: 'Mercury', end_date: '2027-08-18', sandhi_flag: false,
       lord_natal_dignity_d1: null, lord_natal_house_d1: null, lord_natal_nakshatra: null },
  2: { level_n: 2, lord_graha: 'Saturn',  end_date: '2027-08-18', sandhi_flag: false,
       lord_natal_dignity_d1: 'exalted', lord_natal_house_d1: '7', lord_natal_nakshatra: 'Vishakha' },
  3: { level_n: 3, lord_graha: 'Moon',    end_date: '2026-09-17', sandhi_flag: false,
       lord_natal_dignity_d1: 'neutral', lord_natal_house_d1: '11', lord_natal_nakshatra: 'Purva Bhadrapada' },
  4: { level_n: 4, lord_graha: 'Mercury', end_date: '2026-08-25', sandhi_flag: true,
       lord_natal_dignity_d1: null, lord_natal_house_d1: null, lord_natal_nakshatra: null },
}

describe('F-120: buildDashaNarration', () => {
  it('includes level-4 Sukshmadasha in the narration chain', () => {
    const result = buildDashaNarration(allFourLevels, BIRTH_DATE)
    expect(result).toContain('Mercury Sukshmadasha')
  })

  it('labels only the finest level (level-4) as current', () => {
    const result = buildDashaNarration(allFourLevels, BIRTH_DATE)
    expect(result).toMatch(/Mercury Sukshma.*current/)
    expect(result).not.toMatch(/Moon Pratyantardasha.*current/)
  })

  it('surfaces sandhi_flag at level-4', () => {
    const result = buildDashaNarration(allFourLevels, BIRTH_DATE)
    expect(result).toMatch(/sandhi|junction/i)
  })

  it('does not emit sandhi sentence when all flags are false', () => {
    const noSandhi: Record<number, Record<string, unknown>> = Object.fromEntries(
      Object.entries(allFourLevels).map(([k, v]) => [k, { ...v, sandhi_flag: false }])
    )
    const result = buildDashaNarration(noSandhi, BIRTH_DATE)
    expect(result).not.toMatch(/sandhi|junction/i)
  })

  it('preserves correct 3-level behaviour when only levels 1-3 are present', () => {
    const threeLevels = { 1: allFourLevels[1], 2: allFourLevels[2], 3: allFourLevels[3] }
    const result = buildDashaNarration(threeLevels, BIRTH_DATE)
    expect(result).toContain('Moon Pratyantardasha')
    expect(result).toMatch(/Moon Pratyantardasha.*current/)
    expect(result).not.toContain('Sukshmadasha')
  })
})
```

## 4. Sibling Sites Covered

All five files from the diagnosis sibling census are accounted for. None are changed under this lane.

| File | Decision |
|------|---------|
| `platform-mcp/src/tools/kala_views/now.ts` | EXCLUDED — `max_level:2` cap is documented and intentionally MD/AD-scoped per file header (lines 24–28); any "not in a junction" concern at finer levels belongs to F-121 |
| `platform-mcp/src/tools/kala_views/ahead.ts` (lines 759, 777) | EXCLUDED — level∈{1,2} cap is documented, intentionally scoped for `period_echo` feature; no unqualified "current" claim |
| `platform-mcp/src/tools/kala_views/explain.ts` | EXCLUDED — filter at line 302 has no upper bound; all levels pass through (confirmed clean) |
| `platform-mcp/src/tools/kala_views/upaya.ts` | EXCLUDED — no dasha-level chain code present |
| `platform-mcp/src/tools/kala_views/dasha_sandhi.ts` | EXCLUDED — correctly passes `all_levels: true` throughout `buildBoundaries`; confirmed clean |

## 5. Recurrence Guard

The permanent recurrence guard is the exit-test file itself, specifically the test "includes level-4 Sukshmadasha in the narration chain": any future reintroduction of a hardcoded numeric upper-bound cap in `byLevel` population will cause that test to fail.

Additionally, add an ESLint annotation comment directly above the `byLevel` loop in `get_dashas.ts`:
```ts
// INVARIANT(F-120): no upper bound on lvl — collect all levels the caller supplies.
// If you add `lvl > N` here, the narration_F120 test suite will fail.
```
This makes the intent visible at the point of re-entry risk without requiring a project-wide lint rule change.

## 6. Dependencies, Rebuild, and Rollback

**Dependencies:** None. This lane is self-contained. F-121 (structurally analogous defect in `now.ts`) is a separate fix in a separate file and layer; no ordering dependency exists.

**Rebuild policy:** This is NOT a writer-layer fix. The change is pure narration string construction inside the L1 retrieval-layer handler (`platform/src/lib/retrieval/registry/layers/`). No `ga_writers/`, `bo_*` orchestrator writer, or `pipeline/orchestrator/writers/` file is touched. No DB rows are written or modified by this fix. The exit test suite is the verification artifact; no asset shadow-run or rebuild is required or warranted per ND-PARISESA-2.

**Rollback:** Revert the single TypeScript file. The change is pure string-building logic inside a try/catch block; reverting restores the previous 3-level narration exactly. No migration, no data residue, no downstream asset staleness.

## 7. Coverage Table

| Diagnosis claim | Spec coverage |
|---|---|
| (a) Payload correctly returns 4 levels with sandhi_flag=true at level_n=4 — CONFIRMED | Spec does not change payload behaviour; exit test supplies 4-level `byLevel` confirming the fix consumes what the payload already produces correctly |
| (b) Narration hardcoded to 3 levels (`lvl > 3` cap, line 464) — CONFIRMED | §2 change (a): remove cap; recurrence guard test "includes level-4" asserts fix |
| (c) "current" unconditionally on level-3 row (line 495) — CONFIRMED | §2 change (b)+(c): finest-level detection; test "labels only finest level as current" asserts fix |
| (d) sandhi_flag consulted only at level-1 (line 511), never at labeled "current" or finer — PARTIALLY CONFIRMED, net effect confirmed | §2 change (d): check `sandhi_flag` at every level in chain; test "surfaces sandhi_flag at level-4" asserts fix |
| Sibling census (0 undocumented siblings in S4 lease) — CONFIRMED | §4: all 5 sibling files enumerated, each excluded with stated reason |
