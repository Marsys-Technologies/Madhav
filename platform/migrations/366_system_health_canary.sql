-- Migration 366: system_health canary-battery result store
-- Created: 2026-07-09
--
-- R5.1 C5.2 (CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md): "Canary battery -> scheduled
-- job (daily, feeds system_health; alert on regression)."
--
-- system_health is a generic append-only health-probe ledger — one row per probe per
-- run. The canary battery (evals/r5-w0a-canary/canary_runner.ts logic, ported to
-- platform/src/lib/canary/canary_probes.ts) is the first writer; the shape is generic
-- enough for future daily health checks (e.g. sidecar liveness) to reuse the same table
-- rather than each inventing their own.
--
-- Regression alerting reuses the EXISTING mcp_alerts_config + checkAndDispatch
-- mechanism (platform/src/lib/alerts/dispatch.ts) — no new alert channel invented.
-- The canary route computes a regression count (probes that were 'pass' on the prior
-- run and are 'fail' on this run) and feeds it through checkAndDispatch as a
-- MetricSnapshot; these two seed rows are what checkAndDispatch matches against.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- system_health — one row per probe per canary run
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.system_health (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  component   TEXT        NOT NULL,             -- e.g. 'canary_battery'
  probe_id    TEXT        NOT NULL,              -- e.g. 'P1' .. 'P8'
  chart_id    TEXT,                              -- chart scope, when applicable
  status      TEXT        NOT NULL CHECK (status IN ('pass', 'fail', 'error')),
  detail      TEXT,
  latency_ms  NUMERIC,
  run_id      UUID        NOT NULL,              -- groups all probe rows of one run
  checked_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast "what was the prior status for this probe" lookup (regression detection)
-- and "latest run" dashboard queries.
CREATE INDEX IF NOT EXISTS system_health_probe_recency
  ON public.system_health (component, probe_id, chart_id, checked_at DESC);

CREATE INDEX IF NOT EXISTS system_health_run_id
  ON public.system_health (run_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- mcp_alerts_config seed rows — canary regression / failure thresholds
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO public.mcp_alerts_config
  (metric_name, scope, tool_name, threshold_value, comparison, window_hours, channels, enabled)
SELECT v.metric_name, v.scope, v.tool_name, v.threshold_value, v.comparison, v.window_hours, v.channels, v.enabled
FROM (
  VALUES
    ('canary_probe_regression_count', 'global', NULL::text, 1, 'gte', 1, ARRAY['slack']::text[], TRUE),
    ('canary_probe_fail_count',       'global', NULL::text, 3, 'gte', 1, ARRAY['slack']::text[], TRUE)
) AS v(metric_name, scope, tool_name, threshold_value, comparison, window_hours, channels, enabled)
WHERE NOT EXISTS (
  SELECT 1 FROM public.mcp_alerts_config existing
  WHERE existing.metric_name = v.metric_name
    AND existing.scope = v.scope
    AND existing.tool_name IS NOT DISTINCT FROM v.tool_name
);

COMMIT;

-- Down:
-- DELETE FROM public.mcp_alerts_config WHERE metric_name IN ('canary_probe_regression_count', 'canary_probe_fail_count') AND scope = 'global';
-- DROP TABLE IF EXISTS public.system_health;
