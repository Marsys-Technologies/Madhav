# F-122 DIAGNOSIS — `kala_elect_get`'s budget trim deletes the actionable layer, keeps the bookkeeping

Stream: S2 MĀTRĀ. Files: `platform-mcp/src/tools/kala_views/elect.ts` (S2 HOT), consuming
`platform-mcp/src/lib/response_budget.ts` (S2 HOT) and `platform-mcp/src/lib/kala_lattice_query.ts`
(S2). Doctrine violated: CLAUDE.md §N.6 (Serving Density Principle) items 1 and 2 — a low-density
bookkeeping layer (`lattice_adjudication.ledgers[]`, `hora_ladder`) survives a budget trim in full
while the confirmed, actionable `candidates[]` slate is cut to a single row.

Read per the Stage-D contract: `PARISESA_EXECUTION_PLAN_v1_0.md` §3 (Stage D — DIAGNOSE) and
CLAUDE.md §N.6, both read before this document was written. Note: F-13 and F-122 share the file
domain (`kala_lattice_query.ts`'s `JudgmentLedger`/`adjudicateCandidates`) but are **two distinct
defects** — F-13 is "no budget control ran at all"; F-122 is "budget control ran, but its
declared sections don't cover the fields that actually blew the budget." No shared root cause;
see §3 for why.

## 1. Live reproduction

Call run verbatim against the live MCP server:

```
mcp__marsys-jis-direct__kala_elect_get({
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa', undertaking: 'business',
  date_range: {start:'2026-08-15', end:'2026-11-12'}, limit: 4,
  native_janma_nakshatra: 'Purva Bhadrapada', budget_kb: 20,
})
```

Full raw response saved to this lane dir as `repro_raw.json` (the `neutral_annotations` array and
the two `factors_not_computed`/`factors_not_in_corpus` census arrays are elided with a comment in
the saved copy for file-size hygiene — their exact counts are given below from direct inspection
of the live, un-elided response).

**Every element of the finding's claim reproduces exactly:**

| Field | Observed |
|---|---|
| `candidate_count` (top-level, pre-trim total) | `4` |
| `.candidates.length` (actually served) | `1` |
| `lattice_adjudication.ledgers.length` (top-level, NOT trimmed) | `4` — one per original candidate `c0..c3` |
| ledger `c3.dosas_present.length` | `12` — matches the finding's "12-row dosha list" exactly |
| ledger `c3.residual_dosas.length` | `10` — matches "10-row residual_dosa list" exactly |
| ledger `c3.neutral_annotations.length` | ≈60, dominated by `hora_*` entries (24-slot daily Chaldean hora cycle × ~2.5 days spanned by the candidate window) — matches "~60 full hora_* neutral_annotation rows" |
| ledger `c3.convention_only_keys.length` | `114` — matches "114 convention_only_keys" **exactly** |
| the one surviving `candidates[0].hora_ladder.length` | `15` — matches "15 hora_ladder entries" exactly |
| `judgment_flags` | `[{"code":"budget_exceeded_after_trim","detail":"20kb budget still exceeded after full trim."}]` — matches the cited flag **verbatim, including the message text** |
| `budget_kb_applied` / `budget_kb_requested` | `20` / `20` |
| `trim_report` | `[{"path":"(trim_report)","original_count":4,"kept_count":1,"reason":"full trim_report omitted to fit budget", ...}]` — the trim mechanism itself got trimmed away (see §3), which is the tell that the true over-budget content lies outside every section it knows how to cut |

This is not an approximate match — every specific number the finding cited (`12`, `10`, `114`,
`15`, the exact `judgment_flags` message) reproduced exactly. **Confirmed, not
`ALREADY-FIXED`.**

## 2. Claim decomposition

| # | Sub-claim | Verdict |
|---|---|---|
| A | A call returned `candidate_count=4` but only ONE candidate object survived into `.candidates` | **TRUE** (§1). This part is *correct behavior*, not a bug — see §3: `candidates` is deliberately `hardFloor: true, minKeep: 1`, and PASS 1/2 correctly floored it to 1 under a tight 20KB budget. |
| B | The same response emitted ~60 full `hora_*` `neutral_annotation` rows, 15 `hora_ladder` entries, a 12-row dosha list, a 10-row residual_dosa list, and 114 `convention_only_keys` — all in full | **TRUE** (§1), and this **is** the bug — none of these survived because of a deliberate design choice; they survived because **nothing declared them trimmable at all** (§3). |
| C | `judgment_flags` includes `'budget_exceeded_after_trim: 20kb budget still exceeded after full trim'` | **TRUE**, verbatim (§1) — direct evidence the trimmer ran its full PASS 1 + PASS 2 + trim_report-degrade + drill_pointers-revert + `truncateLongStringsInPlace` last-resort walk and *still* could not close the gap, because none of those mechanisms ever look inside the fields actually responsible for the overage. |
| D | "Inverted density priority relative to CLAUDE.md N.6 item 2: the candidate slate is the confirmed, highest-density, most-actionable section and should declare `hardFloor` with a `minKeep`" | **PARTIALLY WRONG, corrected in §3.** `candidates` **already declares** `hardFloor: true, minKeep: 1` (`elect.ts:857-868`) — that part of N.6 item 2 is correctly implemented. The real defect is not an inversion of *declared* priorities; it's that the *undeclared* fields (`lattice_adjudication.ledgers[]` in full, plus each surviving candidate's own `hora_ladder` and most of its `judgment_ledger` sub-arrays) are invisible to the trimmer entirely, so they bypass both the hardFloor mechanism and the generic PASS-2 zero-floor — they can never be cut, at any budget. |
| E | "The trimmer's generic biggest-section-first heuristic appears not to be applied to `lattice_adjudication` at all" | **TRUE, and precisely stated** — confirmed in §3: `lattice_adjudication` is genuinely absent from the `sections: TrimmableSection[]` array `elect.ts` passes to `finalizeMcpBudget`. |

