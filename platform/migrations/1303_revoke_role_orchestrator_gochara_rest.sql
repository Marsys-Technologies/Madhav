-- 1303_revoke_role_orchestrator_gochara_rest.sql
--
-- Pravāha (C40, 2026-10-03): REVOKE the dormant role `role_orchestrator`'s unused WRITE privileges
-- (INSERT, UPDATE, DELETE — table-level and any column-level UPDATE/INSERT) on the five remaining
-- legacy Gochara tables, and USAGE/UPDATE on the id sequences those tables own, where granted.
--
-- ⚠ ORDERING: this migration must be applied ONLY AFTER the Gochara 5 protected window is complete.
-- It is an ordinary ROUTINE migration — NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS
-- (platform/scripts/migrate.ts) — and it is a POST-WINDOW follow-up: merging or applying it before
-- the window closes is out of order. The number 1303 sits above every migration on main and in any
-- open PR (1302 is its pre-window sibling on public.kala_gochara_windows).
--
-- WHY. The pre-window readback W2(b) on 2026-10-03 found `role_orchestrator` among the effective
-- UPDATE/DELETE holders of the legacy Gochara relations. The role is dormant: NOLOGIN, a member of
-- no role, and — unlike the live writers — it holds no EXECUTE on the Gochara lock function
-- (public.ka_gochara_lock_chart), so it could never pass the lock-guarded write path anyway. 1302
-- took public.kala_gochara_windows before the window; this migration completes the set on the
-- remaining five tables once the window is done:
--   public.kala_gochara_authority
--   public.kala_gochara_v2_build_state
--   public.kala_gochara_windows__ssv_20260728c
--   public.kala_gochara_windows_archive_20260805
--   public.kala_gochara_windows_v2
-- Its write privileges are dead capability; removing them shrinks the holder set to exactly the
-- roles that can act, and removes a privilege no code path uses.
--
-- SCOPE: exactly the five tables above (plus their OWNED id sequences, discovered through
-- pg_depend) and exactly one role (role_orchestrator), exactly three table privileges
-- (INSERT, UPDATE, DELETE) plus any column-level UPDATE/INSERT, and USAGE/UPDATE on the sequences
-- where held. No GRANT, no CREATE/ALTER/DROP, no data touched, no other role, no other table,
-- nothing touching ka_gochara_* functions. A read-only SELECT anywhere is unaffected (SELECT
-- stays). Each table is guarded with to_regclass: a MISSING table is a NOTICE no-op (some
-- environments never had every legacy table), never a failure.
--
-- SEQUENCES: the id sequences owned by these tables (pg_depend 'a' dependency) get USAGE and
-- UPDATE revoked WHERE the role holds them; a table with no owned sequence is simply skipped by
-- the catalog loop. The post-check raises if any effective USAGE/UPDATE remains.
--
-- IDEMPOTENT / ABSENT-ROLE NO-OP: where pg_roles has no `role_orchestrator` the whole migration is
-- a NOTICE no-op. REVOKE of a privilege the role does not hold is itself a no-op, so a re-run is
-- harmless. Everything sits inside the one migration transaction (BEGIN/COMMIT belong to
-- platform/scripts/migrate.ts), so a refusal leaves NOTHING changed.
--
-- POST-CHECK (raises, never a silent skip), per existing table:
--   has_table_privilege('role_orchestrator', <table>, 'INSERT'|'UPDATE'|'DELETE') = false
--   has_any_column_privilege('role_orchestrator', <table>, 'INSERT'|'UPDATE')     = false
-- and per owned sequence:
--   has_sequence_privilege('role_orchestrator', <sequence>, 'USAGE'|'UPDATE')     = false
-- has_*_privilege reports EFFECTIVE privilege (direct, PUBLIC, inherited); if any path still shows
-- the privilege the migration fails and rolls back rather than looking migrated.
--
-- LOCK TIMEOUT (pattern: migrations 1218/1255/1302). The first statement is
-- `SET LOCAL lock_timeout = '5s'`: REVOKE takes a brief lock on the table's ACL, and a blocked
-- migrate job must fail fast, not hang a shared deploy.
--
-- SERVING EFFECT AT APPLY: none (no code executes as role_orchestrator; no
-- registry/freshness/trigger touched).
--
-- ROLLBACK NOTE: never re-GRANT blindly. To undo for real, author a new reviewed migration against
-- the then-current state.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    tables text[] := ARRAY[
        'kala_gochara_authority',
        'kala_gochara_v2_build_state',
        'kala_gochara_windows__ssv_20260728c',
        'kala_gochara_windows_archive_20260805',
        'kala_gochara_windows_v2'
    ];
    t text;
    rel regclass;
    col record;
    seq record;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_orchestrator') THEN
        RAISE NOTICE '1303: role role_orchestrator does not exist; no-op';
        RETURN;
    END IF;

    FOREACH t IN ARRAY tables LOOP
        rel := to_regclass(format('public.%I', t));
        IF rel IS NULL THEN
            RAISE NOTICE '1303: public.% does not exist; skipping it', t;
            CONTINUE;
        END IF;

        -- Table-level write privileges (no-op where not held).
        EXECUTE format('REVOKE UPDATE, DELETE, INSERT ON TABLE public.%I FROM role_orchestrator', t);

        -- Column-level UPDATE/INSERT grants, if any exist (a table-level REVOKE does not remove
        -- them). Read from the catalog ACL (pg_attribute.attacl), which lists every column grant
        -- regardless of who made it.
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
            EXECUTE format('REVOKE UPDATE (%I), INSERT (%I) ON TABLE public.%I FROM role_orchestrator',
                           col.column_name, col.column_name, t);
        END LOOP;

        -- Per-table post-check: no effective INSERT/UPDATE/DELETE path may remain.
        IF has_table_privilege('role_orchestrator', format('public.%I', t), 'INSERT')
           OR has_table_privilege('role_orchestrator', format('public.%I', t), 'UPDATE')
           OR has_table_privilege('role_orchestrator', format('public.%I', t), 'DELETE')
           OR has_any_column_privilege('role_orchestrator', format('public.%I', t), 'INSERT')
           OR has_any_column_privilege('role_orchestrator', format('public.%I', t), 'UPDATE') THEN
            RAISE EXCEPTION '1303: role_orchestrator still holds a write privilege on public.%', t;
        END IF;

        -- The id sequences this table OWNS (serial/identity columns, pg_depend auto dependency):
        -- revoke USAGE/UPDATE where held, skip when the table owns none.
        FOR seq IN
            SELECT s.relname AS seqname
              FROM pg_class s
              JOIN pg_depend d ON d.objid = s.oid AND d.deptype = 'a'
             WHERE s.relkind = 'S'
               AND d.refobjid = rel
        LOOP
            IF has_sequence_privilege('role_orchestrator', format('public.%I', seq.seqname), 'USAGE')
               OR has_sequence_privilege('role_orchestrator', format('public.%I', seq.seqname), 'UPDATE') THEN
                EXECUTE format('REVOKE USAGE, UPDATE ON SEQUENCE public.%I FROM role_orchestrator',
                               seq.seqname);
            END IF;
            IF has_sequence_privilege('role_orchestrator', format('public.%I', seq.seqname), 'USAGE')
               OR has_sequence_privilege('role_orchestrator', format('public.%I', seq.seqname), 'UPDATE') THEN
                RAISE EXCEPTION '1303: role_orchestrator still holds USAGE/UPDATE on sequence public.%',
                                seq.seqname;
            END IF;
        END LOOP;
    END LOOP;
END $$;
