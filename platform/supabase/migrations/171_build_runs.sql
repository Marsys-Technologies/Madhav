-- Migration 171: build_runs + build_run_assets + asset_throughput state extension
-- Adds per-chart build orchestration tables and extends asset_throughput with
-- per-chart state tracking columns needed by the cockpit build control UI.

ALTER TABLE asset_throughput
  ADD COLUMN IF NOT EXISTS chart_id UUID REFERENCES charts(id),
  ADD COLUMN IF NOT EXISTS state TEXT NOT NULL DEFAULT 'dormant'
    CHECK (state IN ('dormant','building','lit','stale','error')),
  ADD COLUMN IF NOT EXISTS built_against_upstream_hash TEXT,
  ADD COLUMN IF NOT EXISTS built_against_writer_hash TEXT,
  ADD COLUMN IF NOT EXISTS last_built_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_error TEXT;

-- Drop old PK (was just asset_id) and replace with compound (chart_id, asset_id)
-- Only do this if chart_id column was just added (i.e., no rows have chart_id set).
-- We keep old rows in place; new per-chart rows use the compound PK.
-- To avoid breaking existing throughput measurement rows, we make chart_id nullable
-- and add a partial unique index for the per-chart use-case.
CREATE UNIQUE INDEX IF NOT EXISTS asset_throughput_per_chart_idx
  ON asset_throughput(chart_id, asset_id)
  WHERE chart_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS asset_throughput_chart_state_idx
  ON asset_throughput(chart_id, state)
  WHERE chart_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS build_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL REFERENCES charts(id),
  scope TEXT NOT NULL CHECK (scope IN ('global','layer','asset')),
  scope_target TEXT,
  action TEXT NOT NULL CHECK (action IN ('build','update','rebuild','cascade')),
  state TEXT NOT NULL DEFAULT 'planned'
    CHECK (state IN ('planned','running','paused','completed','stopped','failed')),
  plan JSONB NOT NULL,
  current_asset_id TEXT,
  triggered_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  pause_requested_at TIMESTAMPTZ,
  stop_requested_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS build_runs_chart_active_idx
  ON build_runs(chart_id) WHERE state IN ('running','paused');

CREATE TABLE IF NOT EXISTS build_run_assets (
  run_id UUID NOT NULL REFERENCES build_runs(id) ON DELETE CASCADE,
  asset_id TEXT NOT NULL,
  position INT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued','building','complete','skipped','error','aborted')),
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  error TEXT,
  PRIMARY KEY (run_id, asset_id)
);
