-- platform/migrations/036_analytics_views.sql
-- Migration: monitoring analytics views — three rollups over the four MON-1..4
--            log tables for cost/health/grounding dashboards.
--              v_cost_by_model_30d  — LLM spend + token mix by model/stage
--              v_tool_health_7d     — tool call counts/status/latency
--              v_grounding_health_7d — daily B.3 compliance + citation rates
-- Created by W2-SCHEMA (2026-05-01) — MON-10.
-- Idempotent: CREATE OR REPLACE VIEW.

BEGIN;

-- Cost by model (last 30 days)
CREATE OR REPLACE VIEW v_cost_by_model_30d AS
SELECT
  model_id,
  provider,
  call_stage,
  COUNT(*) AS call_count,
  SUM(input_tokens) AS total_input_tokens,
  SUM(output_tokens) AS total_output_tokens,
  SUM(COALESCE(reasoning_tokens, 0)) AS total_reasoning_tokens,
  SUM(COALESCE(cost_usd, 0)) AS total_cost_usd,
  AVG(latency_ms) AS avg_latency_ms
FROM llm_call_log
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY model_id, provider, call_stage;

-- Tool health (last 7 days)
CREATE OR REPLACE VIEW v_tool_health_7d AS
SELECT
  tool_name,
  COUNT(*) AS total_calls,
  SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS ok_count,
  SUM(CASE WHEN status = 'zero_rows' THEN 1 ELSE 0 END) AS zero_rows_count,
  SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
  SUM(CASE WHEN fallback_used THEN 1 ELSE 0 END) AS fallback_count,
  AVG(latency_ms) AS avg_latency_ms,
  AVG(rows_returned) AS avg_rows_returned
FROM tool_execution_log
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY tool_name;

-- Grounding health (last 7 days)
CREATE OR REPLACE VIEW v_grounding_health_7d AS
SELECT
  DATE_TRUNC('day', created_at) AS day,
  COUNT(*) AS total_queries,
  SUM(CASE WHEN b3_compliant THEN 1 ELSE 0 END) AS b3_compliant_count,
  AVG(citation_count) AS avg_citations,
  AVG(verified_citations) AS avg_verified_citations,
  AVG(total_tokens) AS avg_total_tokens
FROM context_assembly_log
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day DESC;

COMMIT;
