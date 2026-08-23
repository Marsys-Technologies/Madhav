---
lane_id: F-27
spec_author: spec_writer
status: DRAFT
rs_class: RS-A
---

# F-27 — `query_calibration` domain param no-op (verdictSql JOIN fix)

## §1 Root-cause statement

`query_calibration.ts` declares no `domain` field in `input_schema` and never reads `args.domain` in the handler; `mimamsa_calibration` has no life-domain column, so domain filtering requires a JOIN to `mimamsa_predictions` on `prediction_id` — that join was never built. This lane implements the JOIN-based domain filter on `verdictSql` (and the direct `WHERE domain = $n` filter on `multiplierSql`, which already has a `domain` column).

**Scope clarification (vs F-08):** F-08 handles honest removal of `limit`/`offset` from the alias (`register_p1_aliases.ts` Change A2) on the grounds that these are semantically undefined across four aggregated sub-tables. F-27 aligns with that design decision and does NOT add `limit`/`offset` to the primitive. See §6.

## §2 Files to change

### `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` (sole change)

**1. `input_schema` — add domain field only:**
```ts
domain: {
  type: 'string',
  description: 'Filter by life domain (career, wealth, relationship, health, character, spirituality, other). Applies to verdict_distribution (via JOIN mimamsa_predictions) and multipliers sub-tables.',
  required: false,
},
```
Note: `limit` and `offset` are NOT added here. They are removed from the alias by F-08 Change A2; threading them into a primitive that returns four unrelated aggregated sub-tables is semantically undefined.

**2. Handler — read args.domain:**
```ts
const domain = args.domain != null ? String(args.domain) : undefined
```

**3. `verdictSql` — add JOIN + domain filter:**
- Alias `mimamsa_calibration` as `mc`; add `JOIN mimamsa_predictions mp ON mc.prediction_id = mp.prediction_id`.
- Change `WHERE chart_id = $1` → `WHERE mc.chart_id = $1`.
- Build `vParams: unknown[] = [chart_id]`; if `domain` is set, use `const vDomainIdx = vParams.push(domain)` (returns new length), then append `AND mp.domain = $${vDomainIdx}` before GROUP BY.
- Pass `vParams` to `query(verdictSql, vParams)`.
- Note: follow the sibling pattern (`query_predictions.ts:82` uses `p++` with evaluate-before-increment) to keep param index unambiguous.

**4. `multiplierSql` — domain filter on own column:**
- `mimamsa_multipliers` already carries a `domain` column. Build `mConds: string[] = ['chart_id = $1']`; `mParams: unknown[] = [chart_id]`; let `mP = 2`. If `domain` is set, push `domain = $${mP++}` to `mConds` and `domain` to `mParams`.
- Pass `mParams` to `query(multiplierSql, mParams)`.
- Note: this overlaps with F-08 Change B3 in file and purpose; see §6 for build-order handling.

**5. `reliabilitySql` — excluded (documented):**
`mimamsa_reliability` is a stratum aggregate with no `prediction_id` or life-domain column. Domain filter is not applicable. Unchanged.

**6. `qaSql` — excluded (documented):**
`mimamsa_qa_eval` holds chart-level negative-control battery results, not domain-scoped. Unchanged.

**7. Return `filters` field — extend:**
```ts
filters: { include_heldout, promoted_only, domain },
```

**Why alias unchanged:** `register_p1_aliases.ts:1852-1854` already forwards `{ chart_id, domain }` to `callPlatformPrim` (after F-08 Change A2 removes the limit/offset spread). No alias change required from F-27.

## §3 Exit test

**File:** `platform/src/lib/retrieval/registry/layers/L5_mimamsa/__tests__/query_calibration.domain_filter.test.ts`

**Command:** `npx vitest run platform/src/lib/retrieval/registry/layers/L5_mimamsa/__tests__/query_calibration.domain_filter.test.ts`

**Fails today:** `query` is called without JOIN or domain param; assertions on SQL content and param arrays fail.

**Passes after fix:** domain param appears in verdictSql and multiplierSql calls; SQL contains `mimamsa_predictions`.

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async () => ({ rows: [] })),
}))

import { query as mockQuery } from '@/lib/db/client'
import { queryCalibrationCapability } from '../query_calibration'

