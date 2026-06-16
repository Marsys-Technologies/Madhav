-- Migration 262 (CORRECTED 2026-06-17): Register bg_prashna_rules in asset_registry
-- Original version used nonexistent column 'display_name'; correct column is 'english_name'.
-- Also fixed: layer='brahmagyan' (not 'L0'), storage_type='postgres_table', is_active added,
-- wrapped in BEGIN/COMMIT.

BEGIN;

INSERT INTO asset_registry (
    asset_id,
    layer,
    sort_order,
    english_name,
    english_description,
    storage_type,
    scope,
    depends_on,
    count_sql,
    target_floor,
    has_substeps,
    is_active
) VALUES (
    'bg_prashna_rules',
    'brahmagyan',
    5,
    'Prashna Horary Rules',
    'Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.',
    'postgres_table',
    'global',
    ARRAY[]::TEXT[],
    '(SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques)',
    36,
    false,
    true
) ON CONFLICT (asset_id) DO UPDATE SET
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    count_sql           = EXCLUDED.count_sql,
    target_floor        = EXCLUDED.target_floor,
    sort_order          = EXCLUDED.sort_order,
    is_active           = EXCLUDED.is_active;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'bg_prashna_rules';
--   COMMIT;
-- =============================================================================
