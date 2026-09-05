-- 715_bo_drishti_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_drishti. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Sixth migration of L2's 710-729 range.
--
-- bo_drishti's `for question_type, cfg in QUESTION_TYPE_CONFIG.items():` loop
-- (writers/bo_drishti.py:310) is unconditional -- no `continue`, no signal-
-- gating -- so it writes exactly one bodha_question_lenses row per
-- (chart_id, ayanamsha_id, question_type). QUESTION_TYPE_CONFIG has exactly
-- 12 keys. Five invariants, all independently verified live against all
-- three production charts before landing (C12):
--
--   1. Tiling by NAME: the exact 12-question_type set is present per (chart_id,
--      ayanamsha_id), not just count(*) = 12 -- a writer bug that dropped one
--      canonical question_type and duplicated another would still pass a bare
--      count check.
--   2. points_only_assertion is always TRUE -- the module's own "TWO ABSOLUTE
--      GUARDS" docstring: "A lens POINTS, never PRE-ANSWERS." Hardcoded at the
--      single emit site (bo_drishti.py:264); this check verifies the guard was
--      never silently dropped.
--   3. lens_template_version is always 'classical_v1.0' -- the module constant,
--      unaffected by the F-114 formula version bump (see item below).
--   4. template_element_ids_jsonb, wildcard_element_ids_jsonb, and
--      all_relevant_ranked_jsonb are never NULL -- a lens with no computed
--      content would be a silent no-op writer succeeding on nothing.
--   5. citation_ref is never NULL or empty (traceability floor).
--
-- Deliberately NOT checked: lens_formula_version. The current source constant
-- is 'drishti_formula_v1.1' (F-114: "the stored ranked order is now TOTAL...
-- instead of salience-only") but live production shows 'drishti_formula_v1.0'
-- on all 180 rows across all three charts -- bo_drishti has not been rebuilt
-- since that formula change. Asserting v1.1 would be false on 100% of current
-- data (C12: a check that has never been green is a proposal, not a gate).
-- Not filed separately -- this is the same pending-rebuild pattern already on
-- record for several other L2 assets this campaign (bo_bimba domain nodes,
-- bo_samskara embeddings), not a new distinct finding.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1
    FROM (SELECT DISTINCT chart_id, ayanamsha_id FROM bodha_question_lenses) c
    CROSS JOIN unnest(ARRAY[
      'career','wealth','marriage','health','character','spirituality',
      'education','progeny','longevity','foreign_travel','property','siblings'
    ]) AS qt(question_type)
    LEFT JOIN bodha_question_lenses l
      ON l.chart_id = c.chart_id AND l.ayanamsha_id = c.ayanamsha_id
     AND l.question_type = qt.question_type
    WHERE l.lens_id IS NULL
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id
    FROM bodha_question_lenses
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) != 12
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_question_lenses WHERE points_only_assertion IS NOT TRUE
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_question_lenses WHERE lens_template_version != 'classical_v1.0'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_question_lenses
    WHERE template_element_ids_jsonb IS NULL
       OR wildcard_element_ids_jsonb IS NULL
       OR all_relevant_ranked_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_question_lenses WHERE citation_ref IS NULL OR citation_ref = ''
  )
$ic$
 WHERE asset_id = 'bo_drishti';
