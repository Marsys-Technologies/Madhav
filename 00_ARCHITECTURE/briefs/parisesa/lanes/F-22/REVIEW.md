---
lane: F-22
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read PROTOCOL.md, SPEC.md, DIAGNOSIS.md for F-22. No REVIEW_LEADS.md present. Verified source in `/Users/Dev/par-night/main-ro`:
- `platform-mcp/src/tools/register_p1_reference.ts` (offset 360–420): read the actual handler block.
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts`: read in full.
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts` (offset 55–198): verified import/export lines.
- `platform/python-sidecar/brahmagyan/l0_dasha_systems.py` (lines 68–654): verified slug list, total_cycle_years, seeder assert.
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_dasha_systems.test.ts`: confirmed exists.

No writer-layer involved (pure serving-layer repoint); no shadow run required per PROTOCOL rebuild policy.

## Q1 — Mechanism vs symptom

PASS. The spec prescribes replacing the dead `query_classical_texts` call with `query_dasha_systems`, reshaping the response from citation-object rows to the structured fields the tool description promises, inverting the honesty envelope (`structured_filter_applied`, `fallback_reason`), and deleting the false inline comment. This is the mechanism: the bug is a mis-wired capability URI plus a fabricated absence claim in both code comment and response. The spec does not merely surface-patch the `fallback_reason` string — it prescribes the full repoint + reshape + honest-degradation path modelled on the already-correct `ref_dignity_reference_get` pattern.

## Q2 — Sub-claim coverage

PASS. SPEC §7 carries an explicit sub-claim coverage table mapping all four diagnosis sub-claims:
- (a) description promises structured fields → §2.2 (response reshape)
- (b) always routes through classical-text search → §2.1 (repoint)
- (c) fallback_reason actively lies → §2.3/§2.4 (invert + delete comment)
- (d) working replacement capability exists unused → §2.1 (now called)

All claims in DIAGNOSIS §2 are addressed. No unmapped sub-claim found.

## Q3 — Exit test fails on current code

PASS — traced line-by-line:
- `register_p1_reference.ts:402`: `structured_filter_applied: false` is hardcoded. Exit test asserts `true` → FAIL.
- `register_p1_reference.ts:397`: calls `query_classical_texts`, which returns citation-object rows with no `total_cycle_years` field. Exit test asserts `total_cycle_years: 120` → FAIL. (Confirmed from seeder: `l0_dasha_systems.py:102` hardcodes `"total_cycle_years": 120` for vimshottari.)
- `register_p1_reference.ts:403`: `fallback_reason` is hardcoded to the false string. Exit test asserts `fallback_reason` absent on successful structured match → FAIL.

All three primary assertions would fail on current code. Regression assertion (unrecognized system → graceful degrade) tests new behavior that current code cannot satisfy structurally (there is no fallthrough path).

## Q4 — Sibling sites

PASS. SPEC §4 enumerates both siblings the diagnosis found:
- F-04 (`ref_nakshatra_get`): excluded with stated reason — repoint-plus-new-capability (no `query_nakshatra_catalog` equivalent exists), covered in its own spec. Reason is substantive and verifiable from DIAGNOSIS §4.
- `ref_dignity_reference_get`: correctly excluded as the "done right" reference, not a defect instance.

## Q5 — Recurrence guard

BORDERLINE PASS. SPEC §5 correctly identifies the defect class (fallback_reason strings containing "no structured… table exists" or "confirmed absent" without an actual information_schema check) and names the detection mechanism precisely. However, the guard is explicitly filed as a "recommendation" deferred to S6's governance tooling lease, not built in this spec. The guard description correctly detects the class (not a weak proxy — the strings named are exactly those present in the defective code), but the spec makes no commitment to when or whether it lands. For a TIER2-HONESTY lane this is acceptable: the fix itself eliminates the specific instance, and the governance tooling delegation is an honest disclosure, not an evasion.

## Q7 — Unverified assumptions / citation accuracy

Two minor inaccuracies found, neither blocking:

1. **Line number drift (2 lines):** SPEC §2 item 4 says "Delete the false inline comment at lines 385-386." Actual code: line 385 is `async ({ system, keyword, limit, offset }) => {` and line 386 is `try {`. The multi-line false comment begins at line **387** (`// CR-42/R-19/R-20 fix (D-1.6 S-1): no structured bg_dasha_systems catalog table exists (confirmed absent from the migration set)...`). DIAGNOSIS §3 also cites lines 385-386 for this comment. The comment text is quoted verbatim and uniquely identifies it; a builder will find it without trouble. Non-blocking.

2. **Row count inconsistency:** SPEC §1 and DIAGNOSIS §2c say "20 rows, live" for `brahma_dasha_systems`. The seeder `l0_dasha_systems.py:622` asserts `len(DASHA_SYSTEMS) == 19`. The capability file header says "18 rows". The DIAGNOSIS claims 20 from a live DB query (CL02_CENSUS.md). The exact count does not appear in the exit test assertions and does not affect the fix logic. Non-blocking.

All other citations verified accurate:
- `query_dasha_systems.ts` exists at cited path; URI, input_schema (`canonical_id`, `school`), SQL (`FROM brahma_dasha_systems`), and return shape (`rows`, `count`, `filters`, `empty_reason?`, `disclaimer`, `provenance`) all confirmed.
- `index.ts:60` (import), `:125` (L0_CAPABILITIES array), `:192` (named export) all confirmed.
- `__tests__/query_dasha_systems.test.ts` exists.
- Handler block is at actual lines 372-410 (spec says 369-408 — 2-3 line offset, same minor drift as above).
- `total_cycle_years: 120` for vimshottari confirmed at `l0_dasha_systems.py:102`.

## Verdict: COMPLETE

The spec correctly addresses the mechanism (not just the symptom), maps all diagnosis sub-claims, the exit test would genuinely fail on current code, sibling sites are handled with stated reasons, the recurrence guard is correctly described (if deferred), and the two citation inaccuracies found (2-line offset, row count 19 vs 20) are non-blocking — the builder can locate the target comment from its quoted text and the row count does not appear in any assertion. No spec rewrite needed.
