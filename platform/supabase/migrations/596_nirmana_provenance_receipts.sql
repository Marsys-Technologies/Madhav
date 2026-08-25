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

-- Configuration changes invalidate the projection without replacing the last
-- successful receipt.  The next governed build is the only operation allowed
-- to establish a new fresh receipt.
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE
           WHEN reasons ? 'registry_changed' THEN reasons
           ELSE reasons || '["registry_changed"]'::jsonb
         END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS nirmana_registry_receipt_invalidation ON asset_registry;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
  integrity_check_sql, target_floor, asset_kind, asset_type, scope,
  has_writer, is_active, target_table
ON asset_registry
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION nirmana_invalidate_registry_receipts();

CREATE OR REPLACE FUNCTION nirmana_invalidate_chart_receipts()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE
           WHEN reasons ? 'chart_inputs_changed' THEN reasons
           ELSE reasons || '["chart_inputs_changed"]'::jsonb
         END,
         observed_at = now()
   WHERE chart_id = NEW.id;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS nirmana_chart_receipt_invalidation ON charts;
CREATE TRIGGER nirmana_chart_receipt_invalidation
AFTER UPDATE OF birth_date, birth_time, birth_lat, birth_lng, birth_place,
  timezone_id, name, subject_name, preferred_name
ON charts
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION nirmana_invalidate_chart_receipts();

COMMENT ON TABLE asset_provenance_receipts IS
  'Nirmana versioned receipt of exact code/config/upstream/partition/output dimensions. Unknown is explicit, never fresh-by-default.';
COMMENT ON TABLE asset_freshness IS
  'Nirmana reconciliation projection. Database config triggers may invalidate it; only a successful sidecar execution may restore fresh.';

COMMIT;
