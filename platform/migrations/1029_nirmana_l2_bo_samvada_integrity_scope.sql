-- 1029_nirmana_l2_bo_samvada_integrity_scope.sql
--
-- NIRMANA L2 bo_samvada closure: replace the earlier table-wide conformance
-- expression with an independently re-derivable assertion over every chart
-- and ayanamsha represented by the view.  The orchestrator executes registry
-- integrity SQL without a chart bind parameter, so an apparent `$1` scope
-- would fail rather than constrain the check.  All-chart verification is the
-- correct executable scope for this shared DDL view.
--
-- This does not revise migration 663: applied migrations are immutable.
--
-- It proves the claims the digest makes that were previously omitted:
--   * weakest_graha is the L1 Shadbala-rupa minimum, not an RM priority rank;
--   * each top_convergence_domains element is eligible static-natal data;
--   * the array contains no more than five rows and is deterministically
--     ordered, including ties; and
--   * aggregation and completeness hold for every chart/ayanamsha pair, not
--     merely a selected chart while another pair has drifted.

UPDATE asset_registry
SET integrity_check_sql = $ic$
WITH expected_columns AS (
  SELECT ARRAY[
    'avg_salience', 'ayanamsha_id', 'chart_id', 'contradiction_count',
    'digest_at', 'dosha_count', 'max_salience', 'msr_signal_count',
    'top_convergence_domains', 'top_priority_class', 'trap1_count',
    'weakest_graha', 'yoga_count'
  ]::text[] AS names
),
raw_counts AS (
  SELECT chart_id, ayanamsha_id,
         count(DISTINCT signal_id) AS msr_signal_count,
         count(DISTINCT signal_id) FILTER (WHERE signal_type_class = 'yoga') AS yoga_count,
         count(DISTINCT signal_id) FILTER (WHERE signal_type_class = 'dosha') AS dosha_count
  FROM bodha_msr_signals
  GROUP BY chart_id, ayanamsha_id
),
expected_weakest AS (
  SELECT DISTINCT ON (chart_id, ayanamsha_id)
         chart_id, ayanamsha_id,
         CASE fact_subject
           WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
           WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
           WHEN 'SAT' THEN 'Saturn'
         END AS weakest_graha
  FROM chart_facts
  WHERE fact_category = 'graha_shadbala_total'
    AND fact_key = 'rupa'
    AND fact_value_num IS NOT NULL
    AND fact_subject IN ('SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT')
  ORDER BY chart_id, ayanamsha_id, fact_value_num ASC, fact_subject ASC
),
expected_priority AS (
  SELECT DISTINCT ON (chart_id, ayanamsha_id)
         chart_id, ayanamsha_id, remedy_priority_class AS top_priority_class
  FROM bodha_rm_resonances
  ORDER BY chart_id, ayanamsha_id, weakest_rank_in_chart ASC NULLS LAST, graha ASC
),
expected_domains AS (
  SELECT cv.chart_id, cv.ayanamsha_id,
         jsonb_agg(
           jsonb_build_object('domain', cv.domain, 'score', cv.convergence_score, 'n', cv.convergence_count)
           ORDER BY cv.convergence_score DESC NULLS LAST, cv.convergence_count DESC NULLS LAST, cv.domain ASC
         ) FILTER (WHERE cv.rank <= 5) AS domains
  FROM (
    SELECT chart_id, ayanamsha_id, domain, convergence_score, convergence_count,
           row_number() OVER (
             PARTITION BY chart_id, ayanamsha_id
             ORDER BY convergence_score DESC NULLS LAST, convergence_count DESC NULLS LAST, domain ASC
           ) AS rank
    FROM bodha_convergence
    WHERE snapshot_type = 'static_natal'
  ) cv
  GROUP BY cv.chart_id, cv.ayanamsha_id
)
SELECT
  (SELECT array_agg(column_name::text ORDER BY column_name)
   FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'vw_chart_digest')
    = (SELECT names FROM expected_columns)
  AND NOT EXISTS (
    SELECT 1
    FROM raw_counts raw
    FULL JOIN vw_chart_digest v USING (chart_id, ayanamsha_id)
    WHERE raw.chart_id IS NULL OR v.chart_id IS NULL
       OR v.msr_signal_count IS DISTINCT FROM raw.msr_signal_count
       OR v.yoga_count IS DISTINCT FROM raw.yoga_count
       OR v.dosha_count IS DISTINCT FROM raw.dosha_count
  )
  AND NOT EXISTS (
    SELECT 1
    FROM raw_counts raw
    JOIN vw_chart_digest v USING (chart_id, ayanamsha_id)
    LEFT JOIN expected_weakest ew USING (chart_id, ayanamsha_id)
    WHERE v.weakest_graha IS DISTINCT FROM ew.weakest_graha
  )
  AND NOT EXISTS (
    SELECT 1
    FROM raw_counts raw
    JOIN vw_chart_digest v USING (chart_id, ayanamsha_id)
    LEFT JOIN expected_priority ep USING (chart_id, ayanamsha_id)
    WHERE v.top_priority_class IS DISTINCT FROM ep.top_priority_class
  )
  AND NOT EXISTS (
    SELECT 1
    FROM vw_chart_digest v
    LEFT JOIN expected_domains ed USING (chart_id, ayanamsha_id)
    WHERE v.top_convergence_domains IS DISTINCT FROM ed.domains
  )
$ic$
WHERE asset_id = 'bo_samvada';
