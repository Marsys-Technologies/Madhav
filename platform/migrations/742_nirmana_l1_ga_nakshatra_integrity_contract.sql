-- 742_nirmana_l1_ga_nakshatra_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_nakshatra: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: chart_facts, a SHARED table scoped to ga_nakshatra's 16 fact_categories
-- (graha_nakshatra_join, graha_pada_join, nakshatra_lord_placement, graha_kp_lords,
-- cusp_kp_lords, graha_gandanta, graha_degree_flags, nakshatra_dispositor, nakshatra_exchange,
-- nakshatra_conjunction, nakshatra_cogravity, graha_tara_bala, nakshatra_statistics,
-- nakshatra_cross_ayanamsha, kp_house_significators, kp_planet_significations), matching this
-- asset's own count_sql scope. chart_facts_unique_null_formula (chart_id, ayanamsha_id,
-- fact_category, fact_subject, fact_key, build_id) already exactly matches the natural key --
-- no distinctness conjunct (D-CND-03 rule 4).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_nakshatra integrity contract (target table: chart_facts, scoped to 16 fact_categories)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_facts_unique_null_formula (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key,
-- build_id) already exactly matches the natural key -- no distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) FORENSIC gate re-asserted at the data layer for the writer's own build-time check
  -- (_forensic_gate, ga_nakshatra.py:283-295, all five ayanamshas -- no ayanamsha scope, same as
  -- the writer's own guard): Moon must be in Purva Bhadrapada (nakshatra_id=25) for the canonical
  -- chart.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'graha_nakshatra_join' AND fact_subject = 'MOON'
      AND fact_key = 'nakshatra_id_ref' AND fact_value_num <> 25
  )
  -- (b) verification_pass_status honesty (§N.7 item 4 / §N.8): a two_pass_verified or
  -- divergent_flagged status may appear ONLY on the four (fact_category, fact_key) pairs a real
  -- detector runs for -- _nakshatra_pada_verdicts's second-pass re-derivation
  -- (graha_nakshatra_join.nakshatra_id_ref, graha_pada_join.pada_number_ref) and the KP
  -- significator emitter's own two_pass_verdict cross-check against bg_kp_sublord_division
  -- (kp_planet_significations.star_lord, kp_planet_significations.sub_lord). Every other row in
  -- this asset's 16 fact_categories keeps the honest UNVERIFIED_DEFAULT ('single') -- a verified
  -- claim anywhere else would be an unearned status with no detector behind it.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category IN ('graha_nakshatra_join', 'graha_pada_join', 'nakshatra_lord_placement',
                             'graha_kp_lords', 'cusp_kp_lords', 'graha_gandanta',
                             'graha_degree_flags', 'nakshatra_dispositor', 'nakshatra_exchange',
                             'nakshatra_conjunction', 'nakshatra_cogravity', 'graha_tara_bala',
                             'nakshatra_statistics', 'nakshatra_cross_ayanamsha',
                             'kp_house_significators', 'kp_planet_significations')
      AND verification_pass_status IN ('two_pass_verified', 'divergent_flagged')
      AND NOT (
        (fact_category = 'graha_nakshatra_join' AND fact_key = 'nakshatra_id_ref')
        OR (fact_category = 'graha_pada_join' AND fact_key = 'pada_number_ref')
        OR (fact_category = 'kp_planet_significations' AND fact_key = 'star_lord')
        OR (fact_category = 'kp_planet_significations' AND fact_key = 'sub_lord')
      )
  )
  -- (c) nakshatra_id_ref must equal the independent 27-fold division of the SAME
  -- (chart, ayanamsha, subject)'s own longitude_sidereal fact (ga_positions authority, §N.5) --
  -- re-derived here directly (floor(lon / (360/27)) + 1) rather than restated. A row whose
  -- longitude partner is missing entirely also fails this NOT EXISTS.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts n
    WHERE n.fact_category = 'graha_nakshatra_join' AND n.fact_key = 'nakshatra_id_ref'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts p
        WHERE p.chart_id = n.chart_id AND p.ayanamsha_id = n.ayanamsha_id
          AND p.fact_subject = n.fact_subject
          AND p.fact_category = 'graha_position' AND p.fact_key = 'longitude_sidereal'
          AND n.fact_value_num::int = (floor(p.fact_value_num / (360.0/27.0))::int + 1)
      )
  )
  -- (d) cross-ayanamsha sentinel internal consistency: a stable_nakshatra_id row (emitted only
  -- when all 5 ayanamshas agree, ga_nakshatra.py:468-478) implies its sibling
  -- nak_5ay_consistency row for the same subject must read the unanimous "5/5" -- the two rows
  -- are written from the same len(unique)==1 branch and must never disagree about whether
  -- agreement was unanimous.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    WHERE s.fact_category = 'nakshatra_cross_ayanamsha' AND s.fact_key = 'stable_nakshatra_id'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts c
        WHERE c.chart_id = s.chart_id AND c.fact_subject = s.fact_subject
          AND c.fact_category = 'nakshatra_cross_ayanamsha' AND c.fact_key = 'nak_5ay_consistency'
          AND c.fact_value_text = '5/5'
      )
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_nakshatra';
