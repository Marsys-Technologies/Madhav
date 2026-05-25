-- 117_audience_tier_acharya_enum.sql
-- Adds 'acharya' value to the audience_tier CHECK constraint on mcp_api_keys.
-- acharya tier: external accuracy reviewers with full analytical tool access
-- (tool_health + data_coverage permitted; no write/ops tools per house-rules).
--
-- NOTE: audience_tier on mcp_api_keys is a text column with a CHECK constraint
-- (NOT a named Postgres enum type). Introduced by migration 070.
-- ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT is the correct approach.
--
-- Idempotency: checks if 'acharya' is already accepted before making changes.
-- Safe to re-run.
--
-- FIX (applied DAR-P2-S5 2026-05-25): pg_constraint.consrc was removed in PG12.
-- Use pg_get_constraintdef(c.oid) instead for constraint text inspection.

DO $$
DECLARE
  v_conname text;
  v_condef  text;
BEGIN
  -- Find the CHECK constraint on mcp_api_keys that relates to audience_tier.
  -- pg_constraint.consrc was removed in PG12; use pg_get_constraintdef() instead.
  SELECT c.conname, pg_get_constraintdef(c.oid)
    INTO v_conname, v_condef
    FROM pg_constraint c
    JOIN pg_class r ON r.oid = c.conrelid
    WHERE r.relname = 'mcp_api_keys'
      AND c.contype = 'c'
      AND pg_get_constraintdef(c.oid) LIKE '%audience_tier%';

  -- If the constraint already includes 'acharya', nothing to do.
  IF v_conname IS NOT NULL AND v_condef LIKE '%acharya%' THEN
    RAISE NOTICE 'audience_tier constraint already includes acharya — no change needed.';
    RETURN;
  END IF;

  -- Drop the old constraint if it exists.
  IF v_conname IS NOT NULL THEN
    EXECUTE format('ALTER TABLE mcp_api_keys DROP CONSTRAINT %I', v_conname);
  END IF;

  -- Add new CHECK constraint that includes acharya.
  ALTER TABLE mcp_api_keys
    ADD CONSTRAINT mcp_api_keys_audience_tier_check
    CHECK (audience_tier IN ('client', 'super_admin', 'acharya'));

  RAISE NOTICE 'audience_tier constraint updated to include acharya.';
END $$;
