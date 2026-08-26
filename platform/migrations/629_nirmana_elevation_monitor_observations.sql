-- Migration 629: append-only Nirmana elevation monitor observations
-- Created: 2026-08-26

BEGIN;

CREATE OR REPLACE FUNCTION nirmana_elevation_monitor_sorted_unique(items text[])
RETURNS boolean
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS $$
  SELECT $1 IS NOT NULL
    AND $1 = ARRAY(
      SELECT DISTINCT item COLLATE "C" AS item
        FROM unnest($1) AS entries(item)
       WHERE item IS NOT NULL AND item <> ''
       ORDER BY item
    );
$$;

CREATE TABLE IF NOT EXISTS nirmana_elevation_monitor_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  status text NOT NULL CHECK (status IN (
    'in_sync', 'baseline_missing', 'plan_adaptation_required',
    'evidence_refresh_required', 'label_refresh_required',
    'release_attention', 'source_unavailable'
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
  source_state text NOT NULL CHECK (source_state IN ('available', 'unavailable')),
  source_observed_at timestamptz,
  source_age_seconds integer CHECK (source_age_seconds IS NULL OR source_age_seconds >= 0),
  freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unavailable')),
  freshness_deadline_at timestamptz,
  runtime_liveness text NOT NULL CHECK (runtime_liveness IN ('active', 'quiet', 'unavailable')),
  release_state text NOT NULL CHECK (release_state IN ('in_sync', 'out_of_sync', 'unknown', 'unavailable')),
  release_observed_at timestamptz,
  release_age_seconds integer CHECK (release_age_seconds IS NULL OR release_age_seconds >= 0),
  public_detail text NOT NULL CHECK (char_length(public_detail) BETWEEN 1 AND 512),
  source_error_code text CHECK (
    source_error_code IS NULL OR char_length(source_error_code) BETWEEN 1 AND 128
  ),
  CONSTRAINT nirmana_elevation_monitor_affected_ids_canonical CHECK (
    nirmana_elevation_monitor_sorted_unique(affected_asset_ids)
  ),
  CONSTRAINT nirmana_elevation_monitor_digest_shape CHECK (
    (
      status = 'source_unavailable'
      AND current_definition_sha256 IS NULL
      AND candidate_definition_sha256 IS NULL
      AND registry_identity_sha256 IS NULL
      AND registry_contract_sha256 IS NULL
      AND candidate_catalogue_sha256 IS NULL
      AND selected_catalogue_sha256 IS NULL
      AND runtime_sha256 IS NULL
      AND release_sha256 IS NULL
    ) OR (
      status <> 'source_unavailable'
      AND candidate_definition_sha256 IS NOT NULL
      AND registry_identity_sha256 IS NOT NULL
      AND registry_contract_sha256 IS NOT NULL
      AND candidate_catalogue_sha256 IS NOT NULL
      AND selected_catalogue_sha256 IS NOT NULL
      AND runtime_sha256 IS NOT NULL
      AND release_sha256 IS NOT NULL
      AND (
        (status = 'baseline_missing'
          AND current_definition_sha256 IS NULL)
        OR (status = 'label_refresh_required'
          AND current_definition_sha256 IS NOT NULL)
        OR (status NOT IN ('baseline_missing', 'label_refresh_required')
          AND current_definition_sha256 IS NOT NULL)
      )
    )
  ),
  CONSTRAINT nirmana_elevation_monitor_source_shape CHECK (
    (
      status = 'source_unavailable'
      AND source_state = 'unavailable'
      AND source_observed_at IS NULL
      AND source_age_seconds IS NULL
      AND freshness_state = 'unavailable'
      AND freshness_deadline_at IS NULL
      AND runtime_liveness = 'unavailable'
      AND release_state = 'unavailable'
      AND release_observed_at IS NULL
      AND release_age_seconds IS NULL
      AND source_error_code IS NOT NULL
    ) OR (
      status <> 'source_unavailable'
      AND source_state = 'available'
      AND source_observed_at IS NOT NULL
      AND source_age_seconds IS NOT NULL
      AND freshness_state IN ('fresh', 'stale')
      AND freshness_deadline_at = source_observed_at + INTERVAL '15 minutes'
      AND runtime_liveness IN ('active', 'quiet')
      AND release_observed_at IS NOT NULL
      AND release_age_seconds IS NOT NULL
      AND source_error_code IS NULL
    )
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
