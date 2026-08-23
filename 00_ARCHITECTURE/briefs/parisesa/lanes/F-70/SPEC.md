# F-70 SPEC — calibration_maturity serving-layer wiring: remaining 3 kala_* stubs

Stage: SPEC (Stage S) · Campaign: PARIŚEṢA · Lane: F-70 · RS-class: RS-B
Ratified-against: DIAGNOSIS.md (2026-08-16), live source verified 2026-08-17 against main-ro.

---

## §1 Root-cause statement

Three of the eight kala_* view facades (`now.ts`, `ritual.ts`, `story.ts`) still pass `calibrationMaturity: noLelCalibrationMaturity()` to `makeKalaEnvelope` — a hardcoded zero-struct that ignores `kala_field_skill`/`kala_field_weight_versions` rows that already exist in production — while the shared async resolver `fetchCalibrationMaturity(chartId, principal)` was added to `kala_envelope.ts` (attributed to F-140) and is already used by the other five sibling views (priority, elect, upaya, explain, ahead).

> **Drift from diagnosis**: the diagnosis (2026-08-16) recorded all 8 sites as hardcoded stubs. As of main-ro today, 5 have already been fixed. F-70's implementation scope is the 3 remaining sites + 1 stale narration comment.

---

## §2 Files to change

### 2.1 `platform-mcp/src/tools/kala_views/now.ts`
- **Import**: add `fetchCalibrationMaturity` to the existing named import from `../../lib/kala_envelope.js` (alongside `noLelCalibrationMaturity`, which stays — it is used for the type annotation at line 1471 and as a fallback inside `fetchCalibrationMaturity` itself).
- **Call site** (line 1970): change
  ```ts
  calibrationMaturity: noLelCalibrationMaturity(),
  ```
  to
  ```ts
  calibrationMaturity: await fetchCalibrationMaturity(chartId, principal),
  ```
  `chartId` and `principal` are both in scope as parameters of `computeKalaNow` (line 1536-1539). The function is already `async`.

### 2.2 `platform-mcp/src/tools/kala_views/ritual.ts`
- **Import**: add `fetchCalibrationMaturity` to the named import from `kala_envelope.js` (line 80 block). `noLelCalibrationMaturity` import stays (line 81) — remove only if no other call sites remain after the fix (verify; the import at line 81 is currently the only usage driver).
- **Call site** (line 572): change
  ```ts
  calibrationMaturity: noLelCalibrationMaturity(),
  ```
  to
  ```ts
  calibrationMaturity: await fetchCalibrationMaturity(params.chart_id, principal),
  ```
  `params.chart_id` and `principal` are in scope at the enclosing handler (confirmed: `resolveFieldSnapshot(params.chart_id, principal)` at line 563). The handler is already `async` (line 447 signature).

### 2.3 `platform-mcp/src/tools/kala_views/story.ts`
- **Import**: add `fetchCalibrationMaturity` to the named import block from `kala_envelope.js` (line 105 vicinity). `noLelCalibrationMaturity` import stays or is removed if no other usages remain.
- **Call site** (line 756): change
  ```ts
  calibrationMaturity: noLelCalibrationMaturity(),
  ```
  to
  ```ts
  calibrationMaturity: await fetchCalibrationMaturity(input.chart_id, principal),
  ```
  `input.chart_id` and `principal` are parameters of `handleKalaStoryGet` (line 692-694). The function is already `async`.

### 2.4 `platform-mcp/src/tools/kala_views/priority.ts` (narration fidelity fix only — §N.7)
- **Stale comment** (line 14): remove the false assertion `"always the honest noLelCalibrationMaturity() stub at W0 — no calibration plane exists yet anywhere in this campaign, not just for LEL-absent charts"`. Replace with honest description: `calibration_maturity reads live data via fetchCalibrationMaturity (falls back to zero-stub only when chart has no fitted rows)`. This comment is the `priority.ts`-local §N.7 narration violation identified in the diagnosis (§2b).
- No code change at line 434 — it already calls `fetchCalibrationMaturity`.

---

## §3 Exit test

**File**: `platform-mcp/src/tools/kala_views/kala_calibration_maturity_wiring.test.ts` (new file, builder creates)

**Command** (run from the `platform-mcp` directory of the builder worktree):
```
npx vitest run --reporter=verbose src/tools/kala_views/kala_calibration_maturity_wiring.test.ts
```

**Behaviour**:
- **FAILS on today's code**: `now.ts`, `ritual.ts`, `story.ts` each contain `calibrationMaturity: noLelCalibrationMaturity()` → the test's negative assertions trigger.
- **PASSES after fix**: all three files call `fetchCalibrationMaturity` at the `calibrationMaturity` argument; the negative assertions no longer trigger.

