-- Migration 310: L1 Gaṇita Closure — confirmed prod floors (post-migration-309 measurement)
-- ──────────────────────────────────────────────────────────────────────────────────────────
-- Produced by §6 post-merge prod verification (2026-06-18).
-- Per §N.4: target_floor = achieved count after build (floors are aspirational, not gates).
--
-- ga_structural: corrected count_sql (migration 309) measured on prod chart 482012f1.
--   Old floor (conservative, pre-measurement): 74,644
--   Measured count with corrected count_sql:    74,034
--   BUG-1 scope inflation confirmed removed:
--     - 2,835 graha_avastha_%_per_varga rows (owned by ga_condition)
--     - 9,690 strength bala per_varga rows (owned by ga_strength)
--     - 80 nakshatra_pada_sensitive rows (owned by ga_sensitive)
--   Note: floor is below the old conservative value because the corrected count_sql
--   no longer counts the 12,605 rows from other assets.
UPDATE asset_registry
SET
  target_floor = 74034,
  expected_volume_formula = NULL,
  volume_explanation = 'GA8 T1 structural facts — floor 74,034 measured on prod chart 482012f1 with corrected count_sql (migration 309 BUG-1 fix, 2026-06-18). Excludes ga_condition per-varga avasthas + ga_strength bala per_varga + ga_sensitive nakshatra_pada_sensitive rows.'
WHERE asset_id = 'ga_structural';

-- ga_condition: combined floor measured on prod chart 482012f1.
--   ga_condition_composite (D1 avasthas): 45 rows (9 grahas × 5 ayanamshas)
--   chart_facts graha_avastha_%_per_varga (per-varga avasthas): 2,835 rows
--   Total combined: 2,880
--   Note: per-varga count (2,835) is below Amendment-2 estimate (~6,750) because
--   graha_kala_bala_per_varga is FLOORED (NULL values, 735 rows) — these are present
--   but not counted by the combined count_sql (which counts chart_facts avastha rows,
--   not null-valued floor rows). The floor reflects actual countable rows.
UPDATE asset_registry
SET
  target_floor = 2880,
  expected_volume_formula = NULL,
  volume_explanation = 'ga_condition combined: 45 D1 composite rows + 2,835 per-varga avastha chart_facts rows = 2,880 total. Measured on prod chart 482012f1 (2026-06-18). graha_kala_bala_per_varga is floored (NULL fact_value_num, excluded from count).'
WHERE asset_id = 'ga_condition';
