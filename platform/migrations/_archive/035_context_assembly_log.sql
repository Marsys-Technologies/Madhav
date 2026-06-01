-- platform/migrations/035_context_assembly_log.sql
-- Migration: context_assembly_log — one row per query context assembly. Records
--            per-layer token breakdown (L1, L2.5 signals, L2.5 patterns, L4,
--            vector, CGM), the total via a STORED generated column, the
--            synthesis model and its max-context budget, and B.3 grounding
--            compliance (verified_citations >= 1) for grounding dashboards.
-- Created by W2-SCHEMA (2026-05-01) — MON-4.
-- Consumed by W2-INSTRUMENT (Round 3) write helpers + v_grounding_health_7d.
-- Requires:    PostgreSQL 12+ for the GENERATED ... STORED column. If the live
--              DB version is earlier, drop the GENERATED clause and update the
--              column from the application layer.
-- Idempotent:  CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.

BEGIN;

CREATE TABLE IF NOT EXISTS context_assembly_log (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id            UUID NOT NULL UNIQUE,
  l1_tokens           INTEGER DEFAULT 0,
  l2_5_signal_tokens  INTEGER DEFAULT 0,
  l2_5_pattern_tokens INTEGER DEFAULT 0,
  l4_tokens           INTEGER DEFAULT 0,
  vector_tokens       INTEGER DEFAULT 0,
  cgm_tokens          INTEGER DEFAULT 0,
  total_tokens        INTEGER GENERATED ALWAYS AS (
    COALESCE(l1_tokens, 0) + COALESCE(l2_5_signal_tokens, 0) +
    COALESCE(l2_5_pattern_tokens, 0) + COALESCE(l4_tokens, 0) +
    COALESCE(vector_tokens, 0) + COALESCE(cgm_tokens, 0)
  ) STORED,
  synthesis_model_id  TEXT,
  model_max_context   INTEGER,
  b3_compliant        BOOLEAN,    -- verified_citations >= 1
  citation_count      INTEGER,
  verified_citations  INTEGER,    -- Layer 2 cross-ref count (UQE-3-REVISED)
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context_assembly_log_query_id ON context_assembly_log(query_id);
CREATE INDEX IF NOT EXISTS idx_context_assembly_log_b3       ON context_assembly_log(b3_compliant)
  WHERE b3_compliant = false;

COMMIT;
