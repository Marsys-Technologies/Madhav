-- Migration 202: asset_registry service support
-- Adds asset_type / layer_name / layer_index / provides_apis / health_probe / catalog_status columns.
-- Extends storage_type to include 'service'.
-- Backfills existing rows: type='data', layer names+indices, catalog_status.
-- Reversible down-block included.
-- Per: UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md §C, §E, §I

BEGIN;

-- §1 — Add new columns (nullable; backfilled below) ─────────────────────────

ALTER TABLE asset_registry
  ADD COLUMN IF NOT EXISTS asset_type      text DEFAULT 'data',
  ADD COLUMN IF NOT EXISTS layer_name      text,
  ADD COLUMN IF NOT EXISTS layer_index     text,
  ADD COLUMN IF NOT EXISTS provides_apis   jsonb,
  ADD COLUMN IF NOT EXISTS health_probe    jsonb,
  ADD COLUMN IF NOT EXISTS catalog_status  text DEFAULT 'DRAFT';

-- §2 — Extend storage_type CHECK to include 'service' ────────────────────────
-- PostgreSQL auto-names inline CHECK as <table>_<column>_check

ALTER TABLE asset_registry
  DROP CONSTRAINT IF EXISTS asset_registry_storage_type_check;

ALTER TABLE asset_registry
  ADD CONSTRAINT asset_registry_storage_type_check
  CHECK (storage_type IN (
    'postgres_table','pgvector','postgres_view',
    'gcs_jsonl','bigquery','tool_only','service'
  ));

-- §3 — Add CHECK constraints for the new columns ─────────────────────────────

ALTER TABLE asset_registry
  ADD CONSTRAINT asset_registry_asset_type_check
  CHECK (asset_type IN ('data','service'));

ALTER TABLE asset_registry
  ADD CONSTRAINT asset_registry_catalog_status_check
  CHECK (catalog_status IN ('CURRENT','DRAFT'));

-- §4 — Backfill: all existing rows are data assets ───────────────────────────

UPDATE asset_registry SET asset_type = 'data' WHERE asset_type IS NULL;

-- §5 — Backfill: layer_name + layer_index from layer code ────────────────────

UPDATE asset_registry SET
  layer_name  = CASE layer
    WHEN 'brahmagyan' THEN 'Brahmagyan'
    WHEN 'ganita'     THEN 'Gaṇita'
    WHEN 'bodha'      THEN 'Bodha'
    WHEN 'kala'       THEN 'Kāla'
    WHEN 'phala'      THEN 'Phala'
    WHEN 'mimamsa'    THEN 'Mīmāṃsā'
    ELSE layer
  END,
  layer_index = CASE layer
    WHEN 'brahmagyan' THEN 'L0'
    WHEN 'ganita'     THEN 'L1'
    WHEN 'bodha'      THEN 'L2'
    WHEN 'kala'       THEN 'L3'
    WHEN 'phala'      THEN 'L4'
    WHEN 'mimamsa'    THEN 'L5'
    ELSE NULL
  END;

-- §6 — Backfill: catalog_status — L0 bg_* = CURRENT; L1–L5 = DRAFT ──────────
-- (12 finalized L0 data assets; the 2 new service assets added in migration 203)

UPDATE asset_registry
SET catalog_status = 'CURRENT'
WHERE layer = 'brahmagyan';

UPDATE asset_registry
SET catalog_status = 'DRAFT'
WHERE layer IN ('ganita','bodha','kala','phala','mimamsa');

-- §7 — Set NOT NULL on the fields that always have a value ───────────────────

ALTER TABLE asset_registry
  ALTER COLUMN asset_type SET NOT NULL,
  ALTER COLUMN catalog_status SET NOT NULL;

COMMIT;

-- ── Reversible DOWN block (run manually to roll back) ────────────────────────
-- BEGIN;
-- ALTER TABLE asset_registry
--   DROP COLUMN IF EXISTS asset_type,
--   DROP COLUMN IF EXISTS layer_name,
--   DROP COLUMN IF EXISTS layer_index,
--   DROP COLUMN IF EXISTS provides_apis,
--   DROP COLUMN IF EXISTS health_probe,
--   DROP COLUMN IF EXISTS catalog_status;
-- ALTER TABLE asset_registry DROP CONSTRAINT IF EXISTS asset_registry_storage_type_check;
-- ALTER TABLE asset_registry ADD CONSTRAINT asset_registry_storage_type_check
--   CHECK (storage_type IN ('postgres_table','pgvector','postgres_view','gcs_jsonl','bigquery','tool_only'));
-- COMMIT;
