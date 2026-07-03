-- Migration 393: bodha_msr_signals — salience v2 columns — BA-P3B Step 1
-- Adds the new columns required by salience_formula_v2 (formulas.py).
-- Columns are written by bo_laksana v2; populated on next cascade rebuild (Activity 3).

BEGIN;

ALTER TABLE bodha_msr_signals
    ADD COLUMN IF NOT EXISTS salience_pctl_in_class   NUMERIC(6,4),
    ADD COLUMN IF NOT EXISTS salience_inputs_complete  BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS salience_robustness       NUMERIC(6,4),
    ADD COLUMN IF NOT EXISTS aggregation_member        BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS bala_gate                 NUMERIC(6,4),
    ADD COLUMN IF NOT EXISTS functional_context_score  NUMERIC(6,4),
    ADD COLUMN IF NOT EXISTS verification_rescale      NUMERIC(6,4),
    ADD COLUMN IF NOT EXISTS present_but_enfeebled     BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS class_prior               NUMERIC(8,6) DEFAULT 1.0;

COMMENT ON COLUMN bodha_msr_signals.salience_pctl_in_class IS
  'S-A: percentile of computed_salience within (signal_type_class × chart × ayanamsha). '
  'Priors decide BETWEEN families; percentiles rank WITHIN families.';

COMMENT ON COLUMN bodha_msr_signals.salience_inputs_complete IS
  'S-C: FALSE when any salience input fell back to a silent default '
  '(trap #17 — no silent 0.5/1.0/bindus=4 substitution). Signals with FALSE '
  'carry lower epistemic weight; reviewed by L5 calibration.';

COMMENT ON COLUMN bodha_msr_signals.salience_robustness IS
  'S-D: cross-ayanamsha consistency score for this signal. '
  'Computed in second pass over all 5 ayanamsha variants.';

COMMENT ON COLUMN bodha_msr_signals.aggregation_member IS
  'TRUE for atomic sub-signals that roll into a composite profile signal. '
  'Atomic members are never placed in top-band rankings.';

COMMENT ON COLUMN bodha_msr_signals.bala_gate IS
  'yoga-class signals only: clamp(norm_constituent_shadbala, 0.30, 1.00). '
  'NULL for non-yoga-class signals. Part of salience_formula_v2.';

COMMENT ON COLUMN bodha_msr_signals.present_but_enfeebled IS
  'yoga-class: TRUE when bala_gate < 0.60 — the planet is active but weakened. '
  'A state descriptor, not an exclusion filter.';

COMMENT ON COLUMN bodha_msr_signals.class_prior IS
  'brahma_class_priors weight for (signal_type_class × source_subsystem). '
  'DEFAULT 1.0 if no matching row found in priors table.';

COMMENT ON COLUMN bodha_msr_signals.verification_rescale IS
  '{two_pass_verified:1.00, single_pass:0.85, documented_approximation:0.60}. '
  'Replaces log(1+corroboration)/log(10) which had 0.778 ceiling (C5 fix).';

COMMENT ON COLUMN bodha_msr_signals.functional_context_score IS
  'ga_structural functional benefic/malefic per lagna: benefic=1.1, malefic=0.9, neutral=1.0.';

COMMIT;
