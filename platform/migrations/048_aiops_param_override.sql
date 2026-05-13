-- platform/migrations/048_aiops_param_override.sql
-- Migration: AIOps CP.1 — per-stack per-call-type parameter overrides.
-- Stores max_output_tokens, temperature, thinkingBudget, timeout_ms overrides.
-- param_value is jsonb to accommodate heterogeneous value types (number, boolean).

BEGIN;

CREATE TABLE IF NOT EXISTS llm_param_override (
  scope       TEXT NOT NULL,
  stack       TEXT NOT NULL,
  call_type   TEXT NOT NULL,
  param_name  TEXT NOT NULL,
  param_value JSONB NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by  TEXT NOT NULL,
  PRIMARY KEY (scope, stack, call_type, param_name)
);

COMMIT;

-- Down:
-- DROP TABLE IF EXISTS llm_param_override;
