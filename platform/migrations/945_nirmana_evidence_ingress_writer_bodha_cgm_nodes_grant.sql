-- 945_nirmana_evidence_ingress_writer_bodha_cgm_nodes_grant.sql
--
-- NIRMĀṆA — same defect class as 645/646/885/890/898/903/921/922/923/934/935.
-- bo_bimba's frozen `integrity_check_sql` (set by migration 711_bo_bimba_integrity_check.sql;
-- node identity by 714_bo_bimba_node_identity.sql) reads directly from `bodha_cgm_nodes` (no
-- intervening function). Independent fresh-context verification of bo_bimba's `integrity_verified` receipt
-- hit HTTP 500 on first submission attempt; the actual Postgres error surfaced through Cloud Run
-- logs was `permission denied for table bodha_cgm_nodes` (code 42501, routine
-- 'aclcheck_error') -- the `nirmana_evidence_ingress_writer` role (used by the verifier
-- identity's server_reconstructed pool, per migration 632) has never been granted SELECT on this
-- table. Confirmed directly before this migration:
-- `has_table_privilege('nirmana_evidence_ingress_writer', 'bodha_cgm_nodes', 'SELECT')` = false.
--
-- This is the same additive, existence-checked, idempotent single-table SELECT-grant pattern as
-- migrations 921/922/923/885 -- it grants read access only, does not touch bo_bimba's own
-- registry contract, writer code, or any asset digest, and does not widen any other role's
-- access. `bodha_cgm_nodes` is owned by `amjis_app` (verified) with existing read grants to
-- `retrieval_census_ro`, `role_web_serve`, `role_jobs`, `role_sidecar`, and read/write to
-- `role_orchestrator`; this migration adds the one missing grant the verification path needs.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 945 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_tables
    WHERE schemaname = current_schema()
      AND tablename = 'bodha_cgm_nodes'
  ) THEN
    RAISE EXCEPTION 'migration 945 requires bodha_cgm_nodes to already exist';
  END IF;

  IF NOT has_table_privilege('nirmana_evidence_ingress_writer', format('%I.bodha_cgm_nodes', current_schema()), 'SELECT') THEN
    EXECUTE format('GRANT SELECT ON TABLE %I.bodha_cgm_nodes TO nirmana_evidence_ingress_writer', current_schema());
  END IF;
END $$;

COMMIT;
