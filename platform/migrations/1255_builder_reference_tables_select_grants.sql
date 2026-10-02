-- 1255_builder_reference_tables_select_grants.sql
--
-- Suvarna (SS ruling, 2026-10-02): GRANT SELECT to the build-pipeline identity `data_plane_builder` on the SEVEN
-- reference tables that the L1 (Ganita) writers read at build time and that the role cannot read today.
-- A SECOND, SEPARATE SECTION (below the first) grants SELECT on public.brahma_yoga_catalog to the data-plane
-- capture owner `data_plane_l1_owner`. Grants only: no object is created, altered or dropped, no data is touched.
--
-- WHY. `data_plane_builder` (migration 1070; the dedicated identity of the build pipeline job) runs the L1
-- `ga_*` writers. Several of them read L0 reference tables as that role. A data-plane rehearsal and a static
-- grants audit found that the role holds NO privilege on the tables below, so the reads fail with
-- InsufficientPrivilege. Depending on the writer the failure is swallowed (a `try/except` that logs a warning
-- and falls back) or fatal. A swallowed failure is NOT harmless: inside the surrounding build transaction, a
-- failed statement puts the transaction in the aborted state, and the very next statement then fails with
-- InFailedSqlTransaction, so the "tolerated" read still aborts the sub-step. 1225 and 1224 closed the same
-- class for bg_transit_av_gates and chart_grants.
--
-- THE SEVEN TABLES AND THEIR READERS (file:line at authoring, origin/main 9ca920d84)
--   public.reference_nakshatra           pipeline/orchestrator/writers/ga_nakshatra.py:225-232 (_fetch_bg_nakshatra);
--                                        ga_writers/ga_sensitive_degree_writer.py:415 (yogi-lord lookup)
--   public.reference_nakshatra_pada      pipeline/orchestrator/writers/ga_nakshatra.py:236-241 (_fetch_bg_nakshatra)
--   public.bg_shashtiamsha_deities       ga_writers/ga_vargas_writer.py:588
--   public.bg_graha_naisargika_friendship ga_writers/ga_condition_writer.py:690 (read inside try/except: a
--                                        swallowed denial aborts the transaction)
--   public.bg_motion_state_thresholds    ga_writers/ga_condition_writer.py:641 (same try/except abort hazard)
--   public.brahma_vichara_constants      ga_writers/ga_vichara_writer.py:150 (denial is fatal to the writer)
--   public.yoga_family_members           ga_writers/ga_yoga_writer.py:280-292 (_load_yoga_families; called at
--                                        :2835 on every substep; read inside try/except: a swallowed denial
--                                        aborts the transaction). Pure catalog table (yoga_canonical_id,
--                                        family_id; 0 rows at authoring).
-- PROVEN vs INFERRED. ALL SEVEN are PROVEN necessary by a failing read. reference_nakshatra,
-- reference_nakshatra_pada and bg_shashtiamsha_deities: failing reads in the data-plane rehearsal.
-- bg_graha_naisargika_friendship and bg_motion_state_thresholds (ga_condition): proven by the rehearsal's second
-- ledger (the denial is swallowed, then the next statement fails with InFailedSqlTransaction).
-- brahma_vichara_constants (ga_vichara): proven, the denial is not swallowed. yoga_family_members (ga_yoga):
-- proven by the independent reviewer's reproduction with the real writer functions as a builder-shaped role on a
-- disposable PostgreSQL 15 (the swallowed denial aborts the transaction, the next statement fails with
-- InFailedSqlTransaction and ga_yoga ends in `error`) and by the rehearsal on the canonical-shaped path.
--
-- SECTION 2: `data_plane_l1_owner` -> public.brahma_yoga_catalog (SELECT only)
-- The SECURITY DEFINER trigger function l1_data_plane_capture_row() (owner data_plane_l1_owner, search_path
-- pinned) runs, for ga_yoga_firings rows, `SELECT formation_rule_jsonb FROM public.brahma_yoga_catalog WHERE
-- canonical_id = ...`. Production audit (read as suvarna_reader, 2026-10-02): data_plane_l1_owner holds NO
-- privilege on brahma_yoga_catalog (has_table_privilege false for SELECT and for every other privilege), so
-- EVERY ga_yoga_firings insert fails with `permission denied for table brahma_yoga_catalog` and ga_yoga cannot
-- build. PROVEN by the data-plane rehearsal. Live facts behind the strict post-check of this section:
-- data_plane_l1_owner is NOLOGIN, NOINHERIT, not a superuser, bypassrls = false, a member of one role
-- (data_plane_migrator) which gives it nothing on this table; brahma_yoga_catalog is owned by amjis_app, has no
-- RLS and no policy (233 rows), and its ACL does not mention data_plane_l1_owner. So the strict post-check
-- (SELECT held, nothing else by any path) applies cleanly and is kept as strict as section 1's.
-- ORDER: this grant must be live BEFORE the D6 plan's functions are exercised and before ga_yoga builds.
-- SERVING EFFECT AT APPLY: none (the table is read only by the capture trigger and the build).
--
-- NOT HERE (and must stay out of this migration): public.bg_prashna_significators and public.prashna_charts
-- (ga_prashna is OUT of the S-L1 set by SS ruling; chart-scoped horary data is not granted to the builder in this
-- window), the materialized views (REFRESH is owner-only; separate lane), and public.chart_fact_identity (never by
-- this migration).
--
-- AUDIT FACTS (read as the reader role, 2026-10-02; re-verified at authoring): data_plane_builder is not a
-- superuser, rolinherit = false, a member of no role, bypassrls = false; none of the seven tables has RLS enabled
-- or a policy; each is owned by amjis_app, whose ACL does not mention the builder; there is no PUBLIC grant.
-- None of the seven is in the ownership-preflight protected sets (platform/scripts/data-plane-ownership-
-- preflight.ts: L1_ACTIVE_TABLES / L2_ACTIVE_TABLES; the similarly named `reference_nakshatras` there is a
-- different table), so no ACL-allowlist or drift gate sees this grant. The three SQL functions the L1 writers
-- call already grant EXECUTE to the builder.
--
-- PRODUCTION BEHAVIOUR: ONE GRANT PER TABLE (seven in all), issued by the table owner; the migration runner
-- authenticates as amjis_app, which owns all seven (same authority as 1225). A table the role already reads is
-- skipped (no-op), so a re-run, or an environment that already holds the grant, is harmless.
--
-- SCOPE: exactly one privilege (SELECT): seven tables to data_plane_builder (section 1) and one table to
-- data_plane_l1_owner (section 2), each to its own single role. No INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/
-- TRIGGER, no column-level privilege, no sequence, no CREATE, no WITH GRANT OPTION, no role membership.
-- Post-condition asserted per table: SELECT held, and no other privilege held by ANY path (has_table_privilege
-- is effective privilege: direct, PUBLIC, inherited; has_any_column_privilege also catches column-level ones).
--
-- DATA-DRIVEN. Each section has its own list that appears exactly once (section 1: the `tables` array; section
-- 2: the `l1_owner_tables` array); the guards, the grants and the post-check of that section all iterate it.
-- Adding or removing a table is a one-line edit there. Both sections run inside the one migration transaction,
-- so a refusal in either leaves NOTHING granted.
--
-- GUARDS (raise rather than skip: a silent skip would let a database that lacks the privilege look migrated):
-- the role must exist, and every listed name must resolve to an ordinary table (relkind r/p) in schema public.
-- Existence is checked for ALL tables before the first GRANT, so a missing table changes nothing.
--
-- LOCK TIMEOUT (pattern: migration 1218). The first statement is `SET LOCAL lock_timeout = '5s'`: GRANT takes a
-- brief lock on the table's ACL, and a blocked migrate job must fail fast, not hang a shared deploy.
--
-- ORDERING. No effect depends on a writer image; never shares a PR with a writer change. It may merge at any
-- time and must be APPLIED before the S-L1 build window opens (the builds that read these tables as
-- data_plane_builder). It is an ordinary routine migration (not in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS).
--
-- SERVING EFFECT AT APPLY: none (no registry/freshness/trigger touched).
--
-- ROLLBACK NOTE: never REVOKE. Production state may hold any of these grants independently of this file (an
-- owner-path apply, or a later migration), so a REVOKE here could remove a privilege this file did not create
-- and break a build. To undo for real, author a new reviewed migration against the then-current state.
--
-- VERIFICATION AFTER APPLY is by production structure, not the deploy log (Trap 103):
--   SELECT c.relname, has_table_privilege('data_plane_builder', c.oid, 'SELECT')
--     FROM pg_class c WHERE c.oid = ANY (ARRAY[
--       'public.reference_nakshatra'::regclass, 'public.reference_nakshatra_pada'::regclass,
--       'public.bg_shashtiamsha_deities'::regclass, 'public.bg_graha_naisargika_friendship'::regclass,
--       'public.bg_motion_state_thresholds'::regclass, 'public.brahma_vichara_constants'::regclass,
--       'public.yoga_family_members'::regclass]);  -- all true
--   SELECT has_table_privilege('data_plane_l1_owner', 'public.brahma_yoga_catalog', 'SELECT');  -- true
--   plus a relacl diff over all public relations: the only change is data_plane_builder=r/amjis_app on these seven plus
--   data_plane_l1_owner=r/amjis_app on brahma_yoga_catalog.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    -- THE ONE PLACE THE TABLE LIST LIVES. Unqualified names in schema public.
    tables text[] := ARRAY[
        'reference_nakshatra',
        'reference_nakshatra_pada',
        'bg_shashtiamsha_deities',
        'bg_graha_naisargika_friendship',
        'bg_motion_state_thresholds',
        'brahma_vichara_constants',
        'yoga_family_members'
    ];
    tbl     text;
    rel     regclass;
    kind    "char";
    extra   text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        RAISE EXCEPTION '1255: role data_plane_builder does not exist';
    END IF;

    -- Guard pass: every table must exist as an ordinary table in public BEFORE anything is granted.
    FOREACH tbl IN ARRAY tables LOOP
        rel := to_regclass(format('public.%I', tbl));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1255: public.% does not exist', tbl;
        END IF;
        SELECT relkind INTO kind FROM pg_class WHERE oid = rel;
        IF kind NOT IN ('r', 'p') THEN
            RAISE EXCEPTION '1255: public.% is not an ordinary table (relkind %)', tbl, kind;
        END IF;
    END LOOP;

    -- Grant pass: SELECT only, skipped where already held.
    FOREACH tbl IN ARRAY tables LOOP
        rel := format('public.%I', tbl)::regclass;
        IF has_table_privilege('data_plane_builder', rel, 'SELECT') THEN
            RAISE NOTICE '1255: data_plane_builder already holds SELECT on public.%; no-op', tbl;
        ELSE
            EXECUTE format('GRANT SELECT ON TABLE %s TO data_plane_builder', rel);
        END IF;
    END LOOP;

    -- Post-check: SELECT took effect (never trust a silent no-op) and nothing broader is held, by any path.
    FOREACH tbl IN ARRAY tables LOOP
        rel := format('public.%I', tbl)::regclass;
        IF NOT has_table_privilege('data_plane_builder', rel, 'SELECT') THEN
            RAISE EXCEPTION '1255: data_plane_builder lacks SELECT on public.% after the grant', tbl;
        END IF;
        SELECT string_agg(p, ', ' ORDER BY p) INTO extra
          FROM unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) p
         WHERE has_table_privilege('data_plane_builder', rel, p)
            OR (p IN ('INSERT','UPDATE','REFERENCES')
                AND has_any_column_privilege('data_plane_builder', rel, p));
        IF extra IS NOT NULL THEN
            RAISE EXCEPTION '1255: data_plane_builder holds more than SELECT on public.%: %', tbl, extra;
        END IF;
    END LOOP;
