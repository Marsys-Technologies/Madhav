-- 721_bo_upaya_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_upaya. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Twelfth migration of L2's 710-729 range.
--
-- bo_upaya is a large writer (2257 lines) that writes several tables
-- (bodha_rm_resonances, bodha_rm_remedy_prescriptions, and sibling rollup
-- tables bodha_rm_chart_summary / bodha_rm_dosha_remedy_bundles /
-- bodha_rm_pattern_remedies plus dasha-windowed rows). This migration is
-- deliberately scoped to the two primary tables the module's own
-- docstring names -- the rollup tables are a reasonable follow-up, not
-- squeezed into this one.
--
-- Sixteen invariants, all independently verified live against all three
-- production charts before landing (C12). Caught and corrected THREE
-- wrong guesses against source/live data before shipping:
--   - verification_pass_status is NOT the UNVERIFIED_DEFAULT ('single')
--     on either table -- both bodha_rm_resonances (writers/bo_upaya.py:
--     1686) and bodha_rm_remedy_prescriptions (:1847) hardcode
--     'documented_approximation' at their own emit sites; UNVERIFIED_
--     DEFAULT is used elsewhere in this writer (dasha-windowed rows, out
--     of this migration's scope), not for these two tables.
--   - resonance_match_score is NOT bounded [0,1]: resonance_match_score_v1
--     (formulas.py:352-374) is a multiplicative formula with typology_bias
--     / cross_tradition_boost / pattern_alignment terms that can push the
--     result above 1.0 -- confirmed live (max 1.0105 on production data).
--     Checked >= 0 only, matching what the formula's own additive/
--     multiplicative structure (all non-negative factors) actually
--     guarantees.
--
-- bodha_rm_resonances (9 invariants):
--   1. weakest_rank_in_chart in [1, 9] -- exactly one rank per graha,
--      unconditional `for graha in KNOWN_GRAHAS:` loop (no skip/continue).
--   2. resonance_score never negative.
--   3. graha is one of the 9 canonical names.
--   4. remedy_priority_class is one of the 4 values _priority_class() can
--      return (critical, high, medium, low -- rank-relative thirds).
--   5. verification_pass_status always 'documented_approximation'.
--   6. resonance_score_formula_version always the current constant 'v1.0'.
--   7. ayanamsha_id in the 5-canonical set.
--   8. No duplicate (chart_id, ayanamsha_id, graha) row.
--   9. No duplicate (chart_id, ayanamsha_id, weakest_rank_in_chart) --
--      ranks are a real permutation of 1..9 per group, not just bounded.
--
-- bodha_rm_remedy_prescriptions (7 invariants):
--   10. verification_pass_status always 'documented_approximation'.
--   11. target_graha is one of the 9 canonical names.
--   12. resonance_match_score never negative (see note above).
--   13. match_score_formula_version always the current constant 'v1.0'.
--   14. remedy_label_human never NULL or empty.
--   15. target_resonance_id always resolves to a real bodha_rm_resonances
--       row (both tables written together in the same run -- a real FK-
--       style guarantee, not a cross-build staleness risk like the CGM
--       tables).
--   16. At most 3 prescriptions per (chart_id, ayanamsha_id,
--       target_resonance_id) -- the writer's own "top 3 by confidence".

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances WHERE weakest_rank_in_chart < 1 OR weakest_rank_in_chart > 9
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_resonances WHERE resonance_score < 0)
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances
    WHERE graha NOT IN ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances WHERE remedy_priority_class NOT IN ('critical','high','medium','low')
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_resonances WHERE verification_pass_status != 'documented_approximation')
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_resonances WHERE resonance_score_formula_version != 'v1.0')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances
    WHERE ayanamsha_id NOT IN ('lahiri_chitrapaksha','raman','krishnamurti','surya_siddhanta_classical','true_chitra')
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, graha FROM bodha_rm_resonances GROUP BY 1, 2, 3 HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, weakest_rank_in_chart FROM bodha_rm_resonances GROUP BY 1, 2, 3 HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE verification_pass_status != 'documented_approximation'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions
    WHERE target_graha NOT IN ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
  )
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE resonance_match_score < 0)
  AND NOT EXISTS (SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE match_score_formula_version != 'v1.0')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions WHERE remedy_label_human IS NULL OR remedy_label_human = ''
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_rm_remedy_prescriptions p
    WHERE NOT EXISTS (SELECT 1 FROM bodha_rm_resonances r WHERE r.resonance_id = p.target_resonance_id)
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, target_resonance_id
    FROM bodha_rm_remedy_prescriptions
    GROUP BY 1, 2, 3 HAVING count(*) > 3
  )
$ic$
 WHERE asset_id = 'bo_upaya';
