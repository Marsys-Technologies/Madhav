-- Migration 252: Register ga_condition in asset_registry
-- Adds the ga_condition (Planetary Condition Composite) asset to the cockpit catalog.
-- Idempotent: INSERT … ON CONFLICT (asset_id) DO UPDATE.
--
-- Depends on: ga_positions (for graha positions) and ga_vargas (for varga dignity spread).
-- Per §N.4: target_floor = 45 (9 grahas × 5 ayanamshas); aspirational, not a gate.
-- count_sql uses parameterised $1 — the cockpit stats route binds chart_id at runtime.

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
    'ga_condition',
    'ganita',
    29,
    'Graha-sthiti',
    'Planetary Condition Composite',
    'Unified dignity, avastha (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi), motion state, combustion, naisargika/tatkalika/panchadha friendship, graha yuddha, and a 0–1 condition score per graha per ayanamsha.',
    'postgres_table',
    'ga_condition_composite',
    'SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''ga_condition_composite'')',
    45,
    '9_GRAHAS * 5_AYANAMSHAS',
    '{"grahas": 9, "ayanamshas": 5}'::jsonb,
    '9 classical grahas × 5 canonical ayanamshas = 45 rows per chart; one unified condition row per (chart, ayanamsha, graha).',
    ARRAY['ga_positions', 'ga_vargas']::text[],
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
--   DELETE FROM asset_registry WHERE asset_id = 'ga_condition';
--   COMMIT;
-- =============================================================================
