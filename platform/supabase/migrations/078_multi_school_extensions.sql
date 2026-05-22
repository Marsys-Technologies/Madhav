-- 078_multi_school_extensions.sql
-- MCP Transformation v3.2-S4 — Multi-school coverage extensions
-- Adds notes column and substantive-coverage index to school_signal_coverage.
-- Idempotent: uses IF NOT EXISTS throughout.
--
-- Migration number: 078 (reserved for v3.2-S4 per MCP_TRANSFORMATION_PLAN §5)
-- Date: 2026-05-22

-- Add notes column for stance rationale text
ALTER TABLE school_signal_coverage
  ADD COLUMN IF NOT EXISTS notes text;

-- Partial index for substantive (non-silent) coverage lookups — used by
-- cross_school_lookup tool and analytics queries.
CREATE INDEX IF NOT EXISTS ssc_coverage_substantive_idx
  ON school_signal_coverage (school, coverage_type)
  WHERE coverage_type IN ('primary', 'secondary');

-- Partial index by school for full-school retrieval
CREATE INDEX IF NOT EXISTS ssc_school_signal_coverage_idx
  ON school_signal_coverage (signal_id, school, coverage_type);
