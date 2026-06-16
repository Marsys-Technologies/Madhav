-- 278_bg_medical_asset_registry.sql
-- =============================================================================
-- Medical/Ayurvedic Subsystem Gate-1 — asset_registry rows for L0 tables.
--
-- Registers:
--   bg_medical_mappings — 9 graha → Ayurvedic mapping rows
--   bg_nakshatra_medical — 27 nakshatra → body-part rows
--
-- Both are L0 brahmagyan global assets (scope='global').
-- count_sql is a simple full-table COUNT (global, not per-chart).
-- =============================================================================

BEGIN;

INSERT INTO asset_registry (
    asset_id, layer, scope, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, target_floor,
    depends_on, is_active, asset_type, layer_name, layer_index, catalog_status
) VALUES (
    'bg_medical_mappings',
    'brahmagyan',
    'global',
    'Vaidya Graha Kosha',
    'Medical Graha Mappings',
    'Classical Ayurvedic graha → dosha/dhatu/organ/body-part mappings per BPHS Ch.18, '
    'Ashtanga Hridayam, Charaka Samhita. 9 grahas (Sun–Ketu). '
    'L0 static reference — ON CONFLICT DO UPDATE.',
    'postgres_table',
    'bg_medical_mappings',
    'SELECT COUNT(*) FROM bg_medical_mappings',
    9,
    ARRAY[]::text[],
    true,
    'data',
    'Brahmagyan',
    'L0',
    'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
    layer               = EXCLUDED.layer,
    scope               = EXCLUDED.scope,
    sanskrit_name       = EXCLUDED.sanskrit_name,
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    storage_type        = EXCLUDED.storage_type,
    target_table        = EXCLUDED.target_table,
    count_sql           = EXCLUDED.count_sql,
    target_floor        = EXCLUDED.target_floor,
    depends_on          = EXCLUDED.depends_on,
    is_active           = EXCLUDED.is_active,
    asset_type          = EXCLUDED.asset_type,
    layer_name          = EXCLUDED.layer_name,
    layer_index         = EXCLUDED.layer_index,
    catalog_status      = EXCLUDED.catalog_status;

INSERT INTO asset_registry (
    asset_id, layer, scope, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, target_floor,
    depends_on, is_active, asset_type, layer_name, layer_index, catalog_status
) VALUES (
    'bg_nakshatra_medical',
    'brahmagyan',
    'global',
    'Nakshatra Deha Kosha',
    'Nakshatra Body-Part Mappings',
    '27 nakshatras → body-part correspondences per Ashtanga Hridayam / BPHS. '
    'FORENSIC: #25 Purva Bhadrapada → left_side (native Moon nakshatra). '
    'Used by ga_medical for Moon nakshatra body-part lookup.',
    'postgres_table',
    'bg_nakshatra_medical',
    'SELECT COUNT(*) FROM bg_nakshatra_medical',
    27,
    ARRAY[]::text[],
    true,
    'data',
    'Brahmagyan',
    'L0',
    'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
    layer               = EXCLUDED.layer,
    scope               = EXCLUDED.scope,
    sanskrit_name       = EXCLUDED.sanskrit_name,
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    storage_type        = EXCLUDED.storage_type,
    target_table        = EXCLUDED.target_table,
    count_sql           = EXCLUDED.count_sql,
    target_floor        = EXCLUDED.target_floor,
    depends_on          = EXCLUDED.depends_on,
    is_active           = EXCLUDED.is_active,
    asset_type          = EXCLUDED.asset_type,
    layer_name          = EXCLUDED.layer_name,
    layer_index         = EXCLUDED.layer_index,
    catalog_status      = EXCLUDED.catalog_status;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry
--     WHERE asset_id IN ('bg_medical_mappings', 'bg_nakshatra_medical');
--   COMMIT;
-- =============================================================================
