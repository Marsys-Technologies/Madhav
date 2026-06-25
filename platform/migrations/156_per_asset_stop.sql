-- 156_per_asset_stop.sql
-- Ensure build_events exists (it was dropped in a teardown migration after 118
-- applied it; references in dispatcher.py / engine.py / API routes still need it)
-- then add per-asset stop signal columns.
-- All statements are idempotent (IF NOT EXISTS / IF NOT EXISTS DEFAULT).

CREATE TABLE IF NOT EXISTS build_events (
  build_id        text        NOT NULL,
  stage_seq       integer     NOT NULL,
  chart_id        text        NOT NULL,
  ayanamsha_role  text        NOT NULL,
  asset           text        NOT NULL,
  stage           text        NOT NULL,
  status          text        NOT NULL,
  percent         numeric(5,2),
  message         text,
  metadata        jsonb       NOT NULL DEFAULT '{}'::jsonb,
  emitted_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (build_id, stage_seq)
);

CREATE INDEX IF NOT EXISTS build_events_chart_id_emitted_at_idx
  ON build_events (chart_id, emitted_at DESC);

CREATE INDEX IF NOT EXISTS build_events_build_id_emitted_at_idx
  ON build_events (build_id, emitted_at DESC);

ALTER TABLE build_events ADD COLUMN IF NOT EXISTS stop_requested boolean NOT NULL DEFAULT false;
ALTER TABLE build_events ADD COLUMN IF NOT EXISTS asset_id text;

CREATE INDEX IF NOT EXISTS build_events_stop_idx
  ON build_events(build_id, asset) WHERE stop_requested = true;
