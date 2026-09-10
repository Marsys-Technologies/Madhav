---
lane: F-45
stream: S2
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-45/SPEC.md, F-45/DIAGNOSIS.md, F-45/NEEDS_LEASE.md (no REVIEW_LEADS.md present).
Verified against `/Users/Dev/par-night/main-ro` source (read-only mirror of origin/main).
Verified files and line ranges:
- `register_p1_aliases.ts` at :183-196 (dualOutput), :580-603 (bodha_signals_get), :835-862 (kala_priority_ranking_get regAlias), :893-929 (kala_windows_get bespoke handler), :1010-1025 (bodha_remedies_get regAlias)
- `register_p1_synthesis.ts` at :170-185 (local dualOutput / applyAutoBudgetToEnvelope), :825-871 (synth_chart_brief_get count + dualOutput call)
- `call_service_wrappers.ts` at :615-637 (signal_count: result.rows.length)
- `query_temporal_activation.ts` at :360-384 (all four count fields)
- `query_remedies.ts` at :584-602 (resonance_count, prescription_count)
Stream confirmed S2 per LEDGER_S2.md. No writer_asset / data_delta / RS-A references in the spec (pure serving-layer TypeScript fix, no DB migration, no writer rebuild policy applicable).

## Q1 — Mechanism vs. symptom

SPEC addresses the mechanism precisely: narrative count fields are computed from pre-trim array lengths, and both trim paths (`finalizeMcpBudget` in register_p1_aliases.ts's dualOutput; `applyAutoBudgetToEnvelope` in register_p1_synthesis.ts's dualOutput) trim only array-typed sections with no concept of paired scalar fields. The root cause (trim-blindness to companion scalars) is stated in §1 and confirmed by source. Not merely a symptom description. PASS.

## Q2 — Sub-claim coverage

All six DIAGNOSIS sub-claims map to SPEC elements:
- F-45a (bodha_signals_get / served_count) → SPEC §2a row 1 ✓
- F-45b (synth_chart_brief_get / coverage_receipt) → SPEC §2a row 2 ✓
- F-45c (kala_priority_ranking_get / signal_count) → SPEC §2a row 3 ✓
- F-45d (kala_windows_get / activation_count + predicate_count + structural window_family/forward_window risk) → SPEC §2a row 4 (all four count fields) + §4 ✓
- F-45e (bodha_remedies_get / prescription_count + structural resonance_count risk) → SPEC §2a row 5 ✓
- F-45f (no trim_report cross-reference in narrative field) → SPEC §7 row 6: explicitly flagged as a judgment call (resyncing count makes cross-ref moot; VERIFIER to confirm). Acknowledged, not silently dropped. ✓

One minor parenthetical gap: DIAGNOSIS §2 F-45a also names `tier_distribution` and `top_subjects_by_frequency` as stale (computed from the same pre-trim rows). These are NOT in the exit test and not explicitly mentioned in SPEC §2a row 1's fix instruction. However: the natural fix for served_count (moving the entire `verdict_summary` block after finalizeMcpBudget) would automatically fix them too, since all three are set in the same object literal. The SPEC's build instruction allows either "move-count-computation" or "re-derive-after" — either mechanically fixes all three. Not a blocking deficiency; builder should confirm the block is moved in full.

## Q3 — Exit test fails on today's code (traced line-by-line)

1. `bodha_signals_get(top_k=200)`: `inner['verdict_summary'] = { served_count: rows.length, ... }` at register_p1_aliases.ts:588-593 uses pre-trim rows; `finalizeMcpBudget` at :599 trims `signals` 200→20. Assertion `served_count === signals.length` → 200 ≠ 20. **FAILS** ✓

2. `synth_chart_brief_get(depth='complete')`: `verdictCount: verdicts.length` (27) baked into `coverage_receipt` string at :836-843; `dualOutput` at :871 calls `applyAutoBudgetToEnvelope` at register_p1_synthesis.ts:177 which trims `verdict_summary` 27→13. Assertion `.toContain('13 domain verdicts')` on a string containing '27 domain verdicts'. **FAILS** ✓

