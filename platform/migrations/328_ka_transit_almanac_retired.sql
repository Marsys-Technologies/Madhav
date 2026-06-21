-- Migration 328: extend catalog_status check to allow 'RETIRED' for future retired placeholders.
-- Originally intended to mark ka_transit_almanac as RETIRED, but the row is removed in migration 329.
-- This migration only expands the constraint so 'RETIRED' is a valid value for future assets.
ALTER TABLE asset_registry DROP CONSTRAINT IF EXISTS asset_registry_catalog_status_check;
ALTER TABLE asset_registry ADD CONSTRAINT asset_registry_catalog_status_check
  CHECK (catalog_status = ANY (ARRAY['CURRENT'::text, 'DRAFT'::text, 'RETIRED'::text]));
