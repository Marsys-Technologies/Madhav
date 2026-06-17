-- FIX 1 (P1-B BLOCKER): Four invalid count_sqls that fail when executed directly
-- The stored expressions are bare arithmetic without SELECT wrapper; stats route executes them raw
-- Wrap each in SELECT ... AS count to make them valid SQL statements

UPDATE asset_registry
SET count_sql = 'SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques) AS count'
WHERE asset_id = 'bg_prashna_rules';

UPDATE asset_registry
SET count_sql = 'SELECT (SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials) AS count'
WHERE asset_id = 'bg_vastu_directions';

UPDATE asset_registry
SET count_sql = 'SELECT COUNT(*) FROM bg_transit_engine'
WHERE asset_id = 'bg_transit_engine';

UPDATE asset_registry
SET count_sql = 'SELECT COUNT(*) FROM bg_transit_rules'
WHERE asset_id = 'bg_transit_rules';