Net: the finding's *symptom description* (A, B, C) and its *high-level diagnosis of E* were both
exactly right. Its proposed *mechanism* for D (candidates should be hardFloor'd but isn't) was
backwards — candidates already IS correctly hardFloor'd; the actual defect is a **section-coverage
gap**, not a priority inversion.

## 3. Mechanism — file:line, with the actual declared sections quoted

`handleKalaElectGet` (`elect.ts:573-878`) builds the full response object, computing
`lattice_adjudication` from the **pre-trim** candidate set:

```ts
// elect.ts:626-658 — computed from `windows` (the FULL, untrimmed candidate list = 4 here)
const intervals: CandidateInterval[] = windows.map((w, i) => ({ id: `c${i}`, ... }))
let adjudication: LatticeAdjudication | null = null
try {
  latticeSubstrate = await fetchLatticeSubstrate({...}, principal)
  adjudication = adjudicateCandidates(intervals, latticeSubstrate, { subject_label: ... })
} catch { adjudication = null; latticeSubstrate = null }
const ledgerById = new Map((adjudication?.ledgers ?? []).map((l) => [l.candidate_id, l]))
```

`adjudicateCandidates()` (`kala_lattice_query.ts:576`: `const ledgers = candidates.map((c) =>
buildLedger(c, rows, substrate))`) produces **one full `JudgmentLedger` per original candidate**
— 4 ledgers here, `c0..c3`, each with its own `dosas_present`/`residual_dosas`/
`supporting_factors`/`neutral_annotations`/`convention_only_factors`/`convention_only_keys`
(`kala_lattice_query.ts:175-189`, the `JudgmentLedger` interface).

This is assigned **twice** in the response, once per-candidate and once at the top level:

```ts
// elect.ts:764-789 — per-candidate: pulled from ledgerById, one ledger attached per surviving candidate
const candidates: KalaElectCandidate[] = windows.map((w, i) => {
  ...
  return {
    ...
    hora_ladder: w.hora_ladder ?? [],                       // <- NEVER declared trimmable (see below)
    judgment_ledger: ledgerById.get(`c${i}`) ?? null,        // <- only ONE sub-field of this is trimmable (see below)
    ...
  }
})
...
// elect.ts:812-825 — top level: the SAME 4 ledgers, again, regardless of how `candidates` is later trimmed
const response: KalaElectResponse = {
  ...
  candidates,
  candidate_count: candidates.length,
  ...
  lattice_adjudication: adjudication,   // <- the FULL LatticeAdjudication, ALL 4 ledgers, untrimmed
  ...
}
```

`finalizeMcpBudget` is then called with **exactly three** declared `TrimmableSection`s
(`elect.ts:827-869`, quoted in full — this is the complete list, nothing elided):

