-- Migration 119: deterministic-stamp columns on mcp_predictions for Wave-4 learning loop
--
-- Adds the columns 4.learning_loop wires into onFinish so every chat completion logs a
-- row keyed on query_hash (idempotent). Lets the LL substrate later calibrate the
-- computed_salience formula by comparing replays across formula versions for the
-- same (chart_id, ayanamsha_id, query_hash).
--
-- Additive only. Existing columns (prediction_text, confidence, horizon, falsifier)
-- become NULLABLE for the calibration-stamp use-case (a chat completion has no
-- horizon/falsifier — that's only for explicit predictions via /mcp/writes/log_prediction).

ALTER TABLE mcp_predictions
  ADD COLUMN IF NOT EXISTS chart_id                 text,
  ADD COLUMN IF NOT EXISTS ayanamsha_id             text,
  ADD COLUMN IF NOT EXISTS query_hash               text,
  ADD COLUMN IF NOT EXISTS salience_formula_version text,
  ADD COLUMN IF NOT EXISTS model_id                 text,
  ADD COLUMN IF NOT EXISTS predicted_at_iso         timestamptz;

-- Relax NOT NULL constraints so calibration stamps (without horizon/falsifier) can write.
ALTER TABLE mcp_predictions ALTER COLUMN horizon         DROP NOT NULL;
ALTER TABLE mcp_predictions ALTER COLUMN domain          DROP NOT NULL;
ALTER TABLE mcp_predictions ALTER COLUMN prediction_text DROP NOT NULL;
ALTER TABLE mcp_predictions ALTER COLUMN confidence      DROP NOT NULL;
ALTER TABLE mcp_predictions ALTER COLUMN falsifier       DROP NOT NULL;
ALTER TABLE mcp_predictions ALTER COLUMN key_id          DROP NOT NULL;

-- Idempotency: one row per (chart_id, ayanamsha_id, query_hash, salience_formula_version)
CREATE UNIQUE INDEX IF NOT EXISTS mcp_predictions_stamp_uq
  ON mcp_predictions (chart_id, ayanamsha_id, query_hash, salience_formula_version)
  WHERE chart_id IS NOT NULL
    AND ayanamsha_id IS NOT NULL
    AND query_hash IS NOT NULL
    AND salience_formula_version IS NOT NULL;

CREATE INDEX IF NOT EXISTS mcp_predictions_chart_idx
  ON mcp_predictions (chart_id, predicted_at_iso DESC)
  WHERE chart_id IS NOT NULL;
