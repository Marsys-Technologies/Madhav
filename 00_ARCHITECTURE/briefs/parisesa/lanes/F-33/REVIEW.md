---
lane: F-33
stream: S3
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: INCOMPLETE-RETURN
ratified_by: ratifier-1
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, SPEC.md, DIAGNOSIS.md (no REVIEW_LEADS.md present in lane dir). Read source at `/Users/Dev/par-night/main-ro`:
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` (lines 260–592)
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_tajik.ts` (lines 1–240)
- `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_dashas.integration.test.ts` (lines 1–50)
- Grep for `CANONICAL_CHART_ID`, `queryGetDashas`, `judgmentFlag`/`JudgmentFlagEntry` in get_tajik.ts and across the test directory.

All cited line numbers verified live against origin/main source. No code was run (serving-layer TS, no live DB); defect tracing was line-by-line.

## Q1 — Does the spec address mechanism or symptom?

Mechanism. The root cause is precisely identified: `containsDate` (caller-supplied, line 268) and `birthDate` (fetched at lines 451–455) are both in scope inside the `containsDate && systemApplied === 'vimshottari'` block (line 449), but no comparison `containsDate < birthDate` is made, and `judgment_flags` (declared at line 430; only push site is `system_facet_unrecognized` at lines 431–436) has no push for this case — confirmed live. The spec's fix targets the missing comparison and flag, not the symptom (the negative age string). C4's design rationale (pre-birth dasha rows are mathematically correct classical anchors) is preserved by design. This is the right lever.

## Q2 — Every diagnosis sub-claim maps to a spec element?

| Sub-claim | Spec element | Mapped? |
|---|---|---|
| C1: pre-birth as_of_date accepted without rejection | §2a: flag added, query not rejected | YES |
| C2: fully-formed two_pass_verified rows served | §2a: unchanged by design | YES |
| C3: only tell is negative integer in free text | §2a: judgment_flags push adds machine-checkable field | YES |
| C4: fix target is query disclosure, not data correction | §2a: design note explicit, ageAtDate preserved | YES |
| Sibling get_tajik.ts (diagnosis §4) | §2b: parallel flag guard specified | YES |

No unmapped claims.

## Q3 — Would the exit test genuinely fail on today's code?

YES — the test would fail on today's code. Source trace confirms:
- Line 430: `judgment_flags` array declared empty.
- Lines 431–436: ONLY push is `system_facet_unrecognized` (fires only when unknown `system` string is passed — not this case).
- Lines 449–533: `containsDate && systemApplied === 'vimshottari'` block fetches `birthDate` (lines 451–455) and uses it only for `ageAtDate` (lines 471–481) — no comparison against `containsDate`, no flag push.
- Line 585: `...(judgment_flags.length > 0 ? { judgment_flags } : {})` — array is empty, key is entirely absent from response.
- DIAGNOSIS §1 live JSON confirms: no `judgment_flags` key in either call.

So `expect(res.judgment_flags).toBeDefined()` fails today. After the fix `asOfPrecedesBirth` fires and the flag is pushed — test passes.

**However, the test code as written will not compile.** Two concrete errors:
1. `queryGetDashas` is not exported from `get_dashas.ts`. The actual export is `getDashasCapability` (a `CapabilityDescriptor`); the correct invocation pattern — confirmed from `get_dashas.integration.test.ts:18,32–38` — is `getDashasCapability.handler({ chart_id, as_of_date, ayanamsha_id }, undefined)`.
2. `CANONICAL_CHART_ID` is not defined or exported anywhere in the codebase. Every existing test in this directory uses a local `const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'`.

The spec's own routing note claims the test is "concrete and independently verifiable" and "directly executable" by an S5 builder with no access to this session. Both errors are compile-time failures that violate that claim.

## Q4 — All sibling sites covered or excluded with stated reason?

YES. §4 table covers all three files found by the sibling grep:
- `get_dashas.ts` → covered (F-33, §2a).
- `get_graha_yuddha.ts:148` → excluded, stated reason: `birth_date` is the fixed anchor being queried via ephemeris, not compared against a caller-supplied date — correct (verified: function signature is an ephemeris lookup AT birth, no caller-suppliable date compared against it).
- `get_tajik.ts` → covered (§2b).

