-- Migration 324: Update ga_structural count_sql + target_floor after Phase-3 gate fix.
--
-- Context: Phase-3 blind-spot gate — two empty categories diagnosed and fixed:
--   Category 1 (nakshatra_relationship double bug):
--     Bug 1: _build_nakshatra_relationship_rows queried 'nakshatra' key from
--             graha_nakshatra_join, which has no such key. Nakshatra names live
--             in graha_position (fact_key='nakshatra'). Fixed to query graha_position
--             for names (same pattern as GAP-4 nakshatra_dispositor_chain).
--     Bug 2: Constituent refs passed via constituent_facts_array= parameter to
--             _base_row — silently dropped at INSERT (column does not exist in
--             chart_facts). Fixed: refs moved to fact_value_jsonb['constituent_fact_ids'].
--     Result: nakshatra_lord_relationship (45 rows), tara_bala (43 rows),
--             nakshatra_co_tenancy (1 row — Mars & Saturn co-tenant in Vishakha,
--             surya_siddhanta_classical only).
--   Category 2 (bhava_chalit_divergence unknown root cause):
--     Root cause: 'bhava_chalit_house' fact_category was never written by any GA
--     writer. Original builder queried a non-existent upstream category → 0 rows.
--     Fixed: replaced DB query with inline equal-bhava (Sripati) computation from
--     chart_output ascendant longitude + planet longitudes. After fix, builder
--     ran and found 0 divergences for chart 482012f1 — CASE (c): no planet falls
--     near a sign boundary that crosses an equal-bhava cusp for this chart.
--     bhava_chalit_rasi_divergence is legitimately 0 for chart 482012f1 and is
--     NOT added to count_sql (0-row category omitted from floor).
--
-- New build_id: a712b250-7a1c-4932-a03c-d1dfcf03d743
-- Achieved: 106,103 rows across 5 ayanamshas (72 categories: 69 prior + 3 new).
-- Old build_id to purge: 5d11969e-31d9-4693-bc11-8b17cff48f5a.

-- Step 1: Update count_sql — add 3 new nakshatra relationship categories (72 total)
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
      'nakshatra_co_tenancy',
      'nakshatra_dispositor_chain',
      'nakshatra_lord_relationship',
      'net_argala_per_varga',
      'nway_config_per_varga',
      'parivartana_per_varga',
      'pranic_strength_per_graha',
      'sambandha_grade',
      'significator_path',
      'tara_bala',
      'vargottama_per_varga',
      'vimsopaka_bala_per_graha',
      'virupa_drishti',
      'virodha_argala_natal_matrix',
      'yoga_label'
    )
$SQL$,
  target_floor = 106103
WHERE asset_id = 'ga_structural';

-- Step 2: Purge prior build rows (build 5d11969e superseded by a712b250)
DELETE FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND build_id = '5d11969e-31d9-4693-bc11-8b17cff48f5a';
