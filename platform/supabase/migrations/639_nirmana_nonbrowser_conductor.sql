-- Migration 639: durable non-browser Nirmana conductor control plane.
--
-- The tables are deliberately owned by the existing NOLOGIN evidence owner.
-- Runtime code uses the already-distinct campaign-control writer; generic app,
-- monitor, deploy, and Scheduler identities receive no database privilege.

BEGIN;

CREATE TABLE nirmana_evidence.nirmana_elevation_conductor_policies (
  campaign_id text PRIMARY KEY CHECK (campaign_id = 'nirmana-elevation'),
  policy_revision text NOT NULL CHECK (policy_revision = 'nirmana-l0-autonomy/v1'),
  status text NOT NULL CHECK (status IN ('enabled', 'revoked')),
  max_layer text NOT NULL CHECK (max_layer = 'L0'),
  allowed_actions text[] NOT NULL CHECK (
    allowed_actions <@ ARRAY[
      'supersede_definition', 'stage_transition', 'foundation_receipt',
      'asset_analysis', 'optimization_verdict', 'implementation_receipt',
      'build_run_authorization', 'rebuild_observation', 'probe_receipt',
      'producer_coverage', 'non_build_disposition', 'integrity_receipt', 'freeze_receipt'
    ]::text[]
  ),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  revoked_by text,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  CHECK ((status = 'revoked') = (revoked_at IS NOT NULL)),
  CHECK ((revoked_at IS NULL) = (revoked_by IS NULL))
);

CREATE TABLE nirmana_evidence.nirmana_elevation_conductor_leases (
  lease_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id text NOT NULL REFERENCES nirmana_evidence.nirmana_elevation_conductor_policies(campaign_id),
  principal_email text NOT NULL CHECK (principal_email ~ '^amjis-nirmana-(conductor|verifier)@madhav-astrology\.iam\.gserviceaccount\.com$'),
  fence bigint NOT NULL CHECK (fence > 0),
  scope text NOT NULL CHECK (scope = 'T0,F0,L0'),
  acquired_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  expires_at timestamptz NOT NULL,
  released_at timestamptz,
  revoked_at timestamptz,
  CHECK (expires_at > acquired_at),
  CHECK (NOT (released_at IS NOT NULL AND revoked_at IS NOT NULL))
);

CREATE UNIQUE INDEX nirmana_elevation_conductor_one_live_lease
  ON nirmana_evidence.nirmana_elevation_conductor_leases (campaign_id)
  WHERE released_at IS NULL AND revoked_at IS NULL;
CREATE UNIQUE INDEX nirmana_elevation_conductor_fence
  ON nirmana_evidence.nirmana_elevation_conductor_leases (campaign_id, fence);
CREATE UNIQUE INDEX nirmana_elevation_conductor_lease_fence
  ON nirmana_evidence.nirmana_elevation_conductor_leases (lease_id, fence);

CREATE TABLE nirmana_evidence.nirmana_elevation_conductor_receipts (
  receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id text NOT NULL REFERENCES nirmana_evidence.nirmana_elevation_conductor_policies(campaign_id),
  idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 256),
  action text NOT NULL CHECK (action = ANY (ARRAY[
    'supersede_definition', 'stage_transition', 'foundation_receipt',
    'asset_analysis', 'optimization_verdict', 'implementation_receipt',
    'build_run_authorization', 'rebuild_observation', 'probe_receipt',
    'producer_coverage', 'non_build_disposition', 'integrity_receipt', 'freeze_receipt'
  ])),
  lease_id uuid NOT NULL REFERENCES nirmana_evidence.nirmana_elevation_conductor_leases(lease_id),
  fence bigint NOT NULL CHECK (fence > 0),
  definition_revision text,
  observation_id uuid,
  request_digest_sha256 text NOT NULL CHECK (request_digest_sha256 ~ '^[a-f0-9]{64}$'),
  outcome text NOT NULL CHECK (outcome IN ('created', 'idempotent', 'blocked', 'failed')),
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  UNIQUE (campaign_id, idempotency_key),
  CONSTRAINT nirmana_elevation_conductor_receipt_fence_fk
    FOREIGN KEY (lease_id, fence)
    REFERENCES nirmana_evidence.nirmana_elevation_conductor_leases (lease_id, fence)
);

