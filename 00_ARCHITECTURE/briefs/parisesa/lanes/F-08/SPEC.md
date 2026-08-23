---
lane: F-08
stage: S (SPEC)
campaign: PARIŚEṢA
rs_class: RS-B
migration: false
writer_asset: null
data_delta: narrow
---

# F-08 SPEC — `phala_mitigation_get` domain no-op + `mimamsa_calibration_get` domain/limit/offset no-ops

## 1. Root-cause statement

The MCP alias `phala_mitigation_get` in `register_p1_aliases.ts` declares `domain: z.string().optional()` and forwards it to the `mitigation_map` primitive, but neither `phala_mitigation` nor `phala_anchors` has a `domain` column — so no SQL predicate can ever be applied — and the primitive's `input_schema` correctly omits `domain`; the param is silently discarded at the alias-to-primitive boundary, producing byte-identical results for any domain value.

**Diagnosis fix-point correction:** DIAGNOSIS.md §3 and §5 identify `query_phala_calibration.ts` as the fix point, but schema verification (`migrations/brahma_phala_mitigation.sql`) confirms `phala_mitigation` has no `domain` column. Domain filtering cannot be implemented at the primitive without a schema migration. The actual fix point for the primary site is the alias in `register_p1_aliases.ts` (honest parameter removal). The confirmed sibling (`mimamsa_calibration_get` / `query_calibration.ts`) is separately fixable at the primitive because `mimamsa_multipliers` has a `domain text` column (migration `349_mimamsa_gunanaka.sql`).

---

## 2. Files to change

### File A — `platform-mcp/src/tools/register_p1_aliases.ts`

**Change A1 — `phala_mitigation_get` schema (~lines 1738–1753):**
- Remove `domain: z.string().optional()` from the Zod schema object.
- Change handler destructure from `({ chart_id, domain })` to `({ chart_id })`.
- Change `callPlatformPrim('mitigation_map', { chart_id, domain }, principal)` to `callPlatformPrim('mitigation_map', { chart_id }, principal)`.
- **Why:** `phala_mitigation` has no `domain` column (confirmed in schema migration); advertising a filter that can never be applied is a CL-03 honesty defect; honest removal makes the alias truthful without breaking any caller (the param was already a no-op).

**Change A2 — `mimamsa_calibration_get` schema (~lines 1844–1858):**
- Remove `...GlobalBase` spread from the Zod schema object (eliminates `limit` and `offset`).
- Change handler destructure from `({ chart_id, domain, limit, offset })` to `({ chart_id, domain })`.
- Change `callPlatformPrim('query_calibration', { chart_id, domain, limit, offset }, principal)` to `callPlatformPrim('query_calibration', { chart_id, domain }, principal)`.
- **Keep** `domain: z.string().optional()` in the schema — it will now be honored by the primitive after Change B.
- **Why:** `query_calibration` returns four aggregated sub-tables (verdict distribution, reliability curve, multipliers, QA results); applying a single `limit`/`offset` across these is semantically undefined, and paginating four independent sub-queries is out of scope for a CL-03 param-honesty fix. Honest removal.

### File B — `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`

**Change B1 — `queryCalibrationCapability.input_schema` (~line 43, after `promoted_only` entry):**
```ts
domain: {
  type: 'string',
  description: 'Filter multipliers by domain (e.g. career, health, relationship). Applies only to the multipliers sub-table (mimamsa_multipliers.domain).',
  required: false,
},
```

**Change B2 — Handler body (~line 67, after the `promoted_only` read):**
```ts
const domain = args['domain'] as string | undefined
```

**Change B3 — `multiplierSql` construction (~lines 94–101):** Replace the current single-string `WHERE chart_id = $1 ${multFilter}` with a parameterized array:
```ts
const multConds: string[] = ['chart_id = $1']
const multParams: unknown[] = [chart_id]
let mP = 2
if (promoted_only) { multConds.push('gate_passed = true') }
if (domain)        { multConds.push(`domain = $${mP++}`); multParams.push(domain) }
const multiplierSql = `
  SELECT weight_id, mechanism, target_kind, target_ref, domain,
         applied_multiplier, raw_multiplier, n_observations,
         promotion_status, gate_passed, kill_switch_state, divergence_from_classical
  FROM mimamsa_multipliers
  WHERE ${multConds.join(' AND ')}
  ORDER BY applied_multiplier DESC
`
// Replace query(multiplierSql, [chart_id]) → query(multiplierSql, multParams)
```

**Change B4 — `filters` echo in return (~line 129):**
```ts
filters: { include_heldout, promoted_only, domain },
```

**Why:** `mimamsa_multipliers.domain` column confirmed in `migrations/349_mimamsa_gunanaka.sql` (nullable `text`). Domain filtering allows callers to focus the multiplier sub-table on a life-domain without changing the other three sub-tables. Parameterized query prevents SQL injection.

---

## 3. Exit test

Two test files — both must FAIL on current `main-ro` code and PASS after fixes are applied.

