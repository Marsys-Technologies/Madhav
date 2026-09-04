-- 643_nirmana_l0_w3_batch2_registry_accuracy.sql
--
-- NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md L0-W3 IMPLEMENT (L0_W2_DECIDE_v1_0.md
-- §2 NOW items 19, 25). Two independent, additive registry-accuracy fixes,
-- batched in one migration because both are pure asset_registry text/value
-- corrections with no schema change and no interaction.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

-- Item 19: bg_muhurta_lattice.target_floor (91,477) is stale relative to the
-- writer's own binding v2-corpus minimum (164,575, enforced by migration
-- 628's integrity_check_sql since the pancangika/lagna widening landed in
-- migration 530). Live count is 164,886 -- comfortably above the true floor.
-- CLAUDE.md §N.4: floors track achieved counts; a floor that has drifted
-- below what the writer itself now guarantees should be raised to match.
UPDATE asset_registry
   SET target_floor = 164575
 WHERE asset_id = 'bg_muhurta_lattice';

-- Item 25: bg_vastu_directions.english_description says "~22 rows" for
-- bg_vastu_direction_remedials; the actual/floor/integrity-checked count is
-- 24 (2-3 remedies x 8 directions, mostly 3 each) -- confirmed live.
UPDATE asset_registry
   SET english_description =
     'Classical Vastu Shastra direction-graha associations: 8 compass directions each mapped '
     || 'to a ruling graha, secondary graha, element, favorable color, and classical citation '
     || '(Mayamata Ch.6). Also seeds bg_vastu_direction_remedials (24 rows) with 2-3 remedies '
     || 'per direction.'
 WHERE asset_id = 'bg_vastu_directions';

-- Forward reversal (safe at any time -- both are additive value corrections,
-- not schema changes): re-run with the original target_floor (91477) and
-- english_description ("~22 rows") restored.
