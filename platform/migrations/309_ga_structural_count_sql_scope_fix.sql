-- Migration 309: Fix ga_structural count_sql post-enrichment scope inflation (BUG-1)
-- ─────────────────────────────────────────────────────────────────────────────
-- Root cause (L1 Closure Synergy Register BUG-1, 2026-06-18):
-- The enrichment (L1 Enrichment Amendments v2.0, migration 307) added per-varga
-- categories to two other assets:
--   ga_condition: graha_avastha_{baladi,deeptaadi,jagradadi,sayanadi,lajjitadi}_per_varga
--   ga_strength:  {ashtakavarga,graha_sthana,graha_drik,graha_kala,graha_cheshta}_bala_per_varga
--
-- ga_structural count_sql previously had two broad LIKE patterns that now sweep those rows:
--   1. fact_category LIKE 'graha_avastha_%'  → also matches per_varga avastha from ga_condition
--   2. fact_category LIKE '%_per_varga'       → also matches bala/avastha per_varga from other assets
--
-- In addition, 'nakshatra_pada_sensitive' was present in ga_structural's IN list, but
-- those rows are written by ga_sensitive_writer (ga_sensitive owns them; correctly counted
-- by ga_sensitive.count_sql since migration 307). ga_structural should not count them.
--
-- Fix: narrow the two LIKE patterns with explicit NOT IN / NOT LIKE exclusions;
-- remove nakshatra_pada_sensitive from ga_structural's IN list.
-- Per §N.4: target_floor reset to conservative 74644 (pre-argala-per-varga lower bound)
-- until a prod build with the corrected count_sql confirms the exact new count.
-- ─────────────────────────────────────────────────────────────────────────────

UPDATE asset_registry
SET
  target_floor = 74644,
  count_sql = '
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE ''aspect_%''
      OR (fact_category LIKE ''graha_avastha_%'' AND fact_category NOT LIKE ''%_per_varga'')
      OR fact_category LIKE ''%argala_natal_matrix''
      OR fact_category LIKE ''graha_dispositor_%''
      OR (
        fact_category LIKE ''%_per_varga''
        AND fact_category NOT IN (
          ''graha_avastha_baladi_per_varga'',
          ''graha_avastha_deeptaadi_per_varga'',
          ''graha_avastha_jagradadi_per_varga'',
          ''graha_avastha_sayanadi_per_varga'',
          ''graha_avastha_lajjitadi_per_varga'',
          ''ashtakavarga_bindu_per_varga'',
          ''ashtakavarga_pinda_sarva_per_varga'',
          ''graha_sthana_bala_per_varga'',
          ''graha_drik_bala_per_varga'',
          ''graha_kala_bala_per_varga'',
          ''graha_cheshta_bala_per_varga''
        )
      )
      OR fact_category IN (
        ''graha_functional_class_per_ascendant'',
        ''graha_composite_state_classification'',
        ''graha_effective_dignity_modified_by_aspects'',
        ''graha_in_house_composite_strength'',
        ''graha_special_state_rollup'',
        ''graha_tri_deva_role_strength'',
        ''graha_vargottama_amplification_factor'',
        ''graha_yoga_karaka_flag'',
        ''jaimini_tri_deva_role_per_graha'',
        ''karaka_house_lord_overlap_flag'',
        ''karakatva_strength_per_significance'',
        ''composite_dispositor_strength'',
        ''house_strength_classification_rollup'',
        ''pranic_strength_per_graha'',
        ''chandra_bala_natal_baseline'',
        ''tara_bala_natal_baseline'',
        ''yoga_fires'',
        ''dosha_fires'',
        ''conjunction_within_orb'',
        ''panchaka_flag'',
        ''bhadra_flag'',
        ''eclipse_proximity_natal''
      )
    )
'
WHERE asset_id = 'ga_structural';
-- After prod build, run the corrected count_sql for chart 482012f1 and update
-- target_floor to the confirmed value (expected ~76,500 ± 500).
