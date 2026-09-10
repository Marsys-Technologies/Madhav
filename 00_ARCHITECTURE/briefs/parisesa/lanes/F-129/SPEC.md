---
finding_id: F-129
tier: TIER2-HONESTY
lane_status: SPEC
spec_author: spec_writer
---

# F-129 SPEC — synth_chart_brief_get top_discoveries served as raw signal descriptors

## 1. Root-Cause Statement

`register_p1_synthesis.ts:816` aliases `bodha_discoveries.surface_reading` (an internal epistemic-pair diagnostic label, not a narrative sentence) to `statement` in the `synth_chart_brief_get` query, discarding the richer `hypothesis_text`, `depth_reading`, and `why_an_acharya_misses_it` fields that `bo_anveshana.py` already writes to every row in the same table.

## 2. Files to Change

### `platform-mcp/src/tools/register_p1_synthesis.ts` (lines 815–822 only)

**What changes**: Replace the `discResult` SELECT list. Remove `surface_reading AS statement`; add `hypothesis_text`, `depth_reading`, `why_an_acharya_misses_it`, `discovery_class`, `discovery_subsystem`. Expose each field under its honest column name — no `AS statement` alias. `top_discoveries: discResult.rows` at line 868 requires no change once the upstream SELECT is fixed.

**Diff sketch**:
```sql
-- BEFORE (line 816):
SELECT discovery_id, affected_domains_array AS domains, surface_reading AS statement,
       composite_discovery_rank AS salience_score

-- AFTER:
SELECT discovery_id, discovery_class, discovery_subsystem,
       affected_domains_array AS domains,
       hypothesis_text, depth_reading, why_an_acharya_misses_it,
       surface_reading,
       composite_discovery_rank AS salience_score
```

**Why**: `surface_reading` is the L2 Bodha writer's surface/depth epistemic-pair label (`bo_anveshana.py:499,575,638`) — never designed as public prose. `hypothesis_text` is domain-qualified and chart-specific (e.g. `"Pattern {signal_type_id} in {domains} has outsized structural consequence despite low surface visibility"`) and is already in the same DB row. The fix mirrors the pattern already used by the sibling call path `query_discoveries.ts:110–114`, which selects all these fields correctly under honest names.

**No other file changes required.** The writer (`bo_anveshana.py`) already writes correct data; the schema already has the columns; no migration needed.

## 3. Exit Test

**File**: `platform-mcp/src/tools/__tests__/F129.exit.spec.ts`

**Command** (FAILS on today's code, PASSES after fix):
```
npx jest --testPathPattern=F129\.exit --no-coverage
```

**FAILS today** because `surface_reading AS statement` is present at line 816 and `hypothesis_text` is absent from the discResult SELECT.

**PASSES after fix** because neither condition holds.

**Test body**:
```ts
import * as fs from 'fs'
import * as path from 'path'

const SRC = path.resolve(__dirname, '../register_p1_synthesis.ts')

describe('F-129 exit — top_discoveries query fields', () => {
  let src: string
  beforeAll(() => { src = fs.readFileSync(SRC, 'utf-8') })

  it('does NOT alias surface_reading as statement', () => {
    expect(src).not.toMatch(/surface_reading\s+AS\s+statement/i)
  })

  it('selects hypothesis_text in the discResult query block', () => {
    // Anchor: find the const discLimit block (F-129's query, not F-135's)
    const discBlock = src.match(/const discLimit[\s\S]{0,1000}LIMIT \$2[\s\S]{0,60}`, \[chart_id/)
    expect(discBlock).not.toBeNull()
    expect(discBlock![0]).toMatch(/hypothesis_text/)
  })
})

describe('F-129 recurrence guard', () => {
  it('no *_reading column aliased AS statement anywhere in this file', () => {
    // Fails closed on any future query that repeats the same mislabeling pattern
    expect(src).not.toMatch(/\b\w+_reading\s+AS\s+statement\b/i)
  })
})
```

## 4. Sibling Sites Covered

Diagnosis census found **0 additional defect instances**. Both checked siblings are confirmed non-defective:

| Sibling | File | Verdict |
|---------|------|---------|
| `bodha_discoveries_get` → `query_discoveries.ts:110–114` | Selects `surface_reading`, `depth_reading`, `hypothesis_text`, `why_an_acharya_misses_it` each under honest name; no `AS statement` | NOT defective — correct reference pattern |
| `bodha_mechanisms_get` → `query_mechanisms.ts:144–150` | Different table (`bodha_mechanisms`); no `surface_reading` / `statement`-style field exists | NOT defective — different data shape |

No exclusions. All census sites addressed.

## 5. Recurrence Guard

The third `it()` block in `F129.exit.spec.ts` (§3 above) is the lint/contract test: it asserts that no `*_reading` column anywhere in `register_p1_synthesis.ts` is aliased to `statement`. This test lives in the permanent test suite; any future query authoring that reintroduces the pattern fails CI immediately — fails closed.

## 6. Dependencies, Rollback

**Other lanes**: None. F-135 shares `register_p1_synthesis.ts` but touches disjoint code (`buildRankedThemes` / `ranked_themes.weaknesses`, lines 381–470, sourced from `mimamsa_insight_units` not `bodha_discoveries`). Either lane may merge first without conflict.

**Rebuild**: Not required. This is a serving-layer TypeScript change only. `bo_anveshana.py` already writes `hypothesis_text`/`depth_reading`/`why_an_acharya_misses_it` to `bodha_discoveries` for every row; the data is already correct in the DB. A shadow run (Level 0) is sufficient: SELECT the relevant columns for chart `482012f1` within a rolled-back transaction and assert `hypothesis_text` is non-empty and contains no raw `signal_type_id:` token.

**Rollback**: Revert lines 815–822 of `register_p1_synthesis.ts` to the original SELECT list. One-line diff, no DB state to undo.

## 7. Coverage Table

| Diagnosis sub-claim | Spec coverage |
|---------------------|---------------|
| (a) `statement` renders raw `signal_type_id` tokens, not narrative | §2: remove `surface_reading AS statement`; §3: exit test asserts absence |
| (b) 20 rows collapse to 5 template shapes, no chart-specific content | §2: `hypothesis_text` is domain-qualified per `bo_anveshana.py:502,641` |
| (c) `synth_chart_brief_get` is the Mahā-Brief; `top_discoveries` is its cross-domain discoveries field | §2: fix targets exactly the `discResult` query within that handler |
| Mechanism: `surface_reading` = epistemic-pair internal label, not user-facing prose | §1 root-cause, §2 why |
| Richer fields (`hypothesis_text`, `depth_reading`, `why_an_acharya_misses_it`) already exist in same row | §2: fix selects them explicitly; §6: no rebuild needed |
| Sibling `bodha_discoveries_get`/`query_discoveries.ts` already correct — use as pattern | §2 diff mirrors `query_discoveries.ts:110–114` |
| Sibling count: 0 additional defect instances | §4: full census table, no exclusions |
| F-135 disjoint in same file | §6: dependencies note |
| Fix is narrow: no new synthesis, no migration, no rebuild | §6, `migration: false`, `writer_asset: null` |
