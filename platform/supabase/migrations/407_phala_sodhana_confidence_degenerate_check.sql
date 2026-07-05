-- 407_phala_sodhana_confidence_degenerate_check.sql
-- =============================================================================
-- BA_FULL_ASSET_AUDIT fix-forward pass — ph_sodhana finding (L2-Data): the
-- five existing detectors all operate per-anchor, so a posterior/confidence
-- model that has collapsed to a single constant value across every anchor in
-- a chart (e.g. ph_nimitta fed hardcoded defaults instead of per-anchor
-- computed inputs) trips zero per-anchor anomalies and reads as a clean bill
-- of health. A new chart-wide detector (detect_confidence_degenerate in
-- services/ph_sodhana/engine.py) flags chart-wide zero-variance confidence_high
-- as its own anomaly_type. This migration widens the CHECK constraint that
-- previously enumerated only the original 5 anomaly_type values.
--
-- Registry-only / schema-only change; no writer behavior for the existing 5
-- detectors is modified; no rebuild triggered.

BEGIN;

ALTER TABLE phala_sodhana
  DROP CONSTRAINT IF EXISTS phala_sodhana_anomaly_type_check;

ALTER TABLE phala_sodhana
  ADD CONSTRAINT phala_sodhana_anomaly_type_check CHECK (anomaly_type IN (
    'confidence_inflation',
    'magnitude_drift',
    'falsifier_absent',
    'ledger_gap',
    'layer_leakage',
    'confidence_degenerate'
  ));

COMMIT;
