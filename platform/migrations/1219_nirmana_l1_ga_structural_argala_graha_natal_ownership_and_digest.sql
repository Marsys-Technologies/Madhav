-- 1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql
--
-- DRAFT, NOT APPLIED. Suvarna Track I (SS decision N-61, 2026-10-01; design note
-- 00_ARCHITECTURE/briefs/suvarna/exec/DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md). The reviewer/operator
-- applies it through the PR and verifies it (CLAUDE.md N.4: never trust a silent no-op).
-- Transaction ownership belongs to platform/scripts/migrate.ts: no BEGIN/COMMIT here (1086 pattern).
--
-- ga_structural's writer now emits a new chart_facts category, `argala_graha_natal` (graha-level
-- argala, D1 only; AR-1/AR-2/AR-6). Two registry facts must follow it:
--
--   1. fact_category_ownership (the mechanism migration 410 seeded and 842 backfilled). Without a
--      row the category joins the already-unowned ga_structural rows. asset_registry.count_sql for
--      ga_structural JOINs this table (migration 410), so the ownership row IS the count_sql
--      change; count_sql itself is untouched (842's reasoning). `ON CONFLICT DO NOTHING`: safe to
--      re-run. target_floor (aspirational, CLAUDE.md N.4) is deliberately NOT bumped here: it is
--      re-baselined to the achieved count after the single governed ga_structural rebuild (1086's
--      reasoning).
--
--   2. asset_output_digest_specs. ga_structural has ONE active spec (migration 914, sha b2490646...,
--      81 categories in `where_in`). A category outside that list is not digested, so a change to the
--      new rows would not move the output digest and would not stale ga_structural's dependents.
--      This retires that spec and inserts the same spec with `argala_graha_natal` added (82
--      categories). spec_sha256 is canonical_digest (pipeline.orchestrator.provenance) of the new
--      spec; the same function reproduces 914's stored sha exactly, so the computation is the real one.
--      Retired, not deleted: a provenance receipt that references the old spec stays resolvable (609 /
--      1086 precedent). The DO block refuses an unrecognised active row and asserts exactly one active
--      new row afterwards.
--
-- NOT in this migration (proposed follow-ups, see the design note): new integrity_check_sql conjuncts
-- for the new category and for the AR-3 NULL cells (conjunct (e27) is vacuously true on a NULL score);
-- a CHART_FACTS_SCHEMA.json entry; L2 changes (bo_laksana category handling, bo_karanajala, migration
-- 763's cancelled_flag conjunct), which belong to the single batched L2 rebuild.
--
-- Post-apply verification:
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category = 'argala_graha_natal' AND owning_asset_id = 'ga_structural';           -- 1
--   SELECT spec_sha256 FROM asset_output_digest_specs
--    WHERE asset_id = 'ga_structural' AND retired_at IS NULL;   -- d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620

INSERT INTO fact_category_ownership (fact_category, owning_asset_id) VALUES
    ('argala_graha_natal', 'ga_structural')
ON CONFLICT (fact_category, owning_asset_id) DO NOTHING;

DO $$
DECLARE
  unexpected_active_count integer;
  active_new_count integer;
BEGIN
  SELECT count(*)
  INTO unexpected_active_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_structural'
    AND retired_at IS NULL
    AND spec_sha256 NOT IN (
      'b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6',
      'd480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620'
    );

  IF unexpected_active_count <> 0 THEN
    RAISE EXCEPTION
      'ga_structural digest-spec revision refused: % unrecognised active row(s)',
      unexpected_active_count;
  END IF;

  UPDATE asset_output_digest_specs
  SET retired_at = now()
  WHERE asset_id = 'ga_structural'
    AND spec_sha256 = 'b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6'
    AND retired_at IS NULL;

  INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
  VALUES (
    'ga_structural',
    'd480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620',
    '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["argala_graha_natal","argala_natal_matrix","ashtakavarga_anubindu","aspect_jaimini","aspect_jaimini_per_varga","aspect_matrix_summary","aspect_parashari_given","aspect_parashari_per_varga","aspect_parashari_received","aspect_received_by_special_point","aspect_tajik","bhava_bala_aspectual","bhava_bala_directional","bhava_bala_lord","bhava_bala_occupant","bhava_bala_positional","bhava_bala_temporal","bhava_bala_total_extended","bhava_chalit_rasi_divergence","bhava_significance_link","chart_center_of_gravity","chart_cluster","combustion_per_varga","combustion_relationship","composite_dispositor_strength","conjunction_per_varga","conjunction_special_point","conjunction_within_orb","contradiction_pair","convergence_count","dispositor_chain_per_varga","dispositor_tree","dosha_fires","dosha_label","graha_avastha_baladi","graha_avastha_deepta","graha_avastha_jagrad","graha_avastha_lifetime_exposure_summary","graha_centrality","graha_composite_state_classification","graha_dignity_per_varga","graha_dispositor_chain","graha_effective_dignity_modified_by_aspects","graha_functional_class_per_ascendant","graha_in_house_composite_strength","graha_saptavargaja_bala_component","graha_special_state_rollup","graha_tri_deva_role_strength","graha_vargottama_amplification_factor","graha_yoga_karaka_flag","graha_yuddha","graha_yuddha_per_varga","house_strength_classification_rollup","jaimini_tri_deva_role_per_graha","kala_sarpa_per_varga","karaka_bhava_concordance","karaka_house_lord_overlap_flag","karaka_web_per_varga","karakatva_strength_per_significance","kendradhipati_dosha","lord_aspects_lord_per_varga","lord_in_house_per_varga","nakshatra_co_tenancy","nakshatra_dispositor_chain","nakshatra_lord_relationship","net_argala_per_varga","nway_config_per_varga","panchadha_maitri","parivartana_pairs","parivartana_per_varga","pranic_strength_per_graha","retrograde_aspect_modification","sambandha_grade","significator_path","tara_bala","upapada_lagna","vargottama_per_varga","vimsopaka_bala_per_graha","virodha_argala_natal_matrix","virupa_drishti","yoga_fires","yoga_label"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
  )
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

  SELECT count(*)
  INTO active_new_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_structural'
    AND spec_sha256 = 'd480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620'
    AND retired_at IS NULL;

  IF active_new_count <> 1 THEN
    RAISE EXCEPTION
      'ga_structural digest-spec revision failed: expected one active new row, got %',
      active_new_count;
  END IF;
END $$;
