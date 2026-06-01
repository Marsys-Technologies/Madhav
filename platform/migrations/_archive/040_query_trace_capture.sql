-- platform/migrations/040_query_trace_capture.sql
-- Migration: Query Trace Data Capture — extends llm_call_log + tool_execution_log
--            with decision-alternatives, kept/dropped item payloads, and creates
--            three new tables for per-item context assembly, plan alternatives, and
--            synthesis quality scorecards. Also adds query_baseline_stats mat-view.
-- Created: TRACE-T1 (2026-05-05).
-- Idempotent: ADD COLUMN IF NOT EXISTS + CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.
--
-- NOTE: The per-item context assembly table is named context_assembly_item_log (not
--       context_assembly_log) because migration 035 already created context_assembly_log
--       with a per-query aggregate schema. The two tables coexist: 035's table holds
--       aggregate token-layer totals; this table holds per-item rank/status rows.

BEGIN;

-- 1a: Extend llm_call_log with decision trace columns
ALTER TABLE llm_call_log
  ADD COLUMN IF NOT EXISTS decision_alternatives   JSONB,
  ADD COLUMN IF NOT EXISTS decision_reasoning      TEXT,
  ADD COLUMN IF NOT EXISTS prompt_template_id      TEXT,
  ADD COLUMN IF NOT EXISTS prompt_template_version TEXT,
  ADD COLUMN IF NOT EXISTS parent_call_id          UUID REFERENCES llm_call_log(id);

-- 1b: Extend tool_execution_log with kept/dropped item columns
ALTER TABLE tool_execution_log
  ADD COLUMN IF NOT EXISTS raw_result_count    INTEGER,
  ADD COLUMN IF NOT EXISTS kept_result_count   INTEGER,
  ADD COLUMN IF NOT EXISTS dropped_items       JSONB,
  ADD COLUMN IF NOT EXISTS kept_items          JSONB,
  ADD COLUMN IF NOT EXISTS tool_input_payload  JSONB,
  ADD COLUMN IF NOT EXISTS tool_output_summary JSONB,
  ADD COLUMN IF NOT EXISTS error_class         TEXT DEFAULT 'OK';

-- 1c: Per-item context assembly log (named *_item_* — see note above)
CREATE TABLE IF NOT EXISTS context_assembly_item_log (
  id                            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id                      UUID    NOT NULL,
  assembly_step_id              TEXT    NOT NULL,
  item_rank                     INTEGER NOT NULL,
  source_bundle                 TEXT    NOT NULL,
  source_item_id                TEXT    NOT NULL,
  layer                         TEXT    NOT NULL,
  token_cost                    INTEGER NOT NULL,
  relevance_score               REAL,
  status                        TEXT    NOT NULL CHECK (status IN ('INCLUDED', 'TRUNCATED', 'DROPPED')),
  drop_reason                   TEXT    CHECK (
    drop_reason IN ('BUDGET_EXCEEDED', 'DEDUP', 'RELEVANCE_FLOOR') OR drop_reason IS NULL
  ),
  truncated_to_tokens           INTEGER,
  cumulative_tokens_at_decision INTEGER,
  budget_at_decision            INTEGER,
  created_at                    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context_assembly_item_log_query
  ON context_assembly_item_log(query_id, item_rank);

-- 1d: Synthesis quality scorecard (populated from existing checkpoint outputs only)
CREATE TABLE IF NOT EXISTS synthesis_quality_scorecard (
  query_id                      UUID    PRIMARY KEY,
  citation_density              REAL    NOT NULL DEFAULT 0,
  whole_chart_coverage          JSONB   NOT NULL DEFAULT '{}',
  derivation_ledger_compliance  REAL    NOT NULL DEFAULT 0,
  fabricated_computation_flags  JSONB,
  disclosure_tier_verdict       TEXT    NOT NULL DEFAULT 'UNKNOWN',
  composite_score               REAL    NOT NULL DEFAULT 0,
  failures                      JSONB,
  created_at                    TIMESTAMPTZ DEFAULT NOW()
);

-- 1e: Plan alternatives log — records which bundles the LLM planner considered
CREATE TABLE IF NOT EXISTS plan_alternatives_log (
  id                    UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id              UUID    NOT NULL,
  bundle_name           TEXT    NOT NULL,
  was_selected          BOOLEAN NOT NULL,
  rationale             TEXT,
  expected_recall_score REAL,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plan_alternatives_log_query
  ON plan_alternatives_log(query_id);

-- 1f: Baseline stats materialized view
-- Stub: query_type is 'unknown' until a query_type column is propagated to llm_call_log.
-- Reads cost_usd (NUMERIC) cast to DOUBLE PRECISION for percentile aggregation.
-- Refresh manually with: REFRESH MATERIALIZED VIEW query_baseline_stats;
-- This is a stub pending full query_summary population; sample_size may be 0 on a fresh DB.
CREATE MATERIALIZED VIEW IF NOT EXISTS query_baseline_stats AS
SELECT
  'unknown'::TEXT                                                                       AS query_type,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms)                             AS p50_total_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)                             AS p95_total_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY cost_usd::DOUBLE PRECISION)             AS p50_total_cost_usd,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cost_usd::DOUBLE PRECISION)             AS p95_total_cost_usd,
  COUNT(*)                                                                              AS sample_size
FROM llm_call_log
WHERE created_at > NOW() - INTERVAL '30 days'
  AND cost_usd IS NOT NULL
GROUP BY 1;

COMMIT;
