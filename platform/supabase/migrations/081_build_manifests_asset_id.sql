-- 081_build_manifests_asset_id.sql
-- Adds asset_id column to build_manifests so v3.x bootstrap manifests are queryable.
-- Closes recurring AC.*.4 schema-mismatch residual from MCPT v3.2/v3.3 sessions.
-- v3.5 housekeeping (2026-05-22).
BEGIN;

ALTER TABLE build_manifests ADD COLUMN IF NOT EXISTS asset_id text;

-- Backfill from build_id prefix for known MCPT build patterns.
UPDATE build_manifests SET asset_id = 'chart_facts'
  WHERE build_id LIKE 'mcpt-v33-s%' AND asset_id IS NULL;

UPDATE build_manifests SET asset_id = 'classical_texts'
  WHERE build_id LIKE 'mcpt-v32-%' AND asset_id IS NULL;

UPDATE build_manifests SET asset_id = 'msr_signals'
  WHERE build_id LIKE 'mcpt-v34-%' AND asset_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_build_manifests_asset_id
  ON build_manifests (asset_id, triggered_at DESC);

COMMIT;
