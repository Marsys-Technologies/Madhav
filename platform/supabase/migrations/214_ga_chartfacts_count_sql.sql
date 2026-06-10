-- 214_ga_chartfacts_count_sql.sql
-- =============================================================================
-- Register chart_facts-scoped count_sql on asset_registry for the three
-- chart_facts-backed Gaṇita assets: ga_strength, ga_sensitive, ga_sade_sati.
--
-- WHY: the cockpit stats route (/api/cockpit/stats) reads count_sql from
-- asset_registry (SELECT asset_id, count_sql ... FROM asset_registry), NOT from
-- asset_throughput. Migrations 212/213 placed count_sql on asset_throughput, which
-- the stats route never reads — so these three assets show "NOT MIGRATED" on the
-- cockpit even after a successful build (count_sql is null in asset_registry).
--
-- This migration sets asset_registry.count_sql for the three assets, matching the
-- pattern the working table-backed assets already use (ga_positions/ga_vargas/
-- ga_dashas/ga_panchanga all have a chart-scoped count_sql on asset_registry with
-- a $1 chart_id parameter). The stats route binds $1 to the chart_id at query time.
--
-- Category scoping uses prefix LIKE where a writer owns a category family, so the
-- count stays correct if a writer later adds a sibling category. Authoritative
-- category sets extracted from the GA5/GA8/GA9 writer source at d228aa0f.
--
-- Idempotent (UPDATE by asset_id). Reversible (down-block restores null).
-- =============================================================================

BEGIN;

-- ── ga_strength (GA8/GA3 shadbala + ashtakavarga + bhava_bala + vimsopaka) ────
UPDATE asset_registry
SET count_sql = $$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'graha_shadbala_%'
      OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala')
      OR fact_category LIKE 'graha_vimsopaka_%'
      OR fact_category LIKE 'ashtakavarga_%'
      OR fact_category LIKE 'house_bhava_bala_%'
    )
$$
WHERE asset_id = 'ga_strength';

-- ── ga_sensitive (GA5 esoteric / Tajik / KP / Nadi / Lal Kitab points) ───────
UPDATE asset_registry
SET count_sql = $$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category IN (
        'upagraha_position', 'saturn_derived_point', 'saham_position',
        'karaka_chara_position', 'karakamsa_position', 'swamsa_position',
        'arudha_pada', 'midpoint', 'aprakasha_position',
        'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point'
      )
      OR fact_category LIKE 'esoteric_point_%'
      OR fact_category LIKE 'kp_%'
      OR fact_category LIKE 'tajik_%'
    )
$$
WHERE asset_id = 'ga_sensitive';

-- ── ga_sade_sati (GA9 — explicit 15-category set, copied from migration 213) ──
UPDATE asset_registry
SET count_sql = $$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND fact_category IN (
      'sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter',
      'dhaiya_period', 'kantaka_shani_period', 'ashtama_shani_period',
      'ardha_ashtama_shani_period', 'janma_shani_period',
      'vishakha_shani_period', 'anumukha_shani_period',
      'sade_sati_saturn_retrograde_subset', 'sade_sati_cancellation_check',
      'sade_sati_modifier_overlay', 'sade_sati_concurrent_dasha_overlay',
      'sade_sati_downstream_cross_reference'
    )
$$
WHERE asset_id = 'ga_sade_sati';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — restores the pre-214 null count_sql for all three):
--
-- BEGIN;
-- UPDATE asset_registry SET count_sql = NULL
--   WHERE asset_id IN ('ga_strength', 'ga_sensitive', 'ga_sade_sati');
-- COMMIT;
-- =============================================================================
