-- Migration 333: phala_sodhana — Predictive Anchor Anomaly Registry
-- Part of L4 Phala Wave 5. Depends on migration 330 (phala_anchors).
--
-- LEAKAGE-FIREWALL gate (D43a): ph_sodhana detects anomalies + layers leakage.
-- It NEVER auto-corrects and NEVER writes calibration scores (L5 boundary).
-- auto_action column ONLY permits 'stage_for_review'; any attempt to write
-- 'apply' or 'calibrate' is a hard constraint violation.
--
-- Anomaly types detected:
--   confidence_inflation  — confidence_high > G-LADDER ceiling for its n_independent
--   magnitude_drift       — magnitude inconsistent with convergence_score
--   falsifier_absent      — falsifier field empty or not machine-evaluable
--   ledger_gap            — derivation_ledger_jsonb missing required axes
--   layer_leakage         — L5 calibration data found in an L4 field
--                           → writer HALTS with RuntimeError (LEAKAGE-FIREWALL)

CREATE TABLE IF NOT EXISTS phala_sodhana (
    sodhana_id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            uuid        NOT NULL,
    anchor_id           uuid        NOT NULL REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE,

    -- Detection
    anomaly_type        text        NOT NULL CHECK (anomaly_type IN (
                                        'confidence_inflation',
                                        'magnitude_drift',
                                        'falsifier_absent',
                                        'ledger_gap',
                                        'layer_leakage'
                                    )),
    anomaly_severity    text        NOT NULL CHECK (anomaly_severity IN (
                                        'critical', 'major', 'minor', 'informational'
                                    )),
    detected_field      text        NOT NULL,   -- which phala_anchors column triggered this

    -- Evidence
    expected_value_text text,
    observed_value_text text,
    leakage_class       text        CHECK (leakage_class IN (
                                        'interpretation_in_fact_field',
                                        'l5_calibration_attempted',
                                        'l2_contamination'
                                    )),         -- NULL unless anomaly_type = 'layer_leakage'

    -- Recommendation
    recommendation_text text        NOT NULL,

    -- LEAKAGE-FIREWALL constraint: only 'stage_for_review' is permitted
    auto_action         text        NOT NULL DEFAULT 'stage_for_review'
                                    CHECK (auto_action = 'stage_for_review'),

    -- Provenance
    derivation_ledger_jsonb jsonb   NOT NULL,
    source_citation     text        NOT NULL,
    computed_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS phala_sodhana_chart_id ON phala_sodhana (chart_id);
CREATE INDEX IF NOT EXISTS phala_sodhana_anchor_id ON phala_sodhana (anchor_id);
CREATE INDEX IF NOT EXISTS phala_sodhana_severity  ON phala_sodhana (anomaly_severity, anomaly_type);

-- Natural key: one anomaly_type per (anchor_id, detected_field)
CREATE UNIQUE INDEX IF NOT EXISTS phala_sodhana_natural_key
    ON phala_sodhana (anchor_id, anomaly_type, detected_field);

COMMENT ON TABLE phala_sodhana IS
'L4 Phala Anomaly Registry — flags confidence inflation, magnitude drift, '
'missing falsifiers, ledger gaps, and layer-leakage. auto_action is CONSTRAINED '
'to stage_for_review only. Layer leakage triggers writer HALT (LEAKAGE-FIREWALL gate).';

COMMENT ON COLUMN phala_sodhana.auto_action IS
'LOCKED to stage_for_review. The DB constraint enforces this; the writer also '
'enforces it at the Python level. No auto-apply, no auto-calibrate (D43a).';
