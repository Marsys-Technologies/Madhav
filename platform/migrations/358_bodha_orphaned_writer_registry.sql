-- Migration 358: register the 4 orphaned Bodha tables as active assets with writers
-- These tables were created in migration 325 but had no @register writers.
-- Writers are created in this PR (A7 Wave 1 remediation).

-- bo_chart_gestalt: per-chart gestalt pointer synthesis (thin writer; no verdicts stored)
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, scope, has_writer, target_floor, count_sql, created_at)
VALUES (
  'bo_chart_gestalt', 'bodha', 90,
  'bo_chart_gestalt', 'Chart Gestalt',
  'Per-chart gestalt: defining threads, central dynamics, domain verdict map, zoom spine — pointer-only, no verdicts stored',
  'postgres_table', 'per_chart', true, 1,
  'SELECT count(*) FROM bodha_chart_gestalt WHERE chart_id = $1',
  NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET
  has_writer = true, target_floor = EXCLUDED.target_floor,
  count_sql = EXCLUDED.count_sql;

-- bo_cdlm_summary: cross-domain linkage strength summary
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, scope, has_writer, target_floor, count_sql, created_at)
VALUES (
  'bo_cdlm_summary', 'bodha', 91,
  'bo_cdlm_summary', 'CDLM Summary',
  'Per-chart cross-domain linkage strength summary aggregated from bodha_cdlm_cells',
  'postgres_table', 'per_chart', true, 1,
  'SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1',
  NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET has_writer = true, target_floor = EXCLUDED.target_floor,
  count_sql = EXCLUDED.count_sql;

-- bo_cgm_motifs: CGM graph structural motifs
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, scope, has_writer, target_floor, count_sql, created_at)
VALUES (
  'bo_cgm_motifs', 'bodha', 92,
  'bo_cgm_motifs', 'CGM Motifs',
  'Recurring structural patterns detected over the CGM graph: mutual reception, stellium, parivartana chains',
  'postgres_table', 'per_chart', true, 3,
  'SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1',
  NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET has_writer = true, target_floor = EXCLUDED.target_floor,
  count_sql = EXCLUDED.count_sql;

-- bo_cgm_paths: dispositor chain and path analysis
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, scope, has_writer, target_floor, count_sql, created_at)
VALUES (
  'bo_cgm_paths', 'bodha', 93,
  'bo_cgm_paths', 'CGM Paths',
  'Dispositor chain paths and structural path analysis over CGM graph',
  'postgres_table', 'per_chart', true, 9,
  'SELECT count(*) FROM bodha_cgm_paths WHERE chart_id = $1',
  NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET has_writer = true, target_floor = EXCLUDED.target_floor,
  count_sql = EXCLUDED.count_sql;
