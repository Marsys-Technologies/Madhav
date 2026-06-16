-- Migration 287: Register ga_vastu in asset_registry
-- Astrovastu subsystem Gate-1 — L1 per-chart Vastu planet direction map.
-- Idempotent: INSERT ON CONFLICT (asset_id) DO UPDATE.

BEGIN;

INSERT INTO asset_registry (
    asset_id,
    layer,
    sort_order,
    sanskrit_name,
    english_name,
    english_description,
    storage_type,
    target_table,
    count_sql,
    size_sql,
    target_floor,
    expected_volume_formula,
    expected_volume_inputs,
    volume_explanation,
    depends_on,
    scope,
    is_active,
    has_substeps,
    asset_type,
    layer_name,
    layer_index,
    catalog_status
) VALUES (
    'ga_vastu',
    'ganita',
    31,
    'Vastu-graha-dik-mapa',
    'Vastu Planet Direction Map',
    'Maps each classical graha to its ruling Vastu direction (per bg_vastu_directions) and computes direction_impact (weakened / neutral / strengthened) using the condition_score from ga_condition_composite. Produces one row per graha per ayanamsha for grahas with a recognised direction mapping. Indication tier: traditional_vastu.',
    'postgres_table',
    'ga_vastu_planet_direction_map',
    'SELECT COUNT(*) FROM ga_vastu_planet_direction_map WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''ga_vastu_planet_direction_map'')',
    45,
    '9_GRAHAS * 5_AYANAMSHAS',
    '{"grahas": 9, "ayanamshas": 5}'::jsonb,
    'Up to 9 grahas × 5 ayanamshas = 45 rows per chart; rows are emitted only for grahas that have a classical Vastu direction mapping (Ketu may be skipped).',
    ARRAY['ga_condition']::text[],
    'per_chart',
    true,
    true,
    'data',
    'Gaṇita',
    'L1',
    'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
    layer                   = EXCLUDED.layer,
    sort_order              = EXCLUDED.sort_order,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description,
    storage_type            = EXCLUDED.storage_type,
    target_table            = EXCLUDED.target_table,
    count_sql               = EXCLUDED.count_sql,
    size_sql                = EXCLUDED.size_sql,
    target_floor            = EXCLUDED.target_floor,
    expected_volume_formula = EXCLUDED.expected_volume_formula,
    expected_volume_inputs  = EXCLUDED.expected_volume_inputs,
    volume_explanation      = EXCLUDED.volume_explanation,
    depends_on              = EXCLUDED.depends_on,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    has_substeps            = EXCLUDED.has_substeps,
    asset_type              = EXCLUDED.asset_type,
    layer_name              = EXCLUDED.layer_name,
    layer_index             = EXCLUDED.layer_index,
    catalog_status          = EXCLUDED.catalog_status;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ga_vastu';
--   COMMIT;
-- =============================================================================
