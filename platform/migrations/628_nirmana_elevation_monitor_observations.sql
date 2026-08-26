-- Migration 628: append-only Nirmana elevation monitor observations
-- Created: 2026-08-26

BEGIN;

CREATE TABLE IF NOT EXISTS nirmana_elevation_monitor_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  status text NOT NULL CHECK (status IN (
    'in_sync',
    'baseline_missing',
    'plan_adaptation_required',
    'evidence_refresh_required',
    'label_refresh_required',
    'release_attention',
    'source_unavailable'
  )),
  affected_asset_ids text[] NOT NULL DEFAULT '{}'::text[],
  current_definition_sha256 text CHECK (
    current_definition_sha256 IS NULL OR current_definition_sha256 ~ '^[a-f0-9]{64}$'
  ),
  candidate_definition_sha256 text CHECK (
    candidate_definition_sha256 IS NULL OR candidate_definition_sha256 ~ '^[a-f0-9]{64}$'
  ),
  registry_identity_sha256 text CHECK (
    registry_identity_sha256 IS NULL OR registry_identity_sha256 ~ '^[a-f0-9]{64}$'
  ),
  registry_contract_sha256 text CHECK (
    registry_contract_sha256 IS NULL OR registry_contract_sha256 ~ '^[a-f0-9]{64}$'
  ),
  candidate_catalogue_sha256 text CHECK (
    candidate_catalogue_sha256 IS NULL OR candidate_catalogue_sha256 ~ '^[a-f0-9]{64}$'
  ),
  selected_catalogue_sha256 text CHECK (
    selected_catalogue_sha256 IS NULL OR selected_catalogue_sha256 ~ '^[a-f0-9]{64}$'
  ),
  runtime_sha256 text CHECK (
    runtime_sha256 IS NULL OR runtime_sha256 ~ '^[a-f0-9]{64}$'
  ),
  release_sha256 text CHECK (
    release_sha256 IS NULL OR release_sha256 ~ '^[a-f0-9]{64}$'
  ),
  public_detail text NOT NULL CHECK (char_length(public_detail) BETWEEN 1 AND 512),
  source_error_code text CHECK (
    source_error_code IS NULL OR char_length(source_error_code) BETWEEN 1 AND 128
  ),
  CONSTRAINT nirmana_elevation_monitor_source_status_consistent CHECK (
    (status = 'source_unavailable') = (source_error_code IS NOT NULL)
  )
);

CREATE INDEX IF NOT EXISTS nirmana_elevation_monitor_observations_latest_idx
  ON nirmana_elevation_monitor_observations (observed_at DESC, id DESC);

CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_monitor_observation_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'nirmana_elevation_monitor_observations is append-only';
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_monitor_observations_append_only
  ON nirmana_elevation_monitor_observations;
CREATE TRIGGER nirmana_elevation_monitor_observations_append_only
  BEFORE UPDATE OR DELETE OR TRUNCATE ON nirmana_elevation_monitor_observations
  FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_monitor_observation_mutation();

COMMENT ON TABLE nirmana_elevation_monitor_observations IS
  'Append-only scheduler observations of Nirmana program synchronization; never campaign acceptance or build state.';

COMMIT;
