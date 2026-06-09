-- Migration 181: add clear_tables to asset_registry
-- Fixes bg_reference clear: target_table points to reference_nakshatras only,
-- but the asset spans 15 reference_* tables. clear_tables lists every table
-- that must be truncated when this asset is cleared. Falls back to [target_table]
-- when NULL.

BEGIN;

ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS clear_tables text[];

-- bg_reference spans all 15 reference_* tables introduced in migrations 174/178
UPDATE asset_registry
SET clear_tables = ARRAY[
  'reference_planets',
  'reference_nakshatras',
  'reference_signs',
  'reference_aspects',
  'reference_vargas',
  'reference_houses',
  'reference_strength_systems',
  'reference_karakas',
  'reference_upagrahas',
  'reference_constants',
  'reference_topic_tags',
  'reference_glossary',
  'reference_yogas',
  'reference_doshas',
  'reference_dasha_systems'
]
WHERE asset_id = 'bg_reference';

COMMIT;
