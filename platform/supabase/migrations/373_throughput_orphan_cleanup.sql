-- Migration 373: asset_throughput orphan cleanup
--
-- Three classes of orphan produced by the mi_jivanaghatana scope migration (372)
-- and the orchestrator crash during the first full-stack build run:
--
--   A. NULL-chart rows for assets now registered as per_chart.
--      When scope changes global→per_chart the old chart_id=NULL row stays in
--      asset_throughput. The orchestrator's skip-if-complete check then sees that
--      row as 'lit' and silently skips the asset for every chart (inc. the one
--      that needs it built). Fix: delete NULL rows for per_chart assets.
--
--   B. Chart-scoped rows for global assets.
--      Arise from scope changes per_chart→global or from occasional build bugs.
--      Global assets are singletons (chart_id IS NULL); chart-scoped rows are
--      always wrong. Fix: delete chart-scoped rows for global assets.
--
--   C. Assets stuck in 'building' state from a crashed orchestrator run.
--      When the worker connection dies mid-substep, mark_asset_error() cannot
--      execute — the row stays 'building'. The 409 active-run gate then sees these
--      as phantom-building and blocks any new run. Fix: reset to 'error'.
--
-- All three changes are idempotent.

BEGIN;

-- A. Remove NULL-chart throughput rows for per_chart assets.
DELETE FROM asset_throughput
WHERE chart_id IS NULL
  AND asset_id IN (
    SELECT asset_id FROM asset_registry WHERE scope = 'per_chart'
  );

-- B. Remove chart-scoped throughput rows for global assets.
DELETE FROM asset_throughput
WHERE chart_id IS NOT NULL
  AND asset_id IN (
    SELECT asset_id FROM asset_registry WHERE scope = 'global'
  );

-- C. Reset assets stuck in 'building' where no run is currently active.
--    The sub-select excludes charts where a run is genuinely 'running' so we
--    don't clobber an in-flight build on a different chart.
UPDATE asset_throughput
SET
  state     = 'error',
  last_error = 'orphaned_by_crash: orchestrator terminated while asset was in-flight'
WHERE state = 'building'
  AND NOT EXISTS (
    SELECT 1 FROM build_runs
    WHERE build_runs.state = 'running'
      AND build_runs.chart_id IS NOT DISTINCT FROM asset_throughput.chart_id
  );

-- C2. Fix matching build_run_assets rows for already-terminal runs.
UPDATE build_run_assets
SET
  state    = 'error',
  error    = 'orphaned_by_crash: orchestrator terminated while asset was in-flight',
  ended_at = NOW()
WHERE state = 'building'
  AND run_id IN (
    SELECT id FROM build_runs
    WHERE state NOT IN ('running', 'planned', 'paused')
  );

COMMIT;
