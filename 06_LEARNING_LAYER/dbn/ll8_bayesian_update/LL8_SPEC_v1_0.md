---
artifact: LL8_SPEC_v1_0.md
canonical_id: LL8_SPEC
version: "1.1"
status: ACTIVE
mechanism: LL.8
mechanism_label: Bayesian Model Updating
produced_during: M5-A-S1
produced_on: 2026-05-13
activated_during: M5-E-S1
activated_on: 2026-05-14
authored_by: claude-sonnet-4-6
governing_plan: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md §3 M5-A Item 1
activation_condition: >
  DBN parameters exist (dbn_params_v1_0.json PASS, M5-D-S2).
  Held-out validation PASS (mean_lift=1.145, beat_fraction=5/5, M5-D-S3).
  NAP.M5.3 CI reporting policy APPROVED (M5-D-S3).
  All three conditions met as of 2026-05-13. LL.8 is ACTIVE from M5-E close.
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
  - v1.1 (2026-05-14, M5-E-S1): Status SCAFFOLD → ACTIVE. All three activation
      conditions confirmed met (dbn_params_v1_0.json PASS, held-out mean_lift=1.145,
      NAP.M5.3 APPROVED). Added §2b conjugate Beta update protocol (precise cell-level
      update rule). Added §6 Activation Status section. parameter_register.json
      initialized (update_count=0). First live update will fire on next LEL training
      event added post-M5 close.
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

### §3.2b — Conjugate Beta cell-level update protocol (ACTIVE from M5-E)

For new LEL training-partition events, the precise update rule is:

For each new event E with domain D and dasha lord MD:
  1. Identify the CPT row: `dasha_to_domain_posteriors[MD][D]` in dbn_params_v1_0.json
  2. Read current (alpha, beta) for the relevant state cell
  3. Apply conjugate Beta update:
     - If event domain-state = ELEVATED: alpha ← alpha + 1
     - If event domain-state = SUPPRESSED: beta ← beta + 1
     - If event domain-state = NORMAL: no update (NORMAL is the residual state)
  4. Recompute posterior mean = alpha / (alpha + beta)
  5. Write updated (alpha, beta) back to dbn_params_v1_0.json with:
     - update_log entry: {date, event_id, domain, md_lord, update_type}
     - version bump: patch increment (e.g., 1.0 → 1.0.1)
  6. Regenerate 90% HDI via Monte Carlo (300,000 samples, seed = 42 + update_count)
  7. Archive the pre-update JSON snapshot in
     `06_LEARNING_LAYER/dbn/param_history/` with ISO timestamp

Additional kill-switch conditions (supplement to KS.LL8.1):
  - posterior_mean for any domain-state cell < 0.02 or > 0.98
    (degenerate posterior → flag for native review; do not update)
  - alpha + beta > 500 for any cell
    (overfitting risk → convene M7 re-fit; halt updates for that cell)
  - New event's dasha lord not present in existing CPT
    (topology gap → open DISAGREEMENT_REGISTER entry class topology_gap; defer update)

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

## §6 — Activation Status

LL.8 is **ACTIVE** as of M5-E close (2026-05-14).

All three activation conditions are confirmed:

| Condition | Evidence | Date |
|---|---|---|
| DBN parameters exist + fitted | `dbn_params_v1_0.json` PASS (AC.M5D.2) | 2026-05-13 |
| Held-out validation PASS | mean_lift=1.145, beat_fraction=5/5 (AC.M5D.3) | 2026-05-13 |
| NAP.M5.3 CI policy APPROVED | `NAP_M5_3_CI_REPORTING_POLICY_v1_0.md` | 2026-05-13 |

First live update will occur when the next LEL event is added to the training partition
after M5 close. Until then, `parameter_register.json` holds update_count=0.

The SCAFFOLD-era `parameter_register_stub.json` is superseded by the active
`parameter_register.json` in this directory; the stub is retained for historical audit.

---

*End of LL8_SPEC_v1_0.md — v1.1 ACTIVE status. Activated M5-E-S1 2026-05-14.*
*Governing plan: PHASE_M5_PLAN_v1_0.md §3 M5-A Item 1. Original session: M5-A-S1.*
