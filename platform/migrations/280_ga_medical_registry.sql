-- 280_ga_medical_registry.sql
-- =============================================================================
-- Medical/Ayurvedic Subsystem Gate-1 — asset_registry row for ga_medical.
--
-- ga_medical: L1 per-chart Ayurvedic Jyotish indication table.
-- depends_on: ga_condition (condition_score source), ga_positions (sign/nakshatra).
-- has_substeps: true (5 substeps — one per ayanamsha).
-- count_sql: per-chart COUNT (cockpit truth — reads count_sql NOT asset_throughput).
-- target_floor: 45 (9 grahas × 5 ayanamshas).
-- =============================================================================

BEGIN;

INSERT INTO asset_registry (
    asset_id, layer, scope, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, target_floor,
    depends_on, is_active, asset_type, layer_name, layer_index, catalog_status
) VALUES (
    'ga_medical',
    'ganita',
    'per_chart',
    'Vaidya Phala',
    'Medical / Ayurvedic Indications',
    'Per-chart Ayurvedic Jyotish indication summary: dosha aggravation, organ watch, '
    'body-part watch, and indication_strength derived from ga_condition condition_score '
    'joined with bg_medical_mappings. 9 grahas × 5 ayanamshas = 45 rows per chart. '
    'FORENSIC: Sun=Capricorn (debilitated) → strong; '
    'Moon=Purva Bhadrapada → nakshatra_body_part=left_side; '
    'Saturn=Libra (exalted) → mild. '
    'MEDICAL DISCLAIMER: indication_tier=jyotish_indication; not_diagnosis=TRUE.',
    'postgres_table',
    'ga_medical',
    'SELECT COUNT(*) FROM ga_medical WHERE chart_id = $1',
    45,
    ARRAY['ga_condition', 'ga_positions'],
    true,
    'data',
    'Gaṇita',
    'L1',
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
--   DELETE FROM asset_registry WHERE asset_id = 'ga_medical';
--   COMMIT;
-- =============================================================================
