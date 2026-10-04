-- Minimal fixture of the three serving tables, columns/constraints/indexes read from the live database as suvarna_reader
-- on 2026-10-02 (the chart_id / build_id foreign keys to charts / build_runs are omitted: those tables are out of scope).
CREATE TABLE asset_freshness (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
  chart_id uuid,
  scope_key text NOT NULL,
  partition_key text NOT NULL CHECK (btrim(partition_key) <> ''),
  freshness_state text NOT NULL CHECK (freshness_state = ANY (ARRAY['fresh','stale','unknown'])),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(reasons) = 'array'),
  receipt_version text NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, scope_key, partition_key)
);
CREATE TABLE asset_output_digest_specs (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
  spec_sha256 text NOT NULL CHECK (spec_sha256 ~ '^[a-f0-9]{64}$'),
  spec jsonb NOT NULL CHECK (jsonb_typeof(spec) = 'object'),
  reviewed_at timestamptz NOT NULL DEFAULT now(),
  retired_at timestamptz,
  PRIMARY KEY (asset_id, spec_sha256),
  CHECK (retired_at IS NULL OR retired_at >= reviewed_at)
);
CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
CREATE TABLE asset_provenance_receipts (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
  chart_id uuid,
  scope_key text NOT NULL,
  partition_key text NOT NULL CHECK (btrim(partition_key) <> ''),
  receipt_version text NOT NULL,
  code_digest text, config_digest text, upstream_digest text, partition_digest text, output_digest text,
  upstream_receipts jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(upstream_receipts) = 'array'),
  receipt_state text NOT NULL CHECK (receipt_state = ANY (ARRAY['proven','unknown'])),
  unknown_reasons jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(unknown_reasons) = 'array'),
  observed_at timestamptz NOT NULL DEFAULT now(),
  build_id uuid,
  output_digest_spec_sha256 text CHECK (output_digest_spec_sha256 IS NULL OR output_digest_spec_sha256 ~ '^[a-f0-9]{64}$'),
  PRIMARY KEY (asset_id, scope_key, partition_key),
  FOREIGN KEY (asset_id, output_digest_spec_sha256) REFERENCES asset_output_digest_specs(asset_id, spec_sha256) ON DELETE RESTRICT
);
