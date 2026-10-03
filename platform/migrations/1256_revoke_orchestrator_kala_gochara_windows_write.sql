-- 1256_revoke_orchestrator_kala_gochara_windows_write.sql
--
-- Pravāha (C39, 2026-10-03): REVOKE the dormant role `role_orchestrator`'s unused WRITE privileges
-- (UPDATE, DELETE — table-level and any column-level UPDATE) on public.kala_gochara_windows.
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
-- exactly two privileges (UPDATE, DELETE) plus any column-level UPDATE. No GRANT, no CREATE/ALTER/
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
--   has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE') = false
-- has_table_privilege reports EFFECTIVE privilege (direct, PUBLIC, inherited); if any path still
-- shows the privilege the migration fails and rolls back rather than looking migrated.
--
-- LOCK TIMEOUT (pattern: migrations 1218/1255). The first statement is `SET LOCAL lock_timeout = '5s'`:
-- REVOKE takes a brief lock on the table's ACL, and a blocked migrate job must fail fast, not hang a
-- shared deploy.
--
-- ORDERING: an ordinary ROUTINE migration — it is NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS
-- (platform/scripts/migrate.ts) and deploys by the routine path. It may merge and apply at any time
-- before the Gochara 5 window opens.
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
        RAISE NOTICE '1256: role role_orchestrator does not exist; no-op';
        RETURN;
    END IF;

    IF rel IS NULL THEN
        RAISE EXCEPTION '1256: public.kala_gochara_windows does not exist';
    END IF;

    -- Table-level write privileges (no-op where not held).
    EXECUTE 'REVOKE UPDATE, DELETE ON TABLE public.kala_gochara_windows FROM role_orchestrator';

    -- Column-level UPDATE grants, if any exist (a table-level REVOKE does not remove them).
    FOR col IN
        SELECT column_name
          FROM information_schema.column_privileges
         WHERE table_schema = 'public'
           AND table_name = 'kala_gochara_windows'
           AND grantee = 'role_orchestrator'
           AND privilege_type = 'UPDATE'
    LOOP
        EXECUTE format('REVOKE UPDATE (%I) ON TABLE public.kala_gochara_windows FROM role_orchestrator',
                       col.column_name);
    END LOOP;

    -- Post-check: no effective UPDATE or DELETE path may remain (see the header for what these see).
    IF has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE')
       OR has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'DELETE')
       OR has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE') THEN
        RAISE EXCEPTION '1256: role_orchestrator still holds a write privilege on public.kala_gochara_windows after the revokes';
    END IF;
END $$;
