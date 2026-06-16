-- migration 291 — ga_prashna asset_registry entry
-- layer='ganita', layer_index='L1', sort_order=7, has_substeps=true
-- depends_on: ga_positions (needed to read planetary positions), bg_prashna_rules
-- count_sql: counts judgment rows for a given chart_id
BEGIN;
INSERT INTO asset_registry (
    asset_id, layer, layer_index, sort_order, english_name, english_description,
    storage_type, scope, depends_on, count_sql, target_floor, has_substeps, is_active
) VALUES (
    'ga_prashna',
    'ganita',
    'L1',
    7,
    'Prashna Horary Judgment',
    'Per-prashna-chart horary judgment: Prashna-Lagna by each method, querent/quesited significators, Tajik Ithasala/Eesarpha analysis, and fructification timing. Only computed when a prashna chart exists for the chart_id; returns 0 rows for natal charts.',
    'postgres_table',
    'per_chart',
    ARRAY['ga_positions', 'bg_prashna_rules'],
    '(SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1)',
    0,
    true,
    true
) ON CONFLICT (asset_id) DO UPDATE SET
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    depends_on          = EXCLUDED.depends_on,
    count_sql           = EXCLUDED.count_sql,
    has_substeps        = EXCLUDED.has_substeps,
    is_active           = EXCLUDED.is_active;
COMMIT;
