-- 877_nirmana_l1_ga_sensitive_count_sql_precedence_fix.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W3 IMPLEMENT. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Fixes F-A4/F-B2/F-B12 (L1_W2_DECIDE_v1_0.md #93: "count_sql omits rows the
-- writer writes and the serving layer serves... Cockpit truth is wrong")
-- for `ga_sensitive` specifically -- independently re-verified this cycle
-- (the id-group's other two members, `ga_positions`/`ga_sensitive_degree`,
-- were already found correct: their count_sql category lists exactly match
-- the verified writer-ownership lists from migrations 868/876 and 870
-- respectively, no further action needed for them).
--
-- `ga_sensitive`'s existing count_sql has a genuine SQL operator-precedence
-- bug, not a wrong category list -- its category coverage is otherwise
-- exactly correct (independently re-derived and cross-checked against
-- migration 874's own verified 37-category list: 18 explicit literals + a
-- `LIKE 'esoteric_point_%'` prefix (15 categories) + a `LIKE 'tajik_%'`
-- prefix (3 categories) + `bhava_arudha` = 37, matching exactly). The bug:
--
--   WHERE chart_id = $1
--     AND ( fact_category IN (...) OR fact_category LIKE 'esoteric_point_%'
--           OR fact_category LIKE 'tajik_%' )
--    OR fact_category = 'bhava_arudha'
--
-- SQL's AND binds tighter than OR, so this parses as
-- `(chart_id = $1 AND (...)) OR (fact_category = 'bhava_arudha')` -- the
-- trailing `bhava_arudha` branch is NOT scoped by chart_id at all. Confirmed
-- live this has real consequences, not a theoretical footgun: `bhava_arudha`
-- rows exist for all 3 production charts (210 rows each). Run for the
-- canonical chart, the buggy query returns 9195; the correctly-parenthesized
-- query returns 8775 -- a 420-row inflation, exactly the other two charts'
-- 210+210 `bhava_arudha` rows leaking in unscoped. Fix: fold the
-- `bhava_arudha` branch inside the same parenthesized OR-group so it stays
-- under the `chart_id = $1` AND, verified to reproduce the correct 8775
-- count for the canonical chart (independently re-run against live data
-- before writing this migration, not assumed from reading the SQL alone).

UPDATE asset_registry
   SET count_sql = $sql$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category IN (
        'upagraha_position', 'saturn_derived_point', 'saham_position',
        'karaka_chara_position', 'karakamsa_position', 'swamsa_position',
        'arudha_pada', 'midpoint', 'aprakasha_position',
        'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point',
        'sensitive_point_gulika_mandi', 'sun_derived_upagraha', 'special_lagna',
        'nakshatra_pada_sensitive', 'kp_ruling_planets_natal', 'kp_cuspal_significators',
        'bhava_arudha'
      )
      OR fact_category LIKE 'esoteric_point_%'
      OR fact_category LIKE 'tajik_%'
    )
$sql$
 WHERE asset_id = 'ga_sensitive';
