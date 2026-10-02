-- Migration 1239: record the existing production ACL — data_plane_builder
--                 SELECT/INSERT/UPDATE/DELETE on public.kala_gochara_v2_build_state,
--                 public.kala_moorti_nirnaya and public.kala_vedha_gochara
--                 (+ USAGE/SELECT on the two BIGSERIAL identity sequences).
-- Pravāha C19 (steward M20261002T062943-356e, 2026-10-02), closing Pravāha
-- C18's report-only gap list.
-- Created: 2026-10-02. Author: pravaha stream C.
--
-- Numbering: 1239 is free in Pravāha's reserved block 1230-1249 (steward
-- M20261001T231948-c543) at authoring time: no 1239 file on origin/main and
-- none in open Pravāha PRs (taken elsewhere: 1232/1233/1234/1236/1240; 1241
-- reserved; 1237 = #2928, 1238 = #2931 — checked 2026-10-02).
--
-- WHY THIS EXISTS — THIS MIGRATION RECORDS AN EXISTING PRODUCTION ACL.
-- ═════════════════════════════════════════════════════════════════════
-- It CHANGES NOTHING in production: every privilege below was verified
-- read-only against production on 2026-10-02 to be ALREADY HELD by
-- data_plane_builder (for each of the three tables: has_table_privilege is
-- true for SELECT/INSERT/UPDATE/DELETE and false for
-- TRUNCATE/REFERENCES/TRIGGER; pg_class.relacl carries
-- data_plane_builder=arwd/amjis_app; has_sequence_privilege is true for
-- USAGE and SELECT and false for UPDATE on
-- public.kala_moorti_nirnaya_id_seq and public.kala_vedha_gochara_id_seq;
-- kala_gochara_v2_build_state has a composite PRIMARY KEY and no serial
-- column, so there is no sequence to grant). What was missing is the RECORD:
-- no migration in this repo grants any of it (Pravāha C18's report-only gap
-- list), so a fresh environment could never run the ka_gochara writer's
-- build-state bookkeeping upsert or the ka_moorti_nirnaya / ka_vedha_gochara
-- overlay writers. This file makes the ACLs reproducible from the migrations
-- alone, and grants nothing production does not already hold.
--
-- DEPLOY-GATE SAFETY (allowlist drift)
-- ════════════════════════════════════
-- None of the three tables is in the L1/L2 protected producer sets
-- (platform/scripts/data-plane-ownership-preflight.ts:9-32); all three sit
-- in CONTROL_AND_L0_L3_TABLES (same file: kala_gochara_v2_build_state L61,
-- kala_moorti_nirnaya L63, kala_vedha_gochara L65 — the explicit list of
-- relations the builder role is expected to write at runtime) — so these
-- grants MATCH the ownership-status expectation and cannot trip an
-- allowlist-drift gate. The protected-sequence ACL check scopes to L1/L2
-- tables only, so the sequence grants below are outside its allowlist too.
-- The role gains no TRUNCATE/REFERENCES/TRIGGER, no CREATE on schema public,
-- and no privilege on any other relation. The sequence privileges are
-- exactly the ones production holds (USAGE lets each writer's INSERT draw
-- nextval on the BIGSERIAL id; SELECT is what production carries alongside
-- it) — nothing more is granted.
--
-- RUNNER AUTHORITY
-- ════════════════
-- The routine migration runner connects as amjis_app (PROD_DATABASE_URL —
-- platform/scripts/validate-migration-database-routes.ts:12), and amjis_app
-- OWNS all three tables (verified read-only: pg_class relowner = 'amjis_app'
-- for each), so the GRANTs below are issued by the owner. Grant-only, no
-- object created: deliberately a routine migration, like 1237/1238.
--
-- No BEGIN/COMMIT here: the migration runner owns the transaction
-- (platform/scripts/migrate.ts: BEGIN; <SQL>; INSERT INTO _migrations_applied;
-- COMMIT).

DO $mig_1239$
BEGIN
  -- Guard: on an environment where the role does not exist (e.g. a minimal
  -- disposable database), skip cleanly rather than error — the grants are
  -- meaningful only where the builder role exists.
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    RAISE NOTICE '1239: role data_plane_builder does not exist — skipping (no-op)';
    RETURN;
  END IF;

  -- Idempotent: re-granting an already-held privilege is a no-op in PostgreSQL.
  GRANT SELECT, INSERT, UPDATE, DELETE ON public.kala_gochara_v2_build_state TO data_plane_builder;
  GRANT SELECT, INSERT, UPDATE, DELETE ON public.kala_moorti_nirnaya TO data_plane_builder;
  GRANT SELECT, INSERT, UPDATE, DELETE ON public.kala_vedha_gochara TO data_plane_builder;
  GRANT USAGE, SELECT ON SEQUENCE public.kala_moorti_nirnaya_id_seq TO data_plane_builder;
  GRANT USAGE, SELECT ON SEQUENCE public.kala_vedha_gochara_id_seq TO data_plane_builder;

  -- Post-check: the recorded ACLs must be in force after the grant — loud,
  -- not assumed (§N.8).
  IF NOT (has_table_privilege('data_plane_builder', 'public.kala_gochara_v2_build_state', 'SELECT')
      AND has_table_privilege('data_plane_builder', 'public.kala_gochara_v2_build_state', 'INSERT')
      AND has_table_privilege('data_plane_builder', 'public.kala_gochara_v2_build_state', 'UPDATE')
      AND has_table_privilege('data_plane_builder', 'public.kala_gochara_v2_build_state', 'DELETE')
      AND has_table_privilege('data_plane_builder', 'public.kala_moorti_nirnaya', 'SELECT')
      AND has_table_privilege('data_plane_builder', 'public.kala_moorti_nirnaya', 'INSERT')
      AND has_table_privilege('data_plane_builder', 'public.kala_moorti_nirnaya', 'UPDATE')
      AND has_table_privilege('data_plane_builder', 'public.kala_moorti_nirnaya', 'DELETE')
      AND has_table_privilege('data_plane_builder', 'public.kala_vedha_gochara', 'SELECT')
      AND has_table_privilege('data_plane_builder', 'public.kala_vedha_gochara', 'INSERT')
      AND has_table_privilege('data_plane_builder', 'public.kala_vedha_gochara', 'UPDATE')
      AND has_table_privilege('data_plane_builder', 'public.kala_vedha_gochara', 'DELETE')
      AND has_sequence_privilege('data_plane_builder', 'public.kala_moorti_nirnaya_id_seq', 'USAGE')
      AND has_sequence_privilege('data_plane_builder', 'public.kala_moorti_nirnaya_id_seq', 'SELECT')
      AND has_sequence_privilege('data_plane_builder', 'public.kala_vedha_gochara_id_seq', 'USAGE')
      AND has_sequence_privilege('data_plane_builder', 'public.kala_vedha_gochara_id_seq', 'SELECT')) THEN
    RAISE EXCEPTION '1239: post-grant check failed — data_plane_builder does not hold the recorded production ACLs on kala_gochara_v2_build_state / kala_moorti_nirnaya / kala_vedha_gochara';
  END IF;
END
$mig_1239$;
