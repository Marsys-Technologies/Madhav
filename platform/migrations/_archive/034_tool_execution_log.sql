-- platform/migrations/034_tool_execution_log.sql
-- Migration: tool_execution_log — one row per tool call inside a query. Tracks
--            status (ok | zero_rows | error | cache_hit), latency, row counts,
--            cache + fallback usage. Powers tool-health dashboards.
-- Created by W2-SCHEMA (2026-05-01) — MON-3.
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.

BEGIN;

CREATE TABLE IF NOT EXISTS tool_execution_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        UUID NOT NULL,
  tool_name       TEXT NOT NULL,
  params_json     JSONB,
  status          TEXT NOT NULL,  -- 'ok' | 'zero_rows' | 'error' | 'cache_hit'
  rows_returned   INTEGER,
  latency_ms      INTEGER,
  token_estimate  INTEGER,
  data_asset_id   TEXT,
  error_code      TEXT,
  served_from_cache BOOLEAN DEFAULT false,
  fallback_used   BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_query_id  ON tool_execution_log(query_id);
CREATE INDEX IF NOT EXISTS idx_tool_execution_log_tool_name ON tool_execution_log(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_execution_log_status    ON tool_execution_log(status);
CREATE INDEX IF NOT EXISTS idx_tool_execution_log_zero_rows ON tool_execution_log(tool_name)
  WHERE status = 'zero_rows';

COMMIT;
