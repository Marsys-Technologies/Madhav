-- 225_fix_asset_throughput_pk.sql
-- Drop the single-column PRIMARY KEY (asset_id) that was supposed to be removed in
-- migration 171 but was left in place (the DROP CONSTRAINT DDL was noted in the comment
-- but never written). This PK breaks per-chart builds: any INSERT for a new chart hits
-- the PK on the global chart_id=NULL row that already holds that asset_id slot.
--
-- After this migration, uniqueness is enforced by two partial indexes (both already present):
--   asset_throughput_per_chart_idx: UNIQUE (chart_id, asset_id) WHERE chart_id IS NOT NULL  (migration 171)
--   asset_throughput_global_idx:    UNIQUE (asset_id) WHERE chart_id IS NULL                (migration 184)
--
-- Both the orchestrator's ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
-- and the _telemetry.py ON CONFLICT clause will now resolve correctly.
--
-- The cockpit/refresh route uses ON CONFLICT (chart_id, asset_id) without a WHERE clause;
-- since that route always supplies a non-NULL chart_id, Postgres resolves it against
-- asset_throughput_per_chart_idx — safe.

BEGIN;

ALTER TABLE asset_throughput DROP CONSTRAINT IF EXISTS asset_throughput_pkey;

-- Reset stuck build_runs left from the failed attempts (same reaper logic, applied once):
-- Only targets runs that have been `running` for > 30 minutes with no recent asset heartbeat.
UPDATE build_runs
SET state = 'failed',
    ended_at = NOW()
WHERE state = 'running'
  AND started_at < NOW() - INTERVAL '30 minutes'
  AND NOT EXISTS (
    SELECT 1 FROM asset_throughput
    WHERE chart_id = build_runs.chart_id
      AND last_built_at > NOW() - INTERVAL '10 minutes'
  );

COMMIT;
