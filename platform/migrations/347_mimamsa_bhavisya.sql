-- Migration 347: mi_bhavisya — frozen prediction bundle
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_predictions (
  chart_id               uuid        NOT NULL,
  prediction_id          text        NOT NULL,
  source_pramana_id      text        NOT NULL,
  outcome_claim          text        NOT NULL,
  domain                 text        NOT NULL,
  observation_window     daterange   NOT NULL,
  eval_date              date        NOT NULL,
  confidence_band        numrange    NOT NULL,
  magnitude_expected     text        NOT NULL,
  falsifier_jsonb        jsonb       NOT NULL,
  base_rate              numeric,
  emitted_at             timestamptz NOT NULL,
  lifecycle_status       text        NOT NULL,  -- 'pending'|'due'|'confirmed'|'denied'|'partial'
  driving_signals        jsonb       NOT NULL,
  frozen_bundle_hash     text        NOT NULL,
  bundle_formula_version text        NOT NULL,
  created_at             timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_chart_id
  ON mimamsa_predictions (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_lifecycle
  ON mimamsa_predictions (chart_id, lifecycle_status);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_eval_date
  ON mimamsa_predictions (chart_id, eval_date);

CREATE TABLE IF NOT EXISTS mimamsa_manifestation_sets (
  chart_id      uuid        NOT NULL,
  prediction_id text        NOT NULL,
  channel_id    text        NOT NULL,
  domain        text        NOT NULL,
  source        text        NOT NULL,
  citation_ref  jsonb       NOT NULL,
  is_literal    boolean     NOT NULL,
  frozen_at     timestamptz NOT NULL,
  PRIMARY KEY (chart_id, prediction_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_manifestation_sets_chart_id
  ON mimamsa_manifestation_sets (chart_id);

COMMIT;
