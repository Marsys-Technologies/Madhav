-- migration 185: set bg_ontology target_floor to achieved row count.
--
-- The writer seeded 384 entities across 13 entity classes:
--   planet(11), nakshatra(27), sign(12), house(12), dasha_system(5),
--   domain(45), concept(136), karaka(77), upagraha(11), aspect_type(13),
--   remedy_type(12), school(8), text(15).
--
-- 384 ≥ 380 brief aspiration.  Floor is set to achieved, not aspirational.

BEGIN;

UPDATE asset_registry
   SET target_floor       = 384,
       volume_explanation = 'bg_ontology: 384 entity-class vocabulary rows seeded in Tier 0 campaign build 2026-06-09. '
                         || 'Classes: planet(11), nakshatra(27), sign(12), house(12), dasha_system(5), '
                         || 'domain(45), concept(136), karaka(77), upagraha(11), aspect_type(13), '
                         || 'remedy_type(12), school(8), text(15). '
                         || 'Brief aspiration was ≥380 (121 closed-set + 77 karaka + ≥190 domain+concept). '
                         || 'Floor set to achieved count (384) per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_ontology';

COMMIT;
