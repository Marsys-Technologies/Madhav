---
lane: F-134
stream: S3
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, F-134/SPEC.md (revised, cycle 1), F-134/DIAGNOSIS.md, prior REVIEW.md (pool-1, INCOMPLETE-RETURN on D1+D2). No REVIEW_LEADS.md present.
Read source at /Users/Dev/par-night/main-ro:
- reading_checklist.ts lines 240-351 (interfaces 245-263, fetchGocharaSweep 274-351, query 316-333, upcoming_window_count :334, windows map :339-347)
- register_d9_judgment.ts lines 1150-1165 (fetchGocharaSweep call :1154, gochara_domain_not_covered flag :1155-1161) and 1245-1260 (gochara_sweep block :1248-1259)
- register_d8_assess_domain.ts lines 1188-1204 (gochara_sweep block :1192-1203; call confirmed at :1096)
- envelope.ts lines 1096-1107 (JUDGMENT_FLAG_CODES excerpt; 'gochara_domain_not_covered' at :1101)
Traced exit test assertions against live interfaces (mock-only test, no live DB needed).
Verified D1 and D2 closure from prior pool-1 review.

## Q1 — Mechanism vs. symptom

PASS. Spec correctly names the mechanism: `fetchGocharaSweep` uses a pure interval-overlap predicate (`window_end >= $3 AND window_start <= $4`, :326) with ranking by `ABS(signed_intensity)` (:330); neither selection, ranking, nor row mapping (:339-347) ever compares `peak_date` against `start`. The fix is placed at the single shared function (reading_checklist.ts), propagating to both callers. Not symptom-patching.

## Q2 — Diagnosis sub-claims mapped

PASS. All four C1-C4 sub-claims map to spec elements per §8's coverage table:
- C1 (upcoming_window_count=3, window_range from now) → §2a field left as-is + §7 rationale for not redefining it
- C2 (top-ranked window peaked >1 yr ago) → §2a is_past_peak per-window + §2b gochara_top_window_already_peaked flag keyed on windows[0]
- C3 (no structural distinction between past-peaked and future windows) → §2a is_past_peak on every element of top_windows
- C4 (no flag anywhere) → §2a + §2b/§2c passthrough of past_peak_window_count into both served responses + §2d envelope.ts registration
No unmapped diagnosis claim.

## Q3 — Exit test fails on today's code

CONFIRMED. Verified against live source:
- GocharaSweepWindow (:245-253): no is_past_peak field — result.windows[0].is_past_peak → undefined (not true)
- GocharaSweepResult (:255-263): no past_peak_window_count field — result.past_peak_window_count → undefined (not 1)
- fetchGocharaSweep body (:334-347): no isPastPeak logic, no past_peak_window_count assignment — all four assertions fail
- TypeScript compile rejects .is_past_peak property access (not in interface) — stronger red than runtime failure
Exit test is a genuine red on today's code. Internal logic cross-checked: for as_of_date='2026-08-16', peak_date='2025-04-27' → '2025-04-27' < '2026-08-16' → true ✓; peak_date='2030-08-14' → '2030-08-14' < '2026-08-16' → false ✓; null → null ✓; past_peak_window_count=1 ✓; upcoming_window_count=3 ✓. Logic is internally consistent.

## Q4 — Sibling sites

PASS. Live grep confirms exactly two importers of fetchGocharaSweep under layers/:
- register_d9_judgment.ts (:1154) → covered §2b (past_peak_window_count passthrough + new flag)
- register_d8_assess_domain.ts (:1096) → covered §2c (past_peak_window_count passthrough; is_past_peak flows through withSweepDisclosure automatically)
All four assess_* tools share register_d8_assess_domain.ts's single dispatch path — covered for free. No third call site exists.

## Q5 — Recurrence guard

PASS. Exit test type-checks against GocharaSweepWindow/GocharaSweepResult directly — dropping or failing to populate is_past_peak or past_peak_window_count breaks both TypeScript compile and runtime assertions. Single shared function architecture means future callers inherit the fix. No per-site guard needed; type signature is the guard.

## Q7 — Unverified assumptions / file:line citations

PASS (revised spec). All citations verified against live source:
- reading_checklist.ts: interfaces :245-253/:255-263 ✓, function :274 ✓, start binding :280 ✓, query :316-333 ✓, WHERE predicate :326 ✓, ORDER BY :330 ✓, upcoming_window_count :334 ✓, windows map :339-347 ✓
- register_d9_judgment.ts: fetchGocharaSweep call :1154 ✓, gochara_domain_not_covered flag :1155-1161 ✓, gochara_sweep block :1248-1259 with withSweepDisclosure at :1257 ✓ (D2 closed: spec now shows correct withSweepDisclosure form in both Current and Fixed blocks)
- register_d8_assess_domain.ts: call :1096 ✓, gochara_sweep block :1192-1203 with withSweepDisclosure at :1201 ✓ (D2 closed)
- envelope.ts: 'gochara_domain_not_covered' at :1101 ✓, comment at :1102 ✓; §2d insert instruction is actionable (D1 closed: envelope.ts now listed as §2d, 4th file to change)
One cosmetic note: spec cites 'kp_cusp_chain_unavailable' as the start of the envelope.ts:1099-1103 excerpt, but live source has that entry at :1100 (the excerpt header range is off by one). The operative instruction — "insert after 'gochara_domain_not_covered' (line 1101)" — is accurate and unambiguous; this is not a builder-blocking deficiency.
writer_asset/data_delta/RS-A: spec declares no DB migration, no schema change, no asset rebuild (peak_date is already selected; fix is pure application-layer). data_delta: narrow (additive fields only). Consistent with TIER4-POLISH classification and rebuild policy (no rebuild needed, shadow run only per PROTOCOL.md).

## Prior deficiencies resolved

D1 [CRITICAL — envelope.ts omitted from §2]: CLOSED. Revised spec §2d adds envelope.ts as 4th file; correct insertion point (after 'gochara_domain_not_covered' at line 1101) verified against live source.
D2 [SIGNIFICANT — stale withSweepDisclosure code blocks]: CLOSED. §2b 'Current' now shows `top_windows: withSweepDisclosure(gochara.windows ?? [])` (verified at register_d9_judgment.ts:1257). §2c 'Current' now shows `top_windows: withSweepDisclosure(t5Gochara.windows ?? [])` (verified at register_d8_assess_domain.ts:1201). F-119 regression risk is eliminated.

## Verdict: COMPLETE