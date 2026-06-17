-- Migration 305: Fix target_floors stale after Phase B enrichment (L0 Brahmagyan Closure Pass)
-- bg_prashna_rules: 5 Tajik yogas added in Phase B → 36 + 5 = 41
-- bg_transit_rules: 9 Venus gochara phala rows added in Phase B → 41 + 9 = 50
-- Per §N.4: target_floor = achieved count after build (aspirational, not a gate).
UPDATE asset_registry SET target_floor = 41 WHERE asset_id = 'bg_prashna_rules';
UPDATE asset_registry SET target_floor = 50 WHERE asset_id = 'bg_transit_rules';