```ts
const sections: TrimmableSection<KalaElectResponse>[] = [
  kalaEvidenceTrimmableSection<KalaElectResponse>({ instrument: 'kala_elect_get', hint: '...' }),

  {
    path: 'candidates[].judgment_ledger.convention_only_factors',
    label: 'uncited-convention factor spans (all candidates)',
    minKeep: 0,
    getArray: (c) => c.candidates.flatMap((cand) => cand.judgment_ledger?.convention_only_factors ?? []),
    setArray: (c, kept) => { /* redistributes across candidates[].judgment_ledger.convention_only_factors */ },
    recover: { instrument: 'kala_elect_get', hint: '...' },
  },

  {
    path: 'candidates',
    label: 'candidate windows (with judgment ledgers)',
    minKeep: 1,
    getArray: (c) => c.candidates,
    setArray: (c, kept) => { c.candidates = kept as KalaElectCandidate[] },
    recover: { instrument: 'kala_elect_get', hint: '...' },
    hardFloor: true,     // <- THIS IS CORRECT per N.6 item 2, and it worked (§1: 4 -> 1)
  },
]

const budgeted = finalizeMcpBudget(response as unknown as Record<string, unknown>, {
  maxKb: input.budget_kb ?? 40, sections: sections as unknown as TrimmableSection<Record<string, unknown>>[],
  budgetKbRequested: input.budget_kb,
})
```

**What is declared, exhaustively:** (1) `reading.evidence` (the hardFloor argument-evidence
section from `kala_envelope.ts`), (2) one *nested* array —
`candidates[].judgment_ledger.convention_only_factors` — floorable to 0, and (3) the top-level
`candidates` array itself, `hardFloor: true, minKeep: 1`.

**What is NOT declared, and therefore cannot ever be trimmed by any pass, at any budget:**

1. **`lattice_adjudication` itself** (top-level field, `elect.ts:822`, type `LatticeAdjudication |
   null`) — not a single one of its sub-fields (`ledgers`, `pareto`, `gap_report`, `density`)
   appears anywhere in `sections`. Its `ledgers` array holds the **pre-trim** candidate count's
   worth of full ledgers (4 here) regardless of what happens to `candidates` — this is precisely
   why `.candidates` correctly shrank 4→1 while the response still carried 4 full ledgers' worth
   of `dosas_present`/`residual_dosas`/`neutral_annotations`/`convention_only_keys` under
   `lattice_adjudication.ledgers`.
