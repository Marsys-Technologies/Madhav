-- 1302_revoke_role_orchestrator_windows_dml.sql
--
-- Pravāha (C39, 2026-10-03): REVOKE the dormant role `role_orchestrator`'s unused WRITE privileges
-- (UPDATE, DELETE, INSERT — table-level and any column-level UPDATE/INSERT) on public.kala_gochara_windows.
--
-- WHY. The pre-window readback W2(b) on 2026-10-03 found `role_orchestrator` among the effective
-- UPDATE/DELETE holders of the legacy Gochara relations. The role is dormant: NOLOGIN, a member of
-- no role, and — unlike the live writers — it holds no EXECUTE on the Gochara lock function
-- (public.ka_gochara_lock_chart), so it could never pass the lock-guarded write path anyway. Its
-- write privileges are dead capability. Removing them BEFORE the Gochara 5 window shrinks the W2(a)
-- holder set the steward must review to exactly the roles that can act, and removes a privilege no
-- code path uses.
--
-- SCOPE: exactly one table (public.kala_gochara_windows) and exactly one role (role_orchestrator),
-- exactly three privileges (UPDATE, DELETE, INSERT) plus any column-level UPDATE/INSERT. No GRANT, no CREATE/ALTER/
-- DROP, no data touched, no other role, no other table, nothing touching ka_gochara_* functions.
-- A read-only SELECT anywhere is unaffected.
--
-- IDEMPOTENT / ABSENT-ROLE NO-OP: where pg_roles has no `role_orchestrator` the whole migration is a
-- no-op (some environments never had the role). REVOKE of a privilege the role does not hold is
-- itself a no-op, so a re-run is harmless. Everything sits inside the one migration transaction
-- (BEGIN/COMMIT belong to platform/scripts/migrate.ts), so a refusal leaves NOTHING changed.
--
-- POST-CHECK (raises, never a silent skip): after the revokes,
--   has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE')  = false
--   has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'DELETE')  = false
--   has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'INSERT')  = false
--   has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE') = false
--   has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'INSERT') = false
-- has_table_privilege reports EFFECTIVE privilege (direct, PUBLIC, inherited); if any path still
-- shows the privilege the migration fails and rolls back rather than looking migrated.
--
-- LOCK TIMEOUT (pattern: migrations 1218/1255). The first statement is `SET LOCAL lock_timeout = '5s'`:
-- REVOKE takes a brief lock on the table's ACL, and a blocked migrate job must fail fast, not hang a
-- shared deploy.
--
-- ORDERING: an ordinary ROUTINE migration — it is NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS
-- (platform/scripts/migrate.ts) and deploys by the routine path. It must be MERGED AND APPLIED (an ordinary
-- deploy) BEFORE the protected train's first merge (sitting checklist row 7): once 1204 is on main the routine
-- runner refuses at it by name and nothing numbered above it can apply. The number 1302 is above every
-- migration on main and in any open PR, so it is not a <=1240 predecessor of the protected window.
--
-- SERVING EFFECT AT APPLY: none (no code executes as role_orchestrator; no registry/freshness/trigger
-- touched).
--
-- ROLLBACK NOTE: never re-GRANT blindly. To undo for real, author a new reviewed migration against
-- the then-current state.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    rel regclass := to_regclass('public.kala_gochara_windows');
    col record;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_orchestrator') THEN
        RAISE NOTICE '1302: role role_orchestrator does not exist; no-op';
        RETURN;
    END IF;

    IF rel IS NULL THEN
        RAISE EXCEPTION '1302: public.kala_gochara_windows does not exist';
    END IF;

    -- Table-level write privileges (no-op where not held).
    EXECUTE 'REVOKE UPDATE, DELETE, INSERT ON TABLE public.kala_gochara_windows FROM role_orchestrator';

    -- Column-level UPDATE/INSERT grants, if any exist (a table-level REVOKE does not remove them). Read from the
    -- catalog ACL (pg_attribute.attacl), which lists every column grant regardless of who made it.
    FOR col IN
        SELECT a.attname AS column_name
          FROM pg_attribute a, aclexplode(a.attacl) x
         WHERE a.attrelid = rel
           AND a.attnum > 0
           AND NOT a.attisdropped
           AND x.grantee = 'role_orchestrator'::regrole
           AND x.privilege_type IN ('UPDATE', 'INSERT')
         GROUP BY a.attname
    LOOP
        EXECUTE format('REVOKE UPDATE (%I), INSERT (%I) ON TABLE public.kala_gochara_windows FROM role_orchestrator',
                       col.column_name, col.column_name);
    END LOOP;

    -- Post-check: no effective UPDATE or DELETE path may remain (see the header for what these see).
    IF has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE')
       OR has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'DELETE')
       OR has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'INSERT')
       OR has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE')
       OR has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'INSERT') THEN
        RAISE EXCEPTION '1302: role_orchestrator still holds a write privilege on public.kala_gochara_windows after the revokes';
    END IF;
END $$;
