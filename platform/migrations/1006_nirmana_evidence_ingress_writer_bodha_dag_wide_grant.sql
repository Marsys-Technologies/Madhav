-- 1006_nirmana_evidence_ingress_writer_bodha_dag_wide_grant.sql
--
-- NIRMĀṆA — same defect class as 645/646/885/890/898/903/921/922/923/934/935/945/977/1004/1005.
-- This migration is the output of the priority-2 standing duty (RESOLUTION_L1.md v6): a
-- grant/contract pre-flight sweep of every not-yet-frozen L2/L3/L4/L5 asset's frozen
-- `integrity_check_sql`, checking whether `nirmana_evidence_ingress_writer` (the verifier
-- identity's server_reconstructed pool, migration 632) can SELECT every table each check
-- genuinely reads as a FROM/JOIN target (comment-only mentions were excluded).
--
-- Confirmed directly before this migration via `information_schema.table_privileges`: none of
-- the 15 tables below has a SELECT row for `nirmana_evidence_ingress_writer`, while every one
-- of them already grants SELECT to `retrieval_census_ro`, `role_jobs`, `role_sidecar`, and
-- `role_web_serve` (and read/write to `role_orchestrator`) -- the exact established pattern.
-- Table -> asset(s) whose live `integrity_check_sql` reads it as a real FROM/JOIN target:
--   bodha_discoveries, bodha_anomalies                          -> bo_anveshana
--   bodha_cdlm_chart_summary                                    -> bo_cdlm_summary
--   bodha_chart_gestalt                                         -> bo_chart_gestalt
--   bodha_question_lenses                                       -> bo_drishti
--   bodha_contradictions, bodha_rm_remedy_prescriptions,
--   bodha_rm_resonances, bodha_signal_embeddings,
--   synthesis_quality_scorecard                                 -> bo_pramana_mapa
--   bodha_signal_embeddings                                     -> bo_samskara (dup, covered above)
--   bodha_rm_chart_summary, bodha_rm_dasha_windowed_prescriptions,
--   bodha_rm_dosha_remedy_bundles, bodha_rm_pattern_remedies,
--   bodha_rm_remedy_prescriptions, bodha_rm_resonances           -> bo_upaya (dups covered above)
--   bodha_mechanisms                                            -> bo_yantra_mechanism
--
-- Ruled OUT as false positives during the sweep (table name appears only inside a `--` comment
-- in the asset's integrity_check_sql, never as an actual FROM/JOIN target, so no grant is
-- needed): ka_bhavishya_lekha ("projects" -- substring of "the row projects", not a table
-- reference), ka_gochara and ka_vighnakara ("asset_throughput" -- prose reference only), and
-- ka_kshetra ("build_substep_progress" -- prose reference only).
--
-- This is the same additive, existence-checked, idempotent SELECT-grant pattern as migrations
-- 921/922/923/885/945/977/1004/1005 -- it grants read access only, does not touch any asset's
-- own registry contract, writer code, or digest spec, and does not widen any other role's
-- access. All 15 tables are owned by `amjis_app` (verified).

BEGIN;

DO $$
DECLARE
  target_table text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 1006 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH target_table IN ARRAY ARRAY[
    'bodha_discoveries',
    'bodha_anomalies',
    'bodha_cdlm_chart_summary',
    'bodha_chart_gestalt',
    'bodha_question_lenses',
    'bodha_contradictions',
    'bodha_rm_remedy_prescriptions',
    'bodha_rm_resonances',
    'bodha_signal_embeddings',
    'synthesis_quality_scorecard',
    'bodha_rm_chart_summary',
    'bodha_rm_dasha_windowed_prescriptions',
    'bodha_rm_dosha_remedy_bundles',
    'bodha_rm_pattern_remedies',
    'bodha_mechanisms'
  ]
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM pg_tables
      WHERE schemaname = current_schema()
        AND tablename = target_table
    ) THEN
      RAISE EXCEPTION 'migration 1006 requires % to already exist', target_table;
    END IF;

    IF NOT has_table_privilege('nirmana_evidence_ingress_writer', format('%I.%I', current_schema(), target_table), 'SELECT') THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), target_table);
    END IF;
  END LOOP;
END $$;

COMMIT;
