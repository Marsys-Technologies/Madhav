-- 1004_nirmana_evidence_ingress_writer_bodha_convergence_triangulation_grant.sql
--
-- NIRMĀṆA -- same defect class as 645/646/885/890/898/903/921/922/923/934/935/945/977.
-- bo_sangati's frozen `integrity_check_sql` (set by the asset's own registry contract) reads
-- directly from `bodha_cdlm_cells` and `bodha_convergence`; bo_sangati's `natural_key_partition`
-- / provenance also names `bodha_triangulation` as one of its three owned tables. Independent
-- fresh-context verification of a `bo_sangati` `integrity_verified` submission (as the verifier
-- identity, via `record_evidence`) hit HTTP 500 with Postgres error class 42501
-- (`insufficient_privilege`). Confirmed directly before this migration via
-- `information_schema.role_table_grants`: `nirmana_evidence_ingress_writer` (used by the
-- verifier identity's server_reconstructed pool, per migration 632) already has SELECT on
-- `bodha_cdlm_cells` and `asset_registry`, but has never been granted SELECT on
-- `bodha_convergence` or `bodha_triangulation` -- this gap was latent until an asset whose
-- contract spans those two newer CDLM tables (bo_sangati) came up for freezing. See
-- nirmana-adjudication issue #2514.
--
-- This is the same additive, existence-checked, idempotent SELECT-grant pattern as migrations
-- 945/977 -- it grants read access only, does not touch bo_sangati's own registry contract,
-- writer code, or any asset digest, and does not widen any other role's access. Both tables are
-- owned by `amjis_app` (verified) with existing read grants to `retrieval_census_ro`,
-- `role_web_serve`, `role_jobs`, `role_sidecar`, and read/write to `role_orchestrator`; this
-- migration adds the one missing grant the verification path needs, on both tables at once since
-- both are required for the same asset's detector query to run at all.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 1004 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_tables
    WHERE schemaname = current_schema()
      AND tablename = 'bodha_convergence'
  ) THEN
    RAISE EXCEPTION 'migration 1004 requires bodha_convergence to already exist';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_tables
    WHERE schemaname = current_schema()
      AND tablename = 'bodha_triangulation'
  ) THEN
    RAISE EXCEPTION 'migration 1004 requires bodha_triangulation to already exist';
  END IF;

  IF NOT has_table_privilege('nirmana_evidence_ingress_writer', format('%I.bodha_convergence', current_schema()), 'SELECT') THEN
    EXECUTE format('GRANT SELECT ON TABLE %I.bodha_convergence TO nirmana_evidence_ingress_writer', current_schema());
  END IF;

  IF NOT has_table_privilege('nirmana_evidence_ingress_writer', format('%I.bodha_triangulation', current_schema()), 'SELECT') THEN
    EXECUTE format('GRANT SELECT ON TABLE %I.bodha_triangulation TO nirmana_evidence_ingress_writer', current_schema());
  END IF;
END $$;

COMMIT;
