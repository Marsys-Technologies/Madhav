-- FIX 8 (P3-D): Fix NULL target_table for bg_transit_engine and bg_transit_rules
-- Both were registered without target_table; primary tables match the asset_id

UPDATE asset_registry
SET target_table = 'bg_transit_engine'
WHERE asset_id = 'bg_transit_engine' AND target_table IS NULL;

UPDATE asset_registry
SET target_table = 'bg_transit_rules'
WHERE asset_id = 'bg_transit_rules' AND target_table IS NULL;
