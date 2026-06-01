-- platform/migrations/049_aiops_model_health.sql
-- Migration: AIOps CP.1 — model health tracking table.
-- One row per model ID; updated by probe + smoke-test runs.

BEGIN;

CREATE TABLE IF NOT EXISTS llm_model_health (
  model_id       TEXT PRIMARY KEY,
  status         TEXT NOT NULL DEFAULT 'never_probed', -- 'pass' | 'fail' | 'stale' | 'never_probed'
  latency_ms     INTEGER,
  last_probe_at  TIMESTAMPTZ,
  last_error     TEXT,
  last_probed_by TEXT
);

COMMIT;

-- Down:
-- DROP TABLE IF EXISTS llm_model_health;
