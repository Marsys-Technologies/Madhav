-- 239_bg_nakshatra_registry.sql
-- Register bg_nakshatra asset in asset_registry

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active,
    layer_name, layer_index, catalog_status
)
VALUES (
    'bg_nakshatra',
    'brahmagyan',
    15,
    'Nakṣatra-sāraṇī',
    'Nakshatra Reference',
    'Global nakshatra reference — 28 nakshatras (incl. Abhijit), 108 padas, full Ashtakuta + supplementary compatibility matrices (2721 rows).',
    'postgres_table',
    'reference_nakshatra',
    'SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count',
    'SELECT pg_total_relation_size(''reference_nakshatra'')',
    2857,
    'global',
    true,
    'Brahmagyan',
    'L0',
    'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
    english_name = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    count_sql = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor,
    layer_name = EXCLUDED.layer_name,
    layer_index = EXCLUDED.layer_index,
    catalog_status = EXCLUDED.catalog_status;
