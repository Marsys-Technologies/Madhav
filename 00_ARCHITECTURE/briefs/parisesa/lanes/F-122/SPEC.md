# F-122 SPEC — `kala_elect_get` section-coverage gap: undeclared fields bypass budget trimmer

## 1. Root-cause statement
`elect.ts`'s hand-declared `sections: TrimmableSection[]` array omits `lattice_adjudication.ledgers[]` sub-arrays, `candidates[].hora_ladder`, and six of seven `JudgmentLedger` array fields (`convention_only_keys`, `neutral_annotations`, `dosas_present`, `residual_dosas`, `supporting_factors`, `pariharas_applied`), making them structurally invisible to every pass of `finalizeMcpBudget`, so they survive a trim that correctly floors `candidates` 4→1 while shipping the full pre-trim bookkeeping for all four candidates the caller can no longer see.

## 2. Files to change

### `platform-mcp/src/tools/kala_views/elect.ts` — ONLY file to touch

Add the following `TrimmableSection` entries to the `sections` array (currently lines 827–869), inserted in density order **before** the existing `candidates` section so lower-density fields are cut first:

| # | path | minKeep | what it cuts |
|---|---|---|---|
| A | `lattice_adjudication.ledgers[].convention_only_keys` (all ledgers, flatMap) | 0 | 114 deduplicated key strings — bookkeeping only, highest row count |
| B | `lattice_adjudication.ledgers[].neutral_annotations` (all ledgers, flatMap) | 0 | ~60 hora-cycle annotation rows — bookkeeping |
| C | `candidates[].hora_ladder` (all candidates, flatMap) | 0 | 15 HoraSlot entries per surviving candidate |
| D | `lattice_adjudication.ledgers[].supporting_factors` (all ledgers, flatMap) | 0 | corroborating factors, not the operative finding |
| E | `lattice_adjudication.ledgers[].dosas_present` (all ledgers, flatMap) | 0 | 12-row dosha list for trimmed-away candidates |
| F | `lattice_adjudication.ledgers[].residual_dosas` (all ledgers, flatMap) | 0 | 10-row residual list for trimmed-away candidates |
| G | `lattice_adjudication.ledgers[].pariharas_applied` (all ledgers, flatMap) | 0 | applied-remedy rows for trimmed-away candidates (`kala_lattice_query.ts:178`) |

Each section follows the same pattern as the existing `convention_only_factors` section: a `flatMap` getter across all ledgers and a redistributing setter that writes trimmed slices back per-ledger.

**Additionally**, modify the existing `candidates` section's `setArray` callback to sync `lattice_adjudication.ledgers` to only the surviving candidates:
```
setArray: (c, kept) => {
  c.candidates = kept as KalaElectCandidate[]
  if (c.lattice_adjudication) {
    const survivingIds = new Set(
      (kept as KalaElectCandidate[]).map(cand => cand.judgment_ledger?.candidate_id).filter(Boolean)
    )
    c.lattice_adjudication = {
      ...c.lattice_adjudication,
      ledgers: c.lattice_adjudication.ledgers.filter(l => survivingIds.has(l.candidate_id)),
    }
  }
},
```

**Why only `elect.ts`:** `kala_lattice_query.ts` is FROZEN-adjacent (shared engine, ONE-ENGINE-RULE). `response_budget.ts` is S2 HOT / touched by 6 other lanes — the per-tool `sections` declaration in `elect.ts` is the correct and sufficient surface. No other `kala_views/*.ts` file has this exact defect shape (§4).

## 3. Exit test

**File:** `platform-mcp/src/tools/kala_views/__tests__/elect_budget_trim_f122.test.ts`

**Command (FAILS today, PASSES after fix):**
```
npx jest --testPathPattern=elect_budget_trim_f122 --no-coverage
```

**Assertions:**
```ts
// Repro params verbatim from DIAGNOSIS §1
const result = await handleKalaElectGet({
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  undertaking: 'business',
  date_range: { start: '2026-08-15', end: '2026-11-12' },
  limit: 4,
  native_janma_nakshatra: 'Purva Bhadrapada',
  budget_kb: 20,
})

// PRIMARY — FAILS today (flag fires verbatim per DIAGNOSIS §1.C)
expect(result.judgment_flags?.map(f => f.code)).not.toContain('budget_exceeded_after_trim')

// Budget actually honoured
const sizeKb = Buffer.byteLength(JSON.stringify(result), 'utf8') / 1024
expect(sizeKb).toBeLessThanOrEqual(20)

// hardFloor still respected (was correct before; must stay correct)
expect(result.candidates.length).toBeGreaterThanOrEqual(1)

// lattice_adjudication.ledgers bounded to surviving candidates (was 4 vs 1 — DIAGNOSIS §1.B)
expect(result.lattice_adjudication?.ledgers.length ?? 0).toBeLessThanOrEqual(result.candidates.length)

// hora_ladder trimmed (was 15 on a budget-exceeded response — DIAGNOSIS §1.B)
expect(result.candidates[0]?.hora_ladder?.length ?? 0).toBeLessThan(15)
```

