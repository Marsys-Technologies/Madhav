-- 011_audit_log.sql
-- MARSYS-JIS Phase 4 Stream A: audit_log table
-- Persists every query's full execution trace for Discipline stage, calibration, and audit UI.
--
-- ROLLBACK: If this migration fails partway, run:
--   DROP INDEX IF EXISTS idx_audit_log_created_at;
--   DROP INDEX IF EXISTS idx_audit_log_query_id;
--   DROP TABLE IF EXISTS audit_log;

CREATE TABLE IF NOT EXISTS audit_log (
  id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id                UUID        NOT NULL,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  query_text              TEXT        NOT NULL,
  query_class             TEXT        NOT NULL,
  bundle_keys             JSONB       NOT NULL DEFAULT '[]',
  tools_called            JSONB       NOT NULL DEFAULT '[]',
  validators_run          JSONB       NOT NULL DEFAULT '[]',
  synthesis_model         TEXT        NOT NULL,
  synthesis_input_tokens  INTEGER     NOT NULL DEFAULT 0,
  synthesis_output_tokens INTEGER     NOT NULL DEFAULT 0,
  disclosure_tier         TEXT        NOT NULL,
  final_output            TEXT        NOT NULL DEFAULT '',
  audit_event_version     INTEGER     NOT NULL DEFAULT 1,
  CONSTRAINT uq_audit_log_query_id UNIQUE (query_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_query_id   ON audit_log (query_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at DESC);
