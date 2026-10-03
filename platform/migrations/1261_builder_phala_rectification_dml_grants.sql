-- 1261_builder_phala_rectification_dml_grants.sql
--
-- Suvarna (SS ruling N-99, Q-L4-04, A.L4 CF-L4-02 c / TI-L4-44): GRANT SELECT, INSERT, DELETE on public.phala_rectification
-- and public.phala_rectification_best to the build-pipeline identity `data_plane_builder`, and NOTHING else. Grants only:
-- no object is created, altered or dropped, no data is touched, no registry row, function, sequence or role membership.
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1261-001). Number 1261 allocated by SS. Merge only AFTER S-L1 and only on
-- SS's review (see ORDERING below: SS may want it after S-L3). MERGE = APPLY at the next deploy (migrate.ts runs on
-- every deploy, before that deploy's images roll). Precondition of S-L4 (a ph_rectification build).
--
-- WHY. `data_plane_builder` (migration 1070; the dedicated identity of the build pipeline job) holds NO privilege on the
-- two tables, so the ph_rectification writer fails on its first statement (DELETE FROM phala_rectification_best ...)
-- with InsufficientPrivilege. Read as suvarna_reader on 2026-10-03: has_table_privilege('data_plane_builder', t, p) is
-- false for t in (phala_rectification, phala_rectification_best) and p in (SELECT, INSERT, DELETE): six false. The other
-- eight phala_* tables are granted to the builder (DELETE, INSERT, SELECT each; plus UPDATE on phala_phaladesa and
-- phala_suddha_sodhana, whose writers UPDATE). Exact current ACLs of the two tables (pg_class.relacl via aclexplode;
-- identical on both): amjis_app = arwdDxt (owner); retrieval_census_ro r; role_web_serve r; role_orchestrator arwd;
-- role_jobs r; role_sidecar r; nirmana_evidence_ingress_writer r; suvarna_reader r. data_plane_builder: none,
-- directly, via PUBLIC, or by membership (it is a member of no role).
--
-- WHAT THE WRITER ACTUALLY NEEDS (read from the code, not assumed), platform/python-sidecar/pipeline/orchestrator/
-- writers/ph_rectification/__init__.py (statements on these two tables, in order):
--   :288  DELETE FROM phala_rectification_best WHERE chart_id = %s        DELETE, and SELECT (WHERE reads chart_id)
--   :291  DELETE FROM phala_rectification      WHERE chart_id = %s        DELETE, and SELECT
--   :336  INSERT INTO phala_rectification (...) ... RETURNING id          INSERT, and SELECT (RETURNING reads id)
--   :368  INSERT INTO phala_rectification_best (...)                      INSERT
--   No UPDATE, no TRUNCATE, no ON CONFLICT DO UPDATE anywhere in that writer (a test pins that every INSERT/DELETE/UPDATE
--   in it targets only these two tables). So exactly SELECT, INSERT, DELETE on both tables. Not UPDATE (unlike the two
--   phala_ tables whose writers update), not TRUNCATE, not REFERENCES, not TRIGGER.
--   SEQUENCES: none. The primary keys default to gen_random_uuid() (both tables; `id uuid`), the other defaults are
--   constants (lagna_stable, scored_at now(), auto_action, native_adopted); no serial/identity column, so no sequence
--   grant is needed or made.
--   FOREIGN KEYS on insert: phala_rectification_chart_id_fkey and phala_rectification_best_chart_id_fkey -> charts(id);
--   phala_rectification_best_best_candidate_id_fkey -> phala_rectification(id). Referential checks run with the privileges of
--   the table owner, not the builder, so the builder needs nothing on charts for them (and already reads charts).
--   NO triggers on either table (no user trigger in pg_trigger), no RLS (relrowsecurity = false).
--
-- WHO ISSUES THE GRANT. Both tables are owned by amjis_app (pg_class.relowner, read 2026-10-03), whose relacl entry
-- (arwdDxt) is also the grantor of every other entry (the aclexplode grantor column reads amjis_app for all rows). The
-- migration runner authenticates as amjis_app (same authority as 1070, 1225 and 1255), so a GRANT issued here is
-- recorded as `data_plane_builder=ard/amjis_app`: the exact shape of the builder's entries on the other eight phala_*
-- tables. The migration REFUSES to run as a role that is neither the owner nor a member of the owning role (a GRANT by
-- anyone else is, in PostgreSQL, a WARNING and a silent no-op, never an error): guard below, and the post-check proves
-- the privilege actually took.
--
-- SIDE EFFECTS TO DECIDE (read before merging). `data_plane_builder` is ONE role shared by every asset the pipeline job
-- builds, so a grant to it is a grant to every writer that runs as it, not only ph_rectification:
--   (1) ka_kshetra (L3) reads phala_rectification live (services/ka_kshetra/uncertainty.py:185-191 fetch_sigma_t_days,
--       to derive sigma_T). Today that read is denied for the builder; after this migration it succeeds. Migration 1073
--       DELIBERATELY withheld this exact grant ("Strategy 6.2 forbids admitting an event-derived L4 rectification
--       posterior as a live L3 input") and carries an assertion that raised if the builder held it (an applied file,
--       never re-run, and not edited here). Q-L4-04 asks SS whether ka_kshetra may keep that reader. Today the stored
--       posterior has lel_fit_score 0 on every row, so compute_sigma_t_days falls back to the 120 s default either way
--       (fewer than 2 usable candidates), i.e. no numeric change TODAY; but the L3 -> L4 read becomes possible. ORDERING
--       CHOICE FOR SS: apply this migration AFTER the S-L3 ka_kshetra build and BEFORE the S-L4 ph_rectification build,
--       or settle Q-L4-04 first.
--   (2) Same role, same table, DELETE/INSERT: only ph_rectification writes these tables; no other writer names them.
--
-- NOT SUFFICIENT BY ITSELF (found while reading the writer; NOT fixed here, SS ruled exactly these two tables): the
-- ph_rectification writer also SELECTs from public.life_events (_load_chart_training_events, __init__.py:143-147) and
-- data_plane_builder has NO SELECT on life_events (has_table_privilege false, 2026-10-03; ACL: amjis_app arwdDxt,
-- retrieval_census_ro r, role_web_serve r, role_orchestrator arwd, role_jobs r, nirmana_evidence_ingress_writer r,
-- suvarna_reader r; no role_sidecar entry). That read is wrapped in try/except returning [] (structural-only
-- rectification), but the denied statement aborts the surrounding transaction, so the NEXT statement (the chart_facts
-- read, __init__.py:186) fails with InFailedSqlTransaction and ph_rectification ends in error (the failure mode
-- described in 1255). ph_pramana also reads life_events. life_events is chart-scoped private event data, so granting
-- the builder SELECT on it is a decision for SS, not a side effect of this migration. The other reads of
-- ph_rectification (brahma_formula_constants, chart_dashas, chart_facts, charts) are already granted.
--
-- SERVING EFFECT AT APPLY: none. Evidence: a GRANT changes only pg_class.relacl; no asset_registry column is touched, so the
-- live trigger nirmana_registry_receipt_invalidation does not fire and no asset_freshness row changes (no ph_* freshness
-- rows exist anyway); no data is read or written; no serving role (role_web_serve, retrieval_census_ro, ...) gains or loses
-- anything; the builder is not a serving identity. Observable differences: the builder can now run ph_rectification's
-- statements; side effect (1) above.
--
-- GUARDS (raise rather than skip: a silent skip would let a database that lacks the privilege look migrated): the role
-- data_plane_builder must exist; each listed table must resolve to an ordinary table (relkind r/p) in schema public;
-- the migration's user must be able to grant (owner or member of the owner). Existence is checked for ALL tables before the
-- first GRANT, so a missing table changes nothing.
--
-- IDEMPOTENT: a privilege the role already holds is skipped (NOTICE), so a re-run, or an environment that already holds the
-- grant, is harmless and writes no ACL entry.
--
-- POST-CHECK (exactly what it does and does not see): has_table_privilege reports EFFECTIVE privilege (direct, PUBLIC and
-- INHERITED paths), and has_any_column_privilege additionally catches column-level UPDATE/REFERENCES. Per table the builder
-- must hold SELECT, INSERT and DELETE and none of UPDATE, TRUNCATE, REFERENCES, TRIGGER. NOT detected: a privilege reachable
-- only through a NOINHERIT membership (usable by SET ROLE, not held by the role itself), and, on PostgreSQL 17, MAINTAIN
-- (production is 15.18).
--
-- DATA-DRIVEN: the table list and the privilege list each appear exactly once; the guards, grants and post-check iterate them.
--
-- LOCK TIMEOUT (pattern: migration 1218/1255). SET LOCAL lock_timeout = '5s': a GRANT waits on any other uncommitted ACL change
-- to the same table (proved in the live test), and a blocked migrate job must fail fast, not hang a shared deploy.
--
-- NOT DONE HERE: SELECT on life_events (see above); any UPDATE/TRUNCATE; any plan/registry change (adding ph_rectification to
-- the rebuild plan, the ga_dashas edge, the ka_kshetra reader declaration are TI-L4-44's other parts); any REVOKE; the
-- ph_rectification writer's two lel_fit defects (A.L4 finding 5); any rebuild.
--
-- ROLLBACK NOTE: never REVOKE here. Production state may hold any of these grants independently of this file; to undo, author a
-- new reviewed migration against the then-current state.
--
-- VERIFICATION AFTER APPLY is by production structure, not the deploy log (Trap 103):
--   SELECT c.relname, p.priv, has_table_privilege('data_plane_builder', c.oid, p.priv) AS held
--     FROM pg_class c CROSS JOIN (VALUES ('SELECT'),('INSERT'),('DELETE'),('UPDATE'),('TRUNCATE'),('REFERENCES'),('TRIGGER')) p(priv)
--    WHERE c.oid IN ('public.phala_rectification'::regclass, 'public.phala_rectification_best'::regclass) ORDER BY 1, 2;
--     -- SELECT/INSERT/DELETE true; UPDATE/TRUNCATE/REFERENCES/TRIGGER false, on both tables
--   SELECT c.relname, a.grantee::regrole, a.privilege_type, a.grantor::regrole FROM pg_class c, aclexplode(c.relacl) a
--    WHERE c.oid IN ('public.phala_rectification'::regclass, 'public.phala_rectification_best'::regclass)
--      AND a.grantee = 'data_plane_builder'::regrole ORDER BY 1, 3;      -- 3 rows per table, grantor amjis_app
--   plus a relacl diff over all public relations: the only change is data_plane_builder=ard/amjis_app on these two tables.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    -- THE ONE PLACE EACH LIST LIVES. Unqualified table names in schema public.
    tables text[] := ARRAY[
        'phala_rectification',
        'phala_rectification_best'
    ];
    privs text[] := ARRAY['SELECT', 'INSERT', 'DELETE'];
    tbl     text;
    p       text;
    rel     regclass;
    kind    "char";
    owner   oid;
    extra   text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        RAISE EXCEPTION '1261: role data_plane_builder does not exist';
    END IF;

    -- Guard pass: every table must exist as an ordinary table in public, and the migration user must be able to grant on it,
    -- BEFORE anything is granted.
    FOREACH tbl IN ARRAY tables LOOP
        rel := to_regclass(format('public.%I', tbl));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1261: public.% does not exist', tbl;
        END IF;
        SELECT c.relkind, c.relowner INTO kind, owner FROM pg_class c WHERE c.oid = rel;
        IF kind NOT IN ('r', 'p') THEN
            RAISE EXCEPTION '1261: public.% is not an ordinary table (relkind %)', tbl, kind;
        END IF;
        IF NOT pg_has_role(current_user, owner, 'USAGE') THEN
            RAISE EXCEPTION '1261: % is neither the owner of public.% nor a member of its owner; a GRANT would be a silent no-op', current_user, tbl;
        END IF;
    END LOOP;

    -- Grant pass: only the missing privileges.
    FOREACH tbl IN ARRAY tables LOOP
        rel := format('public.%I', tbl)::regclass;
        FOREACH p IN ARRAY privs LOOP
            IF has_table_privilege('data_plane_builder', rel, p) THEN
                RAISE NOTICE '1261: data_plane_builder already holds % on public.%; no-op', p, tbl;
            ELSE
                EXECUTE format('GRANT %s ON TABLE %s TO data_plane_builder', p, rel);
            END IF;
        END LOOP;
    END LOOP;

    -- Post-check: the privileges took (never trust a silent no-op) and nothing broader is held, within the scope stated under
    -- POST-CHECK in the header.
    FOREACH tbl IN ARRAY tables LOOP
        rel := format('public.%I', tbl)::regclass;
        FOREACH p IN ARRAY privs LOOP
            IF NOT has_table_privilege('data_plane_builder', rel, p) THEN
                RAISE EXCEPTION '1261: data_plane_builder lacks % on public.% after the grant', p, tbl;
            END IF;
        END LOOP;
        SELECT string_agg(x, ', ' ORDER BY x) INTO extra
          FROM unnest(ARRAY['UPDATE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']) x
         WHERE has_table_privilege('data_plane_builder', rel, x)
            OR (x IN ('UPDATE', 'REFERENCES') AND has_any_column_privilege('data_plane_builder', rel, x));
        IF extra IS NOT NULL THEN
            RAISE EXCEPTION '1261: data_plane_builder holds more than SELECT, INSERT, DELETE on public.%: %', tbl, extra;
        END IF;
    END LOOP;
END $$;
