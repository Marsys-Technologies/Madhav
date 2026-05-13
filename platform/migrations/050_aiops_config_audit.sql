-- platform/migrations/050_aiops_config_audit.sql
-- Migration: AIOps CP.1 — configuration change audit log.
-- Append-only; rows are never updated. The revert operation inserts a new row
-- with action='revert' and restores the before_value.

BEGIN;

CREATE TABLE IF NOT EXISTS llm_config_audit (
  id            BIGSERIAL PRIMARY KEY,
  occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor_user_id TEXT NOT NULL,
  action        TEXT NOT NULL,   -- 'set_stack' | 'set_routing' | 'set_param' | 'reset_param' | 'probe' | 'revert'
  scope         TEXT,
  stack         TEXT,
  call_type     TEXT,
  param_name    TEXT,
  before_value  JSONB,
  after_value   JSONB,
  notes         TEXT
);

CREATE INDEX IF NOT EXISTS llm_config_audit_occurred_at_idx ON llm_config_audit (occurred_at DESC);

COMMIT;

-- Down:
-- DROP INDEX IF EXISTS llm_config_audit_occurred_at_idx;
-- DROP TABLE IF EXISTS llm_config_audit;
