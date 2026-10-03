-- Migration 1217: grant data_plane_builder INSERT + UPDATE on asset_freshness and on
-- bg_transit_moorti (grant v1.4).
-- Suvarṇa track T-I (builder grant v1.4). Created: 2026-10-01. Author: suvarna stream.
-- Scope confirmed by the SS/Pravāha coordinator 2026-10-01: exactly these two tables;
-- the Gochara contract-table family (ka_gochara_* / kala_gochara_*) is Pravāha's and is
-- deliberately NOT part of this migration.
--
-- WHY THIS EXISTS
-- ═══════════════
-- Two table-level privilege gaps for the pipeline identity (data_plane_builder, the
-- login brahma-build-pipeline-job runs as), each verified read-only against production
-- as suvarna_reader on 2026-10-01 immediately before authoring:
--
--   (a) public.asset_freshness  — the build's receipt/freshness path.
--       relacl for data_plane_builder: r (SELECT only).  has_table_privilege INSERT = f,
--       UPDATE = f.  The sibling table asset_provenance_receipts, written in the SAME
--       transaction by the SAME function, is already arw (migration 1070), so the
--       receipt INSERT succeeds and the very next statement fails:
--         platform/python-sidecar/pipeline/orchestrator/provenance.py
--           :205-214  _upsert_freshness_row — INSERT INTO asset_freshness
--                     (asset_id, chart_id, partition_key, freshness_state, reasons,
--                      receipt_version, observed_at) VALUES (...)
--                     ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE SET
--                     freshness_state, reasons, receipt_version, observed_at
--         reached from three call sites, i.e. EVERY asset completion and EVERY delta-skip:
--           :244-275  persist_successful_receipt -> _upsert_freshness (:274)
--                     (via capture_and_persist_receipt :278-302; asset_runner.py:451,
--                      :1394)
--           :230-241  reconcile_receipt -> _upsert_freshness (:240)
--           :333-386  reattribute_unchanged_receipt -> _upsert_freshness_row (:382)
--                     (the delta-skip path; asset_runner.py:1059)
--       Result today: every asset that completes (or is delta-skipped) aborts its own
--       receipt transaction with 'permission denied for table asset_freshness'.
--       Migration 1070 deliberately granted SELECT only on this table ("read only" — its
--       own verb map, lines 33-35); that was true of the reads then known, but the
--       upsert above was not in its derivation.
--
--   (b) public.bg_transit_moorti — written by the bg_transit_rules / bg_transit_engine
--       L0 seed writer.
--       relacl for data_plane_builder: r (SELECT only; added by migration 1073 for the L3
--       readers).  has_table_privilege INSERT = f, UPDATE = f.  The writer
--         platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py
--           (@register bg_transit_rules AND bg_transit_engine; run() -> seed_transit_rules)
--         platform/python-sidecar/brahmagyan/l0_transit.py
--           :1183-1198  INSERT INTO bg_transit_moorti (nakshatra_offset, moorti_name,
--                       quality_tier, phala_brief, classical_citation, rule_notes)
--                       VALUES (...) ON CONFLICT (nakshatra_offset) DO UPDATE SET
--                       moorti_name, quality_tier, phala_brief, classical_citation,
--                       rule_notes
--       runs this upsert as the LAST step of seed_transit_rules, AFTER the bg_transit_engine
--       and bg_transit_rules upserts and the F-145 stale-row DELETE sweep have already
--       succeeded (builder is already arwd on both of those tables, with USAGE on both
--       id sequences — verified).  The moorti upsert is therefore the single statement
--       that fails, taking the whole bg_transit_rules/bg_transit_engine rebuild with it.
--       Migration 1073's header recorded this exact gap ("a REAL, SEPARATE L0
--       reference-corpus seed gap, recorded for the L0 grants owner rather than silently
--       widened") and kept its own scope SELECT-only; this migration is that separate item.
--
-- DERIVATION OF THE EXACT PRIVILEGE (every statement in source that touches these tables)
-- ══════════════════════════════════════════════════════════════════════════════════════
--   asset_freshness  (grep across platform/ source, tests excluded):
--     INSERT ... ON CONFLICT DO UPDATE   provenance.py:205   -> needs INSERT + UPDATE
--     SELECT (dependency/receipt checks) asset_runner.py:89, run_heavy_writer_standalone.py:103,
--                                        src/lib/build/runPreparation.ts:202 etc.
--                                        -> SELECT, already held (1070)
--     DELETE / TRUNCATE / bare UPDATE    none in any non-migration source
--     (The only UPDATEs are the two non-SECURITY-DEFINER trigger functions
--      nirmana_invalidate_registry_receipts() / nirmana_invalidate_chart_receipts()
--      (migration 596, lines 56-107), which UPDATE asset_freshness as the CALLER. They fire only on
--      UPDATE OF registry-contract columns of asset_registry or birth/identity columns of
--      charts. The builder's own asset_registry write is a column-level UPDATE only (1070
--      grants UPDATE on exactly service_health / last_invoked_at / last_selftest_at, no
--      table-level UPDATE), and those columns are NOT in the trigger column lists, and
--      it holds no UPDATE on charts — so they do not fire for the builder today. Were
--      they ever to, UPDATE on asset_freshness is the privilege they would need, which
--      this migration supplies; no further grant would be required.)
--   bg_transit_moorti:
--     INSERT ... ON CONFLICT DO UPDATE   l0_transit.py:1186 (the only DML in non-test
--                                        source)  -> needs INSERT + UPDATE
--     SELECT                             services/ka_moorti_nirnaya/writer.py:98-101
--                                        (_FETCH_MOORTI_TABLE_SQL, `FROM bg_transit_moorti`,
--                                        executed at :256) -> SELECT, already held (1073)
--     DELETE / TRUNCATE                  none (the writer never deletes moorti rows)
--   Also verified live, so no further grant is needed or issued:
--     * neither table has a serial/identity column or owns a sequence (pg_depend: 0 rows)
--       -> no USAGE on any sequence;
--     * neither table has a user trigger, rule, RLS policy, or enabled RLS; the only
--       triggers are internal FK constraint triggers (asset_freshness -> asset_registry,
--       charts; ON DELETE CASCADE), which PostgreSQL executes as the table owner and so
--       need nothing from the caller;
--     * no view, no SECURITY INVOKER function body that touches either table beyond the
--       two trigger functions above;
--     * ON CONFLICT ... DO UPDATE additionally needs SELECT on the conflict-target
--       columns — held (1070 / 1073).
--
-- WHY TABLE-LEVEL INSERT/UPDATE, NOT COLUMN-LEVEL
-- ═══════════════════════════════════════════════
-- The statements name fixed column lists, so column-level grants (INSERT on the seven
-- insertable asset_freshness columns, UPDATE on the four DO UPDATE SET columns) would
-- technically suffice. Table-level is chosen deliberately:
--   * asset_freshness: parity with its twin asset_provenance_receipts, which 1070 granted
--     table-level SELECT, INSERT, UPDATE for the same writer in the same transaction;
--     a column-level grant here would be the lone exception and every future additive
--     column on this projection (receipt_version arrived that way) would fail mid-build
--     with a runtime 'permission denied' until a follow-up grant. The generated column
--     scope_key is never written by the builder in either form.
--   * bg_transit_moorti: the upsert inserts all six columns and updates all five
--     non-key columns, so column-level would exclude only the primary key from UPDATE —
--     no meaningful narrowing. The builder is already arwd at table level on the two
--     sibling tables the same writer seeds in the same call.
-- If the owner prefers column-level for asset_freshness (blocking UPDATE of the identity
-- columns asset_id / chart_id / partition_key), the equivalent is
--   GRANT INSERT (asset_id, chart_id, partition_key, freshness_state, reasons,
--                 receipt_version, observed_at) ON public.asset_freshness TO data_plane_builder;
--   GRANT UPDATE (freshness_state, reasons, receipt_version, observed_at)
--                 ON public.asset_freshness TO data_plane_builder;
-- and nothing else in this migration changes; that trade-off is surfaced, not taken.
--
-- DEPLOY-GATE SAFETY (allowlist drift)
-- ════════════════════════════════════
-- Neither table is in the protected relation set: asset_freshness and bg_transit_moorti
-- appear in none of L1_ACTIVE_TABLES / L2_ACTIVE_TABLES
-- (platform/scripts/data-plane-ownership-preflight.ts:9-14 and :16-28) nor in the status gate's
-- L1_HISTORY / L2_HISTORY lists (data-plane-ownership-status.ts:14-31), so none of the
-- ACL allowlist checks in data-plane-ownership-status.ts ever see them — the protected
-- sequence ACL check (L229-254), the protected table ACL check (L419-447), the
-- history/view ACL check (L449-483), the lifecycle-function EXECUTE check (L513-557) and
-- the DP-SD-018 write-privilege check (L559-570, which probes TRUNCATE/TRIGGER/REFERENCES
-- only on L1+L2 active tables) are all keyed on those lists or on the l1_/l2_data_plane_*
-- attestation tables. The exact-relation inventory (L164-196) matches only L1/L2 active
-- names and the l1_data_plane_/l2_data_plane_ prefixes. The role-attribute, membership
-- and schema-ACL checks (L78-143, L485-511) do not read table ACLs. This migration adds
-- no membership, no CREATE on schema public, no TRUNCATE/TRIGGER/REFERENCES, no function
-- EXECUTE, and no default-privilege change.
-- Neither table is in CONTROL_AND_L0_L3_TABLES (preflight :32-66), which is the one-shot
-- cutover bootstrap's own grant list (already executed; a one-shot, not a standing gate);
-- that list is not an allowlist any gate reads (its only consumer is the loop at
-- preflight :326).
--
-- RUNNER AUTHORITY
-- ════════════════
-- The routine migration runner connects as amjis_app (PROD_DATABASE_URL —
-- platform/scripts/validate-migration-database-routes.ts:12), and amjis_app OWNS both
-- tables (verified read-only: pg_class.relowner = amjis_app for asset_freshness and
-- bg_transit_moorti, relkind r, RLS off), so the GRANTs below are issued by the owner and
-- recorded with amjis_app as grantor. This is deliberately NOT a protected
-- public-schema migration: it creates no object, only grants on two existing unprotected
-- ones. No SECURITY DEFINER change and no ownership change.
--
-- SCOPE — exactly four privileges, nothing else
-- ═════════════════════════════════════════════
--   asset_freshness   INSERT, UPDATE
--   bg_transit_moorti INSERT, UPDATE
-- Deliberately NOT granted: DELETE on either table (no statement deletes; freshness rows
-- are removed only by the owner-executed FK cascade, and the moorti writer never retires
-- rows), TRUNCATE / TRIGGER / REFERENCES, WITH GRANT OPTION, any sequence privilege (none
-- exist), any other table, and anything on the Gochara contract-table family.
--
-- IDEMPOTENT: GRANT of an already-held privilege is a no-op in PostgreSQL; the migration
-- is re-runnable, adds privileges only, and revokes nothing. The DO block is a
-- fail-closed self-check (CLAUDE.md §N.8): it raises if either grant did not take effect
-- (so a silent no-op cannot be recorded as applied) AND if DELETE, TRUNCATE, REFERENCES or
-- TRIGGER is effective for the builder on either table (least privilege asserted at apply
-- time; a pre-existing wider grant fails the migration loudly instead of being blessed).
--
-- VERIFY AFTER APPLY (read-only; run as suvarna_reader or any role that can call the
-- catalog functions). Expected values in the right-hand column:
--   SELECT has_table_privilege('data_plane_builder','public.asset_freshness','INSERT')    -- t
--        , has_table_privilege('data_plane_builder','public.asset_freshness','UPDATE')    -- t
--        , has_table_privilege('data_plane_builder','public.asset_freshness','SELECT')    -- t (unchanged)
--        , has_table_privilege('data_plane_builder','public.asset_freshness','DELETE')    -- f
--        , has_table_privilege('data_plane_builder','public.asset_freshness','TRUNCATE')  -- f
--        , has_table_privilege('data_plane_builder','public.asset_freshness','TRIGGER')   -- f
--        , has_table_privilege('data_plane_builder','public.asset_freshness','REFERENCES')-- f
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','INSERT')  -- t
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','UPDATE')  -- t
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','SELECT')  -- t (unchanged)
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','DELETE')  -- f
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','TRUNCATE')-- f
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','TRIGGER') -- f
--        , has_table_privilege('data_plane_builder','public.bg_transit_moorti','REFERENCES'); -- f
--   SELECT relname, relacl FROM pg_class
--    WHERE relnamespace = 'public'::regnamespace
--      AND relname IN ('asset_freshness','bg_transit_moorti');
--     -- data_plane_builder=arw/amjis_app on both; every other grantee entry unchanged:
--     --   asset_freshness   amjis_app=arwdDxt, retrieval_census_ro=r, suvarna_reader=r
--     --   bg_transit_moorti amjis_app=arwdDxt, retrieval_census_ro=r, role_web_serve=r,
--     --     role_orchestrator=arwd, role_jobs=r, role_sidecar=r,
--     --     nirmana_evidence_ingress_writer=r, suvarna_reader=r
--   SELECT has_schema_privilege('data_plane_builder','public','CREATE');      -- f (unchanged)
--   SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member
--    WHERE r.rolname = 'data_plane_builder';                                   -- 0 (unchanged)

