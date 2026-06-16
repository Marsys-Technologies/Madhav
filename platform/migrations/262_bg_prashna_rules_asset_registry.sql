-- Migration 262: Register bg_prashna_rules in asset_registry
INSERT INTO asset_registry (asset_id, display_name, layer, scope, asset_type, depends_on,
    count_sql, target_floor, sort_order, has_substeps)
VALUES (
    'bg_prashna_rules',
    'Prashna Horary Rules (bg_prashna_rules)',
    'L0',
    'global',
    'brahmagyan',
    ARRAY[]::TEXT[],
    '(SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques)',
    36,
    5,
    false
) ON CONFLICT (asset_id) DO UPDATE SET display_name = EXCLUDED.display_name;
