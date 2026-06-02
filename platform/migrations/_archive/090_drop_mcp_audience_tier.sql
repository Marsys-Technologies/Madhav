-- 090_drop_mcp_audience_tier.sql
-- Stream A 3.tier_excision (2026-05-28): drop the audience_tier column on
-- mcp_api_keys (introduced 070_mcp_api_keys.sql, constraint-relaxed by
-- 117_audience_tier_acharya_enum.sql). The audience-tier subsystem is
-- redundant overlap with authorizeChartAccess (G2, live since unit 2c).
--
-- ORDER: this migration runs LAST in the unit (commit 3 of 3). The column drop
-- is the only irreversible step — preceded by two commits that strip every
-- read site so live code never references the column when it's gone.
--
-- Idempotency: this migration checks for column existence before dropping;
-- safe to re-run; safe to apply pre- or post-deploy of the code changes (the
-- code drops the SELECT projection in commit 2, so application traffic never
-- expects the column after that point).
--
-- Rollback path: this migration is forward-only. The on_red discipline for
-- this unit is `revert WIP commits and leave branch at main`; the column drop
-- only runs after a green window from commits 1+2, so reverting the unit
-- before this migration is applied is safe. After application, the column
-- and its constraint are gone for good.

DO $$
DECLARE
  v_conname text;
BEGIN
  -- 1. Drop the audience_tier CHECK constraint (regardless of which migration
  --    last touched it — 070 or 117). pg_get_constraintdef is PG12+ safe.
  SELECT c.conname
    INTO v_conname
    FROM pg_constraint c
    JOIN pg_class r ON r.oid = c.conrelid
   WHERE r.relname = 'mcp_api_keys'
     AND c.contype = 'c'
     AND pg_get_constraintdef(c.oid) LIKE '%audience_tier%';

  IF v_conname IS NOT NULL THEN
    EXECUTE format('ALTER TABLE mcp_api_keys DROP CONSTRAINT %I', v_conname);
    RAISE NOTICE 'Dropped audience_tier CHECK constraint: %', v_conname;
  END IF;

  -- 2. Drop the audience_tier column if it still exists.
  IF EXISTS (
    SELECT 1
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'mcp_api_keys'
       AND column_name  = 'audience_tier'
  ) THEN
    ALTER TABLE mcp_api_keys DROP COLUMN audience_tier;
    RAISE NOTICE 'Dropped column mcp_api_keys.audience_tier.';
  ELSE
    RAISE NOTICE 'Column mcp_api_keys.audience_tier already absent — no change.';
  END IF;
END $$;
