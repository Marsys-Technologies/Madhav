-- Migration 321: Add last_error column to build_runs
-- Needed so dispatch failures (runs/route.ts) and watchdog planned-orphan reaper
-- can store their error message, consistent with asset_throughput.last_error.
ALTER TABLE build_runs
  ADD COLUMN IF NOT EXISTS last_error TEXT;
