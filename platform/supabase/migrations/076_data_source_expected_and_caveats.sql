-- Migration 076: Data Source Expected + Tool Caveats
-- MCPT v3.1.0-S4
-- data_source_expected: expected row counts per (tool, category) for coverage reporting.
-- tool_caveats: operator-authored caveats per tool (e.g., "KP backfill pending").

-- ── UP ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS data_source_expected (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  tool_name       text        NOT NULL,                 -- e.g., 'query_chart_facts'
  category        text        NOT NULL,                 -- e.g., 'kp_cusp', 'varshphal', 'house'
  expected_rows   integer     NOT NULL,                 -- expected count at full backfill
  actual_rows     integer,                              -- last known actual count (refreshed by audit job)
  backfill_phase  text,                                 -- e.g., 'v3.3', 'v3.1.0-S1'
  notes           text,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tool_name, category)
);

CREATE TABLE IF NOT EXISTS tool_caveats (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  tool_name       text        NOT NULL,
  caveat_text     text        NOT NULL,                 -- human-readable caveat for capabilities resource
  caveat_class    text        NOT NULL DEFAULT 'data_gap', -- 'data_gap' | 'accuracy' | 'performance' | 'tier_restriction'
  severity        text        NOT NULL DEFAULT 'warn',  -- 'info' | 'warn' | 'error'
  active          boolean     NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  resolved_at     timestamptz
);

-- Indexes
CREATE INDEX IF NOT EXISTS data_source_expected_tool
  ON data_source_expected (tool_name);

CREATE INDEX IF NOT EXISTS tool_caveats_active
  ON tool_caveats (tool_name, active)
  WHERE active = true;

COMMENT ON TABLE data_source_expected IS
  'Expected row counts per (tool_name, category) for data coverage reporting. '
  'Used by data_coverage MCP tool and the capabilities resource. '
  'actual_rows refreshed nightly by the audit job. '
  'MCPT v3.1.0-S4.';

COMMENT ON TABLE tool_caveats IS
  'Operator-authored caveats per tool. Surfaced in the capabilities resource and '
  'data_coverage tool output. Active caveats appear as warnings in tool_health. '
  'MCPT v3.1.0-S4.';

-- ── DOWN ───────────────────────────────────────────────────────────────────────

-- To rollback:
-- DROP INDEX IF EXISTS tool_caveats_active;
-- DROP INDEX IF EXISTS data_source_expected_tool;
-- DROP TABLE IF EXISTS tool_caveats;
-- DROP TABLE IF EXISTS data_source_expected;
