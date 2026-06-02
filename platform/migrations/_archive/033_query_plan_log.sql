-- platform/migrations/033_query_plan_log.sql
-- Migration: query_plan_log — one row per planner invocation. Captures full
--            PlanSchema output as JSONB plus parse success/fallback flags for
--            planner reliability monitoring.
-- Created by W2-SCHEMA (2026-05-01) — MON-2.
-- Note:      Distinct from migration 027 (`query_plans`), which stores the
--            structured plan record itself; this log is the monitoring/audit
--            surface keyed by query_id with raw JSONB payload + fallback flag.
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.

BEGIN;

CREATE TABLE IF NOT EXISTS query_plan_log (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id          UUID NOT NULL UNIQUE,
  conversation_id   UUID,
  chart_id          TEXT,
  planner_model_id  TEXT,
  query_text        TEXT,
  query_class       TEXT,         -- from classifier or planner
  tool_count        INTEGER,
  plan_json         JSONB,        -- full PlanSchema output
  parsing_success   BOOLEAN NOT NULL DEFAULT true,
  parse_error       TEXT,         -- NULL on success
  fallback_used     BOOLEAN DEFAULT false,
  planner_latency_ms INTEGER,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_plan_log_query_id        ON query_plan_log(query_id);
CREATE INDEX IF NOT EXISTS idx_query_plan_log_conversation_id ON query_plan_log(conversation_id);
CREATE INDEX IF NOT EXISTS idx_query_plan_log_created_at      ON query_plan_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_plan_log_fallback        ON query_plan_log(fallback_used)
  WHERE fallback_used = true;

COMMIT;
