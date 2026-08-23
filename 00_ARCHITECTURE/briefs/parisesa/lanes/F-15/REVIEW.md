---
lane: F-15
stream: S2 (MĀTRĀ)
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-15/SPEC.md, F-15/DIAGNOSIS.md, F-14/SPEC.md (authoritative build spec, referenced by companion).
Read source (main-ro, read-only): `registry_bridge.ts` lines 820–870, 1020–1057, 2910–2995, 3009–3077; `lib/response_budget.ts` lines 50–101.
Traced exit-test failure path line-by-line against current source.

## Q1 — Mechanism vs symptom

PASS. The spec addresses all three independent, all-necessary gates: (1) data-table gap — five `DOMAIN_READING_*` maps lack `relationship`/`health` keys (§2a); (2) call-site gap — `assess_marriage` and `assess_health` handlers never invoke `attachDomainCompleteness`/`attachDomainReading` (§2b); (3) universal key-mismatch — `buildAssessResponse` reads `response['completeness']` (a key nothing ever sets) instead of `response['domain_completeness']` (§2c). Mechanism-level, not symptom-level. §2d also covers the silent-no-op disclosure gap when no dossier slice bundle exists.

## Q2 — Every diagnosis sub-claim mapped

PASS.
- C1 (`reading` absent for `assess_marriage`) → §2a + §2b
- C2 (`domain_completeness` absent) → §2a + §2b + §2c + §2d
- C3 (`completeness_directive` absent) → §2a + §2b + §2c
- C4 (root cause = all three gates, not map-key alone) → §2a + §2b + §2c all addressed
- Diagnosis §3 domain-key note (`'relationship'` not `'marriage'`) → §2a + §2b both use `'relationship'` explicitly
- Diagnosis §1 note (key-mismatch affects all four tools) → §2c closes universal fix
- Honest disclosure when no dossier bundle exists → §2d
- deep_dive grounding-drop (diagnosis §3 / F-14 §5 NEW item) → explicitly out-of-scope, cross-referenced in §7 of F-14 and §3 exit test header

No unmapped diagnosis sub-claim found.

## Q3 — Exit test genuinely fails on today's code

PASS. Traced both tests line-by-line against current source:

**Test 1** (`reading digest: all four assess_* tools surface substance-inline reading`):
- `assess_marriage` handler: lines 2989–2990 — `const response = { orientation_context, orientation_ok, ...data }` then immediately `return dualOutputBudgeted(buildAssessResponse(response, 'assess_marriage', ...))`. No `attachDomainCompleteness` or `attachDomainReading` call exists.
- `DOMAIN_READING_FAMILIES` at line 1034–1037: only `{ wealth: ..., career: ... }` — no `relationship` key. `attachDomainReading` at line ~1573 would early-return on `families_total === 0` anyway.
- Result: `grounding.reading` is absent → `expect(grounding).toHaveProperty('reading')` FAILS. Confirmed RED.

**Test 2** (`completeness accounting: honest presence OR honest absence-disclosure, never silent`):
- `attachDomainCompleteness` at line 837: `if (!completeness) return` — bare early return, no `domain_completeness_empty_reason` field set. (Even if called, it isn't called today.)
- `buildAssessResponse` at line 2925: `if (response['completeness'] !== undefined) grounding['completeness'] = response['completeness']` — wrong key; `response['domain_completeness']` is never surfaced into grounding.
- `assess_health` (lines 3071–3072): identical pattern to `assess_marriage` — no attach calls, direct `buildAssessResponse`.
- Result: for `assess_marriage`/`assess_health` the `domain_completeness_empty_reason` field is absent → `expect(grounding).toHaveProperty('domain_completeness_empty_reason')` FAILS. For `assess_career`/`assess_wealth` (which do call attach), `domain_completeness` is silently dropped by the `:2925` key mismatch → `expect(grounding).toHaveProperty('domain_completeness')` FAILS. Confirmed RED.

## Q4 — Sibling sites coverage

PASS. F-15 §4 table covers all five `DOMAIN_READING_*` maps, both missing `assess_marriage` attach calls, `buildAssessResponse` grounding fix, `attachDomainCompleteness` null-return disclosure, and `IMMUNE_HONESTY_FIELDS`. F-14 §4 covers the `health` counterparts in the same commit. No sibling is excluded without a stated reason. The four-tool census (only `assess_wealth`, `assess_career`, `assess_marriage`, `assess_health` exist — confirmed by direct read of the file) is complete.

## Q5 — Recurrence guard

PASS. The exit test iterates all four `assess_*` tools by name. Any future fifth tool that omits the attach calls fails Test 1. Any regression to `buildAssessResponse`'s grounding allow-list fails Test 2. Guard is mechanical, not a weak proxy, runs on every CI push. Recommended static lint (out of scope) noted.

## Q7 — Unverified assumptions / file:line citations

All primary citations verified against main-ro source:
- §2a `:1034-1043`: CONFIRMED. Lines 1034–1043 are the five `DOMAIN_READING_*` maps containing only `wealth`/`career` keys.
- §2b `near :2986-2989` (assess_marriage): CONFIRMED. Lines 2989–2990 show response built and immediately returned; no attach calls.
- §2b `near :3068-3071` (assess_health, from F-14 §2b): CONFIRMED. Lines 3071–3072 identical pattern.
- §2c `:2923-2927`: CONFIRMED. Line 2925 reads `response['completeness']` (wrong key).
- §2d `:835-837`: CONFIRMED. Line 837 is a bare `if (!completeness) return` with no disclosure.
- `IMMUNE_HONESTY_FIELDS` (`response_budget.ts:56-101`): CONFIRMED. File is at `src/lib/response_budget.ts` lines 56–101. Has `domain_completeness` and `completeness_directive` but NOT `domain_completeness_empty_reason` — addition required per §2d.

**ONE minor path deficiency (non-blocking):** F-15 SPEC §2 lists the secondary file as `platform-mcp/src/tools/response_budget.ts`. The actual file is `platform-mcp/src/lib/response_budget.ts` (confirmed by `registry_bridge.ts:63` import: `from '../lib/response_budget.js'`). Since F-14/SPEC.md is the authoritative build spec and uses only the filename `response_budget.ts` without a wrong directory prefix, and the import path in `registry_bridge.ts` itself unambiguously points to `src/lib/`, a builder reading the source would self-correct immediately. This does not block the build.

writer_asset / data_delta / RS-A: not applicable. This is a platform-mcp MCP server presentation layer fix, not a writer-layer fix. §6 explicitly states no asset rebuild, shadow verification only (Level 0). No stale inventory.

## Named deficiencies

None blocking. One observation for the ratifier:
- F-15/SPEC.md §2 wrong secondary path `src/tools/response_budget.ts` (actual: `src/lib/response_budget.ts`). Self-correcting from registry_bridge.ts import; F-14 is the authoritative build spec.

## Verdict: COMPLETE
