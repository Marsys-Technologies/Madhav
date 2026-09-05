-- 663_bo_samvada_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (L2_W1_ANALYSIS_v1_0.md: S8; C12; §N.8). Adds a real
-- integrity_check_sql for bo_samvada, currently NULL (F-L2-13: all 22 L2 assets
-- have integrity_check_sql = NULL). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- What S8 found, and what's already fixed vs. what isn't
-- --------------------------------------------------------------------------
-- bo_samvada is a DDL-only writer: it CREATE OR REPLACE VIEWs vw_chart_digest
-- (bo_samvada.py) and stores no rows of its own. S8 originally flagged its
-- count_sql as "returns 5 for any chart with any signal row, whether or not
-- the writer ever ran" -- an unexplained constant wearing a measured value's
-- clothes. That half is ALREADY fixed: migration 660 gave bo_samvada a real
-- expected_volume_formula ('AYANAMSHAS', 5) pairing the count(*) = 5 assertion
-- per D-CND-01 -- the "5" is now the derived, documented expectation (one
-- vw_chart_digest row per ayanamsha), not a magic number.
--
-- What is NOT fixed: bo_samvada.integrity_check_sql is still NULL. The deeper
-- defect S8 named survives the count_sql fix, because count_sql only asks
-- "does the view currently return N rows for this chart" -- it says nothing
-- about whether THIS BUILD's writer actually ran. A VIEW is not a table with
-- rows this build inserted: per the FROZEN orchestrator contract, a writer
-- runs on ctx.db_conn with NO commit of its own, so if bo_samvada's CREATE OR
-- REPLACE VIEW fails and rolls back to its savepoint, whatever view existed
-- BEFORE this build (a prior successful build's version, potentially an OLDER
-- shape -- bo_samvada.py's own header records a since-removed broken draft)
-- silently remains in place and keeps answering queries. count_sql cannot
-- read false in that scenario: it would still return 5, correctly, for a
-- build whose bo_samvada step never actually completed this cycle. That is
-- exactly the §N.8 Earned-Signal failure mode -- a signal with no code path
-- that can make it read false on the specific claim it makes.
--
-- The fix: a real conformance check, not a heavier count
-- --------------------------------------------------------------------------
-- integrity_check_sql below asserts three independently-derivable invariants,
-- none of them a bare count(*) = N:
--
--   1. Column-set conformance: vw_chart_digest's live column set matches
--      EXACTLY the 13 columns bo_samvada.py's current _CREATE_VIEW_CLEAN
--      defines. This is the check that actually distinguishes "today's
--      writer ran" from "some vw_chart_digest exists" -- the removed broken
--      draft mentioned in bo_samvada.py's own header comment had a different
--      shape, and any future stale-rollback scenario reverting to an older
--      view definition is very likely to differ here too.
--   2. Cross-table consistency: for every (chart_id, ayanamsha_id) group
--      present in bodha_msr_signals, the view's own msr_signal_count /
--      yoga_count / dosha_count are independently re-derived from the same
--      source table and compared -- a FULL-JOIN-shaped consistency check
--      per C12, not a trust-the-view assertion.
--   3. Completeness: no (chart_id, ayanamsha_id) group with signals in
--      bodha_msr_signals is missing from vw_chart_digest.
--
-- Verified live against production before landing (never a check that has
-- not yet been green -- C12): all three conjuncts evaluate TRUE against the
-- canonical chart today.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (
    (SELECT array_agg(column_name::text ORDER BY column_name)
       FROM information_schema.columns WHERE table_name = 'vw_chart_digest')
    = ARRAY['avg_salience','ayanamsha_id','chart_id','contradiction_count','digest_at',
            'dosha_count','max_salience','msr_signal_count','top_convergence_domains',
            'top_priority_class','trap1_count','weakest_graha','yoga_count']::text[]
  )
  AND NOT EXISTS (
    SELECT 1
    FROM vw_chart_digest v
    JOIN (
      SELECT chart_id, ayanamsha_id,
             count(DISTINCT signal_id) AS msr_signal_count,
             count(DISTINCT signal_id) FILTER (WHERE signal_type_class = 'yoga')  AS yoga_count,
             count(DISTINCT signal_id) FILTER (WHERE signal_type_class = 'dosha') AS dosha_count
      FROM bodha_msr_signals
      GROUP BY chart_id, ayanamsha_id
    ) raw ON raw.chart_id = v.chart_id AND raw.ayanamsha_id = v.ayanamsha_id
    WHERE v.msr_signal_count IS DISTINCT FROM raw.msr_signal_count
       OR v.yoga_count       IS DISTINCT FROM raw.yoga_count
       OR v.dosha_count      IS DISTINCT FROM raw.dosha_count
  )
  AND NOT EXISTS (
    SELECT 1
    FROM (SELECT DISTINCT chart_id, ayanamsha_id FROM bodha_msr_signals) src
    LEFT JOIN vw_chart_digest v USING (chart_id, ayanamsha_id)
    WHERE v.chart_id IS NULL
  )
$ic$
 WHERE asset_id = 'bo_samvada';
