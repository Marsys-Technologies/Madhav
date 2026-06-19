-- Migration 323: Update ga_structural count_sql + target_floor after graph-theoretic rebuild.
--
-- Context: 7 graph-theoretic categories (graha_centrality, dispositor_tree, chart_cluster,
-- chart_center_of_gravity, convergence_count, karaka_bhava_concordance, nakshatra_dispositor_chain)
-- ported from orphaned D1-only rows into orchestrator-native per-varga builders (GA8 Phase 3).
-- Two additional categories added: combustion_per_varga, virupa_drishti, significator_path,
-- graha_yuddha_per_varga. Two stale names corrected: net_argala→net_argala_per_varga,
-- nway_configuration→nway_config_per_varga.
--
-- New build_id: 5d11969e-31d9-4693-bc11-8b17cff48f5a
-- Achieved: 106,014 rows across 5 ayanamshas (69 categories).
-- Old orphan build_id purged: 22fcef22-3b50-4357-b128-15c445146eec.

-- Step 1: Fix count_sql — 69 categories, corrected names
UPDATE asset_registry
SET
  count_sql = $SQL$
  SELECT count(*) AS count
  FROM chart_facts
  WHERE chart_id = $1
    AND fact_category IN (
      'argala_natal_matrix',
      'ashtakavarga_anubindu',
      'aspect_jaimini',
      'aspect_jaimini_per_varga',
      'aspect_matrix_summary',
      'aspect_parashari_given',
      'aspect_parashari_per_varga',
      'aspect_parashari_received',
      'aspect_received_by_special_point',
      'aspect_tajik',
      'bhava_bala_aspectual',
      'bhava_bala_directional',
      'bhava_bala_lord',
      'bhava_bala_occupant',
      'bhava_bala_positional',
      'bhava_bala_temporal',
      'bhava_bala_total_extended',
      'bhava_significance_link',
      'chart_center_of_gravity',
      'chart_cluster',
      'combustion_per_varga',
      'composite_dispositor_strength',
      'conjunction_per_varga',
      'conjunction_special_point',
      'conjunction_within_orb',
      'contradiction_pair',
      'convergence_count',
      'dispositor_chain_per_varga',
      'dispositor_tree',
      'dosha_label',
      'graha_avastha_baladi',
      'graha_avastha_deepta',
      'graha_avastha_jagrad',
      'graha_avastha_lajjitadi',
      'graha_avastha_lifetime_exposure_summary',
      'graha_avastha_sayanadi',
      'graha_centrality',
      'graha_composite_state_classification',
      'graha_dignity_per_varga',
      'graha_dispositor_chain',
      'graha_effective_dignity_modified_by_aspects',
      'graha_functional_class_per_ascendant',
      'graha_in_house_composite_strength',
      'graha_saptavargaja_bala_component',
      'graha_special_state_rollup',
      'graha_tri_deva_role_strength',
      'graha_vargottama_amplification_factor',
      'graha_yoga_karaka_flag',
      'graha_yuddha_per_varga',
      'house_strength_classification_rollup',
      'jaimini_tri_deva_role_per_graha',
      'kala_sarpa_per_varga',
      'karaka_bhava_concordance',
      'karaka_house_lord_overlap_flag',
      'karakatva_strength_per_significance',
      'lord_aspects_lord_per_varga',
      'lord_in_house_per_varga',
      'nakshatra_dispositor_chain',
      'net_argala_per_varga',
      'nway_config_per_varga',
      'parivartana_per_varga',
      'pranic_strength_per_graha',
      'sambandha_grade',
      'significator_path',
      'vargottama_per_varga',
      'vimsopaka_bala_per_graha',
      'virupa_drishti',
      'virodha_argala_natal_matrix',
      'yoga_label'
    )
$SQL$,
  target_floor = 106014
WHERE asset_id = 'ga_structural';

-- Step 2: Purge orphan build rows (old D1-only pyjhora_adapter path, now superseded)
DELETE FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND build_id = '22fcef22-3b50-4357-b128-15c445146eec';
