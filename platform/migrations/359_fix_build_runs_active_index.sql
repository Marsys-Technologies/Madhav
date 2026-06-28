-- Replace the partial index that excluded 'planned' state,
-- causing sequential scans for the most common query path.
DROP INDEX IF EXISTS build_runs_chart_active_idx;

CREATE INDEX CONCURRENTLY IF NOT EXISTS build_runs_chart_state_planned_idx
  ON build_runs (chart_id, created_at DESC)
  WHERE state IN ('planned', 'running', 'paused');

-- Missing indexes for timestamp-comparison queries on large tables
CREATE INDEX CONCURRENTLY IF NOT EXISTS bodha_msr_signals_chart_computed_idx
  ON bodha_msr_signals (chart_id, computed_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS chart_facts_chart_computed_idx
  ON chart_facts (chart_id, computed_at DESC);
