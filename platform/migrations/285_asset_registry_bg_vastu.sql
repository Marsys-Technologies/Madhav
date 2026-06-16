-- Migration 285: Register bg_vastu_directions and bg_vastu_direction_remedials in asset_registry
-- Astrovastu subsystem Gate-1 — L0 Brahmagyan static reference assets.
-- Idempotent: INSERT ON CONFLICT (asset_id) DO UPDATE.

BEGIN;

-- ── bg_vastu_directions ───────────────────────────────────────────────────────

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
    'bg_vastu_directions',
    'brahmagyan',
    55,
    'Vastu-dik',
    'Vastu Direction–Graha Reference',
    'Classical Vastu Shastra direction–graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color, and classical citation (Mayamata Ch.6). Also seeds bg_vastu_direction_remedials (~22 rows) with 2–3 remedies per direction.',
    'postgres_table',
    'bg_vastu_directions',
    '(SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials)',
    'SELECT pg_total_relation_size(''bg_vastu_directions'') + pg_total_relation_size(''bg_vastu_direction_remedials'')',
    30,
    '8_DIRECTIONS + 22_REMEDIALS',
    '{"directions": 8, "remedials_per_direction": "2-3", "total_remedials": 22}'::jsonb,
    '8 compass directions + ~22 remedial rows; all rows carry classical_citation.',
    ARRAY[]::text[],
    'global',
    true,
    false,
    'data',
    'Brahmagyan',
    'L0',
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
--   DELETE FROM asset_registry WHERE asset_id IN ('bg_vastu_directions');
--   COMMIT;
-- =============================================================================
