-- Migration 082: Perf System Materialized Views
-- MCPT v3.7 — Operational Gap Closure Phase B
--
-- Adds the 4 perf-system MVs missing from migrations 072–080.
-- Also adds the §4.1 MCP-aware columns to tool_execution_log that
-- migrations 072–080 did not include (needed for MV GROUP BY axes).
--
-- Adapts brief spec to actual production schema:
--   - tool_execution_log uses 'created_at' not 'timestamp'
--   - lel_events table doesn't exist; 'life_events' is the actual table
--   - msr_signals uses 'ingested_at' not 'updated_at'
--   - build_manifests uses 'promoted_at' not 'completed_at'
--   - mcp_audit_findings uses 'check_class' not 'finding_class';
--     cited_signal_ids not present — mv_tool_grounding_24h simplified accordingly

BEGIN;

-- ─── Part 1: Add §4.1 MCP-aware columns to tool_execution_log ───────────────
-- All nullable — existing web-path rows have no MCP context.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'source'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN source text;
    COMMENT ON COLUMN tool_execution_log.source IS
      '"web_consume" | "mcp_primitive" | "mcp_bundle" | "mcp_sub_tool"';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'mcp_key_id'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN mcp_key_id text;
    COMMENT ON COLUMN tool_execution_log.mcp_key_id IS
      'API key ID from mcp_api_keys; NULL for web-path calls.';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'mcp_tool_name'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN mcp_tool_name text;
    COMMENT ON COLUMN tool_execution_log.mcp_tool_name IS
      'MCP-facing tool name (e.g. holistic_bundle). NULL for web-path calls.';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'audience_tier'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN audience_tier text;
    COMMENT ON COLUMN tool_execution_log.audience_tier IS
      '"super_admin" | "acharya" | "client". NULL for web-path calls.';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'bundle_trace_id'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN bundle_trace_id uuid;
    COMMENT ON COLUMN tool_execution_log.bundle_trace_id IS
      'For mcp_sub_tool rows: links back to the parent bundle trace_id.';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'signal_ids_available'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN signal_ids_available text[];
    COMMENT ON COLUMN tool_execution_log.signal_ids_available IS
      'signal_ids returned in this call envelope; the strict cite-allowlist.';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tool_execution_log' AND column_name = 'bundle_size_tokens'
  ) THEN
    ALTER TABLE tool_execution_log ADD COLUMN bundle_size_tokens integer;
    COMMENT ON COLUMN tool_execution_log.bundle_size_tokens IS
      'Estimated tokens in the bundle payload (mcp_bundle rows only).';
  END IF;
END $$;

-- Sparse index for MCP-only queries (future rows only)
CREATE INDEX IF NOT EXISTS tool_execution_log_mcp_tool_idx
  ON tool_execution_log (mcp_tool_name, created_at)
  WHERE mcp_tool_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS tool_execution_log_source_idx
  ON tool_execution_log (source, created_at)
  WHERE source IS NOT NULL;

-- ─── Part 2: Materialized Views ─────────────────────────────────────────────

-- ── View 1: mv_tool_metrics_24h ─────────────────────────────────────────────
-- Per-tool aggregation over last 24h.
-- Refresh cadence: every 5 minutes (Cloud Scheduler job mcpt-mv-tool-metrics-refresh).
-- Empty on first refresh since no MCP calls have mcp_tool_name set yet.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tool_metrics_24h AS
SELECT
  mcp_tool_name,
  COALESCE(source, 'unknown')                                              AS source,
  COALESCE(audience_tier, 'unknown')                                       AS audience_tier,
  count(*)                                                                 AS calls_24h,
  count(*) FILTER (WHERE status = 'ok')                                    AS ok_calls,
  count(*) FILTER (WHERE status = 'zero_rows')                             AS zero_rows_calls,
  count(*) FILTER (WHERE status = 'error')                                 AS error_calls,
  count(*) FILTER (WHERE status = 'ok')::float / NULLIF(count(*), 0)       AS ok_rate,
  count(*) FILTER (WHERE status = 'zero_rows')::float / NULLIF(count(*), 0) AS zero_rows_rate,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY latency_ms)                 AS p50_latency_ms,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)                 AS p95_latency_ms,
  percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms)                 AS p99_latency_ms,
  avg(rows_returned)                                                       AS avg_rows_returned,
  avg(bundle_size_tokens) FILTER (WHERE bundle_size_tokens IS NOT NULL)    AS avg_bundle_size_tokens,
  max(created_at)                                                          AS last_call_at
FROM tool_execution_log
WHERE created_at >= now() - interval '24 hours'
  AND mcp_tool_name IS NOT NULL
GROUP BY mcp_tool_name, COALESCE(source, 'unknown'), COALESCE(audience_tier, 'unknown');

CREATE UNIQUE INDEX IF NOT EXISTS mv_tool_metrics_24h_pk
  ON mv_tool_metrics_24h (mcp_tool_name, source, audience_tier);

-- ── View 2: mv_data_source_coverage ─────────────────────────────────────────
-- Per-asset row counts + last-write timestamp, refreshed nightly.
-- Refresh cadence: nightly 02:00 UTC (Cloud Scheduler job mcpt-mv-data-source-coverage-refresh).
-- Schema deviations from brief: uses promoted_at (not completed_at) from build_manifests;
-- uses life_events (not lel_events); uses ingested_at for msr_signals; date for panchanga/ephemeris.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_data_source_coverage AS
SELECT
  'chart_facts'::text              AS asset_id,
  category                         AS subkey,
  count(*)                         AS row_count,
  max(created_at)                  AS last_row_written_ts,
  (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'chart_facts')
                                   AS last_bootstrap_ts
