# F-13 SPEC — `kala_ritual_get` response-size control

## 1. Root-cause statement

`ritual.ts`'s registration handler (lines 679–694) serializes the full `handleKalaRitualGet` response with bare `JSON.stringify(..., null, 2)` and never calls `finalizeMcpBudget`/`kalaBudgetedDualOutput`; additionally, the `autoDetectTrimmableSections` helper (depth ≤ 2) cannot reach the per-candidate `JudgmentLedger` sub-arrays (`convention_only_factors`, `neutral_annotations`, `convention_only_keys`) because they sit at depth 3+ in Mode 2 (`pattern_search.adjudication.ledgers[i].*`) and inside array elements in Mode 1 (`opportunities[i].judgment_ledger.*`), so both modes produce responses 10–30× the 40 KB sibling default with no trim of any kind.

## 2. Files to change

### `platform-mcp/src/tools/kala_views/ritual.ts` — the only file changed

**Change A — schema**: add `budget_kb: z.number().int().min(10).max(200).optional().describe('Response size ceiling in KB. Default 40.')` to `KalaRitualInputShape` (after `limit`, line ~165). Add matching optional field to `KalaRitualParams` interface (~line 179). Thread it from the registration handler's input destructure through to the budget call.

**Change B — imports**: add `import { finalizeMcpBudget, autoDetectTrimmableSections, type TrimmableSection } from '../../lib/response_budget.js'` at the top of `ritual.ts`.

**Change C — dynamic ledger sections helper**: add a private function `buildLedgerTrimmableSections<T extends Record<string, unknown>>(response: T, toolName: string): TrimmableSection<T>[]` that:
- Iterates `response.pattern_search?.adjudication?.ledgers ?? []` (Mode 2): for each ledger at index `i`, declares three `TrimmableSection`s covering `pattern_search.adjudication.ledgers[i].convention_only_factors`, `…neutral_annotations`, and `…convention_only_keys`, each with `minKeep: 5` and a recover hint pointing back to `kala_ritual_get` with a narrower `sky_pattern_spec`.
- Iterates `response.opportunities ?? []` (Mode 1): for each opportunity at index `i` that has a non-null `judgment_ledger`, declares the same three `TrimmableSection`s at paths `opportunities[i].judgment_ledger.convention_only_factors`, etc., same `minKeep: 5`.
- Returns all declared sections. Sections for arrays with ≤ 5 entries are still declared (safe — `applyResponseBudget` skips a section when its array length is already at/below floor).

**Change D — budgeted return**: replace lines 691–693:
```ts
return {
  content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }],
}
```
with:
```ts
const budgetKb = budget_kb ?? 40
const sections = [
  ...buildLedgerTrimmableSections(response, 'kala_ritual_get'),
  ...autoDetectTrimmableSections(response, 'kala_ritual_get'),
]
const budgeted = finalizeMcpBudget(response, { maxKb: budgetKb, sections })
return {
  content: [{ type: 'text' as const, text: JSON.stringify(budgeted) }],
}
```
(No `structuredContent` dual-output here — `ritual.ts` is not a kala_envelope tool and has no `reading: ArgumentReading` field, so `kalaBudgetedDualOutput` from `shared.ts` is inapplicable; the `finalizeMcpBudget` + `content` pattern used by `now.ts` / `ahead.ts` is the correct analogue.)

**Why these changes and not others**: `response_budget.ts`, `kala_lattice_query.ts`, `kala_sky_pattern.ts`, and `kala_ritual_resonance.ts` are untouched — the fix is purely in the serving/registration layer. No pagination contract is added to the writer or engine layers; callers reduce payload by lowering `budget_kb`, `limit`, or `horizon`.

## 3. Exit test

**File**: `platform-mcp/src/tools/kala_views/__tests__/test_f13_ritual_budget.ts`

**Command**:
```
npx tsx --tsconfig platform-mcp/tsconfig.json \
  platform-mcp/src/tools/kala_views/__tests__/test_f13_ritual_budget.ts
```

