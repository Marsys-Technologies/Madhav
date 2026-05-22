-- Migration 075b: mcp_prediction_outcomes remediation
-- MCPT v3.1 post-deploy fix
-- Migration 075 could not create mcp_prediction_outcomes because it referenced
-- mcp_predictions(id uuid) but the v1 table has prediction_id text PK.
-- This remediation creates mcp_prediction_outcomes against the actual schema.

CREATE TABLE IF NOT EXISTS mcp_prediction_outcomes (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id    text        NOT NULL REFERENCES mcp_predictions(prediction_id) ON DELETE CASCADE,
  outcome_text     text        NOT NULL,
  outcome_occurred boolean     NOT NULL,
  outcome_date     date        NOT NULL,
  recorded_by      text        NOT NULL DEFAULT 'operator',
  calibration_note text,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mcp_prediction_outcomes_prediction_id
  ON mcp_prediction_outcomes (prediction_id);

CREATE INDEX IF NOT EXISTS mcp_prediction_outcomes_outcome_date
  ON mcp_prediction_outcomes (outcome_date DESC);

COMMENT ON TABLE mcp_prediction_outcomes IS
  'Outcome records for prior MCP predictions (PPL discipline). '
  'References mcp_predictions(prediction_id text) — v1 PK schema. '
  'Remediation of migration 075 which assumed uuid PK. MCPT v3.1.';

-- ── DOWN ───────────────────────────────────────────────────────────────────────
-- DROP INDEX IF EXISTS mcp_prediction_outcomes_outcome_date;
-- DROP INDEX IF EXISTS mcp_prediction_outcomes_prediction_id;
-- DROP TABLE IF EXISTS mcp_prediction_outcomes;
