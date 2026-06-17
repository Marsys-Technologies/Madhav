-- Migration 307: Update asset_registry target_floors + count_sql after L1 Phase 3 Enrichment
-- Amendments 1, 2, 3 add per-varga strength/avastha + Tier-1 sensitive points.
-- Per §N.4: target_floor = achieved count after build (aspirational, not a gate).
-- Per §N.4 Cockpit truth: count_sql must cover all rows the writer emits.

-- ga_strength (Amendment 1: per-varga bala categories)
-- Added: graha_sthana_bala_per_varga, graha_drik_bala_per_varga,
--        graha_kala_bala_per_varga, graha_cheshta_bala_per_varga
-- ashtakavarga_bindu_per_varga + ashtakavarga_pinda_sarva_per_varga already
-- covered by existing `ashtakavarga_%` clause.
-- New clause `graha_%_bala_per_varga` covers all 4 new per-varga bala categories.
-- Achieved count for chart 482012f1: 11,936 (up from 2,184 pre-enrichment).
UPDATE asset_registry
SET
  count_sql = '
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE ''graha_shadbala_%''
      OR fact_category IN (''graha_ishta_phala'', ''graha_kashta_phala'')
      OR fact_category LIKE ''%vimsopaka%''
      OR fact_category LIKE ''ashtakavarga_%''
      OR fact_category LIKE ''%bhava_bala%''
      OR fact_category = ''graha_saptavargaja_bala_component''
      OR fact_category LIKE ''graha_%_bala_per_varga''
    )
',
  target_floor = 11936
WHERE asset_id = 'ga_strength';

-- ga_sensitive (Amendment 3: Tier-1 classical sensitive points)
-- Added: sensitive_point_gulika_mandi, sun_derived_upagraha, special_lagna,
--        esoteric_point_sphuta_fertility (covered by esoteric_point_%),
--        esoteric_point_yogi_system (covered by esoteric_point_%),
--        nakshatra_pada_sensitive (existing but was missing from count_sql — 80 rows).
-- Achieved count for chart 482012f1: 8,610 (up from 8,055 floor, 8,195 actual pre-enrichment).
UPDATE asset_registry
SET
  count_sql = '
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category IN (
        ''upagraha_position'', ''saturn_derived_point'', ''saham_position'',
        ''karaka_chara_position'', ''karakamsa_position'', ''swamsa_position'',
        ''arudha_pada'', ''midpoint'', ''aprakasha_position'',
        ''lal_kitab_special_point'', ''maharsi_specific_point'', ''bhrigu_nadi_point'',
        ''sensitive_point_gulika_mandi'', ''sun_derived_upagraha'', ''special_lagna'',
        ''nakshatra_pada_sensitive''
      )
      OR fact_category LIKE ''esoteric_point_%''
      OR fact_category LIKE ''kp_%''
      OR fact_category LIKE ''tajik_%''
    )
',
  target_floor = 8610
WHERE asset_id = 'ga_sensitive';
