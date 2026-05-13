-- platform/migrations/047_aiops_routing_override.sql
-- Migration: AIOps CP.1 — per-stack per-call-type routing overrides.
-- When a row exists here, the runtime_config resolver uses it instead of the
-- STACK_ROUTING registry default. Rows are only present when a super-admin has
-- explicitly overridden a routing choice.

BEGIN;

CREATE TABLE IF NOT EXISTS llm_stack_routing_override (
  scope          TEXT NOT NULL,
  stack          TEXT NOT NULL,
  call_type      TEXT NOT NULL,
  primary_model  TEXT NOT NULL,
  fallback_model TEXT NOT NULL,
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by     TEXT NOT NULL,
  PRIMARY KEY (scope, stack, call_type)
);

COMMIT;

-- Down:
-- DROP TABLE IF EXISTS llm_stack_routing_override;
