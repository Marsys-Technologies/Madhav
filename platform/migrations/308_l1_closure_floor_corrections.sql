-- Migration 308: L1 Gaṇita closure floor corrections
-- Produced by L1 Gaṇita Closure Pass Phase 2 (2026-06-18).
-- Per §N.4: target_floor = achieved count after production build (floors are aspirational, not gates).

-- ga_structural: floor bumped to 87,169 (post all-30-vargas + argala-per-varga expansion,
-- confirmed prod count for chart 482012f1 at L1 closure audit).
-- Previous value 74,644 was the post-all-30-vargas floor before argala-per-varga ran.
UPDATE asset_registry
SET
  target_floor = 87169,
  count_sql = '
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE ''aspect_%''
      OR fact_category LIKE ''graha_avastha_%''
      OR fact_category LIKE ''%argala_natal_matrix''
      OR fact_category LIKE ''graha_dispositor_%''
      OR fact_category LIKE ''%_per_varga''
      OR fact_category IN (
        ''graha_functional_class_per_ascendant'',
        ''graha_composite_state_classification'', ''graha_effective_dignity_modified_by_aspects'',
        ''graha_in_house_composite_strength'', ''graha_special_state_rollup'',
        ''graha_tri_deva_role_strength'', ''graha_vargottama_amplification_factor'',
        ''graha_yoga_karaka_flag'', ''jaimini_tri_deva_role_per_graha'',
        ''karaka_house_lord_overlap_flag'', ''karakatva_strength_per_significance'',
        ''composite_dispositor_strength'', ''house_strength_classification_rollup'',
        ''pranic_strength_per_graha'', ''chandra_bala_natal_baseline'', ''tara_bala_natal_baseline'',
        ''nakshatra_pada_sensitive'', ''yoga_fires'', ''dosha_fires'', ''conjunction_within_orb'',
        ''panchaka_flag'', ''bhadra_flag'', ''eclipse_proximity_natal''
      )
    )
'
WHERE asset_id = 'ga_structural';

-- ga_yoga: floor corrected to 5 (only Yuga Nabhasa yoga fires for chart 482012f1 —
-- this is a deterministically correct 0-row result for most nabhasa categories;
-- target_floor = actual build result, not a generic estimate).
-- Previous floor 50 was a generic pre-build estimate.
UPDATE asset_registry
SET target_floor = 5
WHERE asset_id = 'ga_yoga';
