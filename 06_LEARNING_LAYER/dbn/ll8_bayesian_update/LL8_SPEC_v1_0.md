---
artifact: LL8_SPEC_v1_0.md
canonical_id: LL8_SPEC
version: 1.0
status: SCAFFOLD
mechanism: LL.8
mechanism_label: Bayesian Model Updating
produced_during: M5-A-S1
produced_on: 2026-05-13
authored_by: claude-sonnet-4-6
governing_plan: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md §3 M5-A Item 1
activation_condition: >
  SCAFFOLD at M5. Activates at M5-D once DBN parameters exist (dbn_params_v1_0.json or
  equivalent at 06_LEARNING_LAYER/dbn/). LL.8 transitions from scaffold → active when
  the first fitted parameter set is available and the first PPL outcome arrives for
  comparison against a prior prediction.
kill_switch:
  condition: >
    Update suspended if the credible-interval width of the posterior exceeds 2× the
    prior credible-interval width for the same parameter. This indicates the update
    is destabilizing rather than refining the model.
  enforcement: >
    Before committing any Bayesian update to the parameter register, compute:
      posterior_CI_width / prior_CI_width
    If ratio > 2.0: mark update as SUSPENDED; log in parameter_register with
    reason "kill_switch_triggered"; do not overwrite prior parameters.
    Resume only after native review and explicit NAP override.
  kill_switch_id: KS.LL8.1
changelog:
  - v1.0 (2026-05-13, M5-A-S1): Initial scaffold spec. Activation condition declared;
      kill-switch KS.LL8.1 defined; parameter register stub path declared;
      update mechanism framework specified. Status: SCAFFOLD (activates M5-D).
---

# LL.8 — Bayesian Model Updating Spec v1.0

## §1 — Purpose

LL.8 provides the mechanism by which new Prospective Prediction Log (PPL) outcomes
update the DBN parameter estimates. It is the feedback loop from the world back into
the model, operationalizing the project's commitment to calibration from lived reality.

Per MACRO_PLAN §LL-Appendix.A: LL.8 is `scaffold` at M5 (DBN params not yet exist)
and transitions to `active` at M5-D when the first fitted parameter set is available.

## §2 — Activation condition

LL.8 activates when:
1. `06_LEARNING_LAYER/dbn/dbn_params_v1_0.json` (or equivalent) exists and is
   declared FITTED (not just scaffolded).
2. At least one PPL outcome is available for comparison with a prior prediction.
3. NAP.M5.3 (confidence-interval reporting policy) is APPROVED at M5-D close.

Until all three conditions are met, this spec remains SCAFFOLD status.

## §3 — Update mechanism

### §3.1 — Trigger

A PPL outcome recording triggers an LL.8 candidate update when:
- The prediction had a declared domain, direction, and confidence band
- The outcome contradicts, partially confirms, or confirms the prediction
- The prediction used a DBN signal weight or parameter as part of its derivation

### §3.2 — Update procedure

1. **Identify affected parameters.** Map the prediction's signal chain back to the
   DBN parameters it relies on (documented in the prediction's `signal_chain` field
   or derivable from DERIVATION_LEDGER entries).

2. **Compute posterior.** Using the Bayesian update rule:
   - Prior: current parameter value (from parameter_register)
   - Likelihood: P(outcome | parameter value)
   - Posterior: prior × likelihood / marginal likelihood

3. **Kill-switch check.** Compute posterior_CI_width / prior_CI_width.
   If ratio > 2.0: SUSPEND update (see §2 kill-switch definition).

4. **Record update.** Append to `parameter_register.json`:
   - parameter_id
   - prior_value, prior_CI
   - posterior_value, posterior_CI
   - update_ratio (posterior_CI_width / prior_CI_width)
   - triggering_prediction_id
   - triggering_ppl_outcome
   - update_session
   - kill_switch_triggered: true/false

5. **Overwrite threshold.** Only overwrite the active parameter if:
   - kill_switch_triggered: false
   - At least 3 independent PPL updates have been processed for this parameter
   - OR native explicitly approves early overwrite

### §3.3 — Feedback loop (prediction → outcome → LL.8 update)

```
PPL prediction emitted (M5-A forward)
    ↓
Outcome observed + recorded in PPL ledger
    ↓
LL.8 trigger: map prediction to DBN parameters
    ↓
Compute posterior (Bayesian update)
    ↓
Kill-switch check (posterior_CI / prior_CI ≤ 2.0 ?)
    ├─ YES → Record update in parameter_register; mark as PENDING_OVERWRITE
    └─ NO  → Record SUSPENDED update; notify native for review
    ↓
After ≥3 updates for same parameter: candidate overwrite to active params
    ↓
Native approval (or auto-approve if kill_switch_triggered: false for all 3+)
    ↓
Active parameter updated; LL.8 update cycle complete
```

## §4 — Parameter register

Path: `06_LEARNING_LAYER/dbn/ll8_bayesian_update/parameter_register.json`

Schema declared in `parameter_register_stub.json` (this directory).

The parameter register is a living JSON file. It starts as the stub (empty/schema-only)
and is populated at M5-D when the first DBN parameter fit is available.

## §5 — Integration with other LL mechanisms

- **LL.1 (per-signal weights):** LL.8 updates can cascade to LL.1 signal weights
  when the updated DBN parameter directly corresponds to an LL.1 signal. This cascade
  is documented in the parameter_register entry with `cascades_to_ll1: [signal_ids]`.

- **LL.9 (counterfactual misses):** When LL.8 kill-switch fires, the underlying
  prediction is also flagged for LL.9 miss registry consideration.

- **PPL (Prospective Prediction Log):** Every PPL outcome triggers an LL.8 candidate
  update. The PPL `outcome_recorded_at` timestamp is the trigger event.

## §6 — Kill-switch definition (KS.LL8.1)

The kill-switch protects against runaway parameter updates caused by:
- Single anomalous outcomes overwhelming prior evidence
- Low-quality PPL outcomes (high uncertainty) inflating credible intervals
- Adversarial or exceptional life events unrepresentative of the base rate

**Definition:** Update is SUSPENDED when posterior_CI_width > 2 × prior_CI_width
for the same parameter at the same credible level (default: 80% credible interval
per NAP.M5.3 policy).

**Recovery:** Native reviews SUSPENDED updates manually. Recovery options:
1. Approve the update with a manual annotation explaining the anomalous outcome
2. Discard the update and flag the PPL entry as low-quality
3. Modify the prior before recomputing (requires new NAP override)

---

*End of LL8_SPEC_v1_0.md — SCAFFOLD status. Activates at M5-D.*
*Governing plan: PHASE_M5_PLAN_v1_0.md §3 M5-A Item 1. Session: M5-A-S1.*
