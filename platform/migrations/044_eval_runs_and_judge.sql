-- platform/migrations/044_eval_runs_and_judge.sql
-- Migration: Gate I Performance Command Center — eval-run aggregates + LLM judge verdicts.
-- Brief: CLAUDECODE_BRIEF.md (GATE-I-PERF-CMD-001), W1.
-- Created: gate1-S1 (2026-05-12).
--
-- Creates `eval_runs` (one row per eval-script invocation, holding aggregate KPIs),
-- creates `performance_judge_verdict` (LLM-judge verdicts produced on-demand from the
-- /performance UI), and finalizes the FK from performance_queries.eval_run_id → eval_runs.id.

BEGIN;

CREATE TABLE IF NOT EXISTS eval_runs (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at                 TIMESTAMPTZ,

  golden_set_version          TEXT NOT NULL,
  planner_prompt_version      TEXT,
  synthesis_prompt_version    TEXT,
  triggered_by                TEXT,           -- script name OR user_id

  query_count                 INTEGER DEFAULT 0,
  plan_accuracy_recall        NUMERIC,
  plan_accuracy_precision     NUMERIC,
  citation_rate               NUMERIC,
  avg_latency_total_ms        INTEGER,
  synthesis_pass_rate         NUMERIC,
  retrieval_hit_rate          NUMERIC,
  b10_compliance_rate         NUMERIC,
  b11_compliance_rate         NUMERIC,

  notes                       TEXT
);

CREATE INDEX IF NOT EXISTS eval_runs_created_idx ON eval_runs (created_at DESC);

CREATE TABLE IF NOT EXISTS performance_judge_verdict (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  performance_query_id        UUID NOT NULL
                              REFERENCES performance_queries(id) ON DELETE CASCADE,
  judge_run_id                UUID NOT NULL,
  judge_model                 TEXT NOT NULL,
  planner_verdict             TEXT NOT NULL
                              CHECK (planner_verdict IN ('correct', 'wrong', 'ambiguous')),
  planner_reasoning           TEXT,
  triggered_by_user_id        UUID,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS judge_verdict_pq_idx
  ON performance_judge_verdict (performance_query_id);

CREATE INDEX IF NOT EXISTS judge_verdict_run_idx
  ON performance_judge_verdict (judge_run_id);

-- Finalize FK on performance_queries.eval_run_id now that eval_runs exists.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'performance_queries_eval_run_fk'
  ) THEN
    ALTER TABLE performance_queries
      ADD CONSTRAINT performance_queries_eval_run_fk
      FOREIGN KEY (eval_run_id) REFERENCES eval_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

COMMIT;
