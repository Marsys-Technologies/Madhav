-- ═══════════════════════════════════════════════════════════════════════════════
-- G1-C — DISARM the chart-scoped RLS armed by g1c_arm_rls.sql.
-- Paripraśna P1 FOUNDATION, lane G1-C (NCD-5 · PPR-22).
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- NOT a migration; never auto-applied (see g1c_arm_rls.sql's header for why).
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f platform/scripts/pariprashna/g1c_disarm_rls.sql
--
-- This is the rollback for an arming that went wrong. It disables row security on
-- exactly the tables migration 576 wrote a chart-context policy for, and takes
-- effect on the next statement — no restart, no deploy.
--
-- It deliberately does NOT drop the policies. A dropped policy has to be
-- recreated from a migration to come back; a disabled one is re-armed by running
-- g1c_arm_rls.sql again. Rollback should be cheap and reversible in both
-- directions.

\set ON_ERROR_STOP on

BEGIN;

DO $disarm$
DECLARE
  targets text[];
  tbl text;
  disarmed int := 0;
BEGIN
  SELECT array_agg(DISTINCT tablename ORDER BY tablename)
    INTO targets
  FROM pg_policies
  WHERE schemaname = 'public'
    AND policyname LIKE '%\_g1c\_chart\_context';

  IF targets IS NULL OR array_length(targets, 1) = 0 THEN
    RAISE EXCEPTION
      'G1C_DISARM_NO_POLICIES: no *_g1c_chart_context policies exist here, so there is nothing '
      'this script is responsible for. Refusing to report a successful disarm of nothing.';
  END IF;

  FOREACH tbl IN ARRAY targets LOOP
    EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', tbl);
    disarmed := disarmed + 1;
  END LOOP;

  RAISE NOTICE 'G1C_DISARM: ROW LEVEL SECURITY disabled on % table(s): %',
    disarmed, array_to_string(targets, ', ');
END
$disarm$;

COMMIT;

-- Verification: every one of these must now read false.
SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN (SELECT DISTINCT tablename FROM pg_policies
                    WHERE schemaname = 'public' AND policyname LIKE '%\_g1c\_chart\_context')
ORDER BY 1;
