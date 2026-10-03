-- Migration 1301: Refresh catalogue metadata independently from generation proof.
-- Created: 2026-10-02
-- Transaction owned by platform/scripts/migrate.ts.

ALTER TABLE ai_provider_connections
  ADD COLUMN IF NOT EXISTS catalog_refreshed_at timestamptz,
  ADD COLUMN IF NOT EXISTS catalog_attempted_at timestamptz,
  ADD COLUMN IF NOT EXISTS catalog_error_code text,
  ADD COLUMN IF NOT EXISTS catalog_refresh_epoch bigint NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS catalog_refresh_in_progress boolean NOT NULL DEFAULT false;

ALTER TABLE ai_cli_installations
  ADD COLUMN IF NOT EXISTS entrypoint_sha256 text,
  ADD COLUMN IF NOT EXISTS catalog_refreshed_at timestamptz,
  ADD COLUMN IF NOT EXISTS catalog_attempted_at timestamptz,
  ADD COLUMN IF NOT EXISTS catalog_error_code text,
  ADD COLUMN IF NOT EXISTS catalog_refresh_epoch bigint NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS catalog_refresh_in_progress boolean NOT NULL DEFAULT false;

ALTER TABLE ai_cli_models
  ADD COLUMN IF NOT EXISTS supported_efforts text[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS default_effort text,
  ADD COLUMN IF NOT EXISTS is_catalog_discovered boolean NOT NULL DEFAULT false;

ALTER TABLE ai_connection_models ADD COLUMN IF NOT EXISTS supported_efforts text[];

-- Named constraints are replaced idempotently; applied migration 1300 is retained.
ALTER TABLE ai_custom_configuration_roles
  DROP CONSTRAINT IF EXISTS ai_custom_configuration_roles_effort_check;
ALTER TABLE ai_custom_configuration_roles
  ADD CONSTRAINT ai_custom_configuration_roles_effort_check
  CHECK (effort IS NULL OR effort ~ '^[a-z][a-z0-9_]{0,31}$');

ALTER TABLE ai_cli_models DROP CONSTRAINT IF EXISTS ai_cli_models_effort_catalog_check;
ALTER TABLE ai_cli_models ADD CONSTRAINT ai_cli_models_effort_catalog_check CHECK (
  cardinality(supported_efforts) <= 16 AND array_position(supported_efforts, NULL) IS NULL
  AND array_to_string(supported_efforts, '') !~ '[^a-z0-9_]'
  AND (cardinality(supported_efforts) = 0
    OR array_to_string(supported_efforts, ',') ~ '^[a-z][a-z0-9_]{0,31}(,[a-z][a-z0-9_]{0,31})*$')
  AND (default_effort IS NULL OR default_effort = ANY(supported_efforts))
);

ALTER TABLE ai_connection_models DROP CONSTRAINT IF EXISTS ai_connection_models_effort_catalog_check;
ALTER TABLE ai_connection_models ADD CONSTRAINT ai_connection_models_effort_catalog_check CHECK (
  supported_efforts IS NULL OR (
    cardinality(supported_efforts) <= 16 AND array_position(supported_efforts, NULL) IS NULL
    AND array_to_string(supported_efforts, '') !~ '[^a-z0-9_]'
    AND (cardinality(supported_efforts) = 0
      OR array_to_string(supported_efforts, ',') ~ '^[a-z][a-z0-9_]{0,31}(,[a-z][a-z0-9_]{0,31})*$')
  )
);

-- Existing grants/RLS remain intact: the columns contain safe metadata only.
