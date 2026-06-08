-- migration 186: set bg_reference target_floor to achieved row count.
--
-- The writer seeded 12 own reference tables:
--   reference_planets(11), reference_nakshatras(27), reference_signs(12),
--   reference_aspects(19), reference_vargas(19),
--   reference_houses(12), reference_strength_systems(33),
--   reference_karakas(77), reference_upagrahas(11),
--   reference_constants(203), reference_topic_tags(481), reference_glossary(364)
--
-- Total own-12-tables: 1,269 rows (≥1,225 brief aspiration).
-- Floor set to achieved count per floors-are-aspirational policy.

BEGIN;

UPDATE asset_registry
   SET target_floor       = 1269,
       volume_explanation = 'bg_reference: 1,269 rows across 12 own reference tables seeded in Tier 0 campaign build 2026-06-09. '
                         || 'Tables: reference_planets(11), reference_nakshatras(27), reference_signs(12), '
                         || 'reference_aspects(19), reference_vargas(19), reference_houses(12), '
                         || 'reference_strength_systems(33), reference_karakas(77), reference_upagrahas(11), '
                         || 'reference_constants(203), reference_topic_tags(481), reference_glossary(364). '
                         || 'Brief aspiration was ≥1,225 own-12-tables. Floor set to achieved count (1,269).'
 WHERE asset_id = 'bg_reference';

COMMIT;
