-- Migration 329: hard-remove ka_transit_almanac from asset_registry.
-- Asset subsumed by ka_kalasutra/ka_gochara; zero dependents; orphan row.
-- Delete throughput row first (FK constraint), then the registry row.
-- Both deletes are no-ops if already applied.
DELETE FROM asset_throughput WHERE asset_id = 'ka_transit_almanac';
DELETE FROM asset_registry WHERE asset_id = 'ka_transit_almanac';
