-- platform/migrations/043_performance_schema.sql
-- Migration: Gate I Performance Command Center — unified per-query performance log.
-- Brief: CLAUDECODE_BRIEF.md (GATE-I-PERF-CMD-001), W1.
-- Created: gate1-S1 (2026-05-12).
--
-- Creates `performance_queries`: one row per consume-triggered OR eval-triggered
-- pipeline run. Tagged by `source`. Indexes optimized for time-window slicing,
-- source/class filters, and FK-back lookups.
--
-- The eval_run_id FK is declared as a nullable column here and finalized as a
-- foreign-key constraint in migration 044 (after `eval_runs` exists).
-- The audit_event_id is a soft pointer to audit_log.id; we set ON DELETE SET NULL
-- so a purge of audit_log does not cascade-delete performance rows.

BEGIN;

CREATE TABLE IF NOT EXISTS performance_queries (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Soft FK to audit_log.id for consume rows; null for eval rows.
  audit_event_id              UUID NULL REFERENCES audit_log(id) ON DELETE SET NULL,

  -- Soft FK to eval_runs.id for eval rows; null for consume rows.
  -- Constraint finalized in migration 044.
  eval_run_id                 UUID NULL,

  source                      TEXT NOT NULL CHECK (source IN ('consume', 'eval')),
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),

  query_text                  TEXT,
  query_class                 TEXT,
  plan_type                   TEXT,
  plan_tools_selected         JSONB,
  planner_confidence          NUMERIC,

  latency_planner_ms          INTEGER,
  latency_retrieval_ms        INTEGER,
  latency_synthesis_ms        INTEGER,
  latency_total_ms            INTEGER,

  citations_present           BOOLEAN,
  citation_count              INTEGER DEFAULT 0,
  synthesis_status            TEXT,           -- 'success' | 'failure' | 'partial'
  validator_verdict           TEXT,
  disclosure_tier             TEXT,

  b10_violation               BOOLEAN,        -- W4 detector output
  b11_violation               BOOLEAN,        -- W4 detector output
  retrieval_hit               BOOLEAN,
  retrieval_score_top1        NUMERIC,

  plan_accuracy_label         TEXT DEFAULT 'unjudged'
                              CHECK (plan_accuracy_label IN
                                ('correct', 'wrong', 'ambiguous', 'unjudged', 'n_a')),
  plan_accuracy_source        TEXT
                              CHECK (plan_accuracy_source IN ('golden', 'judge')
                                     OR plan_accuracy_source IS NULL),

  is_prediction               BOOLEAN DEFAULT false,
  prediction_outcome_state    TEXT DEFAULT 'n_a'
                              CHECK (prediction_outcome_state IN
                                ('pending', 'observed_correct', 'observed_incorrect', 'n_a'))
);

CREATE INDEX IF NOT EXISTS perf_queries_created_at_idx
  ON performance_queries (created_at DESC);

CREATE INDEX IF NOT EXISTS perf_queries_source_created_idx
  ON performance_queries (source, created_at DESC);

CREATE INDEX IF NOT EXISTS perf_queries_class_created_idx
  ON performance_queries (query_class, created_at DESC);

CREATE INDEX IF NOT EXISTS perf_queries_audit_event_idx
  ON performance_queries (audit_event_id);

CREATE INDEX IF NOT EXISTS perf_queries_eval_run_idx
  ON performance_queries (eval_run_id);

COMMIT;
