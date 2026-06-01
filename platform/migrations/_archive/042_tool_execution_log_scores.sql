-- 042_tool_execution_log_scores.sql
-- GANGA-OVERNIGHT-S1 P7 D.7.4
--
-- Per-tool quality score columns. Purely additive — no DROP, no NOT NULL,
-- no constraint changes. Safe to roll out without coordination. Brief NOTE:
-- this migration is AUTHORED but NOT applied by the overnight run; the
-- operator runs it during business hours.

ALTER TABLE tool_execution_log
  ADD COLUMN IF NOT EXISTS retrieval_score real,
  ADD COLUMN IF NOT EXISTS rows_returned integer,
  ADD COLUMN IF NOT EXISTS token_estimate integer;

-- Best-effort backfill from existing payload jsonb. Skips rows whose payload
-- doesn't carry an array-shaped 'rows' field. retrieval_score and
-- token_estimate are not backfilled here — there's no clean source.
UPDATE tool_execution_log
   SET rows_returned = jsonb_array_length(payload -> 'rows')
 WHERE rows_returned IS NULL
   AND payload ? 'rows'
   AND jsonb_typeof(payload -> 'rows') = 'array';
