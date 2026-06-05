-- Migration 074: Audit Findings
-- MCPT v3.1.0-S4
-- mcp_audit_findings: individual finding rows from the nightly audit job.
-- audit_job_runs: job execution history.

-- ── UP ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mcp_audit_findings (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  trace_id        text        NOT NULL,                  -- links to tool_execution_log.trace_id
  tool_name       text        NOT NULL,
  check_class     text        NOT NULL,                  -- 'citation_presence' | 'numerical_grounding' | 'forward_looking_logged' | 'sanskrit_glossing' | 'layer_attribution' | 'non_factual_shape'
  severity        text        NOT NULL DEFAULT 'warn',   -- 'warn' | 'error'
  description     text        NOT NULL,                  -- human-readable finding description
  evidence        jsonb,                                 -- extracted evidence (regex matches, claim text, etc.)
  attached_at     timestamptz NOT NULL DEFAULT now(),
  resolved_at     timestamptz,                           -- null = open; set when resolved
  resolved_by     text                                   -- 'operator' | 'auto' | null
);

CREATE TABLE IF NOT EXISTS audit_job_runs (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at      timestamptz NOT NULL DEFAULT now(),
  completed_at    timestamptz,
  status          text        NOT NULL DEFAULT 'running', -- 'running' | 'complete' | 'failed'
  traces_examined integer     NOT NULL DEFAULT 0,
  findings_opened integer     NOT NULL DEFAULT 0,
  findings_closed integer     NOT NULL DEFAULT 0,
  error_message   text,
  job_config      jsonb                                   -- the config used for this run
);

-- Indexes for trace-level audit lookup (used by get_trace extension)
CREATE INDEX IF NOT EXISTS mcp_audit_findings_trace_id
  ON mcp_audit_findings (trace_id);

-- Index for open findings (for dashboard + tool_health)
CREATE INDEX IF NOT EXISTS mcp_audit_findings_open
  ON mcp_audit_findings (check_class, severity, attached_at)
  WHERE resolved_at IS NULL;

-- Index for job history queries
CREATE INDEX IF NOT EXISTS audit_job_runs_started_at
  ON audit_job_runs (started_at DESC);

COMMENT ON TABLE mcp_audit_findings IS
  'Individual finding rows from the operator-side nightly audit job (03:00 UTC). '
  'Each row corresponds to one failed check on one tool response. '
  '6 check classes: citation_presence, numerical_grounding, forward_looking_logged, '
  'sanskrit_glossing, layer_attribution, non_factual_shape. '
  'MCPT v3.1.0-S4. Replaces v3.0 self-audit pattern.';

COMMENT ON TABLE audit_job_runs IS
  'Execution history for the nightly audit job. One row per run. MCPT v3.1.0-S4.';

COMMENT ON COLUMN mcp_audit_findings.check_class IS
  'Audit check that produced this finding. One of: citation_presence, numerical_grounding, '
  'forward_looking_logged, sanskrit_glossing, layer_attribution, non_factual_shape.';

-- ── DOWN ───────────────────────────────────────────────────────────────────────

-- To rollback:
-- DROP INDEX IF EXISTS audit_job_runs_started_at;
-- DROP INDEX IF EXISTS mcp_audit_findings_open;
-- DROP INDEX IF EXISTS mcp_audit_findings_trace_id;
-- DROP TABLE IF EXISTS audit_job_runs;
-- DROP TABLE IF EXISTS mcp_audit_findings;
