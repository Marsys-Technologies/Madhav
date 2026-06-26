-- Migration 348: mi_pramana — matcher + scorecard + calibration
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_calibration (
  chart_id                   uuid        NOT NULL,
  match_id                   text        NOT NULL,
  prediction_id              text        NOT NULL,
  event_id                   text        NOT NULL,
  score_timing               numeric     NOT NULL,
  score_magnitude            numeric     NOT NULL,
  score_domain               numeric     NOT NULL,
  score_falsifier            numeric     NOT NULL,
  score_manifestation        numeric     NOT NULL,
  manifestation_channel      text,
  composite_verdict          text        NOT NULL,  -- 'confirmed'|'partial'|'denied'|'pending'
  composite_score            numeric     NOT NULL,
  base_rate_adjusted_skill   numeric,
  evidence_admissibility     text        NOT NULL,  -- 'clean'|'contaminated'|'held_out'
  n_for_stratum              int         NOT NULL,
  leakage_status             text        NOT NULL,
  scoring_formula_version    text        NOT NULL,
  scored_at                  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, match_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_chart_id
  ON mimamsa_calibration (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_prediction
  ON mimamsa_calibration (chart_id, prediction_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_verdict
  ON mimamsa_calibration (chart_id, composite_verdict);

CREATE TABLE IF NOT EXISTS mimamsa_reliability (
  chart_id                uuid        NOT NULL,
  stratum_key             text        NOT NULL,
  predicted_prob_bin      numrange    NOT NULL,
  observed_rate           numeric,
  n                       int         NOT NULL,
  ci_low                  numeric,
  ci_high                 numeric,
  brier_score             numeric,
  log_loss                numeric,
  ece                     numeric,
  hit_rate_by_tier        numeric,
  held_out_validity       text        NOT NULL,  -- 'pass'|'fail'|'insufficient_n'
  evidence_grade          text        NOT NULL,  -- 'empirical'|'prior_only'|'structural'
  calibration_formula_ver text        NOT NULL,
  computed_at             timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, stratum_key, predicted_prob_bin)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_reliability_chart_id
  ON mimamsa_reliability (chart_id);

COMMIT;