**Fails on today's code**: `JSON.stringify(result)` for a Mode-1 call (chart `482012f1`, `horizon: '90d'`, `limit: 10`) is ~491 KB — assertion `len <= 40 * 1024` throws.

**Passes after fix**: same call with `budget_kb: 40` returns ≤ 40 KB with `trim_report` present.

Test body (sketch — implementer writes the full file):
```ts
import { handleKalaRitualGet } from '../ritual.js'
import { getPrincipalForChart } from '../../test_helpers.js'  // existing pattern
// Shadow-run pattern: open DB connection, run inside transaction, rollback in finally.
async function run() {
  const principal = await getPrincipalForChart('482012f1-710e-4a25-994a-93821f5871aa')
  const result = await handleKalaRitualGet(
    { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', horizon: '90d', limit: 10, budget_kb: 40 },
    principal,
  )
  // (budget is applied by the registration handler, not handleKalaRitualGet;
  //  the test must invoke the registration handler wrapper or apply budget inline.)
  const json = JSON.stringify(result)
  const byteLen = Buffer.byteLength(json, 'utf8')
  if (byteLen > 40 * 1024) throw new Error(`F-13 budget FAIL: ${byteLen} bytes > 40 KB`)
  if (!('trim_report' in result)) throw new Error('F-13: trim_report absent — budget wiring not active')
  console.log(`F-13 PASS: ${byteLen} bytes, trim_report present`)
}
run().catch(e => { console.error(e); process.exit(1) })
```

Note: if `handleKalaRitualGet` returns the raw (unbudgeted) object, the test must apply the budget logic directly (import `finalizeMcpBudget` + `buildLedgerTrimmableSections` + `autoDetectTrimmableSections` and call them on the result) to match what the registration handler does after the fix. Either formulation fails today (raw result is ~491 KB) and passes after.

## 4. Sibling sites covered

From DIAGNOSIS.md §4 — exhaustive census of all 11 non-test files in `platform-mcp/src/tools/kala_views/`:

| File | Budget wiring | Lattice/adjudication | Disposition |
|---|---|---|---|
| `ahead.ts` | `finalizeMcpBudget` (yes) | `fetchLatticeSubstrate` only — zero `adjudicateCandidates`/`scoreElectionQuality`/`JudgmentLedger` hits | **EXCLUDED**: has budget wiring; does not produce ledger-shaped data (confirmed by grep) |
| `dasha_sandhi.ts` | none | none | **EXCLUDED**: no lattice exposure; different defect class (no unbounded-growth driver demonstrated); out of scope for F-13, flagged for future census pass |
| `elect.ts` | `budget_kb` + `finalizeMcpBudget` (yes) | yes (adjudicateCandidates) | **EXCLUDED**: has budget wiring; different defect shape (declared-section coverage gap filed separately as F-122) |
| `explain.ts` | `kalaBudgetedDualOutput` (yes) | none | **EXCLUDED**: has budget wiring; no lattice exposure |
| `now.ts` | `finalizeMcpBudget` (yes) | none | **EXCLUDED**: has budget wiring; no lattice exposure |
| `priority.ts` | `kalaBudgetedDualOutput` (yes) | none | **EXCLUDED**: has budget wiring; no lattice exposure |
| `ritual.ts` | **none** | **yes** (7 refs: adjudicateCandidates, scoreElectionQuality, scoreMode1Opportunities, searchSkyPattern) | **IN SCOPE — this fix** |
| `shared.ts` | helper lib (exports `finalizeMcpBudget` wrapping) | none | **EXCLUDED**: not a tool handler |
| `story.ts` | `budget_kb` + `finalizeMcpBudget` (yes) | none | **EXCLUDED**: has budget wiring; no lattice exposure |
| `upaya.ts` | none | none | **EXCLUDED**: no lattice exposure; same note as `dasha_sandhi.ts` |

