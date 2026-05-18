-- aiops_overrides_active.sql
-- Review query: currently-active (non-expired) routing overrides + their audit trail.
--
-- Run periodically (session open, post-incident) to verify no unexpected overrides are live.
-- Add to daily monitoring script or session-open checklist §G step 0 (per Phase 3C governance amendment).
--
-- Usage:
--   psql $DATABASE_URL -f 00_ARCHITECTURE/aiops_overrides_active.sql

-- ── Active overrides ─────────────────────────────────────────────────────────

SELECT
  o.scope,
  o.stack,
  o.call_type,
  o.primary_model,
  o.fallback_model,
  o.updated_at,
  o.updated_by,
  o.expires_at,
  CASE
    WHEN o.expires_at IS NULL THEN 'permanent'
    ELSE 'expires ' || to_char(o.expires_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI') || ' UTC'
  END AS ttl_status
FROM llm_stack_routing_override o
WHERE o.scope = 'global'
  AND (o.expires_at IS NULL OR o.expires_at > NOW())
ORDER BY o.stack, o.call_type;

-- ── Audit trail for active overrides (last 10 events per override) ────────────

SELECT
  a.occurred_at AT TIME ZONE 'UTC' AS occurred_utc,
  a.actor_user_id,
  a.action,
  a.stack,
  a.call_type,
  a.before_value,
  a.after_value,
  a.notes
FROM llm_config_audit a
WHERE a.scope = 'global'
  AND a.action IN ('set_routing', 'reset_routing')
  AND a.occurred_at > NOW() - INTERVAL '7 days'
  AND a.notes IS DISTINCT FROM 'db_trigger'   -- API-sourced rows only; remove filter for full trail
ORDER BY a.occurred_at DESC
LIMIT 50;
