-- Migration 268: Register ga_transit_anchors in asset_registry
-- Transit/Gochara Subsystem Gate-1 — 2026-06-17
--
-- Adds ga_transit_anchors to the cockpit catalog.
-- Idempotent: INSERT … ON CONFLICT (asset_id) DO UPDATE.
--
-- Depends on: ga_positions (sidereal positions) and ga_structural (house structure).
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
    'ga_transit_anchors',
    'ganita',
    63,
    'Gochara Sthāna',
    'Transit Natal Anchors (ga_transit_anchors)',
    'Natal position anchors for Gochara transit calculation: sign, house from Moon, and absolute sidereal degree per graha per ayanamsha. Forms the reference base for all transit triggers and vedha evaluation.',
    'postgres_table',
    'ga_transit_anchors',
    'SELECT COUNT(*) FROM ga_transit_anchors WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''ga_transit_anchors'')',
    45,
    '9_GRAHAS * 5_AYANAMSHAS',
    '{"grahas": 9, "ayanamshas": 5}'::jsonb,
    '9 classical grahas × 5 canonical ayanamshas = 45 rows per chart; one anchor row per (chart, ayanamsha, graha).',
    ARRAY['ga_positions', 'ga_structural']::text[],
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
--   DELETE FROM asset_registry WHERE asset_id = 'ga_transit_anchors';
--   COMMIT;
-- =============================================================================