Assertions 1, 2, 4, and 5 FAIL today for the exact values the DIAGNOSIS confirmed at §1: flag fires verbatim, size > 20KB (the flag proves it), ledgers=4 vs candidates=1, hora_ladder=15. Assertion 3 (`candidates.length >= 1`) PASSES today — the hardFloor already worked correctly, which is explicitly labeled "correct behavior" in DIAGNOSIS §2.A. The test suite as a whole fails because four of the five assertions are red.

## 4. Sibling sites

All six other files in `kala_views/` were checked (DIAGNOSIS §4). `elect.ts` is the sole file with the "budget sections declared but JudgmentLedger sub-arrays not covered" shape.

| File | Status | Reason excluded |
|---|---|---|
| `ritual.ts` | Excluded — F-13 (different defect) | Zero sections declared at all; the incompleteness pattern requires at least one section to exist |
| `ahead.ts` | Excluded — not exposed | Never calls `adjudicateCandidates`; zero `JudgmentLedger` refs (grep-confirmed by diagnosis) |
| `priority.ts` | Excluded — not exposed | `kalaBudgetedDualOutput` + `autoDetectTrimmableSections`; no lattice/adjudication usage |
| `explain.ts` | Excluded — not exposed | Same as `priority.ts` |
| `story.ts` | Excluded — not exposed | Own `finalizeMcpBudget`, no lattice engine |
| `now.ts` | Excluded — not exposed | Same as `story.ts` |

## 5. Recurrence guard

Add a coverage test at `platform-mcp/src/tools/kala_views/__tests__/elect_sections_coverage.test.ts` that:
1. Imports (or reconstructs) the `sections` array from `elect.ts` (extract to a named export)
2. Collects every `path` string declared
3. Asserts that **all seven** `JudgmentLedger` array fields (`dosas_present`, `pariharas_applied`, `residual_dosas`, `supporting_factors`, `neutral_annotations`, `convention_only_factors`, `convention_only_keys`) appear in at least one `path` under either `candidates[].judgment_ledger.*` or `lattice_adjudication.ledgers[].*` (after this fix: sections A–G cover the six ledger-level fields; the existing `convention_only_factors` section covers the seventh)
4. Asserts `lattice_adjudication` is handled by the `candidates` setArray sync (tested via mock response with ledger count > candidates count)

This makes adding a new array field to `JudgmentLedger` fail the test unless a matching `TrimmableSection` is also added.

Also add F-122 as a named control row in `platform/scripts/governance/ekv_controls.py` (currently absent — DIAGNOSIS §5).

## 6. Dependencies and rollback

**Other lanes:** `response_budget.ts` is S2 HOT / touched by F-46, F-09, F-17, F-28, F-44, F-12 — **no conflict**: this fix does not touch `response_budget.ts`. `kala_views/elect.ts` also touched by F-125 (unrelated orientation fix, different code region) — builder must confirm no merge conflict before enqueuing PR.

**Rebuild:** None. This is a TypeScript tool-layer fix; `elect.ts` writes no DB rows. Verification = Level-0 shadow run only: invoke the tool against chart `482012f1` at `budget_kb: 20`, confirm exit test assertions pass, log the response JSON as `results/F-122.shadow.log`.

**Migration:** false.

**Rollback:** Revert the added `TrimmableSection` entries (A–G) and the `setArray` sync in `elect.ts`. No data change, no downstream effect.

## 7. Coverage table

| Sub-claim (DIAGNOSIS) | Covered here |
|---|---|
| A — `candidates` 4→1 is correct behavior, not a bug | §2 preserves `hardFloor: true, minKeep: 1`; §3 asserts `candidates.length ≥ 1` |
| B — `hora_ladder`/`neutral_annotations`/`dosas_present`/`residual_dosas`/`convention_only_keys`/`pariharas_applied` survive untrimmed | §2 adds TrimmableSection for each (sections A–G); §3 asserts they are bounded after fix |
| C — `budget_exceeded_after_trim` flag fires verbatim | §3 primary assertion: flag absent after fix |
| D (corrected) — candidates IS hardFloor'd; defect is undeclared fields | §2 preserves existing hardFloor; adds sections for all six undeclared fields |
| E — `lattice_adjudication` absent from `sections` entirely | §2 adds `setArray` sync + per-field ledger sections A–G covering all seven JudgmentLedger arrays; §5 recurrence guard verifies all seven |
| §3 — `kala_lattice_query.ts` FROZEN-adjacent | §2 explicitly scopes all changes to `elect.ts` only |
| §4 — 6 other kala_views files checked | §4 above: all 6 explicitly excluded with reasons |
| §5 — no CL-00 control for F-122 | §5 adds named row to `ekv_controls.py` |
| §5 — F-125 merge-order awareness | §6 flags F-125 status check requirement before enqueue |
