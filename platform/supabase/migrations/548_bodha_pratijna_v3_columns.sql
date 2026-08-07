BEGIN;
ALTER TABLE bodha_pratijna
  ADD COLUMN IF NOT EXISTS occurrence_grade NUMERIC(5,3),
  ADD COLUMN IF NOT EXISTS condition_grade NUMERIC(5,3);
COMMENT ON COLUMN bodha_pratijna.occurrence_grade IS 'v3: Occurrence judgment grade — does the chart promise this event?';
COMMENT ON COLUMN bodha_pratijna.condition_grade IS 'v3: Condition reading grade — how afflicted/supported is the configuration?';
COMMIT;