3. `kala_priority_ranking_get(top_k=100)`: `signal_count: result.rows.length` (100) at call_service_wrappers.ts:626 is honest at construction; `regAlias` wraps via register_p1_aliases.ts dualOutput (:183-196) which calls `finalizeMcpBudget` trimming `ranked_signals` 100→50. Assertion `signal_count === ranked_signals.length` → 100 ≠ 50. **FAILS** ✓

4. `kala_windows_get(limit=500)`: `activation_count: activations.rows.length` (500) at query_temporal_activation.ts:365 and `predicate_count: predicates.length` (500) at :377; `dualOutput(data, 'kala_windows_get')` at register_p1_aliases.ts:928 trims activations 500→5 (hard-cap), predicates 500→10. Both assertions fail. **FAILS (×2)** ✓

5. `bodha_remedies_get(fields='all')`: `prescription_count: preRows.length` (27) at query_remedies.ts:592; `regAlias` wraps via dualOutput trimming `prescriptions` 27→13. Assertion 27 ≠ 13. **FAILS** ✓

All six assertions genuinely fail on current source. Live repro in DIAGNOSIS §1 table corroborates.

## Q4 — Sibling sites

All sibling sites identified in DIAGNOSIS §4 are covered:
- `predicate_count` (confirmed live-stale 500→10) → explicitly in §2a row 4 ✓
- `window_family_count` / `forward_window_count` (structural risk, not triggered live this pass) → explicitly included in §2a row 4 and §4 ✓
- `resonance_count` (structural risk, 9 rows — not triggered live this pass) → §2a row 5 says 'Re-derive both' ✓

## Q5 — Recurrence guard

SPEC §5 is honest: §2b (optional `companionCountField` on `TrimmableSection`) is the real recurrence guard. Without §2b (which is not required scope for F-45), no automated guard exists — a future tool with the same pattern requires a new finding. §2b, if built, would detect the defect class directly (not a proxy). The spec does not falsely claim the guard is present. Honest and acceptable. The absence of a mandatory guard does not make the spec incomplete — it is a forward-looking design gap, clearly scoped.

## Q7 — Unverified assumptions / citation accuracy

All nine file:line citations verified against current main-ro source:
- register_p1_aliases.ts:589 (served_count: rows.length) — exact match ✓
- register_p1_aliases.ts:599 (finalizeMcpBudget call) — exact match ✓
- register_p1_synthesis.ts:836-843 (verdictCount: verdicts.length in buildCoverageReceipt) — exact match ✓
- register_p1_synthesis.ts:171 / :177 (dualOutput → applyAutoBudgetToEnvelope) — exact match ✓ (DIAGNOSIS said :170-185, :177 — matches)
- register_p1_synthesis.ts:871 (return dualOutput(envelope(...))) — exact match ✓
- call_service_wrappers.ts:626 (signal_count: result.rows.length) — exact match ✓
- register_p1_aliases.ts:840 (regAlias kala_priority_ranking_get) — exact match ✓
- register_p1_aliases.ts:183-196 (dualOutput → finalizeMcpBudget at maxKb:40) — exact match ✓
- register_p1_aliases.ts:893-929 (kala_windows_get bespoke handler, dualOutput at :928) — exact match ✓
- query_temporal_activation.ts:365,371,375,377 (four count fields) — exact match ✓
- query_remedies.ts:590,592 (resonance_count, prescription_count) — exact match ✓
- register_p1_aliases.ts:1015-1025 (regAlias bodha_remedies_get) — exact match ✓

No unverified assumptions found. Every cited line exists and says what the DIAGNOSIS claims.

writer_asset / data_delta / RS-A: not referenced in spec; confirmed not applicable (pure TypeScript serving-layer fix, no writer layer, no DB migration, rebuild policy does not apply).

## Verdict: COMPLETE

All five §2a call-site fixes are precisely located with verified file:line citations. The exit test genuinely fails on current source across all six assertions (traced against actual code). All DIAGNOSIS sub-claims are mapped. Sibling sites are covered. The recurrence guard gap (§5) is honestly disclosed. No unverified assumptions.

The one builder note: the §2a row 1 fix for bodha_signals_get should move the entire `verdict_summary` block (not just `served_count`) to after `finalizeMcpBudget` to avoid leaving `tier_distribution`/`top_subjects_by_frequency` stale — this is implied by the fix's mechanical description but not explicitly stated in the exit test.
