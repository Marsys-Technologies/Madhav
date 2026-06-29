-- Migration 368: Fix ga_nakshatra / ga_structural count_sql cross-accounting
--
-- Root cause (scout audit 2026-06-29):
--
--   ga_nakshatra's count_sql (as patched by migration 364) wrongly includes 3
--   categories that are actually written by ga_structural_writer.py's
--   _build_nakshatra_relationship_rows() function (lines 5295–5418):
--     nakshatra_co_tenancy   — source: ga_structural.nakshatra_co_tenancy
--     nakshatra_lord_relationship — source: ga_structural.nakshatra_lord_relationship
--     tara_bala              — source: ga_structural.tara_bala
--   ga_nakshatra_emitters.py emits 'graha_tara_bala' (a different category string),
--   not plain 'tara_bala'. These 3 belong to ga_structural's count boundary.
--
--   ga_structural's count_sql (as patched by migration 364) is still missing all 9
--   categories that ga_structural_writer.py provably emits:
--     ashtakavarga_anubindu          — line 1370
--     graha_saptavargaja_bala_component — line 1185
--     vimsopaka_bala_per_graha       — line 1406
--     parivartana_pairs              — line 2520
--     retrograde_aspect_modification — line 4941
--     nakshatra_co_tenancy           — line 5366
--     tara_bala                      — line 5405
--     nakshatra_lord_relationship    — line 5386
--     bhava_chalit_rasi_divergence   — line 5607
--
-- Fix:
--   1. Remove the 3 misattributed categories from ga_nakshatra's IN() list.
--   2. Add all 9 missing categories to ga_structural's IN() list.
--
-- Effect on clear completeness: deriveDeleteSqlFromCountSql() derives the DELETE
-- WHERE clause directly from count_sql, so this migration simultaneously fixes
-- both count accuracy and orphan-safe clearing for both assets. No EXPLICIT_CLEAR_OPS
-- changes needed for either asset.
--
-- Idempotent: pure UPDATEs; safe to re-apply.

-- ── ga_nakshatra ──────────────────────────────────────────────────────────────
-- Remove the 3 categories that belong to ga_structural.
-- Retains all legitimate ga_nakshatra categories from migration 364.
UPDATE asset_registry
SET count_sql = $$SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (
  'graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement',
  'graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags',
  'nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction',
  'nakshatra_cogravity','graha_tara_bala','nakshatra_statistics',
  'nakshatra_cross_ayanamsha'
)$$
WHERE asset_id = 'ga_nakshatra';

-- ── ga_structural ─────────────────────────────────────────────────────────────
-- Add all 9 categories confirmed emitted by ga_structural_writer.py that were
-- absent from the IN() list after migration 364.
UPDATE asset_registry
SET count_sql = $$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'aspect_%'
      OR (fact_category LIKE 'graha_avastha_%' AND fact_category NOT LIKE '%_per_varga')
      OR fact_category LIKE '%argala_natal_matrix'
      OR fact_category LIKE 'graha_dispositor_%'
      OR (
        fact_category LIKE '%_per_varga'
        AND fact_category NOT IN (
          'graha_avastha_baladi_per_varga',
          'graha_avastha_deeptaadi_per_varga',
          'graha_avastha_jagradadi_per_varga',
          'graha_avastha_sayanadi_per_varga',
          'graha_avastha_lajjitadi_per_varga',
          'ashtakavarga_bindu_per_varga',
          'ashtakavarga_pinda_sarva_per_varga',
          'graha_sthana_bala_per_varga',
          'graha_drik_bala_per_varga',
          'graha_kala_bala_per_varga',
          'graha_cheshta_bala_per_varga'
        )
      )
      OR fact_category IN (
        'graha_functional_class_per_ascendant',
        'graha_composite_state_classification', 'graha_effective_dignity_modified_by_aspects',
        'graha_in_house_composite_strength', 'graha_special_state_rollup',
        'graha_tri_deva_role_strength', 'graha_vargottama_amplification_factor',
        'graha_yoga_karaka_flag', 'jaimini_tri_deva_role_per_graha',
        'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
        'composite_dispositor_strength', 'house_strength_classification_rollup',
        'pranic_strength_per_graha', 'chandra_bala_natal_baseline', 'tara_bala_natal_baseline',
        'yoga_fires', 'dosha_fires', 'conjunction_within_orb',
        'panchaka_flag', 'bhadra_flag', 'eclipse_proximity_natal',
        'sambandha_grade', 'nakshatra_dispositor_chain', 'dispositor_tree',
        'bhava_significance_link', 'karaka_bhava_concordance', 'net_argala',
        'nway_configuration', 'chart_center_of_gravity', 'graha_centrality',
        'dispositor_cycle', 'chart_cluster', 'varga_provenance_meta',
        'convergence_count', 'contradiction_pair',
        -- Added in migration 364: first batch of missing categories
        'virupa_drishti', 'yoga_label', 'dosha_label', 'conjunction_special_point',
        'graha_yuddha', 'combustion_relationship', 'significator_path',
        -- Added in migration 368: 9 categories confirmed emitted by ga_structural_writer.py
        -- but absent from the IN() list after migration 364
        'ashtakavarga_anubindu',
        'graha_saptavargaja_bala_component',
        'vimsopaka_bala_per_graha',
        'parivartana_pairs',
        'retrograde_aspect_modification',
        'nakshatra_co_tenancy',
        'tara_bala',
        'nakshatra_lord_relationship',
        'bhava_chalit_rasi_divergence'
      )
    )
$$
WHERE asset_id = 'ga_structural';
