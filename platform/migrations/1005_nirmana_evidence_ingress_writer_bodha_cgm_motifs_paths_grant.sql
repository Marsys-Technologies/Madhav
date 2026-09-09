-- 1005_nirmana_evidence_ingress_writer_bodha_cgm_motifs_paths_grant.sql
--
-- NIRMĀṆA — same defect class as 645/646/885/890/898/903/921/922/923/934/935/945/977/1004.
-- `bo_cgm_motifs`'s frozen `integrity_check_sql` reads `bodha_cgm_motifs`,
-- `bodha_cgm_nodes`, `bodha_cgm_edges`, and `bodha_cgm_chart_topology_summary` directly (no
-- intervening function); `bo_cgm_paths`'s frozen `integrity_check_sql` reads `bodha_cgm_paths`
-- directly. `bo_cgm_motifs`'s natural_key_partition/provenance also names `bodha_cgm_sub_graphs`
-- as one of its owned tables. The `nirmana_evidence_ingress_writer` role (used by the verifier
-- identity's server_reconstructed pool, per migration 632) already has SELECT on
-- `bodha_cgm_edges`/`bodha_cgm_nodes` (migrations 977/945) but was never granted SELECT on
-- `bodha_cgm_motifs`, `bodha_cgm_paths`, `bodha_cgm_sub_graphs`, or
-- `bodha_cgm_chart_topology_summary`. Confirmed directly before this migration via
-- `information_schema.table_privileges`: no row for `nirmana_evidence_ingress_writer` against
-- any of the four tables, while `bodha_cgm_edges`/`bodha_cgm_nodes` (same role) each show
-- SELECT.
--
-- This is the same additive, existence-checked, idempotent SELECT-grant pattern as migrations
-- 921/922/923/885/945/977/1004 -- it grants read access only, does not touch either asset's own
-- registry contract, writer code, or any asset digest, and does not widen any other role's
-- access. All four tables are owned by `amjis_app` (verified) with existing read grants to
-- `retrieval_census_ro`, `role_web_serve`, `role_jobs`, `role_sidecar`, and read/write to
-- `role_orchestrator`; this migration adds the four missing grants the verification path needs
-- to unblock `integrity_verified` for `bo_cgm_motifs` and `bo_cgm_paths`.

BEGIN;

DO $$
DECLARE
  target_table text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 1005 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH target_table IN ARRAY ARRAY[
    'bodha_cgm_motifs',
    'bodha_cgm_paths',
    'bodha_cgm_sub_graphs',
    'bodha_cgm_chart_topology_summary'
  ]
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM pg_tables
      WHERE schemaname = current_schema()
        AND tablename = target_table
    ) THEN
      RAISE EXCEPTION 'migration 1005 requires % to already exist', target_table;
    END IF;

    IF NOT has_table_privilege('nirmana_evidence_ingress_writer', format('%I.%I', current_schema(), target_table), 'SELECT') THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), target_table);
    END IF;
  END LOOP;
END $$;

COMMIT;
