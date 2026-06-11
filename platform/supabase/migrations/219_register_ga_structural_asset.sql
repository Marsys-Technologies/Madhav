-- 219_register_ga_structural_asset.sql
-- =============================================================================
-- Register the `ga_structural` cockpit tile (Gaṇita layer).
--
-- WHY: the GA8 (T1 structural) writer emits ~6,075 rows/build into `chart_facts`
-- — aspects, yogas, doshas, avasthas, argala/virodha-argala, dispositor chains,
-- composite states, karaka/tri-deva roles, and base graha facts — but no cockpit
-- asset claimed those categories, so they were built-but-invisible and the Gaṇita
-- layer header undercounted by ~6k. The five chart_facts-backed tiles
-- (ga_strength, ga_sensitive, ga_sade_sati, ga_panchanga, ga_structural) now
-- partition chart_facts exactly: 2,184 + 8,055 + 11,019 + 221 + 6,075 = 27,554
-- (verified against canonical build 9dac88d5 of chart 482012f1).
--
-- The count_sql is a positive family filter (aspect_%, graha_avastha_%,
-- %argala_natal_matrix, graha_dispositor_%, + the explicit GA8 structural /
-- base-graha categories). It was verified to equal the untiled-complement count
-- exactly (6,075), so it captures the full structural remainder with no overlap
-- against the other four chart_facts tiles.
--
-- Idempotent: INSERT ... ON CONFLICT (asset_id) DO UPDATE. Reversible (DOWN
-- deletes the asset).
-- =============================================================================

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
  storage_type, target_table, count_sql, size_sql, target_floor,
  expected_volume_formula, expected_volume_inputs, volume_explanation,
  depends_on, scope, is_active, asset_type, layer_name, layer_index, catalog_status
) VALUES (
  'ga_structural', 'ganita', 9, 'Saṃracanā', 'Structural facts',
  'GA8 T1 structural layer: aspects (Parāśarī + Jaimini + Tājik), yogas, doshas, graha avasthās, argala/virodha-argala, dispositor chains, composite states, kāraka and tri-deva roles, and base graha facts — per ayanamsha.',
  'postgres_table', NULL,
  $count$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'aspect_%'
      OR fact_category LIKE 'graha_avastha_%'
      OR fact_category LIKE '%argala_natal_matrix'
      OR fact_category LIKE 'graha_dispositor_%'
      OR fact_category IN (
        'graha_position', 'graha_sign_attributes', 'graha_functional_class_per_ascendant',
        'graha_composite_state_classification', 'graha_effective_dignity_modified_by_aspects',
        'graha_in_house_composite_strength', 'graha_special_state_rollup',
        'graha_tri_deva_role_strength', 'graha_vargottama_amplification_factor',
        'graha_yoga_karaka_flag', 'jaimini_tri_deva_role_per_graha',
        'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
        'composite_dispositor_strength', 'house_strength_classification_rollup',
        'pranic_strength_per_graha', 'chandra_bala_natal_baseline', 'tara_bala_natal_baseline',
        'nakshatra_pada_sensitive', 'yoga_fires', 'dosha_fires', 'conjunction_within_orb',
        'panchaka_flag', 'bhadra_flag', 'eclipse_proximity_natal'
      )
    )
  $count$,
  NULL, NULL,
  'GA8_STRUCTURAL_CATEGORIES * AYANAMSHAS',
  NULL,
  'GA8 T1 structural facts (aspects/yogas/doshas/avasthās/argala/dispositors/composite-states/base-graha) across the chart_facts category families — partitions chart_facts together with the strength/sensitive/sade_sati/panchanga tiles.',
  ARRAY[]::text[], 'per_chart', true, 'data', 'Gaṇita', 'L1', 'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
  layer = EXCLUDED.layer,
  sort_order = EXCLUDED.sort_order,
  sanskrit_name = EXCLUDED.sanskrit_name,
  english_name = EXCLUDED.english_name,
  english_description = EXCLUDED.english_description,
  storage_type = EXCLUDED.storage_type,
  target_table = EXCLUDED.target_table,
  count_sql = EXCLUDED.count_sql,
  size_sql = EXCLUDED.size_sql,
  expected_volume_formula = EXCLUDED.expected_volume_formula,
  volume_explanation = EXCLUDED.volume_explanation,
  scope = EXCLUDED.scope,
  is_active = EXCLUDED.is_active,
  asset_type = EXCLUDED.asset_type,
  layer_name = EXCLUDED.layer_name,
  layer_index = EXCLUDED.layer_index,
  catalog_status = EXCLUDED.catalog_status;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ga_structural';
--   COMMIT;
-- =============================================================================
