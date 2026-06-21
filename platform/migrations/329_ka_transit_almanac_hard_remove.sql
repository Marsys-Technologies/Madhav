-- Migration 329: hard-remove ka_transit_almanac from asset_registry.
-- Asset subsumed by ka_kalasutra/ka_gochara; zero dependents; orphan row.
-- Migration 328 previously set catalog_status='RETIRED'; this completes the removal.
DELETE FROM asset_registry WHERE asset_id = 'ka_transit_almanac';
