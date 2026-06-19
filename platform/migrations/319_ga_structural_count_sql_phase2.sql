-- Migration 319: Update ga_structural count_sql to cover all Phase-2 depth categories.
--
-- Root cause: count_sql was authored pre-Phase-2 and used LIKE patterns + a Phase-1 IN list.
-- After Phase-2 rebuild (build_id 22fcef22, 2026-06-18) the writer now emits 65 fact_category
-- types across 77,821 rows. The old count_sql returned 73,942 (missed Phase-2 additions +
-- bhava_bala_* + ashtakavarga_anubindu + vimsopaka_bala_per_graha; also wrongly included
-- panchaka_flag/bhadra_flag/eclipse_proximity_natal/chandra_bala_natal_baseline/
-- tara_bala_natal_baseline which belong to other writers).
--
-- New count_sql: explicit IN list of all 65 GA8 categories, derived from the authoritative
-- build_id query (build_id 22fcef22-3b50-4357-b128-15c445146eec = Phase-2 rebuild).
-- Verified to return exactly 77,821 for chart 482012f1.

UPDATE asset_registry
SET count_sql = $SQL$
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
      'house_strength_classification_rollup',
      'jaimini_tri_deva_role_per_graha',
      'kala_sarpa_per_varga',
      'karaka_bhava_concordance',
      'karaka_house_lord_overlap_flag',
      'karakatva_strength_per_significance',
      'lord_aspects_lord_per_varga',
      'lord_in_house_per_varga',
      'nakshatra_dispositor_chain',
      'net_argala',
      'nway_configuration',
      'parivartana_per_varga',
      'pranic_strength_per_graha',
      'sambandha_grade',
      'vargottama_per_varga',
      'vimsopaka_bala_per_graha',
      'virodha_argala_natal_matrix',
      'yoga_label'
    )
$SQL$
WHERE asset_id = 'ga_structural';
