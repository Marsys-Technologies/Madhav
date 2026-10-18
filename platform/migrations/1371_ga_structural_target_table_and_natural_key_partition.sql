-- 1371_ga_structural_target_table_and_natural_key_partition.sql   (partition text is byte-sorted)
--
-- Certification registry fix (SS N-538, Exec Suvarna). Fills TWO NULL columns of ONE asset_registry row (ga_structural): target_table and natural_key_partition, in ONE guarded UPDATE;
-- nothing else. Same pattern and reasons as migration 1358: the census cells Ldgr and Vocab.identity read only asset_registry.target_table, so the asset reads as having no table;
-- its writer writes ONE table, chart_facts (and never without a partition: once target_table = 'chart_facts' is shared with the other chart_facts writers, provenance.py treats the asset as having
-- co-writers and needs natural_key_partition, else the receipt reason is partition_undeclared and the dependents block on DEP-ASSERT). So both go together.
-- WHY THE 1358 PRECEDENT SHOWS chart_facts WHILE ITS SEED SAYS NULL: migration 1358 set it in the registry; scripts/seed/asset_registry_seed.ts keeps `target_table: null` on purpose (the registry insert is
-- ON CONFLICT DO NOTHING, so a re-seed never reverts a migration, and a fresh database replaying seed then migrations holds NULL, matches the guard, and is set here). The seed entry of this asset
-- is left null for the same reason.
-- THE PARTITION (82 categories, derived, not guessed): the rows of fact_category_ownership whose owning_asset_id is 'ga_structural' (read from production 2026-10-12: 82 categories, sorted; 75 of them
-- carry rows on the native chart, 107,708 rows = the asset's recorded rows_written), in the 872/874/1358 text shape "chart_facts.fact_category IN (<sorted list>)".
-- GUARD. Each column is filled only while it is NULL (COALESCE keeps an existing value); the UPDATE runs only if at least one of the two is NULL. A column that already holds a DIFFERENT value
-- (a target_table other than chart_facts, or a partition text whose md5 is not the one below) RAISES before anything is written: filling the other column next to a foreign value would leave a mismatched pair.
-- Absent row = no-op with a NOTICE. The post-check RAISES unless the row ends with target_table = 'chart_facts' AND the exact partition md5 (a silent no-op is never trusted).
-- TRIGGER EFFECT (real, intended): target_table and natural_key_partition are columns of nirmana_registry_receipt_invalidation (migration 596): the UPDATE stales this asset's freshness rows (registry_changed).
-- VERIFICATION BY PRODUCTION STRUCTURE: SELECT asset_id, target_table, md5(natural_key_partition), length(natural_key_partition) FROM asset_registry WHERE asset_id = 'ga_structural';
--   expect chart_facts, 844a2086ddb289cab723eb8b70d47b1b, 2028
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET target_table = NULL, natural_key_partition = NULL WHERE asset_id = 'ga_structural' AND target_table = 'chart_facts' AND md5(natural_key_partition) = '844a2086ddb289cab723eb8b70d47b1b';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_tt text; v_nkp text;
BEGIN
  SELECT count(*), max(target_table), max(natural_key_partition) INTO v_n, v_tt, v_nkp FROM asset_registry WHERE asset_id = 'ga_structural';
  IF v_n = 0 THEN
    RAISE NOTICE '1371: no ga_structural registry row (empty registry); nothing to do';
  ELSE
    IF v_tt IS NOT NULL AND v_tt IS DISTINCT FROM 'chart_facts' THEN
      RAISE EXCEPTION '1371: ga_structural target_table is already % (not NULL, not chart_facts); refusing to fill the partition next to a foreign table', v_tt;
    END IF;
    IF v_nkp IS NOT NULL AND md5(v_nkp) IS DISTINCT FROM '844a2086ddb289cab723eb8b70d47b1b' THEN
      RAISE EXCEPTION '1371: ga_structural natural_key_partition is already set to a different text (md5 %); refusing to fill target_table next to a foreign partition', md5(v_nkp);
    END IF;
    IF v_tt IS NOT NULL AND v_nkp IS NOT NULL THEN
      RAISE NOTICE '1371: ga_structural target_table and natural_key_partition are already set; nothing to do';
    END IF;
  END IF;
END
$pre$;

UPDATE asset_registry
SET target_table = COALESCE(target_table, 'chart_facts'),
    natural_key_partition = COALESCE(natural_key_partition, $nkp$chart_facts.fact_category IN (argala_graha_natal, argala_natal_matrix, ashtakavarga_anubindu, aspect_jaimini, aspect_jaimini_per_varga, aspect_matrix_summary, aspect_parashari_given, aspect_parashari_per_varga, aspect_parashari_received, aspect_received_by_special_point, aspect_tajik, bhava_bala_aspectual, bhava_bala_directional, bhava_bala_lord, bhava_bala_occupant, bhava_bala_positional, bhava_bala_temporal, bhava_bala_total_extended, bhava_chalit_rasi_divergence, bhava_significance_link, chart_center_of_gravity, chart_cluster, combustion_per_varga, combustion_relationship, composite_dispositor_strength, conjunction_per_varga, conjunction_special_point, conjunction_within_orb, contradiction_pair, convergence_count, dispositor_chain_per_varga, dispositor_tree, dosha_fires, dosha_label, graha_avastha_baladi, graha_avastha_deepta, graha_avastha_jagrad, graha_avastha_lifetime_exposure_summary, graha_centrality, graha_composite_state_classification, graha_dignity_per_varga, graha_dispositor_chain, graha_effective_dignity_modified_by_aspects, graha_functional_class_per_ascendant, graha_in_house_composite_strength, graha_saptavargaja_bala_component, graha_special_state_rollup, graha_tri_deva_role_strength, graha_vargottama_amplification_factor, graha_yoga_karaka_flag, graha_yuddha, graha_yuddha_per_varga, house_strength_classification_rollup, jaimini_tri_deva_role_per_graha, kala_sarpa_per_varga, karaka_bhava_concordance, karaka_house_lord_overlap_flag, karaka_web_per_varga, karakatva_strength_per_significance, kendradhipati_dosha, lord_aspects_lord_per_varga, lord_in_house_per_varga, nakshatra_co_tenancy, nakshatra_dispositor_chain, nakshatra_lord_relationship, net_argala_per_varga, nway_config_per_varga, panchadha_maitri, parivartana_pairs, parivartana_per_varga, pranic_strength_per_graha, retrograde_aspect_modification, sambandha_grade, significator_path, tara_bala, upapada_lagna, vargottama_per_varga, vimsopaka_bala_per_graha, virodha_argala_natal_matrix, virupa_drishti, yoga_fires, yoga_label)$nkp$)
WHERE asset_id = 'ga_structural'
  AND (target_table IS NULL OR natural_key_partition IS NULL);

DO $post$
DECLARE v_n int; v_tt text; v_nkp text;
BEGIN
  SELECT count(*), max(target_table), max(natural_key_partition) INTO v_n, v_tt, v_nkp FROM asset_registry WHERE asset_id = 'ga_structural';
  IF v_n = 1 AND v_tt IS DISTINCT FROM 'chart_facts' THEN
    RAISE EXCEPTION '1371: ga_structural target_table is % after the update (expected chart_facts)', coalesce(v_tt, '<NULL>');
  END IF;
  IF v_n = 1 AND md5(v_nkp) IS DISTINCT FROM '844a2086ddb289cab723eb8b70d47b1b' THEN
    RAISE EXCEPTION '1371: ga_structural natural_key_partition md5 is % after the update (expected 844a2086ddb289cab723eb8b70d47b1b)', coalesce(md5(v_nkp), '<NULL>');
  END IF;
END
$post$;
