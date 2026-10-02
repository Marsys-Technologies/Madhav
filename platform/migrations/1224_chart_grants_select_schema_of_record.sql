-- 1224_chart_grants_select_schema_of_record.sql
--
-- Suvarna Track I (SS ruling 2026-10-02): put `GRANT SELECT ON public.chart_grants TO data_plane_builder` into
-- the migration history, i.e. make the schema-of-record carry a privilege that production already holds.
--
-- WHY. `data_plane_builder` (the dedicated identity of the build pipeline job, migration 1070) must evaluate the
-- row-level policy on public.charts, whose USING expression reads public.chart_grants. Without SELECT on
-- chart_grants the builder's very first `SELECT ... FROM public.charts` fails with InsufficientPrivilege, so
-- every per-chart build fails. Production was repaired by a D6 owner-path apply (exactly one GRANT, run as
-- amjis_app via SET LOCAL ROLE; plan and executor: /Users/Dev/suvarna-evidence/ChartGrants/apply_CG.txt and
-- cg_exec.py; its commit conditions were: relacl diff over all public relations == [chart_grants |
-- data_plane_builder | SELECT absent->present]; relrowsecurity, relforcerowsecurity, pg_policy and role
-- membership diffs empty; builder privileges on chart_grants == SELECT only). A database built PURELY from
-- migrations (a disposable rebuild, a new environment) never received that grant and would fail every per-chart
-- build the same way. This file closes that gap.
--
-- PRODUCTION BEHAVIOUR: A GUARDED NO-OP. Production already holds exactly this grant (live relacl of
-- public.chart_grants includes data_plane_builder=r/amjis_app, read 2026-10-02), so the GRANT is skipped when
-- has_table_privilege('data_plane_builder','public.chart_grants','SELECT') is already true. Nothing is changed
-- there; the migration only records the privilege in the history.
-- FRESH-FROM-MIGRATIONS BEHAVIOUR: the privilege is absent, so exactly one GRANT is issued by the table owner
-- (the migration runner authenticates as amjis_app, which owns public.chart_grants; same authority as 1225).
--
-- SCOPE: exactly one privilege (SELECT, policy evaluation only), one table, one role. No other privilege, no
-- sequence, no policy, no RLS flag, no role membership, no data touched. Post-condition asserted: SELECT held,
-- and none of INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER held by data_plane_builder on chart_grants (true
-- in production by the D6 commit conditions above).
--
-- GUARDS: the table public.chart_grants and the role data_plane_builder must exist, else the migration RAISES
-- (a silent skip would let a database that lacks the privilege look migrated; 1070 already requires the same
-- role). GRANT is idempotent in PostgreSQL, so a re-run is harmless.
--
-- VERIFICATION AFTER APPLY is by production structure, not the deploy log (Trap 103):
--   SELECT has_table_privilege('data_plane_builder','public.chart_grants','SELECT');   -- true
--   SELECT relacl FROM pg_class WHERE oid = 'public.chart_grants'::regclass;           -- unchanged in production
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    extra text;
BEGIN
    IF to_regclass('public.chart_grants') IS NULL THEN
        RAISE EXCEPTION '1224: public.chart_grants does not exist';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        RAISE EXCEPTION '1224: role data_plane_builder does not exist';
    END IF;

    IF has_table_privilege('data_plane_builder', 'public.chart_grants', 'SELECT') THEN
        RAISE NOTICE '1224: data_plane_builder already holds SELECT on public.chart_grants; no-op';
    ELSE
        GRANT SELECT ON TABLE public.chart_grants TO data_plane_builder;
    END IF;

    -- Verify it actually took effect (never trust a silent no-op) and that nothing broader is held.
    IF NOT has_table_privilege('data_plane_builder', 'public.chart_grants', 'SELECT') THEN
        RAISE EXCEPTION '1224: data_plane_builder lacks SELECT on public.chart_grants after the grant';
    END IF;
    SELECT string_agg(p, ', ' ORDER BY p) INTO extra
      FROM unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) p
     WHERE has_table_privilege('data_plane_builder', 'public.chart_grants', p);
    IF extra IS NOT NULL THEN
        RAISE EXCEPTION '1224: data_plane_builder holds more than SELECT on public.chart_grants: %', extra;
    END IF;
END $$;
