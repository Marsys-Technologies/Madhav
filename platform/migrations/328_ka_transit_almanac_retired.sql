-- Migration 328: mark ka_transit_almanac as intentionally retired (subsumed by ka_kalasutra).
-- is_active stays false; catalog_status 'RETIRED' triggers neutral grey UI instead of red NOT MIGRATED.
UPDATE asset_registry
SET catalog_status = 'RETIRED'
WHERE asset_id = 'ka_transit_almanac';
