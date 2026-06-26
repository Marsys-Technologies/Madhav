-- Migration 349: mi_gunanaka — learned-weight register
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_multipliers (
  chart_id                  uuid        NOT NULL,
  weight_id                 text        NOT NULL,
  mechanism                 text        NOT NULL,  -- 'LL1'|'LL2'..'LL8'
  target_kind               text        NOT NULL,  -- 'signal'|'family'|'edge'|'window'
  target_ref                text        NOT NULL,
  domain                    text,
  raw_multiplier            numeric     NOT NULL,
  evidence_factor           numeric     NOT NULL,
  applied_multiplier        numeric     NOT NULL,
  n_observations            int         NOT NULL,
  held_out_validity         text        NOT NULL,
  promotion_status          text        NOT NULL,  -- 'prior_only'|'earning'|'promoted'|'suspended'
  gate_passed               boolean     NOT NULL,
  confidence_high           boolean     NOT NULL,
  neg_control_clear         boolean     NOT NULL,
  kill_switch_state         text        NOT NULL,  -- 'active'|'suspended_degrading'|'suspended_divergence'
  divergence_from_classical numeric,
  audit_trail               jsonb       NOT NULL,
  weight_formula_version    text        NOT NULL,
  updated_at                timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, weight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_multipliers_chart_id
  ON mimamsa_multipliers (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_multipliers_mechanism
  ON mimamsa_multipliers (chart_id, mechanism);

CREATE INDEX IF NOT EXISTS idx_mimamsa_multipliers_target
  ON mimamsa_multipliers (chart_id, target_kind, target_ref);

COMMIT;
