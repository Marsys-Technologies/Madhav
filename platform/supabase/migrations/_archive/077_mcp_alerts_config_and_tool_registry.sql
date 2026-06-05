-- Migration 077: MCP Alerts Config + Tool Registry
-- MCPT v3.1.0-S5
--
-- mcp_alerts_config: per-metric threshold configuration with Slack/email dispatch targets.
-- tool_registry: operator-managed tool enable/disable toggle (tool_enabled boolean).
--
-- The tool_registry supplements the primitives_registry.ts whitelist — the whitelist
-- is code-level (what the server knows about); tool_registry is DB-level (what the
-- operator allows to run at runtime). A tool in the whitelist but disabled in
-- tool_registry returns 503 {tool_disabled: true} from the primitive dispatcher.

-- ── UP ─────────────────────────────────────────────────────────────────────────

-- Table: mcp_alerts_config
-- Each row is one alert rule. When the operator configures thresholds on the
-- dashboard's AlertThresholds tab, rows are upserted here.
CREATE TABLE IF NOT EXISTS mcp_alerts_config (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  metric_name         text        NOT NULL,   -- e.g., 'zero_rows_rate', 'error_rate', 'audit_class1_count'
  scope               text        NOT NULL,   -- 'global' | 'per_tool'
  tool_name           text,                   -- non-null when scope = 'per_tool'
  threshold_value     numeric     NOT NULL,   -- breach threshold (e.g., 0.5 for 50%)
  comparison          text        NOT NULL    -- 'gte' | 'lte' | 'gt' | 'lt'
                        CHECK (comparison IN ('gte', 'lte', 'gt', 'lt')),
  window_hours        integer     NOT NULL DEFAULT 24,
  channels            text[]      NOT NULL DEFAULT '{}', -- ['slack', 'email']
  slack_webhook_url   text,
  email_recipients    text[],
  enabled             boolean     NOT NULL DEFAULT true,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  created_by          text        NOT NULL DEFAULT 'native',
  CONSTRAINT mcp_alerts_config_scope_tool CHECK (
    (scope = 'per_tool' AND tool_name IS NOT NULL) OR
    (scope = 'global'   AND tool_name IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS mcp_alerts_config_enabled
  ON mcp_alerts_config (metric_name, scope, enabled)
  WHERE enabled = true;

-- Seed default alert thresholds per perf brief §7.6
INSERT INTO mcp_alerts_config
  (metric_name, scope, tool_name, threshold_value, comparison, window_hours, channels, enabled)
VALUES
  -- zero_rows_rate >= 0.5 (50%) for any tool over 24h → warn
  ('zero_rows_rate', 'global', NULL, 0.5, 'gte', 24, ARRAY['slack'], true),
  -- error_rate >= 0.1 (10%) for any tool over 24h → critical
  ('error_rate', 'global', NULL, 0.1, 'gte', 24, ARRAY['slack', 'email'], true),
  -- audit class_1 finding count >= 1 in 24h → critical
  ('audit_class1_count', 'global', NULL, 1, 'gte', 24, ARRAY['slack', 'email'], true),
  -- audit class_2 finding count >= 5 in 24h → warn
  ('audit_class2_count', 'global', NULL, 5, 'gte', 24, ARRAY['slack'], true),
  -- tool disabled and still called (operational anomaly)
  ('disabled_tool_call_count', 'global', NULL, 1, 'gte', 1, ARRAY['slack'], true)
ON CONFLICT DO NOTHING;

-- Table: tool_registry
-- Runtime enable/disable per MCP-facing tool name.
-- The primitive dispatcher checks tool_enabled before executing.
-- tool_name matches the MCP-facing name (e.g., 'query_chart_facts'), not the
-- underlying retrieval tool name (e.g., 'chart_facts_query').
CREATE TABLE IF NOT EXISTS tool_registry (
  tool_name           text        PRIMARY KEY,  -- MCP-facing tool name
  tool_enabled        boolean     NOT NULL DEFAULT true,
  disabled_reason     text,       -- human-readable reason for disabling
  disabled_at         timestamptz,
  disabled_by         text,
  enabled_at          timestamptz NOT NULL DEFAULT now(),
  enabled_by          text        NOT NULL DEFAULT 'native',
  updated_at          timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE tool_registry IS
  'Runtime operator toggle for MCP tool enable/disable. '
  'tool_enabled=false causes the primitive dispatcher to return 503 {tool_disabled: true}. '
  'Separate from the code-level whitelist in primitives_registry.ts — both must allow '
  'for a tool call to succeed. MCPT v3.1.0-S5.';

COMMENT ON TABLE mcp_alerts_config IS
  'Per-metric threshold configuration for the Slack/email alerting subsystem. '
  'Edited via the /admin/mcp/health AlertThresholds tab. '
  'Dispatched by platform/src/lib/alerts/dispatch.ts. MCPT v3.1.0-S5.';

-- Seed tool_registry with all MCP-facing tools (all enabled by default)
INSERT INTO tool_registry (tool_name, tool_enabled) VALUES
  ('query_chart_facts',      true),
  ('query_signals',          true),
  ('query_dasha_periods',    true),
  ('query_panchanga',        true),
  ('query_ephemeris',        true),
  ('query_transit_event',    true),
  ('lel_query',              true),
  ('vector_search',          true),
  ('get_cgm_subgraph',       true),
  ('cross_school_lookup',    true),
  ('holistic_bundle',        true),
  ('multi_school_bundle',    true),
  ('read_asset',             true),
  ('get_trace',              true),
  ('list_recent_queries',    true),
  ('tool_health',            true),
  ('data_coverage',          true),
  ('log_prediction',         true),
  ('record_outcome',         true),
  ('flag_disagreement',      true)
ON CONFLICT (tool_name) DO NOTHING;

-- ── DOWN ───────────────────────────────────────────────────────────────────────

-- To rollback:
-- DROP INDEX IF EXISTS mcp_alerts_config_enabled;
-- DROP TABLE IF EXISTS mcp_alerts_config;
-- DROP TABLE IF EXISTS tool_registry;
