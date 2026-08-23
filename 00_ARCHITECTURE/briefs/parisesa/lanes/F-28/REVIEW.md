---
lane: F-28
stream: S2
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, lanes/F-28/SPEC.md (revision 2), lanes/F-28/DIAGNOSIS.md, lanes/F-28/REVIEW.md (prior pool-1 draft, ratified INCOMPLETE-RETURN, deficiency D1: type widening unspecified). Context: revised spec, second review needed.

Verified all cited file:line directly against /Users/Dev/par-night/main-ro (read-only, origin/main):
- tool_name_bridge.ts:237-262 — read directly; all four branches confirmed verbatim
- shared_types.ts:81-82 — read directly; `content: string` confirmed at line 82
- retrieve/types.ts:62-63 — read directly; `content: string` confirmed at line 63
- types.ts:533 — read directly; `ToolResult { content: string | object }` confirmed
- route.ts:161, 176, 177 — read directly; all three `.content`-as-string callsites confirmed
- Ran grep for ToolBundleResult importers (12 files confirmed) and cross-checked `.content` access pattern: only route.ts reads `.content` from a ToolBundleResult as a string; classical_attribution_lookup_tool.ts uses `.content` only to CONSTRUCT ToolBundleResult objects with string literals, not to READ them.

All verification by line-by-line trace; no code executed.

## Q1 — Does the spec address the mechanism or merely the symptom?

COMPLETE. Revised spec correctly identifies the root cause at `tool_name_bridge.ts:257-260`: the JSON.stringify collapse of a structured multi-array object into a single opaque string before any budget trimmer can see the payload. The 120-char truncation at `response_budget.ts:454` is correctly characterised as working-as-designed. The spec targets the collapse, not the truncation.

## Q2 — Do all DIAGNOSIS sub-claims map to a spec element?

COMPLETE. Coverage table at §8 is exhaustive:
- F-28a → §2b removes root cause making truncation the only option. Mapped.
- F-28b (no override param) → explicitly NOT closed; flagged §7 as separate follow-up. Mapped with stated exclusion reason.
- F-28c (data exists in DB) → n/a, no fix needed. Mapped.
- F-28d (unrecoverable) → §2b makes structured arrays addressable. Mapped.

No unmapped DIAGNOSIS claims.

## Q3 — Would the exit tests genuinely fail on today's code?

YES, both fail, traced against current source:

Test 1: `toToolBundleResults({ content: { ... qa_results: [168 items] }, is_error: false })`
- Input has `content` key → line 257 branch fires (confirmed: `if (typeof content === 'object' && 'content' in content)`)
- `inner` = multi-array object, `typeof inner !== 'string'` → line 259: `JSON.stringify(inner)`
- Returns `[{ content: "<JSON string>" }]`
- `typeof result[0].content === 'string'` → `toBe('object')` FAILS
- `result[0].content.qa_results` → undefined → `toHaveLength(168)` FAILS

Test 2: Confirmed by DIAGNOSIS §1 live reproduction that `mimamsa_calibration_get` returns a response containing `[truncated for budget]` → `not.toContain(...)` FAILS; `qa_results` field unreachable inside collapsed string → FAILS.

## Q4 — Are all sibling sites covered or excluded with a stated reason?

ADEQUATE. DIAGNOSIS §4b names 8 same-shape siblings in L5_mimamsa. Spec §4 explicitly discloses these were not independently live-verified as over-40KB, covers the defect class generically via test 1, and recommends a follow-up census scoped to S3 once the fix is BUILD-verified. Stated exclusion with reason is present. The mechanism fix benefits all 172 handlers uniformly; test 1 is the appropriate generic guard.

## Q5 — Is the recurrence guard adequate?

ADEQUATE. Test 1 is a direct unit test on `toToolBundleResults` that asserts `content` is preserved as an object when the inner value has top-level array fields. This guards the defect class (object-with-array-fields collapsing to string), not a fragile proxy. Any future regression on this branch fails the test immediately.

## Q7 — Are any spec citations unverified assumptions?

All primary citations confirmed independently against current source:

- `tool_name_bridge.ts:237-262`: CONFIRMED verbatim — four-branch function, `toToolBundleResults`, "Single ToolResult" branch at 257-260 matches spec's quoted BEFORE code exactly.
- `shared_types.ts:82`: CONFIRMED — `content: string` at line 82.
- `retrieve/types.ts:63`: CONFIRMED — `content: string` at line 63.
- `types.ts:533`: CONFIRMED — `export interface ToolResult { content: string | object ... }` at line 533.
- `route.ts:161, 176, 177`: CONFIRMED — line 161: `s + r.content.length` inside reduce; line 176: `Math.ceil(r.content.length / 4)`; line 177: `text: r.content`. All three match spec's guard table exactly.
- Reviser's claim "12 files import ToolBundleResult, only route.ts reads .content as a string": INDEPENDENTLY VERIFIED. Grep confirms 12 files; the one additional file with a `.content` access (`classical_attribution_lookup_tool.ts:49`) uses it to construct `ToolBundleResult` objects with string literals — the `.content` at line 49 is `a.content` (an interior field of a source attribution object inside a JSON.stringify call), not a read of `ToolBundleResult.content` as string. Spec claim holds.

**Prior deficiency D1 (type widening unspecified) is closed.** Revised §2a now explicitly specifies widening both canonical definitions (`shared_types.ts:82` and `retrieve/types.ts:63`) from `content: string` to `content: string | Record<string, unknown>`, provides guard patterns for all three `.content`-as-string callsites in route.ts, and confirms blast radius by reviser grep (12 files, only 3 callsites in one file need guards). All spec claims verified against current source. No assumptions remain unverified.

**Secondary observation from prior review (not a return-blocker, preserved for builder awareness):** `autoDetectTrimmableSections` scans to limited depth; after the fix, `qa_results` lives at `results[0].content.qa_results` (depth 3) and would not be auto-detected as a declared trimmable section. Consistent with spec's own §7 caveat — not a spec deficiency.

## Named deficiencies (if INCOMPLETE-RETURN)

None.

## Verdict: COMPLETE