GRANT INSERT, UPDATE ON TABLE public.asset_freshness   TO data_plane_builder;
GRANT INSERT, UPDATE ON TABLE public.bg_transit_moorti TO data_plane_builder;

DO $$
DECLARE
  missing text := '';
  excess  text := '';
BEGIN
  -- Positive post-condition: the four granted privileges are effective.
  IF NOT has_table_privilege('data_plane_builder', 'public.asset_freshness', 'INSERT')
    THEN missing := missing || ' asset_freshness.INSERT'; END IF;
  IF NOT has_table_privilege('data_plane_builder', 'public.asset_freshness', 'UPDATE')
    THEN missing := missing || ' asset_freshness.UPDATE'; END IF;
  IF NOT has_table_privilege('data_plane_builder', 'public.bg_transit_moorti', 'INSERT')
    THEN missing := missing || ' bg_transit_moorti.INSERT'; END IF;
  IF NOT has_table_privilege('data_plane_builder', 'public.bg_transit_moorti', 'UPDATE')
    THEN missing := missing || ' bg_transit_moorti.UPDATE'; END IF;
  IF missing <> '' THEN
    RAISE EXCEPTION 'migration 1217: data_plane_builder grants did not take effect:%', missing;
  END IF;

  -- Negative post-condition (least privilege asserted at apply time): nothing beyond
  -- SELECT/INSERT/UPDATE may be effective for data_plane_builder on either table, from any
  -- source (direct grant, PUBLIC, or a role membership).
  IF has_table_privilege('data_plane_builder', 'public.asset_freshness', 'DELETE')
    THEN excess := excess || ' asset_freshness.DELETE'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.asset_freshness', 'TRUNCATE')
    THEN excess := excess || ' asset_freshness.TRUNCATE'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.asset_freshness', 'REFERENCES')
    THEN excess := excess || ' asset_freshness.REFERENCES'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.asset_freshness', 'TRIGGER')
    THEN excess := excess || ' asset_freshness.TRIGGER'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.bg_transit_moorti', 'DELETE')
    THEN excess := excess || ' bg_transit_moorti.DELETE'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.bg_transit_moorti', 'TRUNCATE')
    THEN excess := excess || ' bg_transit_moorti.TRUNCATE'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.bg_transit_moorti', 'REFERENCES')
    THEN excess := excess || ' bg_transit_moorti.REFERENCES'; END IF;
  IF has_table_privilege('data_plane_builder', 'public.bg_transit_moorti', 'TRIGGER')
    THEN excess := excess || ' bg_transit_moorti.TRIGGER'; END IF;
  IF excess <> '' THEN
    RAISE EXCEPTION 'migration 1217: data_plane_builder holds privileges beyond INSERT/UPDATE:%', excess;
  END IF;
END $$;
