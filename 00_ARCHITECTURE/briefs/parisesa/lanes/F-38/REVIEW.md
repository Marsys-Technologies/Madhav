---
lane: F-38
stream: S1 DVARA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-38/SPEC.md, F-38/DIAGNOSIS.md. No REVIEW_LEADS.md found.
Read source at /Users/Dev/par-night/main-ro:
- platform-mcp/src/tools/kala_views/now.ts (2149 lines, full grep + targeted reads)
- platform-mcp/src/lib/authz.ts (48 lines, read in full)
- platform-mcp/src/tools/dossier.ts (lines 44-48, 882-893)
- platform-mcp/src/tools/phala_outlook.ts (lines 260-275)
- platform-mcp/src/tools/chart_selection.ts (lines 200-213)
- Grep for remoteAuthorize across all kala_views/*.ts files
- Grep for AUTHZ_DENIED/ENTITLEMENT_DENIED across all tools/

No live MCP call was re-run (not in scope for reviewer); exit-test failure traced line-by-line against source.

## Q1 — Mechanism vs. symptom

COMPLETE. The spec correctly identifies the mechanism: `now.ts`'s handler
(`registerKalaNowGetTool`, confirmed at lines 2134-2149) calls `computeKalaNow` directly
without any `remoteAuthorize` gate, unlike 7+ named siblings. The symptom (raw HTTP 404
string leaking in `panchanga_native_context_error`) is correctly traced to its source:
line 2012 `panchanga_native_context_error: nativeContextErrorDetail`, which is only reached
because no gate short-circuits the substrate calls. Mechanism addressed, not just symptom.

The SPEC's §0 correction to the DIAGNOSIS is also verified: `callRegistryCapability` at
`now.ts:120` calls `${PLATFORM_URL}/api/retrieval/capability` (confirmed source-read), NOT
`/api/mcp/primitives/[tool]` — so the original DIAGNOSIS lease-note (fix in route-level
middleware) was wrong, and the SPEC's re-direction to `now.ts` is correct.

## Q2 — Sub-claim coverage

COMPLETE. DIAGNOSIS §2 has exactly 3 sub-claims; SPEC §7 provides a coverage table mapping
all three:
1. "no entitlement/existence check before substantial work" → SPEC §2 adds remoteAuthorize gate before Promise.all substrate dispatch
2. "raw upstream HTTP error string leaks verbatim" → SPEC §2: gate short-circuits before call_panchanga_service is ever invoked
3. "caller receives no clean signal" → SPEC §2+§3: one clean AUTHZ_DENIED envelope replaces 15-way partial-failure stitch

No unmapped sub-claims.

## Q3 — Exit test genuinely fails on today's code

TRACED (line-by-line, no live re-run needed):

`mcp__marsys-jis-direct__kala_now_get({chart_id:'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'})`

Code path in today's source:
1. `registerKalaNowGetTool` (now.ts:2134): parses params, checks `!input.chart_id` (UUID is non-empty → passes)
2. Calls `computeKalaNow(input.chart_id, ...)` with NO remoteAuthorize call anywhere (grep confirmed: zero matches for remoteAuthorize in now.ts)
3. Inside computeKalaNow: `callRegistryCapability` and `call_panchanga_service` fire against a nonexistent chart_id
4. panchanga call 404s → `nativeContextError` set at now.ts:1612
5. `nativeContextErrorDetail` = `"HTTP 404: Chart '...' not found"` (now.ts:1613, confirmed)
6. String interpolated at now.ts:1823, placed verbatim on envelope at now.ts:2012
7. Handler returns `dualOutput(result, TOOL_NAME)` (now.ts:2144) — an ok-shaped envelope with the raw 404 string

Conclusion: exit test WOULD FAIL today — no AUTHZ_DENIED returned, raw 404 string present. CONFIRMED.

## Q4 — Sibling sites covered

ACCEPTABLE. SPEC §4 explicitly lists 4 unresolved siblings (explain, ahead, elect, story in
kala_views/) and provides a stated reason for exclusion: each is a separate handler requiring
its own independent trace, and the current spec's fix is file-scoped to now.ts only.
Source-verified: grep for remoteAuthorize in all kala_views/*.ts returns ZERO matches — all
four siblings also lack the gate. The spec's recommendation to run a census before closing
the finding family is correct and concrete. Exclusion-with-stated-reason meets Q4.

## Q5 — Recurrence guard

WEAK-BUT-ACCEPTABLE. SPEC §5 recommends a lint rule requiring every `kala_views/*.ts` with
`scope: per_chart` to import remoteAuthorize. The guard is not built and not required (flagged
as VERIFIER's/conductor's call). The defect class is mechanical (import-then-call missing),
and the proposed lint rule would detect it exactly. Acceptable given the fix itself is a
two-line addition and the spec is honest that §5 is a recommendation. If VERIFIER requires
the lint rule before COMPLETE, that is the ratifier's call, not a blocker here.

## Q7 — Unverified assumptions / file:line citations

All material citations verified against source:
- now.ts:120 `callRegistryCapability` calling `/api/retrieval/capability` — CONFIRMED
- now.ts:1613 `nativeContextErrorDetail` assignment — CONFIRMED
- now.ts:1823 interpolation into narrative string — CONFIRMED
- now.ts:2012 `panchanga_native_context_error: nativeContextErrorDetail` on envelope — CONFIRMED
- dossier.ts:48 `import { remoteAuthorize } from '../lib/authz.js'` — CONFIRMED
- dossier.ts:887 AUTHZ_DENIED message in error object — CONFIRMED
- phala_outlook.ts:266 AUTHZ_DENIED early-return — CONFIRMED (exact line)
- phala_event_anchors.ts:315, mechanism_retrodiction.ts:115, mimamsa_lel_intake.ts:211 — CONFIRMED via grep
- authz.ts fail-closed catch — CONFIRMED; SPEC cites 'authz.ts:44' but actual `catch { return false }` is lines 45-46 (off-by-one, trivial)
- Relative import path `'../../lib/authz.js'` for now.ts (two dirs from platform-mcp/src/lib/) — CONFIRMED correct

One minor inaccuracy: authz.ts line 44 is `return data.authorized === true`; the catch block is lines 45-46. Non-material — the behavior described is correct.

The SPEC's acknowledged Stage-B ambiguity (errOut shape vs. direct `{ content, isError }` sibling pattern) is intentional, not a deficiency — the spec explicitly defers to Stage B and constrains the outcome (must match sibling convention). Builder is responsible for reconciling.

writer_asset / data_delta / RS-A: NOT APPLICABLE. F-38 is a TypeScript tool-gate fix (CL-19), not a writer-layer lane. No rebuild policy applies.

## Verdict: COMPLETE

The spec addresses the mechanism precisely, all DIAGNOSIS sub-claims are mapped, the exit test fails on current source (traced), sibling exclusions have stated reasons, the recurrence guard is present as a recommendation (VERIFIER may escalate), and all material citations check out. One trivial line-number inaccuracy (authz.ts:44 vs 45-46) is non-material. No named deficiencies.
