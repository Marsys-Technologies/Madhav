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

DO $$
DECLARE
  v_conname text;
BEGIN
  -- Find the name of the existing CHECK constraint on mcp_api_keys.audience_tier.
  -- The constraint name may vary by environment (Supabase auto-names it).
  SELECT conname
    INTO v_conname
    FROM pg_constraint
    JOIN pg_class ON pg_class.oid = pg_constraint.conrelid
    WHERE pg_class.relname = 'mcp_api_keys'
      AND pg_constraint.contype = 'c'
      AND pg_constraint.consrc LIKE '%audience_tier%';

  -- If the constraint already includes 'acharya', nothing to do.
  IF v_conname IS NOT NULL THEN
    IF EXISTS (
      SELECT 1
      FROM pg_constraint c
      JOIN pg_class r ON r.oid = c.conrelid
      WHERE r.relname = 'mcp_api_keys'
        AND c.contype = 'c'
        AND c.consrc LIKE '%acharya%'
    ) THEN
      RAISE NOTICE 'audience_tier constraint already includes acharya — no change needed.';
      RETURN;
    END IF;

    -- Drop the old constraint and add the new one including 'acharya'.
    EXECUTE format('ALTER TABLE mcp_api_keys DROP CONSTRAINT %I', v_conname);
  END IF;

  -- Add new CHECK constraint that includes acharya.
  ALTER TABLE mcp_api_keys
    ADD CONSTRAINT mcp_api_keys_audience_tier_check
    CHECK (audience_tier IN ('client', 'super_admin', 'acharya'));

  RAISE NOTICE 'audience_tier constraint updated to include acharya.';
END $$;
