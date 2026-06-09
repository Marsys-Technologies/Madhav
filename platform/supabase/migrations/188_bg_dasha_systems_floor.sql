-- migration 188: set bg_dasha_systems target_floor to achieved row count.
BEGIN;
UPDATE asset_registry
   SET target_floor = 18,
       volume_explanation = 'bg_dasha_systems: 18 dasha system rows seeded Tier 1 campaign 2026-06-09. Brief aspiration was 15-18 (floor >=15). Floor set to achieved count per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_dasha_systems';
COMMIT;
