-- 667_bo_sudarshana_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_sudarshana. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Five real invariants, all independently verified live on all three
-- production charts before landing (C12: never a check that has yet to
-- be green):
--
--   1. Tiling: EXACTLY 9 rows per (chart_id, ayanamsha_id) -- one per
--      GRAHAS entry (sudarshana_emitter.py:57; 9 candidates, the same
--      list bo_vargottama_dhana's check bounds against). Verified 9/9 on
--      all 15 (chart x ayanamsha) combinations, no exceptions.
--   2. agreement vocabulary: one of the three values the writer's own
--      code can produce (confirmed_3frame / partial_2frame / contradicted
--      -- sudarshana_emitter.py:137/140/144), not just the two values
--      that happen to appear on today's three charts (no graha on any of
--      them currently agrees across all three frames) -- the check
--      derives its vocabulary from the source, not from what's observed.
--   3. classification vocabulary: class_from_sun/moon/lagna are each one
--      of the six classical categories the priority-ordered classifier
--      can return (trikona / kendra / dusthana / upachaya / maraka /
--      neutral -- sudarshana_emitter.py:98-107).
--   4. house range guard: house_from_sun/moon/lagna are each in [1, 12].
--   5. Cross-column TRUTH, not just vocabulary: agreement and
--      matching_class are re-derived here from class_from_sun/moon/lagna
--      using the writer's own decision logic (sudarshana_emitter.py:
--      135-144) and compared against the stored values. This is the
--      strongest of the five checks -- it does not just validate that
--      the fields hold legal values, it recomputes what they SHOULD say
--      and asserts they match, so a writer bug that stores a legal but
--      wrong agreement/matching_class for a given trio of classes fails
--      this check even though every individual field still passes its
--      own vocabulary guard.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (
    NOT EXISTS (
      SELECT chart_id, ayanamsha_id
      FROM bodha_msr_signals
      WHERE signal_type_class = 'sudarshana_agreement'
      GROUP BY chart_id, ayanamsha_id
      HAVING count(*) != 9
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'sudarshana_agreement'
      AND configuration_jsonb->>'agreement' NOT IN
          ('confirmed_3frame', 'partial_2frame', 'contradicted')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'sudarshana_agreement'
      AND (
        configuration_jsonb->>'class_from_sun' NOT IN
          ('trikona','kendra','dusthana','upachaya','maraka','neutral')
        OR configuration_jsonb->>'class_from_moon' NOT IN
          ('trikona','kendra','dusthana','upachaya','maraka','neutral')
        OR configuration_jsonb->>'class_from_lagna' NOT IN
          ('trikona','kendra','dusthana','upachaya','maraka','neutral')
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'sudarshana_agreement'
      AND (
        (configuration_jsonb->>'house_from_sun')::int NOT BETWEEN 1 AND 12
        OR (configuration_jsonb->>'house_from_moon')::int NOT BETWEEN 1 AND 12
        OR (configuration_jsonb->>'house_from_lagna')::int NOT BETWEEN 1 AND 12
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'sudarshana_agreement'
      AND (
        CASE
          WHEN configuration_jsonb->>'class_from_lagna' = configuration_jsonb->>'class_from_moon'
           AND configuration_jsonb->>'class_from_moon' = configuration_jsonb->>'class_from_sun'
          THEN configuration_jsonb->>'agreement' = 'confirmed_3frame'
           AND configuration_jsonb->>'matching_class' = configuration_jsonb->>'class_from_lagna'
          WHEN configuration_jsonb->>'class_from_lagna' != configuration_jsonb->>'class_from_moon'
           AND configuration_jsonb->>'class_from_moon' != configuration_jsonb->>'class_from_sun'
           AND configuration_jsonb->>'class_from_lagna' != configuration_jsonb->>'class_from_sun'
          THEN configuration_jsonb->>'agreement' = 'contradicted'
           AND configuration_jsonb->>'matching_class' IS NULL
          ELSE configuration_jsonb->>'agreement' = 'partial_2frame'
           AND configuration_jsonb->>'matching_class' = (
             CASE
               WHEN configuration_jsonb->>'class_from_lagna' = configuration_jsonb->>'class_from_moon'
                 THEN configuration_jsonb->>'class_from_lagna'
               WHEN configuration_jsonb->>'class_from_lagna' = configuration_jsonb->>'class_from_sun'
                 THEN configuration_jsonb->>'class_from_lagna'
               ELSE configuration_jsonb->>'class_from_moon'
             END
           )
        END
      ) IS NOT TRUE
  )
$ic$
 WHERE asset_id = 'bo_sudarshana';
