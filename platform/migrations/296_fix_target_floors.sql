-- FIX 2 (P2-E): Update 6 stale target_floors to match actual row counts
-- Actual counts verified: bg_texts=10651, bg_rules=2912, bg_compendium_index=9538,
--   bg_dasha_systems=18, bg_vastu_directions=32, bg_transit_rules=41

UPDATE asset_registry SET target_floor = 10651 WHERE asset_id = 'bg_texts';
UPDATE asset_registry SET target_floor = 2912  WHERE asset_id = 'bg_rules';
UPDATE asset_registry SET target_floor = 9538  WHERE asset_id = 'bg_compendium_index';
UPDATE asset_registry SET target_floor = 18    WHERE asset_id = 'bg_dasha_systems';
UPDATE asset_registry SET target_floor = 32    WHERE asset_id = 'bg_vastu_directions';
UPDATE asset_registry SET target_floor = 41    WHERE asset_id = 'bg_transit_rules';
