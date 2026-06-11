-- 217_ga_count_sql_reconcile.sql
-- =============================================================================
-- Reconcile asset_registry.count_sql + target_table for the Gaṇita assets whose
-- registered count target diverged from where the L1 build writers actually
-- write. Diagnosed live against prod (chart 482012f1, canonical build 9dac88d5)
-- on 2026-06-11. The cockpit stats route (/api/cockpit/stats) reads count_sql
-- from asset_registry and binds $1 = chart_id; a wrong table / wrong category
-- filter makes a fully-built asset read as 0 ("dormant") on the cockpit.
--
-- Corrections (verified against the canonical build):
--
--   ga_dashas    — WRONG TABLE. count_sql targeted `ganita_dashas` (0 rows; the
--                  table is empty). The ga_dashas writer (GA7) writes to
--                  `chart_dashas` (536,471 rows/build). Repoint table + count_sql.
--
--   ga_panchanga — WRONG TABLE. count_sql targeted `chart_panchanga` (0 rows;
--                  empty table). The ga_panchanga writer (GA4) writes panchanga
--                  facts to `chart_facts` under the `panchanga_*` category family
--                  (221 rows/build). Repoint to chart_facts with a prefix LIKE.
--
--   ga_strength  — CATEGORY GAP. The migration-214 count_sql documents the
--                  intended families as "shadbala + ashtakavarga + bhava_bala +
--                  vimsopaka" but the filter only matched `house_bhava_bala_%`
--                  and `graha_vimsopaka_%` — missing the `bhava_bala_*` family
--                  (420 rows), `vimsopaka_bala_per_graha` (35), and
--                  `graha_saptavargaja_bala_component` (35). Broaden to the full
--                  documented family via `%bhava_bala%` / `%vimsopaka%`. No other
--                  asset owns these categories (there is no ga_structural tile),
--                  so broadening cannot double-count.
--
-- ga_sensitive / ga_sade_sati count_sql are left unchanged: their migration-214
-- category lists already match the writers' real categories (verified non-zero
-- against the canonical build). Their prior cockpit "0" reflected pre-214 state.
--
-- Idempotent (UPDATE by asset_id). Reversible (DOWN block restores prior values).
-- Stale multi-build accumulation in chart_facts/chart_dashas is handled as a
-- separate one-off data cleanup (keep canonical build only), not in this DDL.
-- =============================================================================

BEGIN;

-- ── ga_dashas: ganita_dashas (empty) → chart_dashas (GA7 writer target) ───────
UPDATE asset_registry
SET target_table = 'chart_dashas',
    count_sql    = 'SELECT count(*) FROM chart_dashas WHERE chart_id = $1'
WHERE asset_id = 'ga_dashas';

-- ── ga_panchanga: chart_panchanga (empty) → chart_facts panchanga_* family ────
UPDATE asset_registry
SET target_table = 'chart_facts',
    count_sql    = $$SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND fact_category LIKE 'panchanga%'$$
WHERE asset_id = 'ga_panchanga';

-- ── ga_strength: complete the documented family (add bhava_bala_* + vimsopaka_bala + saptavargaja) ──
UPDATE asset_registry
SET count_sql = $$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'graha_shadbala_%'
      OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala')
      OR fact_category LIKE '%vimsopaka%'
      OR fact_category LIKE 'ashtakavarga_%'
      OR fact_category LIKE '%bhava_bala%'
      OR fact_category = 'graha_saptavargaja_bala_component'
    )
$$
WHERE asset_id = 'ga_strength';

-- ── Activate the three built-but-inactive chart_facts-backed assets ───────────
-- The cockpit stats route loads `WHERE is_active = true`, so these assets did not
-- appear on the cockpit AT ALL (not "showing 0") even though the L1 build writes
-- their data. They were registered is_active=false as "planned, not yet built";
-- the canonical build now populates them, so activate them. ga_tajaka is left
-- inactive — it has no writer output, no count_sql, and no target_table.
UPDATE asset_registry
SET is_active = true
WHERE asset_id IN ('ga_strength', 'ga_sensitive', 'ga_sade_sati');

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — restores the pre-217 count_sql/target_table):
--
-- BEGIN;
-- UPDATE asset_registry
--   SET target_table = 'ganita_dashas',
--       count_sql    = 'SELECT count(*) FROM ganita_dashas WHERE chart_id = $1'
--   WHERE asset_id = 'ga_dashas';
-- UPDATE asset_registry
--   SET target_table = 'chart_panchanga',
--       count_sql    = 'SELECT count(*) FROM chart_panchanga WHERE chart_id = $1'
--   WHERE asset_id = 'ga_panchanga';
-- UPDATE asset_registry
--   SET count_sql = $$
--   SELECT count(*) AS count FROM chart_facts
--   WHERE chart_id = $1
--     AND (
--       fact_category LIKE 'graha_shadbala_%'
--       OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala')
--       OR fact_category LIKE 'graha_vimsopaka_%'
--       OR fact_category LIKE 'ashtakavarga_%'
--       OR fact_category LIKE 'house_bhava_bala_%'
--     )
-- $$
--   WHERE asset_id = 'ga_strength';
-- UPDATE asset_registry SET is_active = false
--   WHERE asset_id IN ('ga_strength', 'ga_sensitive', 'ga_sade_sati');
-- COMMIT;
-- =============================================================================