Conclusion (from DIAGNOSIS §4): `ritual.ts` is the unique intersection of (a) zero budget wiring AND (b) lattice/adjudication engine usage. No other file in `kala_views/` shares F-13's specific defect class.

## 5. Recurrence guard

Add two assertions to the exit test file `test_f13_ritual_budget.ts`:

1. **Schema guard**: `import { KalaRitualInputShape } from '../ritual.js'` and assert `'budget_kb' in KalaRitualInputShape` — if `budget_kb` is ever removed from the schema, this fails.
2. **Size-regression guard**: the Mode-1 size assertion (`byteLen <= 40 * 1024`) is itself the recurrence guard — any rewrite of the registration handler that drops the budget call re-introduces a ≥491 KB response and fails the test immediately.

Additionally, propose adding `F-13` to `platform/scripts/governance/ekv_controls.py` (the 27-check CL-00 battery) as a 28th entry asserting `kala_ritual_get` schema contains `budget_kb` — this is a one-line addition that gives CI-level recurrence protection. (The DIAGNOSIS confirmed F-13 is currently absent from the 27 controls.)

## 6. Dependencies, rollback, and sequencing

**Dependencies**:
- No other lane must complete before this one. `response_budget.ts` and `kala_views/shared.ts` are read-only in this fix (imported, not edited). F-122 (`elect.ts`) touches a different file and is independent.
- `F-46`, `F-09`, `F-17`, `F-28`, `F-44`, `F-12` are noted in the DIAGNOSIS as holding leases on `response_budget.ts` (S2 HOT exclusive in some). Since this fix imports `response_budget.ts` but does NOT edit it, no lease conflict arises.
- F-125 also touches `kala_views/ritual.ts` for an unrelated B.11 orientation defect — merge-order awareness needed: both lanes must not be in the merge queue simultaneously (per PROTOCOL §4 rebuild policy). Sequence: F-13 first (or vice versa), never concurrent.

**Rebuild policy**: This is a serving-layer fix only — no writer, no DB writes. Shadow run per PROTOCOL Level 0 is required (demonstrates the budget trim produces correct output on chart `482012f1` without committing). No asset rebuild needed; status upon shadow pass = `CODE-LANDED · VERIFIED-BY-SHADOW-RUN · DATA-PENDING-FULL-REBUILD` is inapplicable here (serving-layer only — status should be `LIVE` after shadow pass since no data pipeline is involved).

**Rollback**: Revert `ritual.ts` to its prior commit state. No migration to reverse.

## 7. Coverage table

| Diagnosis sub-claim | Spec section covering it |
|---|---|
| A: `ritual.ts` has zero budget wiring | §2 Change B+D (adds imports + finalizeMcpBudget call) |
| B: Mode-2 produces ~1.30 MB | §3 exit test (fails today on raw size); §2 Change C (ledger sections for pattern_search.adjudication.ledgers[*]) |
| C: Mode-1 (`limit=10`) produces ~570 KB | §3 exit test primary assertion; §2 Change C (sections for opportunities[*].judgment_ledger.*) + Change D (autoDetect catches structural.remedy_rows/resonance_rows at depth 2) |
| D (corrected): real driver is per-ledger JudgmentLedger arrays (convention_only_factors 1205 entries, neutral_annotations 617, etc.), not the census | §2 Change C explicitly targets these three sub-arrays with TrimmableSections, not gap_report.census |
| E: sibling `story.ts` / `elect.ts` have `budget_kb` + `finalizeMcpBudget`; `ritual.ts` does not | §2 Change A (adds budget_kb to schema, matching sibling default of 40 KB) |
| Blast radius: F-13 absent from CL-00 27-check battery | §5 recurrence guard (proposes adding F-13 as 28th check to ekv_controls.py) |
| Sibling census: 11 files checked, ritual.ts uniquely has both defects | §4 full per-file table |
| Fix path stays inside S2 lease (no NEEDS-LEASE) | §6 dependencies (response_budget.ts imported not edited; all touched files are S2-owned) |
