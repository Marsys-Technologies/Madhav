---
lane: F-123
stream: S4 (VĀCA — kala_views lease holder; diagnosed in S1, routed per "specs travel; leases don't")
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-3
draft_verdict: COMPLETE
ratified_by: ratifier-3
---

## Method

Read: PROTOCOL.md, SPEC.md (F-123 lane, rewritten post-INCOMPLETE-RETURN), DIAGNOSIS.md, existing REVIEW.md (prior pool-2 pass, ratified INCOMPLETE-RETURN — that pass found SPEC.md was a 104-byte self-referential redirect with no content). No REVIEW_LEADS.md in lane directory.

Source verified at `/Users/Dev/par-night/main-ro`:
- `kala_envelope.ts:268-271` — DrillPointerLike interface: confirmed, no `args` field.
- `kala_envelope.ts:295-297` — `pointerTo(instrument, hint)`: confirmed, 2-param signature only; returns `{ instrument, hint }`.
- `now.ts:1760-1763` — `interpretation_ref: pointerTo('kala_explain_get', '...')`: confirmed, no args payload.
- `now.ts:1752` — triPlane block starts here: confirmed.
- `now.ts:1589` — `const windowFamilies = rawFamilies.length > 0 ? rawFamilies : rawForward`: windowFamilies defined here (in scope at 1752). Import of `kala_envelope.js` at line 87: confirmed.
- `ahead.ts:1836-1839` — `interpretation_ref: pointerTo('kala_explain_get', '...')`: confirmed, no args. Import at line 118: confirmed.
- `priority.ts:383-386` — `interpretation_ref: pointerTo('kala_explain_get', '...')`: confirmed, no args. `domainFilter` at line 378 in scope. Import at line 48: confirmed.
- `explain.ts:656` — `prediction_ref: pointerTo('kala_ahead_get', '...')`: confirmed, instrument is kala_ahead_get (not kala_explain_get).
- `ritual.ts:287` — `intervention_ref: pointerTo('kala_elect_get', '...')`: confirmed.
- `story.ts:564` — `const interpretation_ref = pointerTo('get_domain_reading', '...')`: confirmed, different instrument.
- `elect.ts:740` — `interpretation_ref: pointerTo('get_domain_reading', '...')`: confirmed, different instrument.
- Exit test file `kala_envelope_pointer_args.test.ts`: does NOT exist in source (new file). Correct.

Runtime trace of exit test:
- Test 1: `pointerTo` with cast + 3rd arg at runtime → returns `{ instrument, hint }`, no `args` key → `expect(p).toHaveProperty('args')` RED. ✓
- Tests 2+3: `explainPointerTo` does not exist in source → import fails → both assertions RED. ✓

## Q1 — Mechanism vs symptom

Spec addresses root mechanism: `DrillPointerLike` has no `args` field and `pointerTo` is a 2-param function, so no caller can embed required arguments in a drill pointer. Fix goes to `kala_envelope.ts` (adding the field + typed `explainPointerTo` wrapper) and all three CL-11 caller sites. This is the mechanism, not a symptom patch.

## Q2 — Sub-claim coverage

All diagnosis sub-claims map to spec elements (§7 coverage table verified):
- Claim 1 (kala_explain_get hard-errors on exact call shape): §1 + §2b. ✓
- Claim 2 (chart-scoped pointer; domain-scoped target): §2b primaryDomain derivation + §2a null branch. ✓
- Claim 3 (domain-less explain — no fabricated domain): null branch in explainPointerTo. ✓
- Mechanism (now.ts static pointerTo literal at exact lines): §2b replacement. ✓
- Sibling census (ahead, elect, priority flagged): §4 full table. ✓
- Fix direction A (keep explain.ts contract stable): §2 confirms only envelope + 3 callers touched; explain.ts:586-587 unchanged. ✓
- PAR-F123-NEEDS-LEASE: frontmatter notes S4 routing. ✓

No unmapped sub-claims.

## Q3 — Exit test genuinely fails today

Test 1: calls `pointerTo` cast as `(...a: unknown[]) => Record<string, unknown>` with 3rd arg. JS runtime silently ignores extra args; return value is `{ instrument, hint }` — no `args` key. `expect(p).toHaveProperty('args')` is RED. Confirmed by source: `pointerTo` at lines 295-297 returns only `{ instrument, hint }`.

Tests 2+3: import `explainPointerTo` from `kala_envelope.js` — function not present in source (grep: only `pointerTo`, `noLeverPointer`, `isNoLever` exported in that range). Module import fails at test runtime. Both assertions RED.

All three tests are genuinely RED on today's code.

## Q4 — Sibling sites

All seven sites from sibling census accounted for:
- now.ts:1760 (primary) — fixed §2b. ✓
- ahead.ts:1836 (SIBLING-1) — fixed §2c. ✓
- priority.ts:383 (SIBLING-2) — fixed §2d. ✓
- explain.ts:656 — `prediction_ref: pointerTo('kala_ahead_get', ...)`: different instrument, kala_ahead_get has no required args. Exclusion valid, source confirmed. ✓
- ritual.ts:287 — `intervention_ref: pointerTo('kala_elect_get', ...)`: kala_elect_get has no required domain/bhava. Exclusion valid, source confirmed. ✓
- story.ts:564 — `pointerTo('get_domain_reading', ...)`: different instrument, different defect class. Exclusion valid, source confirmed. ✓
- elect.ts:740 — `pointerTo('get_domain_reading', ...)`: same exclusion, source confirmed. ✓

## Q5 — Recurrence guard

`explainPointerTo(hint, args)` typed wrapper: `args` is `{ domain: string } | { bhava: number } | null` — non-optional in the signature, so TypeScript compile fails at any new call site that omits it. Verifier grep (`grep -r "pointerTo('kala_explain_get'" platform-mcp/src`) finds zero results after the fix (all three uses are replaced with `explainPointerTo`). Guard detects the exact defect class, not a proxy.

## Q7 — Verified assumptions

All `file:line` citations verified against source. One minor imprecision: SPEC §2b states "windowFamilies is fully computed at line 1749, one scope above the triPlane block." In source, windowFamilies is DEFINED at line 1589 (`const windowFamilies = rawFamilies.length > 0 ? rawFamilies : rawForward`); line 1749 is where it is passed to `buildNowReading`. The imprecision is non-blocking — windowFamilies is unambiguously in scope at line 1752 where triPlane is built, and the spec's proposed derivation (`windowFamilies[0]?.domains?.[0]`) is correct. No builder confusion expected.

No `writer_asset`/`data_delta`/RS-A — pure TypeScript MCP layer, no DB writes (SPEC §6 confirms: "No rebuild, pure MCP TypeScript layer; no data written").

## Named deficiencies (if INCOMPLETE-RETURN)

N/A

## Verdict: COMPLETE
