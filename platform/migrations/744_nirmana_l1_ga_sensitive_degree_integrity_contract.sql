-- 744_nirmana_l1_ga_sensitive_degree_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_sensitive_degree:
-- integrity_check_sql was NULL, so the freeze-time detector fell back to count(*) > 0
-- (§N.8 -- an unearned signal).
--
-- Target table: chart_facts, scoped to this asset's own count_sql scope (fact_category IN
-- ('sensitive_degree_check', 'sensitive_point_yogi')). All four conjuncts below target the
-- Yogi-system sub-family (YOGI/AVAYOGI/DUPLICATE_YOGI/SAHAYOGI, sensitive_point_yogi) --
-- ga_sensitive_degree_writer.py's most cross-checkable facet (a chain of exact classical
-- offsets and identity relationships between four derived points), not the other 8
-- sensitive_degree_check facets (mrityu_bhaga, kartari, etc.), which are a candidate for a
-- future F-A14 pass.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_sensitive_degree integrity contract (target table: chart_facts, scoped to
-- sensitive_degree_check + sensitive_point_yogi). D-CND-03: chart-partitioned / row-wise,
-- attribution-preserving. No bare count pin (C12). chart_facts_unique_null_formula already
-- exactly matches the natural key -- no distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) YOGI point_longitude must equal Sun + Moon + 93°20' (mod 360), re-derived from the
  -- SAME (chart, ayanamsha) graha_position longitude_sidereal facts (§N.5), not restated.
  -- Modular-distance tolerance (LEAST(diff, 360-diff)) avoids a false violation at the 0/360
  -- wraparound boundary -- caught live during authoring: without the +720 margin before mod(),
  -- a negative-dividend case returns a NEGATIVE remainder in Postgres numeric mod(), which
  -- silently fails the "> tolerance" comparison regardless of how wrong the value is.
  NOT EXISTS (
    SELECT 1 FROM chart_facts y
    JOIN chart_facts s ON s.chart_id = y.chart_id AND s.ayanamsha_id = y.ayanamsha_id
      AND s.fact_category = 'graha_position' AND s.fact_subject = 'SUN'
      AND s.fact_key = 'longitude_sidereal'
    JOIN chart_facts m ON m.chart_id = y.chart_id AND m.ayanamsha_id = y.ayanamsha_id
      AND m.fact_category = 'graha_position' AND m.fact_subject = 'MOON'
      AND m.fact_key = 'longitude_sidereal'
    WHERE y.fact_category = 'sensitive_point_yogi' AND y.fact_subject = 'YOGI'
      AND y.fact_key = 'point_longitude'
      AND LEAST(
            mod((y.fact_value_num - s.fact_value_num - m.fact_value_num - 93.333333 + 720)::numeric, 360::numeric),
            360 - mod((y.fact_value_num - s.fact_value_num - m.fact_value_num - 93.333333 + 720)::numeric, 360::numeric)
          ) > 0.001
  )
  -- (b) AVAYOGI point_longitude must equal YOGI point_longitude + 186°40' (mod 360), same
  -- modular-distance tolerance and the same +720 margin fix as (a).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts y
    JOIN chart_facts av ON av.chart_id = y.chart_id AND av.ayanamsha_id = y.ayanamsha_id
      AND av.fact_category = 'sensitive_point_yogi' AND av.fact_subject = 'AVAYOGI'
      AND av.fact_key = 'point_longitude'
    WHERE y.fact_category = 'sensitive_point_yogi' AND y.fact_subject = 'YOGI'
      AND y.fact_key = 'point_longitude'
      AND LEAST(
            mod((av.fact_value_num - y.fact_value_num - 186.666667 + 720)::numeric, 360::numeric),
            360 - mod((av.fact_value_num - y.fact_value_num - 186.666667 + 720)::numeric, 360::numeric)
          ) > 0.001
  )
  -- (c) SAHAYOGI must equal DUPLICATE_YOGI's sign and assigned_graha exactly -- the writer's own
  -- docstring: "Sahayogi = the SAME classical quantity as Duplicate-Yogi under its Tajik
  -- Nilakanthi name." A row whose SAHAYOGI partner is missing entirely also fails.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts d
    WHERE d.fact_category = 'sensitive_point_yogi' AND d.fact_subject = 'DUPLICATE_YOGI'
      AND d.fact_key IN ('sign', 'assigned_graha')
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts sy
        WHERE sy.chart_id = d.chart_id AND sy.ayanamsha_id = d.ayanamsha_id
          AND sy.fact_category = 'sensitive_point_yogi' AND sy.fact_subject = 'SAHAYOGI'
          AND sy.fact_key = d.fact_key AND sy.fact_value_text = d.fact_value_text
      )
  )
  -- (d) DUPLICATE_YOGI.assigned_graha must equal the L0 reference_signs authority's lord for
  -- DUPLICATE_YOGI.sign (§N.5) -- never restated from a local table.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts sgn
    JOIN chart_facts g ON g.chart_id = sgn.chart_id AND g.ayanamsha_id = sgn.ayanamsha_id
      AND g.fact_category = 'sensitive_point_yogi' AND g.fact_subject = 'DUPLICATE_YOGI'
      AND g.fact_key = 'assigned_graha'
    WHERE sgn.fact_category = 'sensitive_point_yogi' AND sgn.fact_subject = 'DUPLICATE_YOGI'
      AND sgn.fact_key = 'sign'
      AND NOT EXISTS (
        SELECT 1 FROM reference_signs r
        WHERE lower(r.canonical_name_en) = lower(sgn.fact_value_text)
          AND lower(r.lord) = lower(g.fact_value_text)
      )
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_sensitive_degree';
