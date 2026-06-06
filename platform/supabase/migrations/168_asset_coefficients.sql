-- Migration 168: asset_coefficients
-- Cockpit v2 — measured ratios between upstream and downstream assets
-- All current_value rows start NULL; first build with both assets lit measures them.
-- Applied: 2026-06-06

BEGIN;

CREATE TABLE IF NOT EXISTS asset_coefficients (
  coefficient_name        text PRIMARY KEY,
  description             text NOT NULL,
  upstream_asset_id       text NOT NULL REFERENCES asset_registry(asset_id),
  downstream_asset_id     text NOT NULL REFERENCES asset_registry(asset_id),
  current_value           double precision,         -- NULL until first measurement
  measurement_count       int DEFAULT 0,
  last_measured_at        timestamptz,
  last_measured_build_id  uuid,
  history                 jsonb DEFAULT '[]'::jsonb,
  created_at              timestamptz DEFAULT now()
);

COMMIT;
