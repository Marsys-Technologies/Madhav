-- 1262_chart_fact_identity_asset_registration.sql
--
-- Suvarna (SS ruling; S-L2 blocker B5): REGISTER the Fact Identity Index (public.chart_fact_identity, migration 552) as a
-- first-class L1 asset, and let the build identity read it. Two effects, one transaction:
--   (1) ONE asset_registry row, asset_id `ga_fact_identity`: chart-scoped count_sql, a narrow real-detector integrity_check_sql.
--   (2) GRANT SELECT ON public.chart_fact_identity TO data_plane_builder (SELECT only).
--
-- WHY. `chart_fact_identity` has NO producing asset and NO registry row (TI_L2_06 trace; L1_STATE WP-6 note). It is filled by the
-- standalone, hand-run script platform/python-sidecar/scripts/build_fact_identity_index.py (G-IDX; "NOT a WriterBase/@register
-- orchestrator writer"), and it is READ by the L2 Bodha path: ChartReaderV4.lord_of -> bo_pratijna (chart_reader_v4.py identity-joined
-- dignity attach) and the Bodha identity functions. `data_plane_builder` (migration 1070; the build pipeline's identity) holds NO
-- privilege on it (W1_PRIVILEGE_AUDIT: owner amjis_app; ACL amjis_app arwdDxt, role_orchestrator arwd, role_web_serve/role_jobs/
-- role_sidecar/retrieval_census_ro/suvarna_reader r), so every bo_pratijna read of the index as the builder fails with
-- InsufficientPrivilege (S-L2 blocker B5). Migration 1255 deliberately left this table OUT ("never by this migration"); this is the
-- separate, reviewed migration it pointed at. The cockpit also cannot show the table: with no registry row there is no count_sql for
-- the stats route to read (CLAUDE.md N.4 "Cockpit truth": the stats route reads count_sql, NOT asset_throughput).
--
-- ASSET ID: `ga_fact_identity` (CLAUDE.md N.1: underscore prefix per layer; never a dotted id).
--   * `ga_*` because the index is an L1-owned, deterministic structural parse of chart_facts text (fact_subject / fact_key) with no
--     interpretation: facts layer, B.1. L1_STATE and the S-L1 W6 close report call it "L1-owned by table-name convention"; the parser
--     lives in brahmagyan/ and the build step is an S-L1 W7 runbook step (G-IDX, run AFTER every ga_* build). L2 merely READS it.
--   * not `bo_*`: nothing about it is interpretive, and a bo_ id would put an L1 derived cache behind the L2 DAG/ledger rules.
--   * no collision: no ga_fact_identity id exists in the registry (129 rows read 2026-10-03), in any @register()'d writer, or in any
--     branch (git log --all -S).
-- ROW SHAPE (follows the existing ga_* rows for the layer/naming columns and the `lel_events` row for a no-writer, per-chart,
-- chart_id-bound asset): layer 'ganita', layer_name 'Gaṇita', layer_index 'L1', domain 'chart', rung 'R1', scope 'per_chart',
-- asset_type/asset_kind 'data', storage_type 'postgres_table', catalog_status 'CURRENT', sort_order 52 (after ga_ayurdaya 51).
--   * has_writer = false, has_substeps = false: there is NO @register()'d writer (the script is hand-run). That is the honest value:
--     the plan resolver (WHERE has_writer = true), runPreparation, recalibrationEnqueue and the cockpit plan route all exclude the
--     row, so no build can be scheduled for it and the orchestrator writer-gap pre-flight (runner._check_writer_registry_gaps,
--     registry-writer direction only) is unaffected. A later PR that adds a real writer flips has_writer by its own migration.
--   * is_active = true: the stats route lists WHERE is_active = true; that is the whole point of giving it a count_sql.
--   * target_floor = 0: floors are aspirational, not gates (N.4); no number is known until the S-L1 rebuild lands.
--   * depends_on is NOT named: the column default ('{}') applies. A hand-run asset cannot be scheduled, so a DAG edge would be a
--     fiction, and edges would move the registry DAG pins (registry_depends_on_migrations.json, the level map). Its real upstream is
--     "every chart_facts producer, run last" (script header); the DAG ruling, if any, is a separate SS decision.
--   * natural_key_partition NULL, clear_tables NULL: see CLEAR/INVALIDATION below.
--
-- COUNT_SQL (chart-scoped, `$1` like the registry's other per-chart rows):
--     SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1
--   It counts IDENTITY-BEARING facts of the chart, NOT all chart_facts rows (identity-free facts and unparsed gaps have no row).
--
-- INTEGRITY CLAIM (integrity_check_sql; a bare `SELECT ... AS integrity_passed`, run with NO parameter, across all charts, by
-- asset_runner._probe_asset / the L1 dry-run / the census). It is deliberately NARROW. It claims, and ONLY claims:
--     (a) the index is not empty (a vacuous NOT EXISTS must not read as green: an unbuilt index is "nothing to attest", reported
--         false); and
--     (b) every identity row is consistent with the chart_facts row it was derived from, as that row stands NOW:
--         - the fact exists                                         (FK ON DELETE CASCADE already implies it; a LEFT JOIN keeps the
--                                                                    clause honest if the FK is ever dropped or NOT VALID),
--         - the same chart_id                                       (the FK does NOT check this: a cross-chart row is contamination),
--         - the same build_id                                       (a row built against another chart_facts generation is stale),
--         - provenance text carries the fact's CURRENT subject+key  (`parsed_from` is "fact_subject=..;fact_key=.."; a subject/key
--                                                                    that changed since the parse leaves the row stale; containment,
--                                                                    not equality, because the Python repr() quoting of exotic strings
--                                                                    differs from any SQL quoting).
--   Measured on production 2026-10-03 (reader, SELECT only): 251,468 rows, 0 orphan, 0 chart mismatch, 0 build mismatch, 0 provenance
--   mismatch; the statement ran in ~4 s.
-- WHAT THE SQL CANNOT CHECK (stated, not papered over): the corrected G-IDX check (brahmagyan/fact_identity_check.check_identity_index,
--   SS-ruled) is PYTHON-SIDE: rows == parsed identity-bearing facts; parsed + identity_free + gap == total chart_facts; gap == 0;
--   coverage >= 99.98%; identity_free reason set == the 14 measured + scope_cap_sentinel. All of those need the parse-vs-identity_free
--   classification, which is decided per (fact_category, fact_subject) by Python regex rules AFTER a failed parse; no fact_category is
--   identity-free as such (the same category can hold parsed and identity-free subjects), so "no identity row is of an identity_free
--   category" has no honest SQL form and is NOT asserted. Completeness (a chart whose index covers 1,205 of 143,299 facts, as
--   TI_L2_06 found) is therefore NOT detected by this SQL either: it passes whenever the rows that exist are consistent. Completeness
--   is attested only by `build_fact_identity_index.py --check` at build time, whose verdict this column does not replace.
--
-- GRANT. data_plane_builder: SELECT on public.chart_fact_identity, nothing else (no INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/
-- TRIGGER, no column grant, no GRANT OPTION, no role membership). The builder does NOT write the index (the script runs as amjis_app
-- or role_orchestrator); it only reads it.
--   OWNER FINDING (catalog, read as suvarna_reader on production 2026-10-03; PostgreSQL 15.18): pg_class.relowner of
--   public.chart_fact_identity = amjis_app, relacl {amjis_app=arwdDxt/amjis_app, retrieval_census_ro=r, role_web_serve=r,
--   role_orchestrator=arwd, role_jobs=r, role_sidecar=r, suvarna_reader=r}; asset_registry is also owned by amjis_app. The
--   migration runner authenticates as amjis_app, so the GRANT is issued BY THE OWNER and this is a ROUTINE migration (not an
--   owner-path / protected-window package; contrast 1272/1273, whose objects other roles own). chart_facts is owned by
--   data_plane_l1_owner (the builder already reads it); this migration does not touch it. A guard refuses to run unless the
--   executing role is the owner (or a member that can act as it), because a GRANT by a non-owner without grant option is only a
--   WARNING in PostgreSQL ("no privileges were granted") and would otherwise leave the migration green with nothing granted.
--
-- GUARDS (raise, never skip): the role, asset_registry, chart_facts, build_runs and chart_fact_identity (ordinary table, public)
-- must exist; NO build_runs row may be active (state planned / running / paused: the predicate of the active-run index, migration
-- 359). The registry row is inserted ON CONFLICT (asset_id) DO NOTHING and a PRE-EXISTING row must equal the intended shape (target,
-- scope, no writer, count_sql, integrity_check_sql, active) or the migration fails and rolls back whole.
-- POST-CHECKS (the P2 rule: a WARN-only GRANT counts as failure): has_table_privilege(builder, SELECT) must be true, none of
-- INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER may be held (table- or column-level), and the registry row must read back.
--
-- SERVING EFFECT AT APPLY.
--   * REGISTRY TRIGGER: nirmana_registry_receipt_invalidation is AFTER UPDATE OF (depends_on, natural_key_partition, health_probe,
--     integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table). This migration issues
--     only an INSERT ... ON CONFLICT DO NOTHING and never an UPDATE, so the trigger CANNOT fire: no asset_freshness row is marked
--     stale and no existing asset's registry fingerprint moves (fingerprints are per asset_id). The other registry-reading
--     DB functions (l1_data_plane_capture_row, complete_l1_data_plane_partition, ...) look up rows by their own asset_id and never see
--     the new one.
--   * COCKPIT: the stats route lists active registry rows, so the cockpit shows one NEW tile (ga_fact_identity) whose row count is
--     the chart's identity rows. With no asset_throughput row the badge reads the count_sql fallback (lit-equivalent with the
--     build-state-stale flag) when rows exist. It has no dependents (downstream count 0). The plan/build/recalibration paths exclude it
--     (has_writer = false): no build is created or changed by this migration.
--   * BUILDER: data_plane_builder can now SELECT the index (the B5 unblock). Nothing else changes for any role.
--   * CHART DATA: none read, none written. No other registry row is touched (supplementary xmin check below).
-- CLEAR / INVALIDATION (stated, not changed here): a birth-data correction preserves has_writer = false assets
-- (assetInvalidation.ts), but chart_facts is rebuilt delete-then-insert and chart_fact_identity.fact_id is ON DELETE CASCADE, so the
-- index is emptied for the replaced facts and nothing re-creates it until G-IDX is re-run. A manual cockpit Clear at layer/global
-- scope derives `DELETE FROM chart_fact_identity WHERE chart_id = $1` from this count_sql (no has_writer filter in the clear route);
-- the index is a rebuildable cache, so that is not data loss, but it is not restored by any build. An EXPLICIT_CLEAR_OPS entry is a
-- TypeScript decision outside this migration (reported to SS).
-- ORDER: a precondition of S-L2, applied POST-window. Never shares a PR with a writer change. Routine migration (not in
-- PROTECTED_PUBLIC_SCHEMA_MIGRATIONS); the PR is HELD and not armed.
--
-- LOCK TIMEOUT (pattern: 1218, 1255): the first statement is `SET LOCAL lock_timeout = '5s'` so a blocked migrate job fails fast.
-- ROLLBACK NOTE: never REVOKE or DELETE. Production may hold the grant or the row independently of this file; to undo for real,
-- author a new reviewed migration against the then-current state.
-- VERIFICATION AFTER APPLY is by production structure, not the deploy log (Trap 103):
--   SELECT has_table_privilege('data_plane_builder', 'public.chart_fact_identity', 'SELECT');           -- true
--   SELECT asset_id, is_active, has_writer, scope, count_sql FROM asset_registry WHERE asset_id = 'ga_fact_identity';  -- 1 row
--   plus a relacl diff: the only change is data_plane_builder=r/amjis_app on chart_fact_identity.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $mig$
DECLARE
    -- THE ONE PLACE EACH SQL TEXT LIVES: the INSERT, the pre-existing-row comparison and the read-back all use these variables.
    v_asset_id      constant text := 'ga_fact_identity';
    v_count_sql     constant text := 'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1';
    v_integrity_sql constant text :=
        'SELECT EXISTS (SELECT 1 FROM public.chart_fact_identity) '
        'AND NOT EXISTS ('
        'SELECT 1 FROM public.chart_fact_identity i '
        'LEFT JOIN public.chart_facts f ON f.fact_id = i.fact_id '
        'WHERE f.fact_id IS NULL '
        'OR f.chart_id <> i.chart_id '
        'OR i.build_id IS DISTINCT FROM f.build_id '
        'OR strpos(i.parsed_from, f.fact_subject) = 0 '
        'OR strpos(i.parsed_from, f.fact_key) = 0'
        ') AS integrity_passed';
    tbl             text;
    rel             regclass;
    kind            "char";
    owner_oid       oid;
    n_active        integer;
    n_rows          integer;
    n_other         integer;
    extra           text;
