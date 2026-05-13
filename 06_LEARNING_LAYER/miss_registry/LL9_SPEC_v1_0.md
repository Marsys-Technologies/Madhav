---
artifact: LL9_SPEC_v1_0.md
canonical_id: LL9_SPEC
version: 1.0
status: SCAFFOLD
mechanism: LL.9
mechanism_label: Counterfactual Learning from Misses
produced_during: M5-A-S1
produced_on: 2026-05-13
authored_by: claude-sonnet-4-6
governing_plan: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md §3 M5-A Item 2
activation_condition: >
  SCAFFOLD at M5. Activates at M6 open. Until M6 opens, miss_registry_stub.json
  receives no entries — the registry is formally declared but dormant.
miss_definition: >
  A prediction is a MISS when the recorded PPL outcome contradicts the prediction
  direction at ≥2σ from the predicted probability. Formally:
    observed_probability < (predicted_probability - 2 × predicted_uncertainty)
  OR the outcome is explicitly CONTRADICTED in the PPL ledger and the prediction
  confidence was MED or HIGH.
changelog:
  - v1.0 (2026-05-13, M5-A-S1): Initial scaffold spec. Activation condition declared
      (M6 open); miss definition specified (≥2σ contradiction); registry schema
      declared in miss_registry_stub.json. Status: SCAFFOLD (activates M6).
---

# LL.9 — Counterfactual Learning from Misses Spec v1.0

## §1 — Purpose

LL.9 captures and systematically learns from prediction misses. When a prediction
is falsified, the miss is not discarded — it is analyzed to identify whether the
underlying signal weights, topology assumptions, or prior specifications contributed
to the failure. This counterfactual learning feeds back into M5/M6 model refinement.

Per MACRO_PLAN §LL-Appendix.A: LL.9 is `n/a` at M4, `scaffold` at M5, and activates
at M6. This spec declares the scaffold; activation happens at M6 open.

## §2 — Activation condition

LL.9 activates when:
1. M6 is officially opened (CURRENT_STATE active_macro_phase = M6).
2. The miss_registry has at least one entry (i.e., at least one PPL miss has been
   recorded and scored).
3. The DBN model from M5-D is available for counterfactual analysis.

## §3 — Miss definition

A PPL prediction is classified as a MISS when:

**Condition A (quantitative):** The observed outcome probability falls below the
2σ lower bound of the prediction's stated probability distribution:
```
P(outcome_observed) < predicted_probability - 2 × predicted_uncertainty
```

**Condition B (qualitative):** The PPL ledger explicitly records:
- `outcome: CONTRADICTED`
- AND `confidence_at_creation: MED` or `HIGH`

Low-confidence (LOW) contradicted predictions are tracked but do NOT trigger
LL.9 miss analysis by default (they were already flagged as speculative).

## §4 — Registry schema

Schema: `miss_registry_stub.json` (this directory).

Each miss entry captures:
- The original prediction (PRED.NNN reference)
- The contradiction details (what was predicted vs what was observed)
- Signal chain analysis: which MSR signals were active at the time of the miss
- Hypothesis generation: what might explain the miss (3 candidate hypotheses)
- Counterfactual: what the model would have predicted with corrected parameters
- Action: what parameter or weight adjustment is recommended

## §5 — Counterfactual analysis procedure

When a miss is registered at M6+:

1. **Trace the signal chain.** Identify which DBN nodes and edges contributed to
   the missed prediction. Use DERIVATION_LEDGER entries and the prediction's
   `signal_chain` field.

2. **Generate 3 hypotheses.** For each miss, generate exactly 3 candidate
   explanations:
   - H1: Signal weight incorrect (LL.1/LL.2 calibration error)
   - H2: Topology error (wrong edge or missing edge in DBN)
   - H3: Prior specification error (prior too strong; data didn't overcome it)

3. **Counterfactual prediction.** Run the DBN with each hypothesis correction
   applied. Report which correction (if any) would have predicted the correct
   outcome.

4. **Recommend action.** Based on counterfactual analysis:
   - If H1 confirmed: flag signal weight for LL.2 re-promotion campaign
   - If H2 confirmed: flag topology assumption for M6 topology review
   - If H3 confirmed: flag prior for NAP override and re-specification

5. **Record in miss_registry.** Append entry; mark status as ANALYZED.

## §6 — Integration with other mechanisms

- **LL.8:** When LL.8 kill-switch fires (KS.LL8.1), the underlying prediction is
  auto-flagged for LL.9 miss analysis at M6.
- **LL.1/LL.2:** Miss analysis can recommend re-promotion campaigns or weight
  adjustments, feeding back into the calibration layer.
- **PPL:** Every CONTRADICTED MED/HIGH prediction in the PPL is a miss candidate.
  LL.9 is the formal processing mechanism; PPL is the source ledger.

## §7 — Cadence at M6

At each M6 session:
1. Check PPL for new CONTRADICTED MED/HIGH predictions since last LL.9 pass.
2. For each new miss: execute §5 counterfactual analysis.
3. Append to miss_registry; update summary fields.
4. At M6 close: report total_misses, misses_analyzed, recommendations_pending.

---

*End of LL9_SPEC_v1_0.md — SCAFFOLD status. Activates at M6 open.*
*Governing plan: PHASE_M5_PLAN_v1_0.md §3 M5-A Item 2. Session: M5-A-S1.*
