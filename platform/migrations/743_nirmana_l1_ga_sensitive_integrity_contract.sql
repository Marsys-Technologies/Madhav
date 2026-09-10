-- 743_nirmana_l1_ga_sensitive_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_sensitive: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: chart_facts, a SHARED table scoped to the SAME 18-category-family scope as this
-- asset's own count_sql (17 explicit fact_categories, the esoteric_point_%/tajik_% LIKE
-- families, and bhava_arudha). This is GA5's ~30-category sensitive-points writer
-- (ga_sensitive_writer.py, ~3,200 lines) -- three conjuncts below are a bounded first F-A14 pass,
-- not exhaustive coverage of every category's internal formula.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_sensitive integrity contract (target table: chart_facts, scoped to the count_sql's own
-- 18-category-family scope: 17 explicit fact_categories, esoteric_point_%/tajik_% LIKE families,
-- and bhava_arudha). D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare
-- count pin (C12). chart_facts_unique_null_formula already exactly matches the natural key -- no
-- distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) verification_pass_status vocabulary: the writer's own module docstring claims "Every row
  -- two-pass verified (zero single, zero divergent_flagged)" -- absent-prerequisite rows floor to
  -- 'floored' instead of fabricating a value (no third state exists). Confirmed live: exactly
  -- two_pass_verified/floored appear in this scope today (26,250 + 75), nothing else.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE (fact_category IN (
             'upagraha_position', 'saturn_derived_point', 'saham_position',
             'karaka_chara_position', 'karakamsa_position', 'swamsa_position',
             'arudha_pada', 'midpoint', 'aprakasha_position',
             'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point',
             'sensitive_point_gulika_mandi', 'sun_derived_upagraha', 'special_lagna',
             'nakshatra_pada_sensitive', 'kp_ruling_planets_natal', 'kp_cuspal_significators'
           )
        OR fact_category LIKE 'esoteric_point_%'
        OR fact_category LIKE 'tajik_%'
        OR fact_category = 'bhava_arudha')
      AND verification_pass_status NOT IN ('two_pass_verified', 'floored')
  )
  -- (b) special_lagna's sign_lord must equal the L0 reference_signs authority's lord for the
  -- stored sign (§N.5) -- never restated from a local table. 105/105 rows matched live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts l ON l.chart_id = s.chart_id AND l.ayanamsha_id = s.ayanamsha_id
      AND l.fact_subject = s.fact_subject AND l.fact_category = 'special_lagna'
      AND l.fact_key = 'sign_lord'
    WHERE s.fact_category = 'special_lagna' AND s.fact_key = 'sign'
      AND NOT EXISTS (
        SELECT 1 FROM reference_signs r
        WHERE lower(r.canonical_name_en) = lower(s.fact_value_text)
          AND lower(r.lord) = lower(l.fact_value_text)
      )
  )
  -- (c) bhava_arudha's classical Parashari 2-exception rule (BPHS ch.32 v.2-3, cited in
  -- _build_bhava_arudha_rows, ga_sensitive_writer.py:1619): an arudha can never land in its own
  -- origin house, nor the 7th house counted from the origin -- the writer shifts by 10 signs when
  -- the raw formula would produce either. Re-asserted here directly against the stored house_d1.
  -- 0/210 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_arudha' AND fact_key = 'house_d1'
      AND (
        fact_value_num::int = substring(fact_subject from 'BHAVA_ARUDHA_A(\d+)')::int
        OR fact_value_num::int = (((substring(fact_subject from 'BHAVA_ARUDHA_A(\d+)')::int - 1 + 6) % 12) + 1)
      )
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_sensitive';
