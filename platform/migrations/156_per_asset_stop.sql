-- 156_per_asset_stop.sql
-- Add per-asset stop signal support to build_events.
-- NOTE: Column already added via 160_per_asset_stop.sql; this file is
-- idempotent and safe to apply on a DB that already has this column.
-- Note: build_events uses 'asset' (not 'asset_id') for the asset column.
ALTER TABLE build_events ADD COLUMN IF NOT EXISTS stop_requested boolean NOT NULL DEFAULT false;
ALTER TABLE build_events ADD COLUMN IF NOT EXISTS asset_id text;
CREATE INDEX IF NOT EXISTS build_events_stop_idx ON build_events(build_id, asset) WHERE stop_requested = true;
