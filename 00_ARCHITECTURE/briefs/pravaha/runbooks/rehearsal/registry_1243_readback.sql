-- Read-only post-apply readback for migration 1243 (steward M20261003T020909-6c15). Run with psql against production AFTER the migration applied.
-- (1) both rows present, with the seed-identical 28 columns: the md5 must equal the value below (derived from the migration's own literals on a copy of production's asset_registry).
SELECT asset_id,
       md5(row(asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql, target_floor,
               expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds, asset_type, layer_name,
               layer_index, provides_apis, health_probe, catalog_status, asset_kind, has_writer, has_substeps, writer_timeout_seconds)::text) AS fingerprint,
       CASE asset_id WHEN 'ka_gochara_v4_41_candidate' THEN 'a0f3e234dff2fdd9e4c9a90897e00e13' WHEN 'ka_gochara_v5' THEN '49995b52b7c416c8e0ef8f43b1158b57' END AS expected_fingerprint,
       is_active, has_writer, depends_on
  FROM asset_registry WHERE asset_id IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5') ORDER BY 1;          -- expect 2 rows, fingerprint = expected_fingerprint, is_active f, has_writer t, depends_on {}
-- (2) the registry row count: 129 before (measured read-only 2026-10-03) -> EXACTLY 131 after, and nothing else added.
SELECT count(*) AS registry_rows FROM asset_registry;                                                         -- expect 131
SELECT count(*) AS rows_with_writer FROM asset_registry WHERE has_writer;                                     -- expect 124 (122 + the two)
-- (3) nothing depends on either row.
SELECT count(*) FROM asset_registry WHERE depends_on && ARRAY['ka_gochara_v4_41_candidate','ka_gochara_v5']::text[];   -- expect 0
