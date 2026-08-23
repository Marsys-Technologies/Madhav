---
lane: F-09
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, lanes/F-09/SPEC.md, lanes/F-09/DIAGNOSIS.md. No REVIEW_LEADS.md found (does not exist). Read source at /Users/Dev/par-night/main-ro/platform-mcp/src/lib/response_budget.ts (full read, lines 1-650+ covering both the doc-comment block and autoDetectTrimmableSections function). Ran grep for all `hint:` and `date_range|top_k|limit` occurrences in the file to verify the "SOLE call site" claim. Confirmed autoDetectTrimmableSections is exported (line 508). Confirmed TrimmableSection type shape (recover.hint, line 115). This is a non-writer-layer lane (no DB writes); writer_asset/data_delta/RS-A fields are not applicable.

## Q1 — Mechanism or symptom?

MECHANISM. The spec targets the shared helper `autoDetectTrimmableSections` at `platform-mcp/src/lib/response_budget.ts:508-530`, specifically the hardcoded hint template at line 527 — not the symptom on any individual tool. The root-cause sentence correctly names the function, the line, and why the text is wrong (schema-unaware boilerplate names parameters that most callers don't declare). The fix is at the shared-helper level: one line change covers every proxy tool that goes through this path. PASS.

## Q2 — Sub-claim coverage

Diagnosis makes two sub-claims:
1. "recover_via.hint on phala_outlook_get names date_range/top_k/limit which the tool doesn't declare" → covered by SPEC §2 fix at :527 and §7 table row 1. PASS.
2. "same pattern on plan_retrieval" → SPEC §4 and §7 table row 2 argue plan_retrieval is covered structurally since it goes through the same function. DIAGNOSIS §4 explicitly deferred the sibling census to Stage S; SPEC §4 closes it with the shared-helper argument. Verified by grep: only one occurrence of this hint template in the file (line 527). PASS.

Note: DIAGNOSIS §3 cites `platform/src/lib/response_budget.ts:527` (wrong path — missing `-mcp` segment). The SPEC correctly cites `platform-mcp/src/lib/response_budget.ts:527`. This is the DIAGNOSIS's error; the SPEC is accurate.

## Q3 — Exit test fails on today's code?

YES — verified by reading current source. Line 527 reads:
```
hint: `call ${toolName} again with a narrower filter/date_range, or a smaller top_k/limit, to reach the rest of "${path}"`,
```
The test (`expect(sections[0].recover.hint).not.toMatch(/date_range|top_k|limit/)`) asserts the hint does NOT contain those strings. With current code, the hint DOES contain all three → test FAILS today. Test structure is valid: function is exported (line 508), `recover.hint` matches TrimmableSection type at line 115, a 20-item `items` array triggers `declareIfArray` (threshold is length > 10). PASS.

## Q4 — Sibling sites covered?

Spec §4 claims `autoDetectTrimmableSections` is the SOLE call site of this hint template. Verified: grep for `date_range|top_k|limit` in the file returns exactly one hit (line 527). Lines 292 and 409 have `hint: 'full untrimmed response'` (different pattern, for response_format:legacy paths — not the same defect). The function is called at lines 591 and 614 — both callers inherit the fix since it's in the shared body. plan_retrieval excluded from per-tool re-test with explicit stated reason (same function, §4). PASS.

## Q5 — Recurrence guard genuinely detects the defect class?

The exit test checks `.not.toMatch(/date_range|top_k|limit/)` — this directly tests for the exact strings constituting the defect. Any re-introduction of this hint template at the same call site fails the test immediately. The spec additionally flags (§5) an optional repo-wide lint for broader coverage, left to S2's judgment. The test is a real guard, not a proxy. PASS.

## Q7 — Unverified assumptions / bad citations in SPEC?

- `platform-mcp/src/lib/response_budget.ts:508-530` — verified: function at exactly these lines. PASS.
- `:527` — verified: exact line of the hint template. PASS.
- `:495-507` for doc comment — verified: comment block runs lines 494-507 (one line off in citation but content accurately described). Minor; not a deficiency.
- Spec §2: "instrument (line 526) is already correct" — verified: line 526 reads `instrument: toolName,` — the dynamic value, not a hardcoded wrong string. PASS.
- Spec §6 mentions LEDGER_S2.md entries — this is a background reference to an existing ledger document, not a code citation; not checked exhaustively but not a blocking concern.
- No writer_asset, data_delta, or RS-A fields referenced — correctly omitted (no DB-write path in this lane). PASS.

## Named deficiencies (if INCOMPLETE-RETURN)

None.

## Verdict: COMPLETE

All five rubric questions pass. The spec targets the mechanism at the correct file:line, all diagnosis sub-claims map to spec elements, the exit test genuinely fails on today's source (confirmed by reading line 527), the sole-call-site claim is verified by grep, and the recurrence guard accurately detects the defect class. One minor citation imprecision (doc comment starts at line 494, spec says 495) is non-blocking. DIAGNOSIS has a wrong path prefix (`platform/` vs `platform-mcp/`) but the SPEC is correct. Ready for ratification and S2 build.
