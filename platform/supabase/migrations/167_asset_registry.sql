-- Migration 167: asset_registry
-- Cockpit v2 — authoritative per-asset metadata catalog (39 assets, 6 layers)
-- Applied: 2026-06-06

BEGIN;

CREATE TABLE IF NOT EXISTS asset_registry (
  asset_id                text PRIMARY KEY,
  layer                   text NOT NULL CHECK (layer IN ('brahmagyan','ganita','bodha','kala','phala','mimamsa')),
  sort_order              int NOT NULL,
  sanskrit_name           text NOT NULL,
  english_name            text NOT NULL,
  english_description     text NOT NULL,
  storage_type            text NOT NULL CHECK (storage_type IN ('postgres_table','pgvector','postgres_view','gcs_jsonl','bigquery','tool_only')),
  target_table            text,
  count_sql               text,
  size_sql                text,
  target_floor            int,
  expected_volume_formula text,
  expected_volume_inputs  jsonb,
  volume_explanation      text,
  depends_on              text[] DEFAULT ARRAY[]::text[],
  scope                   text NOT NULL CHECK (scope IN ('global','per_chart')),
  is_active               boolean DEFAULT true,
  estimated_seconds       int,
  created_at              timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_asset_registry_layer ON asset_registry(layer, sort_order);

COMMIT;
