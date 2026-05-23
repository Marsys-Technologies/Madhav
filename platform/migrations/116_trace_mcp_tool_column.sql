-- 116_trace_mcp_tool_column.sql
-- Adds mcp_tool column to query_trace_steps for MCP-facing name alignment.
-- MCP primitive calls stored retrieval-side names (e.g. chart_facts_query) in
-- step_name; this column stores the MCP-facing name (e.g. query_chart_facts).
-- Backfills from data_summary->>'mcp_tool' where available (populated by
-- platform route after this migration ships).

ALTER TABLE query_trace_steps ADD COLUMN IF NOT EXISTS mcp_tool TEXT;

-- Backfill historical rows where data_summary contains mcp_tool
UPDATE query_trace_steps
SET mcp_tool = data_summary->>'mcp_tool'
WHERE mcp_tool IS NULL
  AND data_summary ? 'mcp_tool';

-- Index for tool-name queries (list_recent_queries + get_trace MCP tool lookups)
CREATE INDEX IF NOT EXISTS idx_query_trace_steps_mcp_tool
  ON query_trace_steps (mcp_tool)
  WHERE mcp_tool IS NOT NULL;