describe('query_calibration — domain filter (F-27)', () => {
  beforeEach(() => vi.mocked(mockQuery).mockClear())

  it('input_schema declares domain', () => {
    expect(queryCalibrationCapability.input_schema).toHaveProperty('domain')
    // limit and offset intentionally absent — removed from alias by F-08 Change A2
    expect(queryCalibrationCapability.input_schema).not.toHaveProperty('limit')
    expect(queryCalibrationCapability.input_schema).not.toHaveProperty('offset')
  })

  it('no domain: verdictSql param array is length 1 (chart_id only)', async () => {
    await queryCalibrationCapability.handler({ chart_id: CHART_A }, {})
    const calls = vi.mocked(mockQuery).mock.calls
    const verdictCall = calls.find(c => String(c[0]).includes('composite_verdict'))!
    expect(verdictCall).toBeDefined()
    expect((verdictCall[1] as unknown[])).toHaveLength(1)
  })

  it('domain wired: verdictSql JOINs mimamsa_predictions and carries domain param', async () => {
    await queryCalibrationCapability.handler({ chart_id: CHART_A, domain: 'career' }, {})
    const calls = vi.mocked(mockQuery).mock.calls
    const verdictCall = calls.find(c => String(c[0]).includes('composite_verdict'))!
    expect(String(verdictCall[0])).toContain('mimamsa_predictions')
    expect((verdictCall[1] as unknown[])).toContain('career')
  })

  it('domain wired: multiplierSql also carries domain param', async () => {
    await queryCalibrationCapability.handler({ chart_id: CHART_A, domain: 'career' }, {})
    const calls = vi.mocked(mockQuery).mock.calls
    const multCall = calls.find(c => String(c[0]).includes('mimamsa_multipliers'))!
    expect((multCall[1] as unknown[])).toContain('career')
  })
})
```

## §4 Sibling sites covered

Diagnosis §4 enumerated 7 sibling L5_mimamsa files — all correctly implement domain filtering:
- `query_life_events.ts:140` ✓
- `query_insights.ts:96` ✓
- `query_manifestation_grammar.ts:87` ✓
- `query_manifestation_sets.ts:72` ✓
- `query_predictions.ts:82` ✓
- `lel_intake_checklist.ts` (in-memory filter) ✓
- `query_mechanism_retrodiction.ts:317` (prefix-match filter) ✓

No additional fix sites. Defect is localized to `query_calibration.ts` alone.

**Out-of-scope lead:** `phala_mitigation_get` / `mitigation_map` (L4 Phala) — covered by F-08 Change A1, not by F-27.

## §5 Recurrence guard

The exit test §3 item 1 (`input_schema declares domain`) acts as the schema-presence guard: any future removal fails the test. The negative assertions (`limit`/`offset` absent) guard that future authors do not re-add semantically undefined pagination to this primitive.

The broader CL-03 param-parity harness (hash-divergence per optional filter, cross-tool) flagged in diagnosis §5 is a campaign-level suggestion; F-08 §5 defines the alias-primitive contract test that addresses this systematically.

## §6 Dependencies and rollback

### Cross-lane: F-08 (S5 MŪLA) — conflict acknowledged

F-08 modifies `query_calibration.ts` at Changes B1–B4: adds `domain` to `input_schema` (B1), reads it in handler (B2), applies it to `multiplierSql` via parameterized-array pattern (B3), extends the `filters` echo (B4). F-27 §2 Changes 1–4 overlap with these on the same lines of the same file.

**Design conflict resolved:**
- *Limit/offset:* F-08 Change A2 removes `limit`/`offset` from the alias on the grounds they are semantically undefined across four aggregated sub-tables. F-27 aligns with this decision and does NOT add `limit`/`offset` to the primitive. Conflict closed.
- *multiplierSql domain:* Both lanes implement domain filtering on `multiplierSql`. Code shape differs (F-08 uses `multConds/multParams/mP` pattern; F-27 uses the same pattern in §2 change #4). They are functionally equivalent. **Build-order instruction:** the conductor must assign `query_calibration.ts` to ONE builder bundle. If F-08 lands first, the builder for F-27 need only add the `verdictSql` JOIN — F-27's unique contribution. If F-27 lands first, F-08 B1–B4 can be omitted by the F-08 builder. Either ordering is safe; do not apply both independently.
- *verdictSql domain JOIN:* This is F-27's unique contribution. F-08 does NOT implement domain filtering on `verdictSql` (F-08 only covers `multiplierSql`). The JOIN `mimamsa_predictions mp ON mc.prediction_id = mp.prediction_id` is new work that only F-27 specifies.

**Summary of responsibility split (for conductor):**
| Change | F-08 | F-27 |
|---|---|---|`
| phala_mitigation_get domain removal (alias) | ✓ owns | out of scope |
| mimamsa_calibration_get limit/offset removal (alias) | ✓ owns | aligned, drops from primitive |
| query_calibration.ts input_schema domain field | B1 | §2 change #1 — same output; one builder only |
| query_calibration.ts handler domain read | B2 | §2 change #2 — same output; one builder only |
| query_calibration.ts multiplierSql domain filter | B3 | §2 change #4 — same output; one builder only |
| query_calibration.ts verdictSql JOIN domain filter | ✗ not covered | ✓ §2 change #3 — F-27 unique |
| query_calibration.ts filters echo | B4 | §2 change #7 — same output; one builder only |

### Other dependencies
- **Migration:** None. `mimamsa_calibration.prediction_id` FK already present (confirmed in DIAGNOSIS §3 schema inspection). Read-path change only.
- **Rebuild:** Not a writer-layer fix. No asset rebuild triggered. `writer_asset: null`, `data_delta: narrow`.
- **Rollback:** Revert `query_calibration.ts` to HEAD. No DB state change.

## §7 Coverage table

| Diagnosis sub-claim | Covered by |
|---|---|
| (a) domain param declared in alias schema (line 1849) | Alias verified correct; no alias change — §2 rationale |
| (b) result_hash identical with/without domain | Exit test §3 items 2–3: domain wired → params differ |
| (c) 57-row calibration data across 4 verdict classes | Confirms real data exists; exit test uses mock |
| Mechanism: input_schema omits domain (lines 27-43) | §2 change #1 adds domain only (not limit/offset) |
| Mechanism: handler never reads args.domain (lines 64-67) | §2 change #2 reads args.domain |
| Mechanism: verdictSql has no domain predicate | §2 change #3 adds JOIN + filter (F-27 unique) |
| Mechanism: mimamsa_calibration has no domain column | §2 change #3 — JOIN mimamsa_predictions instead |
| Bonus: limit/offset no-ops | Resolved by honest removal in F-08 Change A2; NOT implemented in primitive |
| Sibling census: 7 correct, 1 defect | §4 documented |
| Adjacent lead (phala_mitigation_get) | F-08 Change A1; out of scope for F-27 |
| Blast radius: different file from F-10 | §6 confirms no F-10 conflict |
| Blast radius: F-08 conflict | §6 acknowledged and resolved — conductor assigns one builder for query_calibration.ts |
| CL-03 param-parity harness | F-08 §5 defines the alias-primitive contract test |