Spec also notes builder should re-run the grep at build time in case a new file has landed in `L1_ganita/**` since diagnosis — appropriate caveat.

## Q5 — Is there a recurrence guard and does it detect the defect class?

Partially. The two exit tests in §3 are the stated guard. When they compile and run, they detect the defect class correctly (flag absence on pre-birth query vs. flag absence on normal query). The rationale for no lint (two call sites, disproportionate machinery) is stated and reasonable.

But the guard is only as strong as the test compilation — see Q3 deficiencies. Until the test code is corrected to use `getDashasCapability.handler` and a locally-declared chart ID, the guard file cannot enter CI.

## Q7 — Any unverified assumptions or broken citations?

All cited line numbers verified against current source and are accurate within ±1 line (rounding from comment/blank lines):
- `:268` containsDate — CONFIRMED (line 268).
- `:430` judgment_flags declaration — CONFIRMED (line 430).
- `:432-435` system_facet_unrecognized — CONFIRMED (lines 431–436).
- `:448` containsDate block — CONFIRMED (line 449, spec says "Near :448" — accurate).
- `:451-454`/`:455` birthDate fetch — CONFIRMED (lines 451–455).
- `:471-479` ageAtDate — CONFIRMED (lines 471–481).
- `:585` judgment_flags attachment — CONFIRMED (line 585).
- `judgmentFlag` helper import — CONFIRMED (line 29 import, line 432 use).
- `get_tajik.ts:22-30` resolveVarshaYearForDate — CONFIRMED (lines 22–31).
- `get_tajik.ts` call site `:180`/`:185` — CONFIRMED (lines 186–188).
- `get_tajik.ts` has NO `judgment_flags` infrastructure — CONFIRMED (grep returned empty). Spec correctly anticipates this with its §2b caveat.

One minor ambiguity in §2a: "Place this flag FIRST in the array (unshift, or push before the `system_facet_unrecognized` check)." The `system_facet_unrecognized` check runs at lines 431–436, BEFORE `birthDate` is fetched (lines 451–455). A builder cannot push before that check without also moving the birthDate fetch earlier. The practical implementation is `unshift` inside the `containsDate` block — the spec's primary suggestion is correct; the parenthetical alternative is misleading but not blocking (any builder reading the source will reach the same `unshift` conclusion).

**writer_asset / data_delta check (ND-PARISESA-2):** `get_dashas.ts` and `get_tajik.ts` are confirmed serving-layer TypeScript files — they call `query(...)` against already-built tables, carry no `@register`/`WriterBase` pattern. §6's "no rebuild needed" declaration is accurate. No `writer_asset` field applies; `data_delta` is effectively none.

## Named deficiencies (INCOMPLETE-RETURN)

1. **`queryGetDashas` is not a real import** — `get_dashas.ts` exports `getDashasCapability` (CapabilityDescriptor). Correct test invocation: `import { getDashasCapability } from '../get_dashas'` then `getDashasCapability.handler({ chart_id: CHART_ID, as_of_date: '1980-01-01', ayanamsha_id: 'lahiri_chitrapaksha' }, undefined)`. See `__tests__/get_dashas.integration.test.ts:18,32–38` for the exact pattern. Fix: replace `queryGetDashas({...})` with `getDashasCapability.handler({...}, undefined)` throughout §3.

2. **`CANONICAL_CHART_ID` is not defined or exported anywhere** — no shared export of this name exists in the codebase (grep confirmed). All existing tests in this directory declare `const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'`. Fix: add `const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'` at the top of the test file and replace `CANONICAL_CHART_ID` with `CHART_ID` in §3's test code.

## Verdict: INCOMPLETE-RETURN

The mechanism analysis is accurate and complete; all line citations verified; sibling coverage is correct; the data-layer no-rebuild claim is confirmed. The blocking issue is the exit test in §3: two undefined identifiers (`queryGetDashas`, `CANONICAL_CHART_ID`) make it a compile-time failure, which breaks the spec's own "directly executable" guarantee and prevents the guard from entering CI. Both fixes are one-line changes with an existing pattern to copy from.