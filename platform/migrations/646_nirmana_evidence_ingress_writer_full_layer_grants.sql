-- Migration 646: grant nirmana_evidence_ingress_writer SELECT on every
-- non-L0 production table any asset's integrity_check_sql actually reads.
--
-- Migration 632 (immutable) established nirmana_evidence_ingress_writer as
-- the least-privilege server role backing every layer's integrity_verified /
-- asset_frozen / probe_accepted submission, granting SELECT on an explicit
-- whitelist -- its own comment says any new detector relation needs "a
-- reviewed migration addition before an ingress receipt can be earned."
-- That whitelist covered only L0's bg_*/brahma_*/reference_* surface plus a
-- handful of core campaign tables. Migration 645 added the two tables one L5
-- asset's check needed (Nirmana #1869) after its first real certification
-- attempt failed live with `permission denied`.
--
-- #1869's own recommendation (not acted on there, acted on here): audit
-- every asset's integrity_check_sql for out-of-whitelist reads in one pass
-- rather than discover them one certification at a time. This migration is
-- that audit's fix. Derived, not guessed: scanned every non-null
-- asset_registry.integrity_check_sql for a real `FROM <table>` / `JOIN
-- <table>` reference (not a bare word-boundary match, which produced false
-- positives from comment prose mentioning a table name in passing --
-- `projects`, `asset_throughput`, `build_substep_progress` were all such
-- false positives on inspection and are correctly excluded here) against
-- every real table in the current schema, then subtracted the role's
-- current live grants. The result: 65 tables, spanning every non-L0 layer's
-- own production data (kala_*, mimamsa_*, phala_*, plus bodha_cdlm_cells /
-- bodha_msr_signals / bodha_pratijna and the L1 chart_facts/chart_dashas
-- core tables several L3 checks read) -- essentially every layer's own
-- target surface was missing from the original whitelist, which only ever
-- covered L0.
--
-- Additive only: does not touch migration 632's already-applied
-- REVOKE-then-GRANT sequence, migration 645's grants, or any other role's
-- privileges. Idempotent and existence-checked, matching 632's own pattern.
BEGIN;

DO $$
DECLARE
  relation_name text;
  new_read_relations constant text[] := ARRAY[
    'bodha_cdlm_cells',
    'bodha_msr_signals',
    'bodha_pratijna',
    'chart_dashas',
    'chart_facts',
    'gochara_resonance_map',
    'kala_activation',
    'kala_activation_predicates',
    'kala_avadhi',
    'kala_bhavishya',
    'kala_convergence',
    'kala_darshana',
    'kala_field',
    'kala_field_gof',
    'kala_field_salience',
    'kala_field_skill',
    'kala_field_snapshots',
    'kala_field_weight_versions',
    'kala_field_windows',
    'kala_gochara_v2_build_state',
    'kala_gochara_windows',
    'kala_gochara_windows_archive_20260805',
    'kala_gochara_windows_v2',
    'kala_jivana_parva',
    'kala_kota_chakra',
    'kala_moorti_nirnaya',
    'kala_obstruction',
    'kala_sudarshana_varsha',
    'kala_taranga',
    'kala_tithi_pravesha',
    'kala_vedha_gochara',
    'mimamsa_anchor_adjustment',
    'mimamsa_attribution',
    'mimamsa_calibration',
    'mimamsa_calibration_snapshot',
    'mimamsa_convergence_adjustment',
    'mimamsa_discoveries',
    'mimamsa_event_provenance',
    'mimamsa_export_log',
    'mimamsa_fact_adjustment',
    'mimamsa_insight_embeddings',
    'mimamsa_insight_units',
    'mimamsa_intervention_ledger',
    'mimamsa_journal',
    'mimamsa_load_bearing',
    'mimamsa_manifestation_grammar',
    'mimamsa_manifestation_sets',
    'mimamsa_multipliers',
    'mimamsa_negative_controls',
    'mimamsa_predictions',
    'mimamsa_preferences',
    'mimamsa_qa_eval',
    'mimamsa_reliability',
    'mimamsa_signal_adjustment',
    'mimamsa_signal_families',
    'phala_anchors',
    'phala_mitigation',
    'phala_muhurta',
    'phala_phaladesa',
    'phala_pramana',
    'phala_rectification',
    'phala_rectification_best',
    'phala_sankrama',
    'phala_sodhana',
    'phala_suddha_sodhana'
  ];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 646 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH relation_name IN ARRAY new_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
    END IF;
  END LOOP;

  -- Verify exactly the intended grants landed -- SELECT only, on exactly
  -- these tables, nothing broader (mirrors 632's and 645's own post-grant
  -- assertion style).
  IF EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = ANY(new_read_relations)
       AND privilege_type <> 'SELECT'
  ) THEN
    RAISE EXCEPTION 'migration 646 granted more than SELECT on one or more of the new relations';
  END IF;
  IF (
    SELECT count(DISTINCT table_name) FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = ANY(new_read_relations)
       AND privilege_type = 'SELECT'
  ) <> (
    SELECT count(*) FROM unnest(new_read_relations) AS rel
     WHERE to_regclass(format('%I.%I', current_schema(), rel)) IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 646 did not grant SELECT on every existing target relation';
  END IF;
END;
$$;

COMMIT;

-- Reversal (only before any integrity_verified receipt relies on any of
-- these grants): REVOKE SELECT ON <the 65 tables above> FROM
-- nirmana_evidence_ingress_writer;
