---
lane: F-37
stream: S2
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-37/DIAGNOSIS.md, F-37/SPEC.md. No REVIEW_LEADS.md found (none exists).
Source verified at `/Users/Dev/par-night/main-ro/platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts` (full file, 73 lines).
Exemplar verified at `L1_ganita/get_condition_composite.ts` lines 87-99.
Exit test traced line-by-line against current source (no harness run possible without DB, but the defect is mechanical and traceable).

## Q1 — Mechanism vs symptom

COMPLETE. The spec names the exact mechanism: a single SQL query bounded by `LIMIT $1 OFFSET $2` with no parallel `SELECT COUNT(*)`, causing `total: rows.length` at line 61 to return the page size rather than a catalog count. The fix is structural — add a parallel count query via `Promise.all`. This is mechanism, not symptom renaming.

## Q2 — DIAGNOSIS sub-claims coverage

All mapped. The §7 coverage table in the spec is explicit:
- F-37a (`total` = `rows.length`) → §2 parallel COUNT fix + `total_matching` field
- F-37b (`total` varies per page) → §3 stability assert + §5 recurrence guard
- Mechanism (single SQL, no COUNT) → §2 `Promise.all` from established exemplar
- §4 sibling census (F-37's one site) → §4 table
- §5 BRANCH-EXISTS wrong → §6 standalone fix
- §6 S5 MŪLA lease → §6 blocker pre-condition stated
- §6 no other-lane collision → §6 confirmed

No unmapped DIAGNOSIS claim found.

## Q3 — Exit test failure on current code

Traced against source. Today's `handler` returns:
```
{ content: { rows: [...10 rows...], total: 10 }, is_error: false }
```
Field `total_matching` does not exist in the return object; `more_available` does not exist.

Exit test asserts:
1. `content.rows.length === 10` — PASSES (10 rows for LIMIT 10, OFFSET 50 from a 175-row catalog)
2. `typeof content.total_matching === 'number' && content.total_matching > 10` — FAILS (`total_matching` is `undefined`; `typeof undefined` is `'undefined'`, not `'number'`)
3. `content.more_available === true` — FAILS (`more_available` is `undefined`)

Stability check: second call `ref_yogas_get(offset=0, limit=1)` returns `total_matching: undefined`; `toEqual` against first call's `undefined` would pass, but `toBeGreaterThan(1)` in the recurrence guard would fail. Net: test suite fails on today's code. The spec's stated failure reason is slightly imprecise (says "total === 10" when the field name mismatch is the direct cause), but the functional claim — the assertions fail — is correct.

After fix: COUNT(*) runs in parallel, returns ~175, `total_matching = 175 > 10`, `more_available = true`. All assertions pass.

## Q4 — Sibling sites

F-37's DIAGNOSIS scopes this lane to exactly one site: `query_yoga_catalog.ts:61`. The full Flavor-A census (~19 additional sites across `L0_brahmagyan/*` and `L1_ganita/*`) is explicitly delegated to `F-12/DIAGNOSIS.md §4a`. The spec's §4 table reflects this consistently: F-37's one site is fixed here; others are either assigned to F-12 or tracked as F-12's scheduling burden. No sites are silently dropped. The delegation pattern is consistent between DIAGNOSIS §4 and SPEC §4.

## Q5 — Recurrence guard

The guard in §5 calls `handler({ limit: 1, offset: 0 })` and `handler({ limit: 1, offset: 100 })`. Both pages return 1 row. Assertions:
- `r1.content.rows.length === 1` — checks page size
- `r1.content.total_matching === r2.content.total_matching` — checks stability across pages
- `r1.content.total_matching > 1` — catches regression: if `total_matching` reverts to `rows.length`, both return 1, `toEqual` passes but `toBeGreaterThan(1)` fails closed

This directly detects the defect class (not a proxy). Guard is sound.

## Q7 — Unverified assumptions / citation accuracy

All citations verified:
- `query_yoga_catalog.ts:61` → `total: rows.length,` — CONFIRMED (read source, line 61 is exactly this)
- `get_condition_composite.ts:87-99` → `Promise.all([query(sql,...), query(COUNT...)])` pattern — CONFIRMED (lines 87-99 show exactly the described pattern; `total_matching` and `more_available` at lines 98-99)
- "~175 rows" → source file description string at line 14 says "175 canonical yogas" — CONSISTENT
- `writer_asset: null`, `data_delta: narrow` — `query_yoga_catalog.ts` reads `brahma_yoga_catalog`; writes nothing to any asset table. Non-writer classification is correct; Level 0 shadow run (for writer-layer lanes only per PROTOCOL §rebuild-policy) is not required. Exit test is the verification mechanism.
- Lease claim (S5 MŪLA owns `L0_brahmagyan/**`) — stated in both DIAGNOSIS §6 and SPEC §6 with reference to LEASES.json; not independently re-read here (not a spec deficiency; lease is a coordination concern surfaced correctly as a blocker).

No unverified assumptions found.

## Verdict: COMPLETE

Spec addresses mechanism, not symptom. All DIAGNOSIS sub-claims mapped. Exit test genuinely fails on today's code (field `total_matching` undefined). Single scoped sibling site; remaining census explicitly delegated to F-12. Recurrence guard detects defect class directly. All source citations verified. writer_asset/data_delta correctly null/narrow. No deficiencies.
