-- migration 189: set bg_doshas target_floor to achieved row count.
BEGIN;
UPDATE asset_registry
   SET target_floor = 50,
       volume_explanation = 'bg_doshas: 50 dosha rows seeded Tier 1 campaign 2026-06-09. Brief aspiration was 50 (design target 50-65). Floor set to achieved count per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_doshas';
COMMIT;
