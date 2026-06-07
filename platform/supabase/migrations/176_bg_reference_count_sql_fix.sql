-- Fix bg_reference count_sql: was missing leading SELECT keyword, making it invalid SQL.
-- Also ensures the 5-table sum is consistent with the seed file.
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) AS count'
WHERE asset_id = 'bg_reference';
