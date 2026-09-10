-- 750_nirmana_l1_ga_ayurdaya_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_ayurdaya: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- First migration in L1's SECOND continuation range, 750-759 (adjudication #1972, Conductor
-- ruling) -- 740-749 (the first continuation, adjudication #1947) is now fully consumed.
--
-- Target table: chart_facts, scoped to fact_category='ayurdaya'.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_ayurdaya integrity contract (target table: chart_facts, scoped to fact_category='ayurdaya')
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_facts_unique_null_formula already exactly matches the natural key -- no distinctness
-- conjunct (D-CND-03 rule 4).
SELECT
  -- (a) classification (stored as fact_value_text on the total_years row) must match the
  -- writer's own classify_ayus() thresholds (alpayu<32, madhyayu 32-64, purnayu>64,
  -- ga_ayurdaya_writer.py:104-110) applied to the SAME row's fact_value_num -- re-derived here
  -- directly rather than restated. 45/45 rows matched live.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'ayurdaya' AND fact_key = 'total_years'
      AND fact_value_text <> (
        CASE WHEN fact_value_num < 32.0 THEN 'alpayu'
             WHEN fact_value_num < 64.0 THEN 'madhyayu'
             ELSE 'purnayu' END
      )
  )
  -- (b) applicable_method's embedded value_jsonb.totals must agree with the SAME (chart,
  -- ayanamsha)'s three separately-stored PINDAYU/NISARGAYU/AMSAYU total_years rows -- a row
  -- whose sibling total_years partner is missing entirely also fails this NOT EXISTS. 15/15
  -- rows matched live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts am
    WHERE am.fact_category = 'ayurdaya' AND am.fact_subject = 'CHART'
      AND am.fact_key = 'applicable_method'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts p, chart_facts n, chart_facts a
        WHERE p.chart_id = am.chart_id AND p.ayanamsha_id = am.ayanamsha_id
          AND p.fact_category = 'ayurdaya' AND p.fact_subject = 'PINDAYU' AND p.fact_key = 'total_years'
          AND n.chart_id = am.chart_id AND n.ayanamsha_id = am.ayanamsha_id
          AND n.fact_category = 'ayurdaya' AND n.fact_subject = 'NISARGAYU' AND n.fact_key = 'total_years'
          AND a.chart_id = am.chart_id AND a.ayanamsha_id = am.ayanamsha_id
          AND a.fact_category = 'ayurdaya' AND a.fact_subject = 'AMSAYU' AND a.fact_key = 'total_years'
          AND (am.fact_value_jsonb->'totals'->>'pindayu')::numeric = p.fact_value_num
          AND (am.fact_value_jsonb->'totals'->>'nisargayu')::numeric = n.fact_value_num
          AND (am.fact_value_jsonb->'totals'->>'amsayu')::numeric = a.fact_value_num
      )
  )
  -- (c) each total_years row's own value must equal the sum of its embedded per_graha
  -- contributions plus lagna_years -- an internal arithmetic-consistency check on the writer's
  -- own JSONB payload. 45/45 rows matched live (0.01-year tolerance for float rounding).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'ayurdaya' AND fact_key = 'total_years'
      AND abs(
        (SELECT COALESCE(SUM(v::numeric), 0) FROM jsonb_each_text(fact_value_jsonb->'per_graha') AS x(k, v))
        + COALESCE((fact_value_jsonb->>'lagna_years')::numeric, 0)
        - fact_value_num
      ) > 0.01
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_ayurdaya';
