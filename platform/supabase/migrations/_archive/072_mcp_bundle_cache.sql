-- Migration 072: MCP Bundle Cache
-- MCPT v3.1.0-S2
-- Stores 5-minute content-addressable bundle results.
-- Cache key: sha256(query_text + JSON(composition_params) + tier + chart_id)

-- ── UP ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mcp_bundle_cache (
  cache_key      text        PRIMARY KEY,                          -- sha256 hex
  bundle_name    text        NOT NULL,                             -- 'holistic_bundle' | 'multi_school_bundle'
  audience_tier  text        NOT NULL,
  chart_id       uuid        NOT NULL,
  envelope_json  jsonb       NOT NULL,                             -- full envelope (arch §5)
  cached_at      timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL                              -- cached_at + interval '5 minutes'
);

-- Expiry index for periodic cleanup
CREATE INDEX IF NOT EXISTS mcp_bundle_cache_expiry ON mcp_bundle_cache (expires_at);

-- Composite index for bundle_name + tier lookups (for telemetry)
CREATE INDEX IF NOT EXISTS mcp_bundle_cache_bundle_tier
  ON mcp_bundle_cache (bundle_name, audience_tier);

COMMENT ON TABLE mcp_bundle_cache IS
  'Content-addressable cache for MCP Tier 2 bundle results. TTL: 5 minutes. '
  'Key: sha256(query_text + JSON(composition_params) + tier + chart_id). '
  'Periodic cleanup: DELETE FROM mcp_bundle_cache WHERE expires_at < now(); '
  'This should run every 10 minutes via pg_cron or Cloud Scheduler.';

COMMENT ON COLUMN mcp_bundle_cache.cache_key IS 'sha256 hex of (bundle_name + query_text + composition_params + tier + chart_id)';
COMMENT ON COLUMN mcp_bundle_cache.envelope_json IS 'Full MCP bundle envelope (holistic or multi_school), conforming to arch §5 envelope contract';
COMMENT ON COLUMN mcp_bundle_cache.expires_at IS 'cached_at + 5 minutes; rows past this timestamp are stale and should be deleted';

-- ── DOWN ───────────────────────────────────────────────────────────────────────

-- To rollback this migration:
-- DROP INDEX IF EXISTS mcp_bundle_cache_bundle_tier;
-- DROP INDEX IF EXISTS mcp_bundle_cache_expiry;
-- DROP TABLE IF EXISTS mcp_bundle_cache;
