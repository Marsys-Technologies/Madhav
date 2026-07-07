-- Migration 419: JL-026 close — remove the ga_structural -> ga_condition DAG edge
-- (the migration-416 edge is no longer needed; graha_yuddha is now single-writer).
-- Created: 2026-07-07
--
-- Migration 416 added `ga_condition` to ga_structural.depends_on purely to
-- serialize the ONE overlapping pair whose idempotency DELETEs clobbered each
-- other (graha_avastha_lajjitadi, graha_avastha_sayanadi — later JL-022 — and
-- the third dual-write graha_yuddha found afterward). JL-022 moved lajjitadi/
-- sayanadi to ga_condition-only (migrations 417/418). JL-026 audit (2026-07-07)
-- proved graha_yuddha was the LAST remaining co-written chart_facts category,
-- and that ga_structural is its de-facto sole authority anyway (running after
-- ga_condition via this edge, its delete+re-insert clobbered ga_condition's
-- rows every build — ga_condition's write never survived).
--
-- Fix landed with this migration: ga_condition no longer emits the graha_yuddha
-- category (ga_condition_writer._build_d1_avastha_rows), leaving ga_structural
-- (_build_graha_yuddha_rows, two_pass_verified) as sole writer. With ZERO
-- co-written categories remaining, the delete scopes are disjoint, so the
-- serialization edge is obsolete. ga_structural does NOT read any ga_condition-
-- produced category (verified: it reads positions/vargas/strength/nakshatra/
-- sensitive categories, all covered by its other direct edges), so dag_edge_guard
-- stays green. This is the documented DOWN of migration 416.
--
-- NOTE: ga_structural also carries a direct ga_strength/ga_vargas/ga_positions/
-- ga_nakshatra/ga_sensitive/ga_dashas/ga_panchanga edge set in the DB; only the
-- ga_condition edge is removed here.

BEGIN;

UPDATE asset_registry
SET depends_on = array_remove(depends_on, 'ga_condition')
WHERE asset_id = 'ga_structural'
  AND 'ga_condition' = ANY(depends_on);

COMMIT;

-- DOWN (re-instates the migration-416 edge; only valid if graha_yuddha is made
-- dual-write again, which it is not):
-- UPDATE asset_registry
-- SET depends_on = (
--   SELECT array_agg(DISTINCT d ORDER BY d)
--   FROM unnest(depends_on || ARRAY['ga_condition']) AS d
-- )
-- WHERE asset_id = 'ga_structural' AND NOT ('ga_condition' = ANY(depends_on));
