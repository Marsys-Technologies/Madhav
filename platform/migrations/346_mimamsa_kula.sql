-- Migration 346: mi_kula — signal-family registry + negative controls
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_signal_families (
  family_id           text        NOT NULL,
  display_name        text        NOT NULL,
  layman_name         text        NOT NULL,
  family_class        text        NOT NULL,  -- 'classical'|'external_science'|'tradition'|'negative_control'
  evidence_tier       text        NOT NULL,  -- 'TIER1_SCIENCE'|'TIER2_PLAUSIBLE'|'TRADITION'|'NEGATIVE_CONTROL'|'CLASSICAL_CITED'
  soundness_basis     text        NOT NULL,  -- 'scientific'|'astrological'|'both'
  binding_kind        text        NOT NULL,  -- 'natal'|'event_date'|'lifetime_index'|'meta'
  default_state       text        NOT NULL,  -- 'ON'|'OFF'|'CONTROL_ONLY'
  prior_weight        numeric     NOT NULL,
  calibration_status  text        NOT NULL,  -- 'prior_only'|'earning'|'promoted'|'suspended'
  citation_refs       jsonb       NOT NULL,
  binding_spec        jsonb       NOT NULL,
  data_source_pin     jsonb,
  apply_point         text,
  interaction_value   numeric,
  interaction_status  text,
  is_active           boolean     NOT NULL,
  formula_version     text        NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (family_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_signal_families_class
  ON mimamsa_signal_families (family_class);

CREATE INDEX IF NOT EXISTS idx_mimamsa_signal_families_tier
  ON mimamsa_signal_families (evidence_tier);

CREATE TABLE IF NOT EXISTS mimamsa_negative_controls (
  control_id           text        NOT NULL,
  known_false_basis    text        NOT NULL,
  citation_refs        jsonb       NOT NULL,
  binding_spec         jsonb       NOT NULL,
  expected_score       text        NOT NULL,
  tolerance            numeric     NOT NULL,
  last_harness_score   numeric,
  last_harness_status  text,       -- 'pass'|'FAIL'
  formula_version      text        NOT NULL,
  PRIMARY KEY (control_id)
);

COMMIT;
