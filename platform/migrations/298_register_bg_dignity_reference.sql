-- FIX 5 (P3-A): Register bg_dignity_reference in asset_registry + seed throughput record
-- Tables exist with data: bg_dignity_reference(9) + bg_avastha_schemes(35) +
--   bg_combustion_orbs(8) + bg_graha_naisargika_friendship(72) + bg_motion_state_thresholds(27) = 151 rows
-- Migration 250_bg_dignity_reference.sql created the tables; this migration registers the asset.

INSERT INTO asset_registry (
  asset_id, layer, sort_order, catalog_status, is_active, scope, asset_type,
  sanskrit_name, english_name, english_description,
  storage_type, target_table, depends_on, count_sql, target_floor
)
VALUES (
  'bg_dignity_reference',
  'brahmagyan',
  66,
  'CURRENT',
  true,
  'global',
  'data',
  'Graha-avasthā',
  'Planetary Dignity & State Reference',
  'Planetary dignity and state reference: exaltation/debilitation/own-sign boundaries, naisargika friendship matrix, avastha schemes, combustion orbs, motion state thresholds. 5 sub-tables, 151 total rows.',
  'postgres_table',
  'bg_dignity_reference',
  ARRAY[]::text[],
  'SELECT (SELECT COUNT(*) FROM bg_dignity_reference) + (SELECT COUNT(*) FROM bg_avastha_schemes) + (SELECT COUNT(*) FROM bg_combustion_orbs) + (SELECT COUNT(*) FROM bg_graha_naisargika_friendship) + (SELECT COUNT(*) FROM bg_motion_state_thresholds) AS count',
  151
)
ON CONFLICT (asset_id) DO UPDATE
  SET catalog_status = 'CURRENT',
      is_active = true,
      target_floor = 151,
      count_sql = EXCLUDED.count_sql;

-- Seed global throughput record (chart_id IS NULL = global asset)
-- Unique constraint: asset_throughput_global_idx UNIQUE (asset_id) WHERE chart_id IS NULL
INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_dignity_reference', NULL, 'lit', 151, 151, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 151, expected_rows = 151, last_built_at = NOW();