CREATE TABLE nirmana_evidence.nirmana_elevation_conductor_readiness_receipts (
  readiness_receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id text NOT NULL REFERENCES nirmana_evidence.nirmana_elevation_conductor_policies(campaign_id),
  verifier_principal_email text NOT NULL CHECK (verifier_principal_email = 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com'),
  policy_revision text NOT NULL CHECK (policy_revision = 'nirmana-l0-autonomy/v1'),
  definition_revision text NOT NULL,
  definition_manifest_sha256 text NOT NULL CHECK (definition_manifest_sha256 ~ '^[a-f0-9]{64}$'),
  main_sha text NOT NULL CHECK (main_sha ~ '^[a-f0-9]{40}$'),
  deployed_sha text NOT NULL CHECK (deployed_sha ~ '^[a-f0-9]{40}$'),
  cloud_run_revision text NOT NULL CHECK (cloud_run_revision ~ '^amjis-web-[a-z0-9-]+$'),
  migration_set_sha256 text NOT NULL CHECK (migration_set_sha256 ~ '^[a-f0-9]{64}$'),
  source_observation_id uuid NOT NULL,
  lease_id uuid NOT NULL,
  fence bigint NOT NULL CHECK (fence > 0),
  verdict text NOT NULL CHECK (verdict IN ('pass', 'fail')),
  checks jsonb NOT NULL,
  checked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  expires_at timestamptz NOT NULL,
  CHECK (expires_at > checked_at),
  CONSTRAINT nirmana_elevation_conductor_readiness_fence_fk
    FOREIGN KEY (lease_id, fence)
    REFERENCES nirmana_evidence.nirmana_elevation_conductor_leases (lease_id, fence)
);

CREATE INDEX nirmana_elevation_conductor_readiness_fresh
  ON nirmana_evidence.nirmana_elevation_conductor_readiness_receipts (campaign_id, checked_at DESC);

CREATE OR REPLACE FUNCTION nirmana_evidence.nirmana_elevation_prevent_conductor_receipt_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Nirmana conductor receipts are append-only';
END;
$$;

CREATE TRIGGER nirmana_elevation_conductor_receipts_append_only
  BEFORE UPDATE OR DELETE ON nirmana_evidence.nirmana_elevation_conductor_receipts
  FOR EACH ROW EXECUTE FUNCTION nirmana_evidence.nirmana_elevation_prevent_conductor_receipt_mutation();
CREATE TRIGGER nirmana_elevation_conductor_readiness_append_only
  BEFORE UPDATE OR DELETE ON nirmana_evidence.nirmana_elevation_conductor_readiness_receipts
  FOR EACH ROW EXECUTE FUNCTION nirmana_evidence.nirmana_elevation_prevent_conductor_receipt_mutation();

ALTER TABLE nirmana_evidence.nirmana_elevation_conductor_policies OWNER TO nirmana_evidence_owner;
ALTER TABLE nirmana_evidence.nirmana_elevation_conductor_leases OWNER TO nirmana_evidence_owner;
ALTER TABLE nirmana_evidence.nirmana_elevation_conductor_receipts OWNER TO nirmana_evidence_owner;
ALTER TABLE nirmana_evidence.nirmana_elevation_conductor_readiness_receipts OWNER TO nirmana_evidence_owner;
ALTER FUNCTION nirmana_evidence.nirmana_elevation_prevent_conductor_receipt_mutation() OWNER TO nirmana_evidence_owner;

-- The verifier uses a separately provisioned secret-backed database login.
-- It can record only readiness evidence and cannot create definitions, labels,
-- lifecycle receipts, or lease state. The password is intentionally absent:
-- production provisioning must use the reviewed secret path.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_verifier_writer') THEN
    CREATE ROLE nirmana_evidence_verifier_writer LOGIN NOINHERIT NOCREATEDB NOCREATEROLE;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_verifier_writer'
    AND (rolsuper OR rolreplication OR rolbypassrls OR rolinherit)) THEN
    RAISE EXCEPTION 'Nirmana verifier writer must be a non-inheriting, non-elevated login';
  END IF;
END;
$$;

REVOKE ALL ON TABLE nirmana_evidence.nirmana_elevation_conductor_policies,
  nirmana_evidence.nirmana_elevation_conductor_leases,
  nirmana_evidence.nirmana_elevation_conductor_receipts,
  nirmana_evidence.nirmana_elevation_conductor_readiness_receipts FROM PUBLIC, amjis_app, nirmana_evidence_ingress_writer;
