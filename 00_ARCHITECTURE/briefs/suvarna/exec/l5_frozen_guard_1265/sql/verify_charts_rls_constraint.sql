-- READ ONLY (run by the operator as suvarna_reader; hash-bound in the plan). STANDING CONSTRAINT (SS): no FORCE ROW LEVEL SECURITY on public.charts
-- without first revisiting the 1265 chart-deletion guard. Run in every dry run and in every W-step read-back. Expected: verdict = OK.
SELECT c.relname,
       c.relrowsecurity AS rls_enabled,
       c.relforcerowsecurity AS rls_forced,
       pg_get_userbyid(c.relowner) AS owner,
       CASE WHEN c.relforcerowsecurity
            THEN 'FAIL: FORCE ROW LEVEL SECURITY is set on public.charts. STOP: the 1265 chart-deletion discriminator (SECURITY DEFINER) is unsafe under it. Revisit the guard before keeping FORCE.'
            ELSE 'OK' END AS verdict
  FROM pg_class c
 WHERE c.relnamespace = 'public'::regnamespace AND c.relname = 'charts';
-- the discriminator must be SECURITY DEFINER and owned by the owner of charts (expect true, true)
SELECT p.prosecdef AS definer, p.proowner = c.relowner AS owned_by_charts_owner
  FROM pg_proc p, pg_class c
 WHERE p.proname = 'l5_frozen_chart_cascade_authorizes' AND c.relnamespace = 'public'::regnamespace AND c.relname = 'charts';
