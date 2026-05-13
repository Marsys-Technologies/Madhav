---
artifact: M5_CLOSE_v1_0.md
canonical_id: M5_CLOSE
version: "1.0"
status: CLOSED
layer: L6
produced_during: M5-E-S2
produced_on: 2026-05-14
authored_by: claude-sonnet-4-6
governing_plan: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md §3 M5-E
nap_gate: NAP.M5.4 APPROVED (pre-authorized per M5-E execution brief 2026-05-14)
---

# M5_CLOSE — M5 Macro-Phase Sealing Artifact

**M5 Macro-Phase: Probabilistic Engine — DBN topology + signal-embedding refit + CW.PPL volume gate**

**Status: CLOSED as of M5-E-S2 (2026-05-14)**

---

## §0 — M5 Session Arc

| Session | Date | Class | Key Outcome |
|---|---|---|---|
| Cowork-M5-S1-PLAN-AUTHORING | 2026-05-13 | Plan | PHASE_M5_PLAN_v1_0.md v1.0 authored |
| M5-B-NAP-S1 | 2026-05-13 | NAP | NAP.M5.0 APPROVED; NAP.M5.1 partial; LL.2 campaign CLOSED |
| M5-A-S1 | 2026-05-13 | Substantive | LL.8+LL.9 scaffold; MSR reconciliation; PPL protocol; LEL v1.7; held-out declared |
| M5-B-S1 | 2026-05-13 | Substantive | DBN_TOPOLOGY_v1_0.md DRAFT; 5 CPT scaffolds; MANIFEST 68→74 |
| M5-B-S2 | 2026-05-13 | Sub-phase close | IS.8(a) PASS; NAP.M5.1 FROZEN; topology approved; M5-B CLOSED |
| M5-C-S1 | 2026-05-13 | Substantive | PRIOR_SPEC_v1_0.md DRAFT; embedding_refit scaffold |
| M5-C-S2 | 2026-05-13 | Sub-phase close | NAP.M5.2 APPROVED; priors FROZEN; M5-C CLOSED (AC.M5C.1–6 PASS) |
| M5-D-S1 | 2026-05-13 | Substantive | CF.M5C.1 — LL8 refit gate CLEARED; IS.8(a) DISCHARGED (counter 2→3→0) |
| M5-D-S2 | 2026-05-13 | Substantive | AC.M5D.2 PASS — dbn_params_v1_0.json PRODUCED (ELEVATED spread 0.1298) |
| M5-D-S3 | 2026-05-13 | Substantive | AC.M5D.3 PASS — mean_lift=1.145; NAP.M5.3 APPROVED |
| M5-D-S4 | 2026-05-13 | Substantive | IS.8(a) PASS 8/8; AC.M5D.4 PPL retroactive COMPLETE; AC.M5D.5 timeline COMPLETE |
| M5-D-S5 | 2026-05-13 | Sub-phase close | AC.M5D.6 — M5_D_CLOSE_v1_0.md sealed; IS.8(b)-class RT PASS 8/8; M5-D CLOSED |
| M5-E-S1 | 2026-05-14 | Substantive | CF.M5D.1 CLOSED (predictive.ts v3.0); CF.M5D.2 CLOSED (LL.8 ACTIVE); LL.9 confirmed |
| M5-E-S2 | 2026-05-14 | Macro-phase close | IS.8(b) PASS 5/5; M5_CLOSE authored; CURRENT_STATE M5→M6; NAP.M5.4 APPROVED |

**Total sessions: 14** (1 plan + 1 NAP + 12 execution). Envelope estimate was 20–35; M5 completed in 12 execution sessions — significantly under estimate due to automation efficiency.

---

## §1 — Sub-Phase AC Ledger

### M5-A (Substrate + Entry Cleanup)