END $$;

-- SECTION 2: data_plane_l1_owner -> public.brahma_yoga_catalog (see the header). Same guards, same strict post-check.
DO $$
DECLARE
    -- THE ONE PLACE THE SECTION-2 LIST LIVES. Unqualified names in schema public; grantee is data_plane_l1_owner.
    l1_owner_tables text[] := ARRAY[
        'brahma_yoga_catalog'
    ];
    tbl     text;
    rel     regclass;
    kind    "char";
    extra   text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_l1_owner') THEN
        RAISE EXCEPTION '1255: role data_plane_l1_owner does not exist';
    END IF;

    FOREACH tbl IN ARRAY l1_owner_tables LOOP
        rel := to_regclass(format('public.%I', tbl));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1255: public.% does not exist', tbl;
        END IF;
        SELECT relkind INTO kind FROM pg_class WHERE oid = rel;
        IF kind NOT IN ('r', 'p') THEN
            RAISE EXCEPTION '1255: public.% is not an ordinary table (relkind %)', tbl, kind;
        END IF;
    END LOOP;

    FOREACH tbl IN ARRAY l1_owner_tables LOOP
        rel := format('public.%I', tbl)::regclass;
        IF has_table_privilege('data_plane_l1_owner', rel, 'SELECT') THEN
            RAISE NOTICE '1255: data_plane_l1_owner already holds SELECT on public.%; no-op', tbl;
        ELSE
            EXECUTE format('GRANT SELECT ON TABLE %s TO data_plane_l1_owner', rel);
        END IF;
    END LOOP;

    FOREACH tbl IN ARRAY l1_owner_tables LOOP
        rel := format('public.%I', tbl)::regclass;
        IF NOT has_table_privilege('data_plane_l1_owner', rel, 'SELECT') THEN
            RAISE EXCEPTION '1255: data_plane_l1_owner lacks SELECT on public.% after the grant', tbl;
        END IF;
        SELECT string_agg(p, ', ' ORDER BY p) INTO extra
          FROM unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) p
         WHERE has_table_privilege('data_plane_l1_owner', rel, p)
            OR (p IN ('INSERT','UPDATE','REFERENCES')
                AND has_any_column_privilege('data_plane_l1_owner', rel, p));
        IF extra IS NOT NULL THEN
            RAISE EXCEPTION '1255: data_plane_l1_owner holds more than SELECT on public.%: %', tbl, extra;
        END IF;
    END LOOP;
END $$;
