-- MARSYS Chat V2 — γ3: Prediction logging (PPL)
-- DO NOT APPLY automatically — §M manual intervention required.
-- Apply to staging first, verify, then production.
--
-- Learning Layer rule #4: outcome NEVER captured at logging time.
-- Only captured at later observation. outcome column is intentionally nullable.

CREATE TABLE IF NOT EXISTS predictions (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id             UUID NOT NULL REFERENCES query_trace_steps(query_id) ON DELETE CASCADE,
  conversation_id      UUID REFERENCES conversations(id) ON DELETE SET NULL,
  prediction_text      TEXT NOT NULL,
  confidence           NUMERIC(4, 3) CHECK (confidence >= 0 AND confidence <= 1),
  horizon              TEXT,        -- e.g. "6 months", "1 year", "by 2026-12"
  falsifier            TEXT,        -- condition that would prove the prediction wrong
  logged_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- Outcome fields — NEVER populated at logging time (Learning Layer rule #4)
  outcome              TEXT    NULL,
  outcome_observed_at  TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS predictions_query_id_idx ON predictions (query_id);
CREATE INDEX IF NOT EXISTS predictions_conversation_id_idx ON predictions (conversation_id);
CREATE INDEX IF NOT EXISTS predictions_logged_at_idx ON predictions (logged_at DESC);

-- RLS: owner-only reads (predictions are owned by the chart's owner via query_trace_steps)
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY predictions_select ON predictions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM query_trace_steps qts
      WHERE qts.query_id = predictions.query_id
        AND qts.user_id = auth.uid()
    )
  );

CREATE POLICY predictions_insert ON predictions
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM query_trace_steps qts
      WHERE qts.query_id = predictions.query_id
        AND qts.user_id = auth.uid()
    )
  );

COMMENT ON TABLE predictions IS
  'PPL: Prospective Prediction Log. Records time-indexed predictions from assistant output. '
  'outcome is intentionally nullable — never captured at logging time per Learning Layer rule #4.';
