-- platform/migrations/058_aiops_routing_override_ttl.sql
-- Migration: Phase 3C observability hardening — expires_at TTL column.
--
-- Rationale: AIOps automation that writes emergency overrides has no self-expiry
-- mechanism. The 2026-05-15 regression ran 3 days because the override row persisted
-- indefinitely. This column lets automation set a TTL so temporary overrides
-- auto-expire without requiring explicit deletion.
--
-- Policy (Phase 3C):
--   - AIOps automation: MUST set expires_at = NOW() + INTERVAL '72 hours' (default)
--     or NOW() + INTERVAL '4 hours' for critical emergencies
--   - Control Panel (manual super-admin): expires_at = NULL = permanent policy override
--   - The resolver (runtime_config.ts) ignores rows where expires_at <= NOW()
--
-- Existing rows: all existing rows get expires_at = NULL (permanent) to preserve
-- current behavior. The nim synthesis override (gemini-2.5-flash policy) is permanent.

BEGIN;

ALTER TABLE llm_stack_routing_override
  ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ DEFAULT NULL;

COMMENT ON COLUMN llm_stack_routing_override.expires_at IS
  'NULL = permanent override (manual policy). Non-NULL = auto-expire at this time. '
  'AIOps automation MUST set this to NOW() + 72h (or shorter for emergencies). '
  'The resolver ignores rows where expires_at <= NOW().';

COMMIT;

-- Down:
-- ALTER TABLE llm_stack_routing_override DROP COLUMN IF EXISTS expires_at;
