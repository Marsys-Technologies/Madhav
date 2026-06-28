-- Migration 364: Fix count_sql gaps that caused post-clear chart_facts orphans
--
-- Root cause (discovered DB audit 2026-06-29): three assets emit fact_categories /
-- secondary tables that were absent from their count_sql. The clear mechanism derives
-- its DELETE statement from count_sql via deriveDeleteSqlFromCountSql() — so any
-- category missing from count_sql's WHERE clause silently survives a clear, producing
-- orphaned rows that no build can re-own and no registry-aware clear can remove.
--
-- Affected assets and missing coverage:
--   ga_structural — 7 fact_categories confirmed emitted by ga_structural_writer.py
--                   but absent from the count_sql IN() list:
--                   virupa_drishti, yoga_label, dosha_label, conjunction_special_point,
--                   graha_yuddha, combustion_relationship, significator_path
--   ga_nakshatra  — 3 fact_categories emitted by ga_nakshatra writers but missing
--                   from the count_sql IN() list:
--                   nakshatra_lord_relationship, tara_bala, nakshatra_co_tenancy
--   mi_adhilepa   — writes mimamsa_convergence_adjustment + mimamsa_anchor_adjustment
--                   as secondary output tables beyond its registered target_table
--                   (mimamsa_load_bearing). The DELETE completeness for the two
--                   secondary tables is fixed in code (EXPLICIT_CLEAR_OPS in
--                   platform/src/lib/cockpit/assetClearSpec.ts). This migration fixes
--                   the count side so the Cockpit stat includes all three tables.
--
-- For ga_structural + ga_nakshatra: deriveDeleteSqlFromCountSql() converts
--   SELECT count(*) … FROM chart_facts WHERE chart_id=$1 AND (…)
-- into the equivalent DELETE, so extending the WHERE clause here fixes BOTH
-- count accuracy AND clear completeness in one change — no EXPLICIT_CLEAR_OPS
-- entry needed for either asset.
--
-- Idempotent: pure UPDATEs of count_sql.

-- ── ga_structural ─────────────────────────────────────────────────────────────
-- Adds the 7 missing categories to the existing IN() list.
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
        -- Added in migration 364: categories emitted by ga_structural_writer.py
        -- that were missing from the IN() list, causing post-clear orphaned rows
        'virupa_drishti', 'yoga_label', 'dosha_label', 'conjunction_special_point',
        'graha_yuddha', 'combustion_relationship', 'significator_path'
      )
    )
$$
WHERE asset_id = 'ga_structural';

-- ── ga_nakshatra ──────────────────────────────────────────────────────────────
-- Adds nakshatra_lord_relationship, tara_bala, nakshatra_co_tenancy to the IN list.
-- (count_sql had nakshatra_lord_placement but not nakshatra_lord_relationship;
--  graha_tara_bala but not plain tara_bala; nakshatra_cogravity but not nakshatra_co_tenancy)
UPDATE asset_registry
SET count_sql = $$SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (
  'graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement',
  'graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags',
  'nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction',
  'nakshatra_cogravity','graha_tara_bala','nakshatra_statistics',
  'nakshatra_cross_ayanamsha',
  -- Added in migration 364: missing from IN list, causing post-clear orphaned rows
  'nakshatra_lord_relationship','tara_bala','nakshatra_co_tenancy'
)$$
WHERE asset_id = 'ga_nakshatra';

-- ── mi_adhilepa ───────────────────────────────────────────────────────────────
-- Extends count to include the two secondary tables the writer emits beyond
-- mimamsa_load_bearing. DELETE completeness for these tables is handled in code
-- via EXPLICIT_CLEAR_OPS (assetClearSpec.ts).
UPDATE asset_registry
SET count_sql = $$SELECT
  (SELECT count(*) FROM mimamsa_load_bearing           WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_convergence_adjustment WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_anchor_adjustment      WHERE chart_id = $1) AS count$$
WHERE asset_id = 'mi_adhilepa';