BEGIN
    -- ---------------------------------------------------------------- guards
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        RAISE EXCEPTION '1262: role data_plane_builder does not exist';
    END IF;
    FOREACH tbl IN ARRAY ARRAY['asset_registry', 'chart_facts', 'build_runs', 'chart_fact_identity'] LOOP
        rel := to_regclass(format('public.%I', tbl));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1262: public.% does not exist', tbl;
        END IF;
        SELECT relkind INTO kind FROM pg_class WHERE oid = rel;
        IF kind NOT IN ('r', 'p') THEN
            RAISE EXCEPTION '1262: public.% is not an ordinary table (relkind %)', tbl, kind;
        END IF;
    END LOOP;

    SELECT count(*) INTO n_active FROM public.build_runs WHERE state IN ('planned', 'running', 'paused');
    IF n_active <> 0 THEN
        RAISE EXCEPTION '1262: % build run(s) are active (planned/running/paused); apply only with no active build', n_active;
    END IF;

    rel := 'public.chart_fact_identity'::regclass;
    SELECT relowner INTO owner_oid FROM pg_class WHERE oid = rel;
    IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN
        RAISE EXCEPTION '1262: current_user % cannot act as the owner (%) of public.chart_fact_identity; a grant by a non-owner is only a WARNING, so this migration refuses. Route the grant through the owner-path package.',
            current_user, pg_get_userbyid(owner_oid);
    END IF;

    -- ------------------------------------------------------- registry row (INSERT only: the receipt-invalidation trigger is AFTER UPDATE)
    INSERT INTO public.asset_registry (
        asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
        storage_type, target_table, count_sql, size_sql, target_floor,
        volume_explanation, scope, is_active,
        asset_type, layer_name, layer_index, catalog_status, integrity_check_sql,
        has_substeps, asset_kind, has_writer, domain, rung
    ) VALUES (
        v_asset_id,
        'ganita',
        52,
        'Tathya-paricaya-sūcī',
        'Fact Identity Index',
        'Derived index of chart_facts identity (graha / house / varga / sign / pair) parsed from fact_subject and fact_key by the single deterministic parser brahmagyan/fact_identity_parser.py (migration 552). NOT a built asset: it has no @register()''d writer (has_writer = false); it is filled per chart by the hand-run script scripts/build_fact_identity_index.py (G-IDX), as role amjis_app or role_orchestrator, AFTER every ga_* build, because chart_fact_identity.fact_id is ON DELETE CASCADE from chart_facts. Read by the L2 Bodha identity path (ChartReaderV4 -> bo_pratijna). Rebuildable from chart_facts alone.',
        'postgres_table',
        'chart_fact_identity',
        v_count_sql,
        'SELECT pg_total_relation_size(''chart_fact_identity'')',
        0,
        'Counts IDENTITY-BEARING facts of the chart only: identity-free facts (catalog labels, fixed reference rows, scope-cap sentinels) and unparsed gaps have no row, so this is never the chart_facts row count. The completeness verdict (rows == parsed, gap == 0, reason set) is produced by build_fact_identity_index.py --check, not by this registry row.',
        'per_chart',
        true,
        'data',
        'Gaṇita',
        'L1',
        'CURRENT',
        v_integrity_sql,
        false,
        'data',
        false,
        'chart',
        'R1'
    )
    ON CONFLICT (asset_id) DO NOTHING;

    -- Read-back: exactly one row, and it IS the intended shape (a pre-existing divergent row is not silently accepted).
    SELECT count(*) INTO n_rows
      FROM public.asset_registry
     WHERE asset_id = v_asset_id
       AND layer = 'ganita'
       AND target_table = 'chart_fact_identity'
       AND scope = 'per_chart'
       AND has_writer IS FALSE
       AND has_substeps IS FALSE
       AND is_active IS TRUE
       AND catalog_status = 'CURRENT'
       AND count_sql = v_count_sql
       AND integrity_check_sql = v_integrity_sql;
    IF n_rows <> 1 THEN
        RAISE EXCEPTION '1262: asset_registry row % is missing or differs from the intended shape (matching rows: %)', v_asset_id, n_rows;
    END IF;

    -- Supplementary (visible tuple versions only; NOT proof nothing else was touched): no other asset_registry row version was
    -- written by this transaction.
    SELECT count(*) INTO n_other
      FROM public.asset_registry
     WHERE xmin = pg_current_xact_id()::xid
       AND asset_id <> v_asset_id;
    IF n_other <> 0 THEN
        RAISE EXCEPTION '1262: % other asset_registry row(s) were modified by this migration', n_other;
    END IF;

    -- ------------------------------------------------------------------- grant (SELECT only; skipped where already held)
    IF has_table_privilege('data_plane_builder', rel, 'SELECT') THEN
        RAISE NOTICE '1262: data_plane_builder already holds SELECT on public.chart_fact_identity; no-op';
    ELSE
        EXECUTE format('GRANT SELECT ON TABLE %s TO data_plane_builder', rel);
    END IF;

    -- Post-check: SELECT took effect (never trust a WARN-only no-op) and nothing broader is held (effective privileges; column-level
    -- INSERT/UPDATE/REFERENCES too; NOT a privilege reachable only through a NOINHERIT membership, and not PG17 MAINTAIN: production is 15.18).
    IF NOT has_table_privilege('data_plane_builder', rel, 'SELECT') THEN
        RAISE EXCEPTION '1262: data_plane_builder lacks SELECT on public.chart_fact_identity after the grant';
    END IF;
    SELECT string_agg(p, ', ' ORDER BY p) INTO extra
      FROM unnest(ARRAY['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']) p
     WHERE has_table_privilege('data_plane_builder', rel, p)
        OR (p IN ('INSERT', 'UPDATE', 'REFERENCES')
            AND has_any_column_privilege('data_plane_builder', rel, p));
    IF extra IS NOT NULL THEN
        RAISE EXCEPTION '1262: data_plane_builder holds more than SELECT on public.chart_fact_identity: %', extra;
    END IF;
END
$mig$;
