-- SYNTHETIC OFFLINE FIXTURE, not a production registry census or monitor receipt.
-- Column types: supabase/167_asset_registry.sql, 202 (service metadata),
-- 223 (substeps), 242 (kind), 342 (writer), 417 (timeout). Only Kala placeholders.
SET ROLE amjis_app;
CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY, layer text, sort_order int, sanskrit_name text,
  english_name text, english_description text, storage_type text, target_table text,
  count_sql text, size_sql text, target_floor int, expected_volume_formula text,
  expected_volume_inputs jsonb, volume_explanation text, depends_on text[], scope text,
  is_active boolean, estimated_seconds int, asset_type text, layer_name text,
  layer_index text, provides_apis jsonb, health_probe jsonb, catalog_status text,
  asset_kind text, has_writer boolean, has_substeps boolean, writer_timeout_seconds int
);
INSERT INTO asset_registry (asset_id, layer, has_writer, is_active, depends_on)
SELECT 'fixture_kala_' || i, 'kala', i <= 122, false, '{}'::text[]
FROM generate_series(1,129) i;
CREATE TABLE asset_provenance_receipts (asset_id text);
CREATE TABLE build_run_assets (asset_id text);
CREATE TABLE asset_throughput (asset_id text);
CREATE TABLE nirmana_elevation_monitor_observations (observed_at timestamptz, status text);
INSERT INTO nirmana_elevation_monitor_observations VALUES
  ('2000-01-01T00:00:00Z', 'source_unavailable'),
  ('2000-01-02T00:00:00Z', 'source_unavailable');
