-- ═══════════════════════════════════════════════════════════════════════════════
-- G1-C — ARM the chart-scoped RLS created by migration 576.
-- Paripraśna P1 FOUNDATION, lane G1-C (NCD-5 · PPR-22).
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- THIS FILE IS NOT A MIGRATION AND IS NOT AUTO-APPLIED.
--
-- It lives under `platform/scripts/pariprashna/`, not under `platform/migrations/`
-- or `platform/supabase/migrations/`. `platform/scripts/migrate.ts` reads only
-- those two directories (see its main(), `dirs = [...]`), so the deploy-time
-- runner will never execute this file. Arming RLS is a deliberate operator act
-- with live traffic consequences, and it is gated on a decision this session was
-- not authorized to make.
--
-- RUN IT ONLY as part of the cutover described in
--   00_ARCHITECTURE/briefs/pariprashna_swarm/G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0.md
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f platform/scripts/pariprashna/g1c_arm_rls.sql
--
-- ── THE SAFETY QUESTION THIS SCRIPT ANSWERS FOR ITSELF ─────────────────────────
-- Enabling RLS on a table denies every role for which no policy grants access.
-- Migration 576 wrote policies for the five new roles ONLY. The credential the
-- application currently serves on (`amjis_app`) has no policy — so the instant
-- RLS is enabled, one of two things is true:
--
--   (a) `amjis_app` OWNS the table. Table owners bypass RLS unless FORCE ROW
--       LEVEL SECURITY is set (it is not, anywhere). Arming is then a no-op for
--       the running application, and safe.
--   (b) `amjis_app` does NOT own the table. Arming immediately denies the running
--       application every row of that table. That is a production outage.
--
-- This script does not guess. It MEASURES ownership and REFUSES to arm anything
-- if the answer is (b) for even one table — CLAUDE.md §N.8: a safety signal needs
-- a detector that can make it read false, and this is that detector. Override is
-- deliberate and explicit (see G1C_ARM_ACCEPT_OWNERSHIP_RISK below), never a
-- default.
--
-- ── DISARM ────────────────────────────────────────────────────────────────────
-- `g1c_disarm_rls.sql`, same directory. Rollback is one statement per table and
-- takes effect immediately; it does not drop the policies.

\set ON_ERROR_STOP on

-- Operator-settable inputs, with defaults. Override at call time, e.g.
--   psql "$DATABASE_URL" -v g1c_app_role=role_web_serve \
--        -v g1c_accept_ownership_risk=yes -f .../g1c_arm_rls.sql
\if :{?g1c_app_role}
\else
  \set g1c_app_role 'amjis_app'
\endif
\if :{?g1c_accept_ownership_risk}
\else
  \set g1c_accept_ownership_risk 'no'
\endif

BEGIN;

-- Hand the psql variables to the DO block, which can only read GUCs.
SET LOCAL g1c.app_role = :'g1c_app_role';
SET LOCAL g1c.accept_ownership_risk = :'g1c_accept_ownership_risk';

DO $arm$
DECLARE
  -- The role the live application connects as. Override at call time with
  --   psql -v g1c_app_role=some_other_role ...
  app_role text := coalesce(
    nullif(current_setting('g1c.app_role', true), ''),
    'amjis_app'
  );
  -- Set to the exact string 'yes' ONLY when an operator has read the ownership
  -- report below and consciously accepts arming despite a non-owner app role
  -- (e.g. because the app has already been cut over to role_web_serve, which is
  -- the normal, correct reason for this to be set).
  accept_risk text := coalesce(
    nullif(current_setting('g1c.accept_ownership_risk', true), ''),
    'no'
  );
  tbl text;
  targets text[];
  not_owned text[] := ARRAY[]::text[];
  owner_name text;
  armed int := 0;
BEGIN
  -- Arm exactly the tables migration 576 wrote a chart-context policy for —
  -- derived from pg_policies, not from a second hand-maintained list that could
  -- drift away from the migration's.
  SELECT array_agg(DISTINCT tablename ORDER BY tablename)
    INTO targets
  FROM pg_policies
  WHERE schemaname = 'public'
    AND policyname LIKE '%\_g1c\_chart\_context';

  IF targets IS NULL OR array_length(targets, 1) = 0 THEN
    RAISE EXCEPTION
      'G1C_ARM_NO_POLICIES: no *_g1c_chart_context policies exist in this database. '
      'Migration 576 has not been applied here. Refusing to arm nothing and report success.';
  END IF;

  -- ── The detector ──────────────────────────────────────────────────────────
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = app_role) THEN
    FOREACH tbl IN ARRAY targets LOOP
      SELECT pg_get_userbyid(c.relowner) INTO owner_name
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public' AND c.relname = tbl;

      IF owner_name IS DISTINCT FROM app_role THEN
        not_owned := not_owned || (tbl || ' (owner: ' || coalesce(owner_name, '?') || ')');
      END IF;
    END LOOP;
  ELSE
    RAISE NOTICE
      'G1C_ARM: role "%" does not exist in this database — treating ownership check as '
      'not-applicable (this is normal on a local scratch DB).', app_role;
  END IF;

  IF array_length(not_owned, 1) > 0 THEN
    IF accept_risk <> 'yes' THEN
      RAISE EXCEPTION
        'G1C_ARM_REFUSED_NOT_OWNER: enabling RLS would immediately deny "%" all rows of % '
        'table(s) it does not own: %. Nothing has been armed; this transaction rolls back. '
        'Either (1) cut the application over to role_web_serve FIRST and re-run, or '
        '(2) if the cutover has already happened and this is the expected state, re-run with '
        '-v g1c_accept_ownership_risk=yes to record a conscious acceptance.',
        app_role, array_length(not_owned, 1), array_to_string(not_owned, '; ');
    END IF;
    RAISE WARNING
      'G1C_ARM: proceeding despite % non-owned table(s) because g1c.accept_ownership_risk=yes '
      'was set explicitly: %', array_length(not_owned, 1), array_to_string(not_owned, '; ');
  END IF;

  -- ── Arm ───────────────────────────────────────────────────────────────────
  FOREACH tbl IN ARRAY targets LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl);
    armed := armed + 1;
  END LOOP;

  RAISE NOTICE 'G1C_ARM: ROW LEVEL SECURITY enabled on % table(s): %',
    armed, array_to_string(targets, ', ');
END
$arm$;

COMMIT;

-- ── Post-arm verification (read-only; run it, do not skip it) ─────────────────
-- Every armed table must show rowsecurity = true AND at least 2 g1c policies.
SELECT c.relname                                    AS table_name,
       c.relrowsecurity                             AS rls_enabled,
       c.relforcerowsecurity                        AS rls_forced,
       count(p.policyname) FILTER (WHERE p.policyname LIKE '%\_g1c\_%') AS g1c_policies
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_policies p ON p.schemaname = n.nspname AND p.tablename = c.relname
WHERE n.nspname = 'public'
  AND c.relname IN (SELECT DISTINCT tablename FROM pg_policies
                    WHERE schemaname = 'public' AND policyname LIKE '%\_g1c\_chart\_context')
GROUP BY 1, 2, 3
ORDER BY 1;
