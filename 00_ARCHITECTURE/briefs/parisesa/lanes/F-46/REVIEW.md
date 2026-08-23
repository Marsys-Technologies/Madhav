---
lane: F-46
stream: S2
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Post-revision re-review. Read: PROTOCOL.md, lanes/F-46/SPEC.md (revised), lanes/F-46/DIAGNOSIS.md, lanes/F-46/REVIEW.md (prior pool-1 INCOMPLETE-RETURN, ratified), lanes/F-46/NEEDS_LEASE.md. Source verified at /Users/Dev/par-night/main-ro/platform-mcp/src/:
- response_budget.ts lines 361-444 (finalizeMcpBudget confirmed), 570-598 (applyAutoBudgetToEnvelope confirmed, doc-comment at 571-583)
- register_p1_ganita.ts lines 155-170 (dualOutput, call site at 162 confirmed)
- register_p1_synthesis.ts lines 170-184 (dualOutput, call site at 177 confirmed)

Prior verdict carried two named deficiencies: (1) test 1 assertion path res.content.trim_report — should be res.trim_report; (2) test 2 path res.content.budget_kb_applied — should be res.budget_kb_applied. Checked current SPEC.md §3 against both.

## Q1 — Mechanism vs symptom

PASS. Unchanged from prior review. The spec correctly identifies the mechanism: both dualOutput helpers call applyAutoBudgetToEnvelope (which only appends trim_report) instead of finalizeMcpBudget (which additionally sets budget_kb_applied and merges drill_pointers). Fix replaces the weaker function at both call sites — root-cause, not symptom.

## Q2 — Sub-claim → spec element mapping

PASS. Unchanged.
- F-46a (no budget_kb_applied/requested): §2a+§2b via finalizeMcpBudget:380-381. ✓
- F-46b (recover_via not merged to drill_pointers): §2a+§2b via finalizeMcpBudget:384. ✓
- F-46c (scope — 19 tools, 2 suspects refuted): §4 + regression-guard test. ✓
- Lease routing: NEEDS_LEASE.md confirms conductor resolved as ordered handoff per LEASES.json (register_p1_ganita.ts → S1; register_p1_synthesis.ts → S5→S4 chain). SPEC §6 covers this. ✓

## Q3 — Exit test fails today?

PASS (both prior deficiencies fixed).

Deficiency 1 fixed: SPEC §3 test 1 assertion 1 now reads `expect(res.trim_report.length).toBeGreaterThan(0)` with explicit comment "trim_report is at envelope top level, not inside content". Source confirms: applyAutoBudgetToEnvelope line 596 writes `envelopeObj['trim_report'] = [...]` directly on the envelope object. DIAGNOSIS live JSON confirms trim_report is present at envelope top level today. This assertion PASSES today (trim did happen). ✓

Deficiency 2 fixed: SPEC §3 test 2 final assertion now reads `expect(res.budget_kb_applied).toBe(40)` with explicit comment "budget_kb_applied is set on envelope by finalizeMcpBudget (response_budget.ts:380), not inside content". This assertion PASSES today for kala_projections_get (already on strong path). ✓

Test 1 failure trace (today vs after fix):
- `res.trim_report.length > 0`: PASSES today (trim_report populated at envelope top) AND after fix. ✓ stable.
- `res.budget_kb_applied` (toHaveProperty): FAILS today — applyAutoBudgetToEnvelope never sets this field. After fix (finalizeMcpBudget:380): PASSES. ✓ correct red/green.
- `res.drill_pointers.length > 0`: FAILS today — confirmed [] in DIAGNOSIS live JSON. After fix (finalizeMcpBudget:384 mergeTrimPointersIntoPointers): PASSES. ✓ correct red/green.

Test 2: PASSES today (kala_projections_get already uses finalizeMcpBudget via register_p1_aliases.ts). Must continue to pass after fix — fix does not touch register_p1_aliases.ts. ✓

## Q4 — Sibling sites

PASS. Unchanged. All 19 affected tools (13 ganita + 6 synthesis) covered by the two dualOutput function replacements. Two refuted corpus suspects (kala_projections_get, mimamsa_lel_query in register_p1_aliases.ts) explicitly excluded with stated reasons and guarded by regression test.

## Q5 — Recurrence guard

MODERATELY PASS. Unchanged. §5 recommends deleting applyAutoBudgetToEnvelope once both call sites are replaced (zero callers remaining, confirmed by DIAGNOSIS §4 grep — exactly 2 real call sites). Deletion eliminates the defect class structurally. Conditional phrasing acceptable.

## Q7 — Unverified assumptions / file:line citations

PASS. All primary citations verified against current source:
- response_budget.ts:584-598 (applyAutoBudgetToEnvelope): CONFIRMED exactly as quoted in DIAGNOSIS §3
- response_budget.ts:361-444 (finalizeMcpBudget span): CONFIRMED
- response_budget.ts:370 (applyResponseBudget call inside finalizeMcpBudget): CONFIRMED
- response_budget.ts:380-381 (budget_kb_applied, budget_kb_requested assignments): CONFIRMED
- response_budget.ts:384 (mergeTrimPointersIntoPointers call): CONFIRMED
- register_p1_ganita.ts:162 (applyAutoBudgetToEnvelope call): CONFIRMED
- register_p1_synthesis.ts:177 (applyAutoBudgetToEnvelope call): CONFIRMED

No writer_asset / data_delta / RS-A assessment needed: code-path-only lane, no writer-layer assets touched.

## Named deficiencies

None. Both deficiencies from the prior INCOMPLETE-RETURN verdict are resolved in the revised SPEC.md.

## Verdict: COMPLETE

All five rubric questions pass. The revised spec correctly fixes both exit-test path errors identified in the prior review. Mechanism analysis, claim mapping, sibling coverage, recurrence guard, and all line citations are verified against current source. Fix shape (one-line swap at each dualOutput call site) matches the proven pattern at register_p1_aliases.ts:188 and is structurally sound. Ready for BUILD per the two-piece sequencing in §6.