FROM chart_facts
GROUP BY category

UNION ALL

SELECT 'msr_signals', null, count(*), max(ingested_at),
       (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'msr_signals')
FROM msr_signals

UNION ALL

SELECT 'life_events', category, count(*), null,
       (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'life_events')
FROM life_events
GROUP BY category

UNION ALL

SELECT 'classical_texts', work, count(*), max(created_at),
       (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'classical_texts')
FROM classical_texts
GROUP BY work

UNION ALL

SELECT 'rag_chunks', canonical_id, count(*), max(created_at),
       (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'rag_chunks')
FROM rag_chunks
GROUP BY canonical_id

UNION ALL

SELECT 'panchanga_daily', null, count(*), max(date)::timestamptz,
       (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'panchanga_daily')
FROM panchanga_daily

UNION ALL

SELECT 'ephemeris_daily', null, count(*), max(date)::timestamptz,
       (SELECT max(promoted_at) FROM build_manifests WHERE asset_id = 'ephemeris_daily')
FROM ephemeris_daily;

-- COALESCE on subkey so NULL subkeys don't defeat the uniqueness requirement
-- needed for REFRESH MATERIALIZED VIEW CONCURRENTLY.
CREATE UNIQUE INDEX IF NOT EXISTS mv_data_source_coverage_pk
  ON mv_data_source_coverage (asset_id, COALESCE(subkey, ''));

-- ── View 3: mv_session_summary ───────────────────────────────────────────────
-- Per-MCP-session rollup (grouped by key + hour), refreshed every 10 minutes.
-- Only includes MCP-source rows (source LIKE 'mcp%').
-- Will be empty on first refresh since existing web-path rows have source=NULL.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_session_summary AS
SELECT
  COALESCE(mcp_key_id, 'web')                                              AS mcp_key_id,
  COALESCE(audience_tier, 'unknown')                                       AS audience_tier,
  date_trunc('hour', created_at)                                           AS session_hour,
  count(DISTINCT mcp_tool_name) FILTER (WHERE source = 'mcp_primitive')   AS unique_primitives,
  count(*) FILTER (WHERE source = 'mcp_primitive')                         AS primitive_calls,
  count(*) FILTER (WHERE source = 'mcp_bundle')                            AS bundle_calls,
  count(*) FILTER (WHERE source = 'mcp_sub_tool')                          AS sub_tool_calls,
  sum(rows_returned)                                                       AS total_rows_returned,
  count(*) FILTER (WHERE status = 'zero_rows')                             AS zero_rows_calls,
  sum(bundle_size_tokens) FILTER (WHERE source = 'mcp_bundle')             AS total_bundle_tokens
FROM tool_execution_log
WHERE source LIKE 'mcp%'
GROUP BY COALESCE(mcp_key_id, 'web'), COALESCE(audience_tier, 'unknown'),
         date_trunc('hour', created_at);

CREATE UNIQUE INDEX IF NOT EXISTS mv_session_summary_pk
  ON mv_session_summary (mcp_key_id, session_hour);

-- ── View 4: mv_tool_grounding_24h ────────────────────────────────────────────
-- Per-tool audit finding rate over 24h, refreshed every 15 minutes.
--
-- Simplified from brief spec: the full brief version requires cited_signal_ids[]
-- on mcp_audit_findings (not present in production schema) and signal_ids_available[]
-- on tool_execution_log (added in Part 1 above, but will be NULL for existing rows).
-- This version counts audit findings per tool name from mcp_audit_findings.tool_name,
-- surfacing violation_rate and info_rate as the primary health signal.
-- Will be upgraded to citation-grounding rate once signal_ids_available is populated
-- by the MCP server's tool execution path (v3.8 backfill).

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tool_grounding_24h AS
SELECT
  tel.mcp_tool_name,
  count(DISTINCT tel.id)                                                        AS traces,
  count(DISTINCT af.id)                                                         AS audit_findings_count,
  count(DISTINCT af.id) FILTER (WHERE af.severity = 'info')::float /
    NULLIF(count(DISTINCT tel.id), 0)                                           AS info_rate,
  count(DISTINCT af.id) FILTER (WHERE af.severity IN ('warn', 'class_1', 'class_2'))::float /
    NULLIF(count(DISTINCT tel.id), 0)                                           AS violation_rate
FROM tool_execution_log tel
LEFT JOIN mcp_audit_findings af
  ON af.tool_name = tel.mcp_tool_name
  AND af.attached_at >= now() - interval '24 hours'
WHERE tel.created_at >= now() - interval '24 hours'
  AND tel.mcp_tool_name IS NOT NULL
GROUP BY tel.mcp_tool_name;

CREATE UNIQUE INDEX IF NOT EXISTS mv_tool_grounding_24h_pk
  ON mv_tool_grounding_24h (mcp_tool_name);

-- ─── Part 3: Initial population ─────────────────────────────────────────────
-- Refresh all 4 MVs immediately so they're populated on first query.

REFRESH MATERIALIZED VIEW mv_tool_metrics_24h;
REFRESH MATERIALIZED VIEW mv_data_source_coverage;
REFRESH MATERIALIZED VIEW mv_session_summary;
REFRESH MATERIALIZED VIEW mv_tool_grounding_24h;

COMMIT;