**Test content** (source-scan, same pattern as `ritual.test.ts`):
```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

// ROOT = platform-mcp (4 levels up from the test file itself)
// test file: platform-mcp/src/tools/kala_views/kala_calibration_maturity_wiring.test.ts
// path.resolve(file, '../../..') would land at platform-mcp/src — one level too shallow
const ROOT = path.resolve(fileURLToPath(import.meta.url), '../../../..')
const kalaViews = path.join(ROOT, 'src/tools/kala_views')

function src(file: string): string {
  return readFileSync(path.join(kalaViews, file), 'utf-8')
}

describe('F-70: calibration_maturity wiring — no unconditional zero-stubs in kala_views', () => {
  const FILES_TO_FIX = ['now.ts', 'ritual.ts', 'story.ts'] as const

  for (const file of FILES_TO_FIX) {
    it(`${file}: calibrationMaturity does NOT call noLelCalibrationMaturity() unconditionally`, () => {
      const source = src(file)
      // This assertion FAILS on current code (the stub is still there) and PASSES after fix.
      expect(source).not.toMatch(/calibrationMaturity:\s*noLelCalibrationMaturity\(\)/)
    })

    it(`${file}: calibrationMaturity calls fetchCalibrationMaturity`, () => {
      const source = src(file)
      expect(source).toContain('fetchCalibrationMaturity')
    })
  }

  it('priority.ts: stale false comment removed', () => {
    const source = src('priority.ts')
    expect(source).not.toContain('no calibration plane exists yet')
  })
})
```

---

## §4 Sibling sites covered

The diagnosis §3.1 census lists 8 sites. Disposition per site:

| # | File | Line (diag) | Current state | F-70 action |
|---|---|---|---|---|
| 1 | `now.ts` | 1970 | **STILL BROKEN** — `noLelCalibrationMaturity()` | Fix in §2.1 |
| 2 | `priority.ts` | 434 | Already fixed (calls `fetchCalibrationMaturity`) | Narration comment fix §2.4 |
| 3 | `ahead.ts` | 1984 | Already fixed (calls `fetchCalibrationMaturity`) | No change needed |
| 4 | `upaya.ts` | 427 | Already fixed (calls `fetchCalibrationMaturity`) | No change needed |
| 5 | `ritual.ts` | 572 | **STILL BROKEN** — `noLelCalibrationMaturity()` | Fix in §2.2 |
| 6 | `explain.ts` | 699 | Already fixed (calls `fetchCalibrationMaturity`) | No change needed |
| 7 | `story.ts` | 756 | **STILL BROKEN** — `noLelCalibrationMaturity()` | Fix in §2.3 |
| 8 | `elect.ts` | 761 | Already fixed (calls `fetchCalibrationMaturity`) | No change needed |

All 8 diagnosis sites accounted for. No site excluded without reason. Five pre-fixed by a prior lane (F-140 introduced `fetchCalibrationMaturity` and wired it to priority, elect, upaya, explain, ahead).

---

## §5 Recurrence guard

The exit test file (`kala_calibration_maturity_wiring.test.ts`) is the recurrence guard: any future builder who reverts to `calibrationMaturity: noLelCalibrationMaturity()` in the `makeKalaEnvelope` call in any of the three files will cause those test assertions to fail in CI.

Additional guard: the existing TypeScript compiler (`tsc --noEmit`) enforces that `fetchCalibrationMaturity` is called as `await fetchCalibrationMaturity(...)` (the function returns `Promise<CalibrationMaturity>`); forgetting the `await` produces a type error at the `makeKalaEnvelope` call site since `calibrationMaturity` is typed `CalibrationMaturity`, not `Promise<CalibrationMaturity>`.

---

## §6 Dependencies and rollback

**Dependencies**:
- `fetchCalibrationMaturity` is already exported from `platform-mcp/src/lib/kala_envelope.ts` (lines 472-523, verified in main-ro). No new shared code needs to be written; this fix is purely import + call-site changes.
- No other lane is required to land first.
- **Cross-lane note**: the diagnosis flagged a secondary defect in `ka_kshetra/stage4_field.py` (unscoped weight-version query at line 772-776). That defect is explicitly out of F-70 scope — it should be a separate lane.

**Rollback**: revert three call-site lines and four import lines across `now.ts`, `ritual.ts`, `story.ts`, and the comment line in `priority.ts`. No schema change, no migration rollback needed.

---

## §7 Coverage table — diagnosis sub-claims

| Diagnosis claim | Covered by |
|---|---|
| (a) All 8 kala_* views hardcode zero-stub | §4 accounts for all 8; §2 fixes the 3 remaining |
| (b) Tool descriptions assert false global absence (§N.7 violation) | §2.4 fixes the `priority.ts` comment; the MCP-facing description string in `priority.ts` derives from the same comment block — fixing the comment closes the §N.7 violation |
| (c) Real computation exists in `mi_bhara.py`, writes 3 tables | No change needed here; confirms `fetchCalibrationMaturity`'s SQL query has real rows to read |
| (d) Zero serving-layer consumers of the 3 tables | Fixed by §2.1–2.3: the 3 fixed views now read `kala_field_skill` via `fetchCalibrationMaturity` |
| (e) Contradictory sibling surface (`mimamsa_insight_get`) reports 57 real matches | After fix, `now.ts`/`ritual.ts`/`story.ts` will read real values; contradiction resolved for all 8 views |
| §3.1 eight call sites verified | All accounted for in §4 |
| §3.5 join path traced | Confirms `fetchCalibrationMaturity`'s query is correct; no spec change needed |
| §3.5 secondary defect in `ka_kshetra/stage4_field.py` | Out of F-70 scope; flagged for conductor |

---

## Writer-layer declaration

This fix does NOT touch any `ga_writers/`, `bo_*` orchestrator writer, or `pipeline/orchestrator/writers/` file. It is a pure MCP serving-layer (TypeScript) change. `writer_asset: null`. Verification path: TypeScript `tsc --noEmit` + exit test source-scan. No shadow run required (no Python writer executed).
