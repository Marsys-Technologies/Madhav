-- Migration 075: Prediction Outcomes + mcp_predictions extensions
-- MCPT v3.1.0-S4
-- mcp_prediction_outcomes: outcome recording against prior predictions.
-- mcp_predictions extensions: adds calibration columns.

-- ── UP ─────────────────────────────────────────────────────────────────────────

-- mcp_predictions base table (if not already created by migration 071)
CREATE TABLE IF NOT EXISTS mcp_predictions (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  trace_id        text        NOT NULL,
  user_uid        text        NOT NULL,
  prediction_text text        NOT NULL,
  confidence      float       NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
  horizon_days    integer     NOT NULL CHECK (horizon_days > 0),
  falsifier       text        NOT NULL,
  signal_ids      text[]      NOT NULL DEFAULT '{}',
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz GENERATED ALWAYS AS (created_at + (horizon_days || ' days')::interval) STORED
);

-- Add calibration columns to mcp_predictions (idempotent)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'mcp_predictions' AND column_name = 'resolved'
  ) THEN
    ALTER TABLE mcp_predictions
      ADD COLUMN resolved       boolean,                -- null = open; true = correct; false = incorrect
      ADD COLUMN resolved_at    timestamptz,
      ADD COLUMN brier_score    float;                  -- Brier score = (p - outcome)^2; lower is better
  END IF;
END $$;

-- mcp_prediction_outcomes: outcome records
CREATE TABLE IF NOT EXISTS mcp_prediction_outcomes (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id    uuid        NOT NULL REFERENCES mcp_predictions(id) ON DELETE CASCADE,
  outcome_text     text        NOT NULL,                -- description of what actually happened
  outcome_occurred boolean     NOT NULL,                -- did the predicted event occur?
  outcome_date     date        NOT NULL,                -- when the outcome was observed
  recorded_by      text        NOT NULL DEFAULT 'operator',  -- 'operator' | 'system' | 'native'
  calibration_note text,                               -- operator commentary on confidence calibration
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS mcp_predictions_user_uid
  ON mcp_predictions (user_uid, created_at DESC);

CREATE INDEX IF NOT EXISTS mcp_predictions_horizon
  ON mcp_predictions (expires_at)
  WHERE resolved IS NULL;

CREATE INDEX IF NOT EXISTS mcp_prediction_outcomes_prediction_id
  ON mcp_prediction_outcomes (prediction_id);

COMMENT ON TABLE mcp_prediction_outcomes IS
  'Outcome records for prior MCP predictions (PPL discipline). '
  'One row per outcome recording against mcp_predictions. '
  'Brier score populated on the parent mcp_predictions row after outcome is recorded. '
  'MCPT v3.1.0-S4.';

COMMENT ON COLUMN mcp_predictions.brier_score IS
  'Brier score = (confidence - outcome)^2. Range 0.0–1.0; lower = better calibration. '
  'Populated when an outcome is recorded via mcp_prediction_outcomes.';

-- ── DOWN ───────────────────────────────────────────────────────────────────────

-- To rollback:
-- DROP INDEX IF EXISTS mcp_prediction_outcomes_prediction_id;
-- DROP INDEX IF EXISTS mcp_predictions_horizon;
-- DROP INDEX IF EXISTS mcp_predictions_user_uid;
-- DROP TABLE IF EXISTS mcp_prediction_outcomes;
-- ALTER TABLE mcp_predictions
--   DROP COLUMN IF EXISTS resolved,
--   DROP COLUMN IF EXISTS resolved_at,
--   DROP COLUMN IF EXISTS brier_score;
