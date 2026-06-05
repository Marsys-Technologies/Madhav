-- Migration 064: add user_id to query_trace_steps
-- Required by /api/predictions ownership check (O4 fix).
-- Purely additive: ADD COLUMN IF NOT EXISTS + sparse index.
-- Safe to apply on live table; no locks beyond brief index build.

ALTER TABLE query_trace_steps
  ADD COLUMN IF NOT EXISTS user_id TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_qts_user_id
  ON query_trace_steps (user_id)
  WHERE user_id IS NOT NULL;

COMMENT ON COLUMN query_trace_steps.user_id IS
  'Added by 064 to support PPL ownership check in /api/predictions.';
