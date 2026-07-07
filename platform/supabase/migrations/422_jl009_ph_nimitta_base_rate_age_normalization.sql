-- Migration 422: JL-009 point-2 — record the ph_nimitta base_rate age-normalization rule
-- as a formula constant (code, not convention). Created: 2026-07-07
--
-- Native/Ācārya-Pratinidhi structural directive (BA_PHASE4_RUNWAY_PLAN R1.1, point 2):
-- the brahma_event_ontology.base_rate_by_age weights are RELATIVE per-class age weights
-- with inconsistent per-row sums (observed 0.81–1.30) — NOT a probability distribution.
-- ph_nimitta's base_rate consumption MUST row-normalize the age-band vector to sum 1.0 at
-- lookup, then select the band containing the anchor's predicted date (peak_date, else
-- window_start) relative to the native's birth date; age-unknown → uniform prior (0.20).
-- Implemented in services/ph_nimitta/base_rate.py; asserted by test_ph_nimitta_base_rate.
-- This entry makes the rule a durable, discoverable formula constant (class=engineering:
-- document-only, not a tunable value).

BEGIN;

INSERT INTO brahma_formula_constants
  (constant_id, value_jsonb, class, consumer_assets, citation_or_ratification, calibratable, bounds, version)
VALUES
  ('ph_nimitta_base_rate_age_normalization',
   '{"rule":"row_normalize_to_1_then_select_age_band",
     "source":"brahma_event_ontology.base_rate_by_age",
     "age_basis":"native age at anchor peak_date (else window_start) vs birth datetime_iso",
     "bands":["band_0_12","band_13_25","band_26_40","band_41_60","band_60_plus"],
     "age_unknown_fallback":"uniform_prior",
     "uniform_prior":0.20,
     "consumer_formula":"posterior = base_rate * promise_lift * activation_lift * trigger_lift * robustness_mod"}'::jsonb,
   'engineering',
   ARRAY['ph_nimitta'],
   'JL-009 point-2 (native glance 2026-07-07, BA_JUDGMENT_LEDGER): base_rate_by_age rows are relative weights (sums 0.81-1.30); ph_nimitta must row-normalize to 1.0 at lookup and pick the age band of the anchor date. Code: services/ph_nimitta/base_rate.py; test: tests/test_ph_nimitta_base_rate.py.',
   false,
   NULL,
   '1.0')
ON CONFLICT (constant_id) DO UPDATE
  SET value_jsonb              = EXCLUDED.value_jsonb,
      class                    = EXCLUDED.class,
      consumer_assets          = EXCLUDED.consumer_assets,
      citation_or_ratification = EXCLUDED.citation_or_ratification,
      calibratable             = EXCLUDED.calibratable,
      bounds                   = EXCLUDED.bounds,
      version                  = EXCLUDED.version;

COMMIT;

-- DOWN:
-- DELETE FROM brahma_formula_constants WHERE constant_id = 'ph_nimitta_base_rate_age_normalization';