2. **`candidates[].hora_ladder`** (`elect.ts:179` in the `KalaElectCandidate` interface,
   `elect.ts:777` where it's populated) — no `TrimmableSection` targets this path at all, at any
   nesting.
3. **`candidates[].judgment_ledger.{dosas_present, pariharas_applied, residual_dosas,
   supporting_factors, neutral_annotations, convention_only_keys}`** — only
   `convention_only_factors` (one of seven array fields on `JudgmentLedger`, per
   `kala_lattice_query.ts:175-189`) is covered. The other six, including the two the finding
   specifically cited by count (`dosas_present`=12, `residual_dosas`=10), and
   `convention_only_keys` (114, a *different* field from `convention_only_factors` — a
   deduplicated key list, not the full factor objects) are structurally invisible to the trimmer.

**Why the generic auto-detector doesn't save this either:** `elect.ts` doesn't call
`autoDetectTrimmableSections` at all (it hand-declares its own `sections`), but even if it did,
that helper only descends one level of nesting (`response_budget.ts:508-569`:
`declareIfArray(key, ...)` for top-level arrays, then one more level via
`topVal[nestedKey]`) — `lattice_adjudication.ledgers` and `candidates[].judgment_ledger.*` are
both **two or more** levels deep from the response root, structurally out of that helper's reach
too. This is the same depth limitation noted in F-13's blast radius (§5 there) — a shared,
cross-cutting gap in `response_budget.ts`'s generic mechanism, not something either individual
`kala_views/*.ts` file caused on its own, though each file's hand-declared `sections` list is
still the correct place to close the gap per-tool (as `elect.ts` already does for one of seven
`JudgmentLedger` arrays).

**Confirms the finding's E claim precisely** ("the trimmer's ... heuristic appears not to be
applied to `lattice_adjudication` at all") and **corrects its D claim**: `candidates` is not
missing its hardFloor — it has one, and it worked. The actual defect is that `lattice_adjudication`
(a near-duplicate, pre-trim copy of the same per-candidate data) and most of each surviving
candidate's own ledger/hora_ladder fields were never given ANY declared section, so they sail
through PASS 1, PASS 2 (which only re-floors sections that exist in the list — see
`response_budget.ts:274-282`, `runPass('zero')` iterates `sections`, not the whole object), and
even the last-resort `truncateLongStringsInPlace` (`response_budget.ts:454-492`), which only
shortens individual long *string* values, never shrinks an *array*.

## 4. Sibling census

See F-13/DIAGNOSIS.md §4 for the full `kala_views/*.ts` budget-wiring table. Restated for this
finding's specific question — "which other files build a `JudgmentLedger`-bearing response and
duplicate it at two nesting depths the way `elect.ts` does":

- **`ritual.ts`** (F-13): builds the same `JudgmentLedger` shape (via `adjudicateCandidates`/
  `scoreElectionQuality`) but has **zero** budget wiring at all — no `sections` list exists to
  audit for gaps, because none is declared. Not a sibling of F-122's specific "declared-but-
  incomplete section list" shape; it's the more severe "no section list at all" shape (F-13).
- **`ahead.ts`**: calls `fetchLatticeSubstrate` but never `adjudicateCandidates` — confirmed zero
  `judgment_ledger`/`JudgmentLedger` references anywhere in the file (grep, zero hits). It cannot
  exhibit this defect because it never produces the data shape that causes it.
- **`priority.ts`, `explain.ts`**: use `kalaBudgetedDualOutput` (`shared.ts`), which layers
  `kalaEvidenceTrimmableSection` + `autoDetectTrimmableSections` — no lattice/ledger exposure
  (zero `adjudicateCandidates`/lattice refs in either file), so no sibling risk.
- **`story.ts`, `now.ts`**: have their own `finalizeMcpBudget` call with their own declared
  sections, but zero lattice/adjudication engine usage — different response shape, not exposed to
  this specific "duplicate nested ledger" pattern.

**Conclusion: `elect.ts` is the only file in `kala_views/` with this exact defect shape** (budget
wiring present, but a `JudgmentLedger`-bearing response duplicated at a depth its own declared
sections don't reach). No third sibling exists. The closest relative is F-13 (same underlying
`JudgmentLedger` data type, same file family, structurally different defect — missing budget
control entirely rather than an incomplete section list).

## 5. Blast radius

- **CL-00 regression battery** (`platform/scripts/governance/ekv_controls.py`, 27 named-finding
  checks: F-32, F-72, F-75-77, F-80, F-82-88, F-91, F-96-103, F-105-106, F-109, F-137-138):
  **F-122 is NOT among the 27 controls checked.** No automatic regression protection exists for
  this fix; Stage S should add a dedicated test asserting `lattice_adjudication.ledgers.length`
  and each surviving candidate's `hora_ladder`/`judgment_ledger.*` array lengths are bounded
  under a tight `budget_kb`, plus a `judgment_flags` assertion that `budget_exceeded_after_trim`
  no longer fires at the finding's own repro parameters.
- **Other lanes sharing these files**: `F-46`, `F-09`, `F-17`, `F-28`, `F-44`, `F-12` all touch
  `platform-mcp/src/lib/response_budget.ts` (marked S2 HOT/exclusive by `F-46`'s own
  `NEEDS_LEASE.md` and `F-44`'s `DIAGNOSIS.md` — no conflict, but sequence against those lanes'
  status if the fix needs to touch `response_budget.ts` itself, e.g. to add a generic
  deeper-nesting auto-detect pass rather than hand-declaring every path). `F-125`'s sibling-census
  table also lists `kala_views/elect.ts` for an unrelated B.11-orientation finding — same file,
  different code region, no expected overlap, flagged for merge-order awareness only.
- **`kala_lattice_query.ts` is FROZEN-adjacent** — it is explicitly documented as the shared
  ONE-ENGINE-RULE engine both `elect.ts` and `ritual.ts` consume
  (`kala_lattice_query.ts:11-18,74-76`). The fix for F-122 should live entirely in `elect.ts`'s
  own `sections` declaration (adding `TrimmableSection`s for `lattice_adjudication.ledgers[].*`
  and `candidates[].hora_ladder`/the remaining `judgment_ledger` sub-arrays) — it should **not**
  need to change `JudgmentLedger`'s shape or `adjudicateCandidates`'s behavior, which would risk
  the shared engine both tools and F-13's eventual fix depend on.
- **User-facing impact**: at `budget_kb: 20`, a caller asking for a lean response gets one that
  both (a) discards 3 of 4 candidates from the field it explicitly asked to see, and (b) still
  ships ~20KB+ of duplicate bookkeeping for candidates it can no longer see in the trimmed
  `candidates` array — worse than either purely honoring the budget or purely ignoring it. This
  is the same failure shape CLAUDE.md §N.6 was written to prevent (a budget trim zeroing a
  populated, actionable section while a less-actionable one survives) — confirmed present here in
  the top-level/per-candidate duplication path, which §N.6's authors did not anticipate when
  `candidates` was made `hardFloor: true` (that fix protected the right section from the trimmer's
  own logic; it didn't protect against a second, undeclared copy of the same data sitting
  elsewhere in the same response).
- **No NEEDS-LEASE flag required** — `elect.ts` and `response_budget.ts` are both within S2's
  existing lease per the task brief.
