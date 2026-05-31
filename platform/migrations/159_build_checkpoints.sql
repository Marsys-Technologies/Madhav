-- 159_build_checkpoints.sql
-- Per-asset checkpoint tracking for resumable builds.
-- NOTE: Table already created via 159_build_checkpoints.sql; this file is
-- idempotent and safe to apply on a DB that already has these objects.
CREATE TABLE IF NOT EXISTS build_checkpoints (
  build_id       uuid        NOT NULL,
  asset_id       text        NOT NULL,
  ayanamsha_id   text        NOT NULL,
  status         text        NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending','running','success','failed','stopped','skipped')),
  completed_at   timestamptz,
  pct_complete   numeric(5,2) DEFAULT 0,
  error_text     text,
  retry_count    int         NOT NULL DEFAULT 0,
  started_at     timestamptz,
  PRIMARY KEY (build_id, asset_id, ayanamsha_id)
);
CREATE INDEX IF NOT EXISTS build_checkpoints_status_idx ON build_checkpoints(build_id, status);
CREATE INDEX IF NOT EXISTS build_checkpoints_asset_idx  ON build_checkpoints(asset_id, status);
