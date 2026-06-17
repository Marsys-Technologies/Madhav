-- FIX 3 (P2-A): bg_reference.target_table stale pointer
-- Currently points at reference_nakshatras (deprecated/superseded table)
-- Canonical reference table for planets is reference_planets

UPDATE asset_registry
SET target_table = 'reference_planets'
WHERE asset_id = 'bg_reference';
