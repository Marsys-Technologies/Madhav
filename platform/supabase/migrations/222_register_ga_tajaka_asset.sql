-- 222_register_ga_tajaka_asset.sql
-- =============================================================================
-- Activate the `ga_tajaka` (Tājaka / Vārṣaphal) cockpit tile — the ONE
-- deliberately-parked L1 asset (was is_active=false, target_table=null, no
-- writer). The GA-Tajaka writer (ga_tajaka_writer.py) now precomputes the A7
-- hybrid window (past → present+5 years) × 5 ayanamshas into the dedicated
-- `l1_tajik_varsha_year_lords` table (created in migration 221).
--
-- Flips: is_active=true, target_table, count_sql, and target_floor = achieved
-- canonical count for chart 482012f1 (per the floors=achieved-count rule used
-- for the other 8 ga_* assets in migration 220).
--
-- count_sql is the simple per-chart row count (one row per varsha × ayanamsha).
-- Idempotent (ON CONFLICT (asset_id) DO UPDATE). Reversible DOWN block below.
-- [verify-against: prod]
-- =============================================================================

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
  storage_type, target_table, count_sql, size_sql, target_floor,
  expected_volume_formula, expected_volume_inputs, volume_explanation,
  depends_on, scope, is_active, asset_type, layer_name, layer_index, catalog_status
) VALUES (
  'ga_tajaka', 'ganita', 8, 'Tājaka', 'Tajaka Varshaphal',
  'Vārṣaphal annual chart per varsha (solar-return year): Muntha position, Vārṣeśa (year-lord) by tajik_classical + panchavargiya methods with candidate scoring, and the Tājik yogas firing in each annual chart — A7 hybrid storage (past→present+5 precomputed; rest on-demand), per ayanamsha.',
  'postgres_table', 'l1_tajik_varsha_year_lords',
  'SELECT count(*) AS count FROM l1_tajik_varsha_year_lords WHERE chart_id = $1',
  NULL, 240,
  'WINDOW_VARSHAS * AYANAMSHAS',
  NULL,
  'target_floor = 240 = achieved canonical count for chart 482012f1 (2026-06-11): the A7 hybrid window varsha 1..48 (birth 1984 → present+5 ≈ 2031) × 5 ayanamshas. Storage is hybrid — varshas outside the precomputed window are computed on-demand by the retrieval tool via ga_tajaka_writer.compute_varsha().',
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
  target_floor = EXCLUDED.target_floor,
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
-- DOWN (manual rollback — re-park the asset):
--   BEGIN;
--   UPDATE asset_registry SET is_active = false, target_table = NULL,
--     count_sql = NULL, target_floor = NULL WHERE asset_id = 'ga_tajaka';
--   COMMIT;
-- =============================================================================
