-- Migration 398: phala_anchors — posterior model columns (BA-P5B)
-- Adds posterior point estimate + lift vector + structured falsifier to phala_anchors.
-- G-LADDER (confidence_low/confidence_high) RETAINED for backward compat — values
-- are now derived as (posterior ± 0.05) clamped to [0.01, 0.80].
-- JL-009 OPEN GATE: posterior values use placeholder base_rate=0.10 until native
-- reviews and ratifies brahma_event_ontology base-rate priors before anchor freeze.

BEGIN;

ALTER TABLE phala_anchors
    ADD COLUMN IF NOT EXISTS posterior              DOUBLE PRECISION
        CHECK (posterior >= 0.0 AND posterior <= 1.0),
    ADD COLUMN IF NOT EXISTS lift_vector_jsonb      JSONB,
    ADD COLUMN IF NOT EXISTS structured_falsifier_jsonb JSONB;

COMMENT ON COLUMN phala_anchors.posterior IS
  'BA-P5B: Bayesian product-model posterior. '
  'posterior = base_rate × promise_lift × activation_lift × trigger_lift × robustness_mod. '
  'Replaces the G-LADDER point estimate; confidence_low/confidence_high are now a ±0.05 '
  'compatibility band derived from this value. '
  'JL-009: base_rate priors are PLACEHOLDERS — not calibrated until native freeze.';

COMMENT ON COLUMN phala_anchors.lift_vector_jsonb IS
  'BA-P5B: AnchorLiftVector decomposition — '
  '{base_rate, promise_lift, activation_lift, trigger_lift, '
  'ayanamsha_robustness_modifier, posterior}. '
  'Enables per-factor audit and reweighting without rebuilding anchors.';

COMMENT ON COLUMN phala_anchors.structured_falsifier_jsonb IS
  'BA-P5B: StructuredFalsifier — machine-evaluable refutation spec: '
  '{event_class_id, magnitude_floor, domain, window_end, attestation_required, '
  'refutation_condition, confirmation_condition}. '
  'Drives L5 mi_pramana adjudication and LEL intake form. '
  'The legacy `falsifier` text column is kept for human-readable display.';

COMMIT;
