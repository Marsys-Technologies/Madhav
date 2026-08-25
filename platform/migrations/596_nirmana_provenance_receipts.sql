-- NIRMANA F0 Lane B: durable, sidecar-owned build provenance receipts.
--
-- A receipt is keyed by the canonical asset_id, its execution scope, and the
-- declared natural-key partition.  It is deliberately separate from
-- asset_throughput: throughput is operational progress, while a receipt is the
-- evidence required to call that progress fresh.  NULL component digests are
-- never promoted to fresh; they are represented as receipt_state='unknown'.

BEGIN;

CREATE TABLE IF NOT EXISTS asset_provenance_receipts (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
  chart_id uuid NULL REFERENCES charts(id) ON DELETE CASCADE,
  scope_key text GENERATED ALWAYS AS (COALESCE(chart_id::text, '__global__')) STORED,
  partition_key text NOT NULL,
  receipt_version text NOT NULL,
  code_digest text NULL,
  config_digest text NULL,
  upstream_digest text NULL,
  partition_digest text NULL,
  output_digest text NULL,
  upstream_receipts jsonb NOT NULL DEFAULT '[]'::jsonb,
  receipt_state text NOT NULL CHECK (receipt_state IN ('proven', 'unknown')),
  unknown_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  observed_at timestamptz NOT NULL DEFAULT now(),
  build_id uuid NULL REFERENCES build_runs(id) ON DELETE SET NULL,
  PRIMARY KEY (asset_id, scope_key, partition_key),
  CHECK (btrim(partition_key) <> ''),
  CHECK (jsonb_typeof(upstream_receipts) = 'array'),
  CHECK (jsonb_typeof(unknown_reasons) = 'array')
);

CREATE INDEX IF NOT EXISTS asset_provenance_receipts_scope_idx
  ON asset_provenance_receipts (chart_id, asset_id);

CREATE TABLE IF NOT EXISTS asset_freshness (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
  chart_id uuid NULL REFERENCES charts(id) ON DELETE CASCADE,
  scope_key text GENERATED ALWAYS AS (COALESCE(chart_id::text, '__global__')) STORED,
  partition_key text NOT NULL,
  freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  receipt_version text NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, scope_key, partition_key),
  CHECK (btrim(partition_key) <> ''),
  CHECK (jsonb_typeof(reasons) = 'array')
);

CREATE INDEX IF NOT EXISTS asset_freshness_scope_state_idx
  ON asset_freshness (chart_id, freshness_state, asset_id);

COMMENT ON TABLE asset_provenance_receipts IS
  'Nirmana versioned receipt of exact code/config/upstream/partition/output dimensions. Unknown is explicit, never fresh-by-default.';
COMMENT ON TABLE asset_freshness IS
  'Nirmana sidecar reconciliation result. Planner reads this projection; planner requests do not mutate it.';

COMMIT;
