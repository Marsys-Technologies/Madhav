-- 710_bo_arudha_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_arudha. Transaction ownership belongs to
-- platform/scripts/migrate.ts. First migration of L2's new 710-729 range
-- (660-669 exhausted by the prior six M-14 checks; #1878 ruling).
--
-- bo_arudha (bodha_writers/arudha_emitter.py) emits three signal shapes per
-- (chart_id, ayanamsha_id), none of them a plain fixed count:
--   - exactly ONE 'arudha:AL_bhava_relation' row (unconditional once the AL
--     fact exists);
--   - exactly TWO 'arudha:ARUDHA_A{2,11}_tenancy' rows (one per pada, emitted
--     whether or not the pada is tenanted);
--   - ZERO to NINE 'arudha:AL_conjunction:<GRAHA>' rows (one per graha
--     actually conjunct AL's house -- genuinely variable, GRAHAS has 9
--     entries so 9 is the hard ceiling, and a graha can appear at most once
--     per group).
-- Seven real invariants, all independently verified live against all three
-- production charts before landing (C12: never a check that has yet to be
-- green):
--   1. AL_bhava_relation tiling: exactly 1 per (chart_id, ayanamsha_id).
--   2. Tenancy tiling: exactly 2 per (chart_id, ayanamsha_id).
--   3. Conjunction bound + no-duplicate-graha: <=9 per group, no
--      (chart_id, ayanamsha_id, graha_code) tuple repeated.
--   4. relationship_classification vocabulary, derived from the writer's
--      own emitted literals (classify_house's five categories plus
--      'neutral', 'al_conjunction', 'arudha_pada_tenancy') -- not just the
--      values observed live.
--   5. valence vocabulary per row shape: AL_bhava_relation in
--      {benefic, neutral} only (the writer never assigns 'malefic' to it);
--      AL_conjunction in {benefic, malefic} only (GRAHAS' natural-benefic/
--      natural-malefic split is exhaustive -- no graha is natively neutral).
--   6. Cross-column TRUTH re-derivation: for every AL_bhava_relation row,
--      relationship_classification must equal 'al_' || classify_house(
--      al_house), recomputed here from the writer's own priority-ordered
--      house-membership sets (sudarshana_emitter.py:75-108) -- catches a
--      wrong-but-legal category the vocabulary check alone would miss.
--   7. constituent_facts_array is never empty -- every arudha signal
--      references at least one L1 fact_id (traceability floor).
--
-- Deliberately NOT checked: exact per-chart conjunction/tenancy occupant
-- counts (genuinely chart-data-dependent, not a writer invariant) and
-- domains_affected_array vocabulary (out of this migration's scope; no
-- defect observed there this pass).

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) FILTER (WHERE signal_type_id = 'arudha:AL_bhava_relation') != 1
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) FILTER (WHERE signal_type_id LIKE 'arudha:ARUDHA_A%_tenancy') != 2
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, configuration_jsonb->>'graha_code' AS gc
    FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha' AND signal_type_id LIKE 'arudha:AL_conjunction:%'
    GROUP BY 1, 2, 3
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha' AND signal_type_id LIKE 'arudha:AL_conjunction:%'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) > 9
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha'
      AND relationship_classification NOT IN (
        'al_trikona', 'al_kendra', 'al_dusthana', 'al_upachaya', 'al_maraka',
        'al_neutral', 'al_conjunction', 'arudha_pada_tenancy'
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha' AND signal_type_id = 'arudha:AL_bhava_relation'
      AND valence NOT IN ('benefic', 'neutral')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha' AND signal_type_id LIKE 'arudha:AL_conjunction:%'
      AND valence NOT IN ('benefic', 'malefic')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha' AND signal_type_id = 'arudha:AL_bhava_relation'
      AND relationship_classification != 'al_' || (
        CASE
          WHEN (configuration_jsonb->>'al_house')::int IN (1, 5, 9) THEN 'trikona'
          WHEN (configuration_jsonb->>'al_house')::int IN (1, 4, 7, 10) THEN 'kendra'
          WHEN (configuration_jsonb->>'al_house')::int IN (6, 8, 12) THEN 'dusthana'
          WHEN (configuration_jsonb->>'al_house')::int IN (3, 6, 10, 11) THEN 'upachaya'
          WHEN (configuration_jsonb->>'al_house')::int IN (2, 7) THEN 'maraka'
          ELSE 'neutral'
        END
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'arudha'
      AND (constituent_facts_array IS NULL
           OR array_length(constituent_facts_array, 1) IS NULL
           OR array_length(constituent_facts_array, 1) = 0)
  )
$ic$
 WHERE asset_id = 'bo_arudha';
