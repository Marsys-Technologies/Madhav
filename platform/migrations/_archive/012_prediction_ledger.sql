-- 012_prediction_ledger.sql
-- MARSYS-JIS Phase 4 Stream B: prediction_ledger table
-- Holds time-indexed predictions for prospective calibration (CLAUDE.md §E, Learning Layer rule #4).
-- The outcome column is intentionally nullable: it is populated post-hoc only after reality
-- checks in. Writing a prediction with outcome pre-populated is refused by the writer layer.
--
-- ROLLBACK: If this migration fails partway, run:
--   DROP INDEX IF EXISTS idx_prediction_ledger_subject_horizon;
--   DROP INDEX IF EXISTS idx_prediction_ledger_horizon_start;
--   DROP INDEX IF EXISTS idx_prediction_ledger_query_id;
--   DROP TABLE IF EXISTS prediction_ledger;

CREATE TABLE IF NOT EXISTS prediction_ledger (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id              UUID        NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  prediction_text       TEXT        NOT NULL,
  confidence            NUMERIC(4,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  horizon_start         DATE        NOT NULL,
  horizon_end           DATE        NOT NULL,
  falsifier             TEXT        NOT NULL,
  subject               TEXT        NOT NULL DEFAULT 'native:abhisek',
  outcome               TEXT,
  outcome_observed_at   TIMESTAMPTZ,
  calibration_bucket    TEXT
);

CREATE INDEX IF NOT EXISTS idx_prediction_ledger_query_id
  ON prediction_ledger (query_id);

CREATE INDEX IF NOT EXISTS idx_prediction_ledger_horizon_start
  ON prediction_ledger (horizon_start);

CREATE INDEX IF NOT EXISTS idx_prediction_ledger_subject_horizon
  ON prediction_ledger (subject, horizon_start);
