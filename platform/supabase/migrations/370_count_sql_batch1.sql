-- 368_count_sql_batch1.sql
-- Fix count_sql for ga_panchanga, ga_prashna, bo_samvada, bo_upaya.
--
-- ga_panchanga: existing LIKE 'panchanga%' misses all 5 non-prefixed categories
--               (bhadra_flag, panchaka_flag, eclipse_proximity_natal,
--                tara_bala_natal_baseline, chandra_bala_natal_baseline).
--               Expand filter to include them explicitly.
--
-- ga_prashna:   count_sql only counted ga_prashna_judgment rows; add
--               ga_prashna_lagna to the sum.
--
-- bo_samvada:   writer only creates a view (vw_chart_digest), emits 0 rows.
--               count_sql was wrongly querying bodha_msr_signals (bo_laksana's
--               table). Fix to SELECT 0 AS count.
--
-- bo_upaya:     count_sql summed bodha_rm_dasha_windowed_prescriptions but
--               bo_upaya never writes that table. Remove the phantom summand.

-- ── ga_panchanga ──────────────────────────────────────────────────────────────
UPDATE asset_registry
SET count_sql = $sql$
SELECT count(*) AS count
FROM   chart_facts
WHERE  chart_id = $1
  AND  (
         fact_category LIKE 'panchanga%'
      OR fact_category = 'bhadra_flag'
      OR fact_category = 'panchaka_flag'
      OR fact_category = 'eclipse_proximity_natal'
      OR fact_category = 'tara_bala_natal_baseline'
      OR fact_category = 'chandra_bala_natal_baseline'
       )
$sql$
WHERE asset_id = 'ga_panchanga';

-- ── ga_prashna ────────────────────────────────────────────────────────────────
UPDATE asset_registry
SET count_sql = $sql$
SELECT (
  (SELECT COUNT(*) FROM ga_prashna_lagna    WHERE chart_id = $1) +
  (SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1)
) AS count
$sql$
WHERE asset_id = 'ga_prashna';

-- ── bo_samvada ────────────────────────────────────────────────────────────────
UPDATE asset_registry
SET count_sql = 'SELECT 0 AS count'
WHERE asset_id = 'bo_samvada';

-- ── bo_upaya ──────────────────────────────────────────────────────────────────
UPDATE asset_registry
SET count_sql = $sql$
SELECT (
  (SELECT count(*) FROM bodha_rm_resonances           WHERE chart_id = $1) +
  (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1)
) AS count
$sql$
WHERE asset_id = 'bo_upaya';