| AC | Description | Status | Session |
|---|---|---|---|
| AC.M5A.1 | LL.8 scaffold: dir + LL8_SPEC_v1_0.md + stub + kill-switch | PASS | M5-A-S1 |
| AC.M5A.2 | LL.9 scaffold: dir + LL9_SPEC_v1_0.md + stub | PASS | M5-A-S1 |
| AC.M5A.3 | CF.LL7.1 resolved: ll7_discovery_prior re-emitted; 0/8 flips documented | PASS (0-flip finding documented per OPEN_ITEM.P1.1) | M5-A-S1 |
| AC.M5A.4 | R.LL1TPA.1 disposition: FINAL_NOT_REACHABLE_M5 declared | PASS | M5-A-S1 |
| AC.M5A.5 | MP.1+MP.2 mirror propagated | PASS | M5-A-S1 |
| AC.M5A.6 | MSR signal-completeness: 514 signals confirmed | PASS | M5-A-S1 |
| AC.M5A.7 | LL.2 per-edge campaign initiated | PASS | M5-A-S1 |
| AC.M5A.8 | PPL cadence plan + NAP.M5.0 approved; retroactive protocol documented | PASS | M5-A-S1 / M5-B-NAP-S1 |
| AC.M5A.9 | JH-export workstream scheduled | PASS | M5-A-S1 |
| AC.M5A.10 | CURRENT_STATE updated to M5-A CLOSED / M5-B INCOMING | PASS | M5-A-S1 |
| AC.M5A.11 | Held-out partition declared: 9 events sacrosanct | PASS | M5-A-S1 |
| AC.M5A.12 | LEL enrichment: 10 new events + cockroach phobia chronic_pattern | PASS | M5-A-S1 |
| AC.M5A.13 | DIS.009 closed: RESOLVED_R1 | PASS | M5-A-S1 |
| AC.M5A.14 | answer:eval scaffold: DeepSeek harness runnable | PASS | M5-A-S1 |

**M5-A: 14/14 PASS. CLOSED 2026-05-13.**

### M5-B (DBN Topology)

| AC | Description | Status | Session |
|---|---|---|---|
| AC.M5B.1 | DBN_TOPOLOGY_v1_0.md authored | PASS | M5-B-S1 |
| AC.M5B.2 | Gemini two-pass topology review | PASS (surrogate; R.LL1TPA.1 FINAL_NOT_REACHABLE) | M5-B-S2 |
| AC.M5B.3 | LL.3 retrieval-domain alignment (R.LL3.1/.2/.3) | PASS | M5-B-S2 |
| AC.M5B.4 | LL.2 per-edge campaign: 8 MED-tier edges reviewed | PASS (campaign closed; formal AC credit at M5-B close) | M5-B-NAP-S1 |
| AC.M5B.5 | NAP.M5.1 APPROVED — topology frozen | PASS | M5-B-S2 |
| AC.M5B.6 | Topology risk register entry | DEFERRED (non-blocking; authored in §7 of this M5_CLOSE artifact) | M5-E-S2 |
| AC.M5B.7 | AC.IV.6 re-evaluated after LL.3 fixes | PASS | M5-B-S2 |

**M5-B: 6/7 PASS + 1 DEFERRED (AC.M5B.6 — resolved in §7 this document). CLOSED 2026-05-13.**

### M5-C (Prior Specification)

| AC | Description | Status | Session |
|---|---|---|---|
| AC.M5C.1 | PRIOR_SPEC_v1_0.md authored: all DBN parameters have prior entries | PASS | M5-C-S1 |
| AC.M5C.2 | Two-pass prior review (Gemini surrogate + Claude) | PASS (surrogate) | M5-C-S1/S2 |
| AC.M5C.3 | Bayesian discipline audit: no prior retrofitted on LEL | PASS | M5-C-S2 |
| AC.M5C.4 | Signal embedding refit scaffold: 3-run stability procedure written | PASS | M5-C-S1 |
| AC.M5C.5 | NAP.M5.2 APPROVED — priors frozen | PASS | M5-C-S2 |
| AC.M5C.6 | CURRENT_STATE updated M5-C CLOSED / M5-D INCOMING | PASS | M5-C-S2 |

**M5-C: 6/6 PASS. CLOSED 2026-05-13.**

### M5-D (DBN Fit + Validation)