**Test file 1:** `platform-mcp/src/__tests__/f08_phala_mitigation_alias.test.ts`
```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

describe('F-08: phala_mitigation_get alias domain removal', () => {
  it('register_p1_aliases.ts must not declare domain in phala_mitigation_get schema', () => {
    const src = readFileSync(resolve(__dirname, '../tools/register_p1_aliases.ts'), 'utf-8')
    const idx = src.indexOf("'phala_mitigation_get'")
    expect(idx).toBeGreaterThan(-1)
    const block = src.slice(idx, idx + 500)
    // FAIL today: `domain: z.string().optional()` IS in the block
    // PASS after Change A1: removed
    expect(block).not.toMatch(/domain\s*:\s*z\.string/)
  })
})
```
**Run:** `cd /Users/Dev/par-night/wt/<bundle>/platform-mcp && npx vitest run src/__tests__/f08_phala_mitigation_alias.test.ts`

**Test file 2:** `platform/src/__tests__/f08_calibration_domain.test.ts`
```ts
import { describe, it, expect } from 'vitest'
import { queryCalibrationCapability } from '../lib/retrieval/registry/layers/L5_mimamsa/query_calibration'

describe('F-08 sibling: queryCalibrationCapability domain filter', () => {
  it('input_schema must declare domain field', () => {
    // FAIL today: domain absent from input_schema
    // PASS after Change B1: present
    expect('domain' in queryCalibrationCapability.input_schema).toBe(true)
  })
  it('input_schema domain must be string type', () => {
    const d = (queryCalibrationCapability.input_schema as Record<string, {type: string}>)['domain']
    expect(d?.type).toBe('string')
  })
})
```
**Run:** `cd /Users/Dev/par-night/wt/<bundle>/platform && npx vitest run src/__tests__/f08_calibration_domain.test.ts`

---

## 4. Sibling sites covered

| Site | Status | Coverage |
|---|---|---|
| `phala_mitigation_get` / `query_remedy_program` (primary) | COVERED | Change A1: remove `domain` from alias schema |
| `mimamsa_calibration_get` / `query_calibration.ts` (confirmed sibling) | COVERED | Change A2 + B1–B4: remove `limit`/`offset` from alias; implement `domain` in primitive |
| L4_phala internal 5-file check (query_domain_result, query_muhurat, query_phala_calibration, query_predictive_anchors, query_prospective_ledger) | EXCLUDED (clean) | Diagnosis §4 confirmed zero within-file declared-but-unread fields |
| ~46 `callRegistryCap`/`callSidecarPath` call sites | EXCLUDED (false positives) | Diagnosis §4 spot-check confirmed params ARE forwarded correctly; regex extraction artefact |

---

## 5. Recurrence guard

Add `platform-mcp/src/__tests__/alias_primitive_contract.test.ts` — a CI contract test that:
1. Parses all `callPlatformPrim('<primitive>', { ...params }, principal)` call sites in `register_p1_aliases.ts`.
2. Loads each target primitive's `CapabilityDescriptor.input_schema` by importing from the relevant layer file.
3. Asserts that every forwarded param key is declared in the primitive's `input_schema`.

This enforces: ∀ param `p` forwarded via `callPlatformPrim` to primitive `T`, `p ∈ T.input_schema`. A future divergence (new alias param not added to primitive) will fail this test closed before merge.

Builder note: The contract test is a SEPARATE deliverable from the two exit tests above. It may be written after the primary fixes land.

---

## 6. Dependencies and rollback

**Dependencies:** None. No other active F-xx lane in the overnight run modifies `register_p1_aliases.ts` for `phala_mitigation_get` or `mimamsa_calibration_get`, nor `query_calibration.ts`.

**Rebuild:** Not required. This is a retrieval-layer fix (no writer-layer data change). No `data_delta: broad` condition; shadow-only verification is not applicable (not a writer-layer lane). Verifier should spot-call both tools after merge to confirm behavioral change.

**Rollback:** `git revert <commit>` on the two changed files. No DB migration means no rollback complexity. No data written or mutated.

---

## 7. Coverage table

| Diagnosis sub-claim | Spec response |
|---|---|
| (a) `domain` declared in alias Zod schema | Change A1: removed from `phala_mitigation_get` |
| (b) `domain` never read at primitive boundary | CONFIRMED: primitive `input_schema` is correct; `phala_mitigation` has no `domain` column; fix is alias-side |
| (c) Byte-identical results regardless of domain | Resolved: alias no longer accepts `domain`; callers cannot pass it |
| (d) No disclosure in `filters` echo or `warnings` | Resolved: param dropped from alias entirely; no echo needed |
| §3 fix-point claim (`query_phala_calibration.ts`) | CORRECTED: no change needed to that file; see diagnosis correction in §1 above |
| §4 sibling `mimamsa_calibration_get` domain no-op | COVERED: Change A2 + B1–B4 |
| §4 sibling `limit`/`offset` no-op | COVERED: Change A2 removes both from alias |
| §4 L4_phala internal check — zero matches | Documented in §4; excluded (clean) |
| §4 ~46 callRegistryCap/callSidecarPath — false positives | Documented in §4; excluded |
| §5 lease flag for `query_phala_calibration.ts` | SUPERSEDED: fix is alias-side; no lease needed for that file |
| §5 sibling lease for `query_calibration.ts` | COVERED in this spec; Change B1–B4 |