REVOKE ALL ON TABLE nirmana_evidence.nirmana_elevation_conductor_policies,
  nirmana_evidence.nirmana_elevation_conductor_leases,
  nirmana_evidence.nirmana_elevation_conductor_receipts,
  nirmana_evidence.nirmana_elevation_conductor_readiness_receipts FROM nirmana_evidence_verifier_writer;
GRANT SELECT ON nirmana_evidence.nirmana_elevation_conductor_policies TO nirmana_campaign_control_writer;
GRANT REFERENCES (campaign_id) ON nirmana_evidence.nirmana_elevation_conductor_policies TO nirmana_campaign_control_writer;
GRANT USAGE ON SCHEMA nirmana_evidence TO nirmana_campaign_control_writer;
GRANT SELECT, INSERT, UPDATE ON nirmana_evidence.nirmana_elevation_conductor_leases TO nirmana_campaign_control_writer;
GRANT SELECT, INSERT ON nirmana_evidence.nirmana_elevation_conductor_receipts TO nirmana_campaign_control_writer;
GRANT SELECT, INSERT ON nirmana_evidence.nirmana_elevation_conductor_readiness_receipts TO nirmana_campaign_control_writer;
GRANT USAGE ON SCHEMA nirmana_evidence TO nirmana_evidence_verifier_writer;
GRANT SELECT ON nirmana_evidence.nirmana_elevation_conductor_policies,
  nirmana_evidence.nirmana_elevation_conductor_leases,
  nirmana_evidence.nirmana_elevation_campaign_definitions TO nirmana_evidence_verifier_writer;
GRANT INSERT ON nirmana_evidence.nirmana_elevation_conductor_readiness_receipts TO nirmana_evidence_verifier_writer;
GRANT SELECT ON TABLE public.nirmana_elevation_monitor_observations, public._migrations_applied
  TO nirmana_evidence_verifier_writer;

INSERT INTO nirmana_evidence.nirmana_elevation_conductor_policies (
  campaign_id, policy_revision, status, max_layer, allowed_actions, expires_at
) VALUES (
  'nirmana-elevation', 'nirmana-l0-autonomy/v1', 'enabled', 'L0',
  ARRAY['supersede_definition', 'stage_transition', 'foundation_receipt', 'asset_analysis',
    'optimization_verdict', 'implementation_receipt', 'build_run_authorization',
    'rebuild_observation', 'probe_receipt', 'producer_coverage', 'non_build_disposition',
    'integrity_receipt', 'freeze_receipt'],
  TIMESTAMPTZ '2026-09-30 00:00:00+00'
) ON CONFLICT (campaign_id) DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner')
    OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer')
    OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_verifier_writer') THEN
    RAISE EXCEPTION 'Nirmana conductor requires the established evidence owner and campaign-control writer roles';
  END IF;
  IF (SELECT relowner::regrole::text FROM pg_class WHERE oid = 'nirmana_evidence.nirmana_elevation_conductor_policies'::regclass) <> 'nirmana_evidence_owner'
    OR has_table_privilege('amjis_app', 'nirmana_evidence.nirmana_elevation_conductor_policies', 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')
    OR NOT has_table_privilege('nirmana_campaign_control_writer', 'nirmana_evidence.nirmana_elevation_conductor_leases', 'SELECT, INSERT, UPDATE')
    OR has_table_privilege('nirmana_campaign_control_writer', 'nirmana_evidence.nirmana_elevation_conductor_policies', 'INSERT, UPDATE, DELETE, TRUNCATE')
    OR NOT has_table_privilege('nirmana_evidence_verifier_writer', 'nirmana_evidence.nirmana_elevation_conductor_readiness_receipts', 'INSERT')
    OR has_table_privilege('nirmana_evidence_verifier_writer', 'nirmana_evidence.nirmana_elevation_conductor_leases', 'INSERT, UPDATE, DELETE, TRUNCATE')
    OR has_table_privilege('nirmana_evidence_verifier_writer', 'nirmana_evidence.nirmana_elevation_conductor_receipts', 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE') THEN
    RAISE EXCEPTION 'Nirmana conductor ownership or least-privilege grants are not exact';
  END IF;
END;
$$;

COMMIT;