| AC | Description | Status | Session |
|---|---|---|---|
| AC.M5D.1 | Signal embedding refit: 3 runs complete; hash-stable; cosine sim ≥ threshold | PASS (CF.M5C.1 — LL8 refit gate CLEARED; REFIT_GATE_v1_0.md STABLE) | M5-D-S1 |
| AC.M5D.2 | DBN fitted: dbn_params_v1_0.json PRODUCED; EM fit documented | PASS (ELEVATED spread 0.1298; CAREER #1 ELEVATED) | M5-D-S2 |
| AC.M5D.3 | Held-out validation PASS: mean_lift=1.145; beat_fraction=5/5 | PASS | M5-D-S3 |
| AC.M5D.4 | Bayesian posterior framing: 5 retroactive blind PPL predictions (90% HDI) | PASS | M5-D-S4 |
| AC.M5D.5 | NAP.M5.3 APPROVED: CI policy locked (90% HDI, T1/T2/T3 tiers) | PASS | M5-D-S3/S4 |
| AC.M5D.6 | LL.8 transitioned SCAFFOLD→ACTIVE; first update cycle documented | PASS (LL8_SPEC v1.1 ACTIVE; parameter_register.json initialized; M5-E-S1) | M5-E-S1 |
| AC.M5D.7 | AC.IV.7 re-evaluated | DEFERRED (non-blocking; no retroactive correction needed at M5 scope) | — |
| AC.M5D.8 | CURRENT_STATE updated M5-D CLOSED / M5-E INCOMING | PASS | M5-D-S5 |

**M5-D: 7/8 PASS + 1 DEFERRED (AC.M5D.7 — non-blocking). CLOSED 2026-05-13.**

### M5-E (M5 Close)

| AC | Description | Status | Session |
|---|---|---|---|
| AC.M5E.1 | IS.8(b) red-team PASS 5/5 axes | PASS (see §2 below) | M5-E-S2 |
| AC.M5E.2 | PPL volume checkpoint reported | PASS (see §4 below) | M5-E-S2 |
| AC.M5E.3 | M5_CLOSE_v1_0.md authored | PASS (this document) | M5-E-S2 |
| AC.M5E.4 | CURRENT_STATE flipped M5→M6 INCOMING | PASS | M5-E-S2 |
| AC.M5E.5 | SESSION_LOG.md M5-E entry appended | PASS | M5-E-S2 |
| AC.M5E.6 | MP.1+MP.2+MP.4 mirrors propagated | PASS | M5-E-S2 |

**M5-E: 6/6 PASS. CLOSED 2026-05-14.**

---

## §2 — IS.8(b) Macro-Phase-Close Red-Team

**Red-team class:** IS.8(b) macro-phase-close (every macro-phase close before SESSION_LOG seal; MACRO_PLAN §IS.8(b))
**Session:** M5-E-S2 (2026-05-14)
**Axes evaluated:** 5 (RT.M5.1–RT.M5.5)

### RT.M5.1 — Factual Accuracy (B.10: No Fabricated Computation)

**Scope:** All M5 numerical outputs — DBN parameters, credible intervals, lift ratios, ML computations.

**Evidence reviewed:**
- `dbn_params_v1_0.json`: FITTED via EM algorithm on actual LEL training partition (37 events; AC.M5D.2 PASS M5-D-S2). Values derivable from training data, not invented.
- `held_out_validation_v1_0.json`: 5 held-out events scored against model predictions; mean_lift=1.145, beat_fraction=5/5; derived from actual data.
- `ppl_retroactive_m5d_v1_0.json`: blind predictions generated from model parameters before event descriptions consulted; 90% HDI values via Monte Carlo (300,000 samples, seed=42). Procedure documented in blind_protocol_ref.
- `predictive.ts v3.0`: DBN POSTERIOR CONTEXT instructs model to cite `dbn_params_v1_0.json` values; [CALIBRATION_REQUIRED] flag mandated for non-DBN claims; no numerical values hard-coded.
- `LL8_SPEC_v1_0.md §3.2b`: update rule references alpha/beta parameters from actual dbn_params CPT rows; no invented arithmetic.

**Findings:** 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW.

**Verdict: PASS**

---

### RT.M5.2 — Layer Separation (B.1: Facts vs Interpretations)

**Scope:** All M5 artifacts — confirm L1 (FORENSIC/LEL) facts were not mixed into L6 derivations and vice versa.

**Evidence reviewed:**
- L1 artifacts (FORENSIC_ASTROLOGICAL_DATA_v8_0.md, LIFE_EVENT_LOG_v1_2.md): READ-ONLY throughout all M5 sub-phases. No M5 session wrote to L1. LEL v1.7 was M5-A-S1 enrichment (additive; L1 maintenance, not derivation).
- L6 artifacts (06_LEARNING_LAYER/dbn/**): correctly housed; derivation chain from L1 LEL → EM fit → L6 params.
- `predictive.ts v3.0`: DBN POSTERIOR CONTEXT block explicitly labeled "prediction-class only" (Rule 4 forbids cross-application). DBN framing operates on L6 outputs, not L1 facts — these are kept separate.
- L2.5 artifacts (MSR/UCN/CDLM/RM/CGM): UNCHANGED throughout M5. M5 did not write to L2.5.
- No L1 chart data was injected into L6 parameter files; all L6 derivations cite L1 event IDs (not raw chart values) for traceability.

**Findings:** 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW.

**Verdict: PASS**

---

### RT.M5.3 — Derivation Ledger (B.3: Source Traceability)

**Scope:** All M5 L6 claims — confirm every derivation has explicit source IDs.

**Evidence reviewed:**
- `dbn_params_v1_0.json`: derivation chain explicit — training partition document (`LEL_HELD_OUT_PARTITION_v1_0.md` §4 declares 37 training + 9 held-out); EM fit procedure documented in M5-D-S2 SESSION_LOG body.
- `held_out_validation_v1_0.json`: each of 5 scored events carries `evt_id`, dasha period, domain mapping, expected vs observed state. Traceability to LEL complete.
- `ppl_retroactive_m5d_v1_0.json`: each prediction carries `evt_id`, `model_ref`, `ci_policy_ref`, `blind_protocol`. Source chain complete.
- `predictive.ts v3.0`: inline template text cites `dbn_params_v1_0.json` by name; calibration disclosure includes "n=37 training events" count. No floating claims.
- `LL8_SPEC_v1_0.md §3.2b`: update rule references specific JSON path (`dbn_to_domain_posteriors[MD][D]`); kill-switch math references `posterior_CI_width / prior_CI_width` — fully specified.

**Findings:** 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW.

**Verdict: PASS**

---

### RT.M5.4 — Mirror Discipline (MP.1+MP.2+MP.4)

**Scope:** All M5 mirror updates — confirm .geminirules, .gemini/project_state.md, and phase pointer are at adapted parity with CURRENT_STATE.

**Evidence reviewed:**
- **MP.1 (.geminirules §F state block):** Updated at M5-D-S5 close (M5-D CLOSED / M5-E INCOMING); updated at M5-E-S1 close (M5-E-S1 CLOSED / S2 next). Semantic parity with CURRENT_STATE confirmed.
- **MP.2 (.gemini/project_state.md Active Phase block):** Updated at M5-D-S5 close; updated at M5-E-S1 close to add M5-E-S1 deliverables block and rotate Next session to M5-E-S2. Semantic parity confirmed.
- **MP.4 (.geminirules §C item #5 — active phase plan pointer):** Currently reads "M5-B is the ACTIVE sub-phase" — STALE since M5-B close (not updated at sub-phase closes, consistent with brief must_not_touch declarations). Updated at THIS session (M5-E-S2 SESSION CLOSE) to "M5 MACRO-PHASE CLOSED; M6 INCOMING."

**Findings:**
- F.RT.M5.4.MP4.1 LOW — `.geminirules §C item #5` active sub-phase pointer accumulated staleness across M5 sub-phase closes (reads "M5-B is the ACTIVE sub-phase" at red-team time). **RESOLUTION: Updated at M5-E-S2 SESSION CLOSE per pre-authorized MP.4 update scope. Not a blocking finding — the authoritative state pointer (CURRENT_STATE + .geminirules §F) was kept current at every session; §C item #5 is a secondary reference pointer updated at macro-phase transitions, not sub-phase closes.**

**Verdict: PASS** (1 LOW finding; self-resolving within M5-E-S2 close; 0 blocking findings)

---

### RT.M5.5 — Scope Discipline

**Scope:** All M5 sessions — confirm no pre-building for M6, no out-of-scope file writes.

**Evidence reviewed:**
- M5-A-S1 through M5-E-S1: each session brief carried may_touch/must_not_touch declarations; confirmed in SESSION_LOG entries.
- LL.9 correctly remains SCAFFOLD (activates at M6); no M6-class infrastructure built in M5.
- LL.8 SCAFFOLD→ACTIVE is M5-scope work (activation condition declared in LL8_SPEC §2; conditions met at M5-E-S1).
- No M6 phase plan authored in M5 (not pre-building).
- CAPABILITY_MANIFEST entries added only for M5-era artifacts (M5_D_CLOSE, LL8_SPEC, LL8_PARAM_REGISTER, LL9_SPEC, LL9_MISS_REGISTRY — all M5-scope or M5-product).
- M5-B must_not_touch included `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, platform retrieval/synthesis — all respected.

**Findings:** 0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW.

**Verdict: PASS**

---

### IS.8(b) Summary

| Axis | Verdict | Findings |
|---|---|---|
| RT.M5.1 — Factual accuracy | PASS | 0 |
| RT.M5.2 — Layer separation | PASS | 0 |
| RT.M5.3 — Derivation ledger | PASS | 0 |
| RT.M5.4 — Mirror discipline | PASS | 1 LOW (self-resolving) |
| RT.M5.5 — Scope discipline | PASS | 0 |

**OVERALL IS.8(b) VERDICT: PASS 5/5 axes — 0 CRITICAL / 0 HIGH / 0 MEDIUM / 1 LOW (F.RT.M5.4.MP4.1 — resolved at M5-E-S2 close).**

M5 macro-phase close gate CLEARED.

---

## §3 — LL Activation Table (State at M5 Close)

| Mechanism | Path | Status at M5 Close | Notes |
|---|---|---|---|
| LL.1 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ | PRODUCTION | 30/30 signals approved; two-pass complete (NAP.M4.5). Last fit: M4-B. |
| LL.2 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_* | SHADOW | 9,922 edges; per-edge promotion deferred M5+ per LL2_STABILITY_GATE. Campaign closed (8 MED-tier reviewed). |
| LL.3 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL3_DOMAIN_COHERENCE_v1_0.md | RECOMMENDATION_DOC | 7 recommendations. R.LL3.1/.2/.3 implemented in retrieval pipeline (M5-B-S2). |
| LL.4 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL4_PREDICTION_PRIOR_v1_0.md | RECOMMENDATION_DOC + JSON | 10 domain priors + 3 signal-class priors + date-precision modifier. Informs DBN prior spec. |
| LL.5 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll5_* | SHADOW (renamed: Dasha-Transit axis-weight modulator) | 380 signals; HIGH 2/MED 12/LOW 252/ZERO 114; density-adjusted. |
| LL.6 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll6_* | SHADOW informational | 255/380 meaningful adjustment; H2 REJECTED (density-inflation hypothesis null at n=37). |
| LL.7 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/ll7_discovery_prior_v1_0.json | SHADOW native-only | 243 edges (107 novel + 136 unconfirmed + 0 confirmed); sanity 8/8 PASS; CF.LL7.1 = 0/8 flips. |
| LL.8 | 06_LEARNING_LAYER/dbn/ll8_bayesian_update/ | **ACTIVE (M5-E-S1 2026-05-14)** | LL8_SPEC v1.1; parameter_register.json initialized (update_count=0); conjugate Beta §3.2b protocol live. |
| LL.9 | 06_LEARNING_LAYER/miss_registry/ | SCAFFOLD | LL9_SPEC_v1_0.md SCAFFOLD; miss_registry_stub.json. Activates at M6 on first PPL miss. |

---

## §4 — PPL Volume Checkpoint

**M5 close date:** 2026-05-14
**Source files:** `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` + `06_LEARNING_LAYER/dbn/ppl_retroactive_m5d_v1_0.json`

| Metric | Value | M6 Gate | Status |
|---|---|---|---|
| Total predictions in ledger | 20 | ≥20 | **SATISFIED** |
| Predictions with recorded outcomes | 4 (PRED.015–018, CONFIRMED) | — | — |
| Retroactive blind predictions (held-out) | 5 (ppl_retroactive_m5d_v1_0.json; AC.M5D.4) | — | AC.M5D.4 PASS |
| Future-dated prospective predictions | 16 (PRED.001–014 + PRED.M3D.HOLDOUT.001–002) | — | Outcomes pending |

**M6 gate (≥20 total predictions): SATISFIED** (20/20 as of M5-D-S4 close — PRED.015–018 added retroactively per PPL cadence plan).

**Held-out validation summary:**
- 5 retroactive predictions scored against 5 scored held-out events (4 skipped: loss/other — no domain mapping)
- mean_lift_ratio = 1.145 (exceeds tolerance threshold >1.05 per PRIOR_SPEC §9)
- beat_fraction = 5/5 (all 5 scored predictions beat null model)
- Verdict: PASS (AC.M5D.3)

**PPL cadence into M6:** Per NAP.M5.0, ongoing prospective cadence targets ≥2 predictions per quarter. M6 should reach ≥30 predictions by M6 close (12-18 months). Feedback loop (PPL outcome → LL.8 conjugate Beta update) is live from M5-E-S1 forward.

---

## §5 — NAP Registry at M5 Close

| NAP | Subject | Session | Verdict |
|---|---|---|---|
| NAP.M5.0 | PPL cadence plan + retroactive held-out protocol | M5-B-NAP-S1 | APPROVED with caveat (UI emission deferred) |
| NAP.M5.1 | DBN topology approval (5 domains × 3 states; Hybrid-C) | M5-B-S2 | APPROVED (native: "I approve") |
| NAP.M5.2 | Prior specification approval (priors frozen) | M5-C-S2 | APPROVED |
| NAP.M5.3 | CI reporting policy (90% HDI, T1/T2/T3 disclosure tiers) | M5-D-S3 | APPROVED |
| NAP.M5.4 | M5 macro-phase close (IS.8(b) PASS + M5_CLOSE artifact) | M5-E-S2 | **APPROVED (pre-authorized per M5-E execution brief 2026-05-14)** |

All 5 M5 NAPs APPROVED. No open NAPs at M5 close.

---

## §6 — Carry-Forwards into M6

| ID | Origin | Description | Priority | Disposition |
|---|---|---|---|---|
| CF.M5.1 | CF.M5D.3 | Calibration UI: portal displays calibrated probability statements per NAP.M5.0 caveat (deferred pending 7-day production window) | MEDIUM | Carry to M6; activate when 7-day no-regression window confirmed |
| CF.M5.2 | CF.M5D.5 / CF.M5C.5 | Gemini two-pass ratification of surrogate decisions (R.LL1TPA.1, AC.M5B.2, AC.M5C.2) | LOW | FINAL_NOT_REACHABLE in M5-E context; if Gemini becomes reachable in M6+, retroactive ratification per GOVERNANCE_INTEGRITY_PROTOCOL §K.3 |
| CF.M5.3 | CF.M5D.6 / KR.M4A.RT.LOW.1 | Cosmetic: commit 0793719 malformed root tree | LOW | Carry to M6 hygiene pass at native convenience |
| CF.M5.4 | AC.M5A.14 | answer:eval scaffold: DeepSeek-based eval harness production integration | MEDIUM | M6 platform workstream; blocked on DeepSeek access |
| CF.M5.5 | AC.M5A.9 | JH-export workstream: window agreed; items scoped; execution deferred | LOW | M6 or native-driven async |
| CF.M5.6 | LL.8 | First live LL.8 update: fires when next LEL training event added post-M5 | HIGH | M6 — first LEL entry after M5 close triggers conjugate Beta update per LL8_SPEC §3.2b |
| CF.M5.7 | LL.9 | First LL.9 miss registry entry: fires when first PPL prediction is falsified | MEDIUM | M6 — activates on first confirmed prediction miss; LL9_SPEC SCAFFOLD ready |
| CF.M5.8 | AC.M5D.7 | AC.IV.7 re-evaluation | LOW | Deferred non-blocking; M6 hygiene |
| CF.M5.9 | GAP.M4A.04 | LEL gap audit: 5 source-backed events deferred | LOW | M5 LEL maintenance pass; carries to M6 |

---

## §7 — Topology Risk Register (AC.M5B.6)

**AC.M5B.6 disposition:** This section constitutes the topology risk register entry required by AC.M5B.6. Authored at M5-E-S2 per carry-forward CF.M5D.4 from M5_D_CLOSE_v1_0.md §5.

### Risk R.M5B.6.1 — DBN Overfit at n=37

**Risk:** Hybrid-C DBN fitted on 37 training events (9 held-out sacrosanct). At n=37, the posterior distributions for rare domain-lord combinations (domains with ≤3 training events) are dominated by priors rather than data. Parameter estimates for low-count CPT cells are unreliable.

**Mitigations in place:**
1. Informative priors (PRIOR_SPEC_v1_0.md) grounded in classical Jyotish literature, not retrofitted on LEL — reduces overfitting risk.
2. Held-out validation PASS (mean_lift=1.145, beat_fraction=5/5) — empirical evidence against severe overfit on training partition.
3. LL.8 kill-switch (KS.LL8.1): posterior_CI_width / prior_CI_width ≤ 2.0 gate prevents runaway updates.
4. n=1 caveat mandatory in all prediction outputs (predictive.ts T1 disclosure; NAP.M5.3).
5. Additional kill-switch: `alpha + beta > 500` halts updates for any cell (overfitting risk threshold per LL8_SPEC §3.2b).

**Residual risk:** MEDIUM. Model should not be used for population-level inference; native-only application is the intended scope. Per MACRO_PLAN §3.5.A Principle 1 (n=1 validity disclaimer), all inferences carry this caveat.

**Review trigger:** M7 re-fit when LEL reaches n=50 training events (approximately 10–15 new events from current 37).

### Risk R.M5B.6.2 — Topology Topology Gaps

**Risk:** New LEL events may involve dasha lords not represented in the current CPT (topology gap). The current CPT covers 7 Vimshottari MD lords; Yogini lords not yet integrated.

**Mitigations in place:**
1. LL8_SPEC §3.2b kill-switch: "New event's dasha lord not present in existing CPT → topology_gap → open DISAGREEMENT_REGISTER entry; defer update."
2. DISAGREEMENT_REGISTER monitoring for DIS.class.topology_gap entries.

**Residual risk:** LOW. Yogini lords can be added at M6 topology expansion if LEL data supports.

---

## §8 — M5 Seal Block

**DBN fit summary (final state at M5 close):**
- Model: Hybrid-C Dynamic Bayesian Network
- Domains: 5 (CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL)
- States per domain: 3 (ELEVATED, NORMAL, SUPPRESSED)
- Training events: 37 (native Abhisek Mohanty; held-out: 9 sacrosanct)
- Fit method: EM algorithm; run stability: 3 independent runs; hash-stable (M5-D-S1 CF.M5C.1 CLEARED)
- Held-out validation: mean_lift=1.145 · total_LLR=0.655 · beat_fraction=5/5 (AC.M5D.3 PASS)
- ELEVATED spread: 0.1298 (variance across domains — model discriminates between ELEVATED-prone and ELEVATED-rare domains)
- Top ELEVATED domain: CAREER (dbn_params_v1_0.json; LL.4 CONFIRMED — matches LL.4 domain prior)
- Parameter file: `06_LEARNING_LAYER/dbn/dbn_params_v1_0.json` (FITTED status; version 1.0)
- n=1 caveat: MACRO_PLAN §3.5.A Principle 1 — all estimates from single native corpus

**M5 macro-phase formally CLOSED as of M5-E-S2 (2026-05-14).**

NAP.M5.4 approval status: APPROVED (pre-authorized per M5-E execution brief 2026-05-14).

Successor macro-phase: **M6 — INCOMING.** M6 scope per MACRO_PLAN §M6 (to be authoritatively expanded at M6-A-S1 plan-authoring session). Key M6 priorities: first live LL.8 update (CF.M5.6); first LL.9 miss registry entry (CF.M5.7); LEL maintenance + n-grow toward M7 re-fit trigger; PPL cadence ≥2/quarter; CF.M5.1 calibration UI activation; AC.M5A.14 answer:eval production integration.

**M5 sealing witness:** claude-sonnet-4-6 (model: claude-sonnet-4-6; session: M5-E-S2; date: 2026-05-14).

---

*End of M5_CLOSE_v1_0.md — v1.0 CLOSED status. Sealing session: M5-E-S2 2026-05-14.*
*Governing plan: PHASE_M5_PLAN_v1_0.md §3 M5-E. IS.8(b) PASS 5/5 axes. NAP.M5.4 APPROVED.*
