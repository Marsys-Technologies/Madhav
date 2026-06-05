-- Migration 169: asset_throughput
-- Cockpit v2 — per-asset writer throughput (rows/second), measured not assumed.
-- rows_per_second is NULL until first measured build; cockpit shows "estimating..."
-- Applied: 2026-06-06

BEGIN;

CREATE TABLE IF NOT EXISTS asset_throughput (
  asset_id                text PRIMARY KEY REFERENCES asset_registry(asset_id),
  rows_per_second         double precision,         -- NULL until first measurement
  measurement_count       int DEFAULT 0,
  last_measured_at        timestamptz,
  last_measured_build_id  uuid,
  history                 jsonb DEFAULT '[]'::jsonb
);

COMMIT;
