-- platform/migrations/032_llm_call_log.sql
-- Migration: llm_call_log — one row per LLM API call (planner, synthesis,
--            title, history_summary, context_assembly). Captures token usage,
--            cost, latency, fallback status, and provider-specific payload
--            (reasoning_trace etc.) for observability.
-- Created by W2-SCHEMA (2026-05-01) — MON-1.
-- Consumed by  W2-INSTRUMENT (Round 3) write helpers.
-- Idempotent:  CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.

BEGIN;

CREATE TABLE IF NOT EXISTS llm_call_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        UUID NOT NULL,
  conversation_id UUID,
  call_stage      TEXT NOT NULL,  -- 'planner' | 'synthesis' | 'title' | 'history_summary' | 'context_assembly'
  model_id        TEXT NOT NULL,
  provider        TEXT NOT NULL,
  input_tokens    INTEGER,
  output_tokens   INTEGER,
  reasoning_tokens INTEGER,       -- o-series and deepseek-reasoner only; NULL otherwise
  latency_ms      INTEGER,
  cost_usd        NUMERIC(12, 8),
  fallback_used   BOOLEAN DEFAULT false,
  error_code      TEXT,           -- NULL on success
  payload         JSONB,          -- reasoning_trace, raw_response_metadata, etc.
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_call_log_query_id    ON llm_call_log(query_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_model_id    ON llm_call_log(model_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_call_stage  ON llm_call_log(call_stage);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_created_at  ON llm_call_log(created_at DESC);

COMMIT;
