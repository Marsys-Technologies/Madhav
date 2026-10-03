-- Migration 1231: record the existing production ACL — data_plane_builder
--                 SELECT/INSERT/UPDATE/DELETE on public.gochara_resonance_map
--                 (+ USAGE/SELECT on its identity sequence).
-- Pravāha C9 (steward M20261002T004019-3811, 2026-10-02), on Pravāha C7's finding.
-- Created: 2026-10-02. Author: pravaha stream C.
--
-- Numbering: 1231 is the lowest free number of Pravāha's reserved block
-- 1230-1249 (steward M20261001T231948-c543) at authoring time: no 1231 file on
-- origin/main and none in open PR #2889 (1230) or #2897 (checked
-- 2026-10-02).
--
-- WHY THIS EXISTS — THIS MIGRATION RECORDS AN EXISTING PRODUCTION ACL.
-- ═════════════════════════════════════════════════════════════════════
-- It CHANGES NOTHING in production: every privilege below was verified
-- read-only against production on 2026-10-02 to be ALREADY HELD by
-- data_plane_builder (pg_class.relacl for public.gochara_resonance_map
-- carries data_plane_builder=arwd/amjis_app; has_table_privilege is true for
-- SELECT/INSERT/UPDATE/DELETE; has_sequence_privilege is true for USAGE and
-- SELECT on public.gochara_resonance_map_id_seq). What was missing is the
-- RECORD: no migration in this repo grants any of it (Pravāha C7's builder-role
-- fixture had to mirror the ACL out-of-band as PRODUCTION_MIRROR_GRANTS), so a
-- fresh environment could never run ka_gochara_resonance — the writer whose
-- only target this table is. This file makes the ACL reproducible from the
-- migrations alone, and grants nothing production does not already hold.
--
-- DEPLOY-GATE SAFETY (allowlist drift)
-- ════════════════════════════════════
-- gochara_resonance_map is not in the L1/L2 protected producer sets
-- (platform/scripts/data-plane-ownership-preflight.ts:9-32); it sits in
-- CONTROL_AND_L0_L3_TABLES (same file, ~L41-76) — the explicit list of
-- relations the builder role is expected to write at runtime — so this grant
-- MATCHES the ownership-status expectation and cannot trip an allowlist-drift
-- gate. The protected-sequence ACL check scopes to L1/L2 tables only, so the
-- sequence grant below is outside its allowlist too. The role gains no
-- TRUNCATE/REFERENCES/TRIGGER, no CREATE on schema public, and no privilege on
-- any other relation. The sequence privileges are exactly the ones production
-- holds (USAGE lets the writer's INSERT draw nextval on the BIGSERIAL id;
-- SELECT is what production carries alongside it) — nothing more is granted.
--
-- RUNNER AUTHORITY
-- ════════════════
-- The routine migration runner connects as amjis_app (PROD_DATABASE_URL —
-- platform/scripts/validate-migration-database-routes.ts:12), and amjis_app
-- OWNS gochara_resonance_map (verified read-only: pg_class relowner =
-- 'amjis_app'), so the GRANTs below are issued by the owner. Grant-only, no
-- object created: deliberately a routine migration, like 1225.
--
-- No BEGIN/COMMIT here: the migration runner owns the transaction
-- (platform/scripts/migrate.ts: BEGIN; <SQL>; INSERT INTO _migrations_applied;
-- COMMIT).

DO $mig_1231$
BEGIN
  -- Guard: on an environment where the role does not exist (e.g. a minimal
  -- disposable database), skip cleanly rather than error — the grant is
  -- meaningful only where the builder role exists.
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    RAISE NOTICE '1231: role data_plane_builder does not exist — skipping (no-op)';
    RETURN;
  END IF;

  -- Idempotent: re-granting an already-held privilege is a no-op in PostgreSQL.
  GRANT SELECT, INSERT, UPDATE, DELETE ON public.gochara_resonance_map TO data_plane_builder;
  GRANT USAGE, SELECT ON SEQUENCE public.gochara_resonance_map_id_seq TO data_plane_builder;

  -- Post-check: the recorded ACL must be in force after the grant — loud, not
  -- assumed (§N.8).
  IF NOT (has_table_privilege('data_plane_builder', 'public.gochara_resonance_map', 'SELECT')
      AND has_table_privilege('data_plane_builder', 'public.gochara_resonance_map', 'INSERT')
      AND has_table_privilege('data_plane_builder', 'public.gochara_resonance_map', 'UPDATE')
      AND has_table_privilege('data_plane_builder', 'public.gochara_resonance_map', 'DELETE')
      AND has_sequence_privilege('data_plane_builder', 'public.gochara_resonance_map_id_seq', 'USAGE')
      AND has_sequence_privilege('data_plane_builder', 'public.gochara_resonance_map_id_seq', 'SELECT')) THEN
    RAISE EXCEPTION '1231: post-grant check failed — data_plane_builder does not hold the recorded production ACL on gochara_resonance_map';
  END IF;
END
$mig_1231$;
