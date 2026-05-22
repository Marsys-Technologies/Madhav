-- Migration 073: Perf Log Extensions
-- MCPT v3.1.0-S4
-- Extends tool_execution_log with 5 perf-system columns for the nightly audit.

-- ── UP ─────────────────────────────────────────────────────────────────────────

-- Add 5 columns to tool_execution_log if it exists; create minimal version if not.
DO $$
BEGIN
  -- Create the table if it doesn't exist yet (v3.0 may have created it already)
  CREATE TABLE IF NOT EXISTS tool_execution_log (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id        text        NOT NULL,
    tool_name       text        NOT NULL,
    started_at      timestamptz NOT NULL DEFAULT now(),
    completed_at    timestamptz,
    status          text        NOT NULL DEFAULT 'ok',   -- 'ok' | 'error' | 'timeout'
    audience_tier   text        NOT NULL DEFAULT 'super_admin',
    latency_ms      integer,
    response_text   text,                                -- response body for audit heuristics
    created_at      timestamptz NOT NULL DEFAULT now()
  );

  -- Add perf-system columns (idempotent)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'citation_count'
  ) THEN
    ALTER TABLE tool_execution_log
      ADD COLUMN citation_count     integer,            -- count from extract_citations heuristic
      ADD COLUMN has_numerical      boolean,            -- extract_numerical_claims result
      ADD COLUMN is_forward_looking boolean,            -- forward_looking heuristic result
      ADD COLUMN sanskrit_compliant boolean,            -- sanskrit_glossing heuristic (client tier)
      ADD COLUMN audit_flagged      boolean DEFAULT false; -- set true if any audit check fails
  END IF;
END $$;

-- Index for trace-based lookups (used by get_trace + nightly audit)
CREATE INDEX IF NOT EXISTS tool_execution_log_trace_id
  ON tool_execution_log (trace_id);

-- Index for audit job: find un-audited rows from last 24h
CREATE INDEX IF NOT EXISTS tool_execution_log_audit_queue
  ON tool_execution_log (created_at, audit_flagged)
  WHERE audit_flagged IS DISTINCT FROM true;

COMMENT ON TABLE tool_execution_log IS
  'Per-tool execution record for every MCP tool call. '
  'Extended in migration 073 with 5 perf-system columns populated by the nightly audit job. '
  'MCPT v3.1.0-S4.';

COMMENT ON COLUMN tool_execution_log.citation_count IS
  'Number of citation references (SIG.MSR.NNN, [^N], etc.) extracted from response_text by the audit heuristic.';
COMMENT ON COLUMN tool_execution_log.has_numerical IS
  'True if response_text contains numerical astrological claims (degrees, virupa, etc.).';
COMMENT ON COLUMN tool_execution_log.is_forward_looking IS
  'True if the forward_looking heuristic detected prospective language in response_text.';
COMMENT ON COLUMN tool_execution_log.sanskrit_compliant IS
  'True if client-tier responses gloss Sanskrit terms in English (client tier only; null for other tiers).';
COMMENT ON COLUMN tool_execution_log.audit_flagged IS
  'Set true by the nightly audit job if any of the 6 audit checks fails for this row.';

-- ── DOWN ───────────────────────────────────────────────────────────────────────

-- To rollback this migration:
-- ALTER TABLE tool_execution_log
--   DROP COLUMN IF EXISTS citation_count,
--   DROP COLUMN IF EXISTS has_numerical,
--   DROP COLUMN IF EXISTS is_forward_looking,
--   DROP COLUMN IF EXISTS sanskrit_compliant,
--   DROP COLUMN IF EXISTS audit_flagged;
-- DROP INDEX IF EXISTS tool_execution_log_audit_queue;
-- DROP INDEX IF EXISTS tool_execution_log_trace_id;
