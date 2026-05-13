-- platform/migrations/051_aiops_catalog_snapshot.sql
-- Migration: AIOps CP.1 — provider catalog snapshots.
-- Stores the last-fetched catalog for each provider so the UI can show
-- an offline view and the stale-cache fallback has a persistent source.

BEGIN;

CREATE TABLE IF NOT EXISTS llm_catalog_snapshot (
  provider    TEXT NOT NULL,
  model_id    TEXT NOT NULL,
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw_payload JSONB NOT NULL,
  augmented   JSONB NOT NULL,  -- with context window, params, cost metadata
  PRIMARY KEY (provider, model_id, fetched_at)
);

CREATE INDEX IF NOT EXISTS llm_catalog_snapshot_provider_fetched_idx
  ON llm_catalog_snapshot (provider, fetched_at DESC);

COMMIT;

-- Down:
-- DROP INDEX IF EXISTS llm_catalog_snapshot_provider_fetched_idx;
-- DROP TABLE IF EXISTS llm_catalog_snapshot;
