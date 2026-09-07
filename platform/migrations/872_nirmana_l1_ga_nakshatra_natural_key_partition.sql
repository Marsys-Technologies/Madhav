-- 872_nirmana_l1_ga_nakshatra_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Fifth of seven natural_key_partition backfills authorized by the
-- Conductor's ruling on adjudication #2180 (2026-09-07). Prior four:
-- ga_positions (868, PR #2205, merged), ga_ayurdaya (869, PR #2208,
-- merged), ga_sensitive_degree (870, PR #2209), ga_sade_sati (871,
-- PR #2212).
--
-- ga_nakshatra's registered @register writer
-- (pipeline/orchestrator/writers/ga_nakshatra.py) composes rows from two
-- source modules: ga_nakshatra_emitters.py (12 categories --
-- graha_nakshatra_join, graha_pada_join, cusp_kp_lords,
-- graha_degree_flags, graha_gandanta, graha_kp_lords, graha_tara_bala,
-- nakshatra_cogravity, nakshatra_conjunction, nakshatra_dispositor,
-- nakshatra_exchange, nakshatra_statistics) and ga_kp_significators.py
-- via its emit_kp_significators() call (2 more -- kp_house_significators,
-- kp_planet_significations). 14 total, verified directly against every
-- fact_category literal in both source files.
--
-- Distinct from get_nakshatra.ts's own NAKSHATRA_CATEGORIES const, which
-- claims 16: this session's F-B32 slice 3 (cycle 151) already found the
-- other two the tool overclaims -- nakshatra_lord_placement and
-- nakshatra_cross_ayanamsha -- have zero live rows and no writer call
-- site in either source file, confirmed again here. natural_key_
-- partition describes what the writer OWNS, not what a serving tool
-- claims to cover.
--
-- Confirmed no overlap: grepped all six sibling writers for all 14
-- category strings, zero hits.

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category IN (graha_nakshatra_join, graha_pada_join, cusp_kp_lords, graha_degree_flags, graha_gandanta, graha_kp_lords, graha_tara_bala, nakshatra_cogravity, nakshatra_conjunction, nakshatra_dispositor, nakshatra_exchange, nakshatra_statistics, kp_house_significators, kp_planet_significations)'
 WHERE asset_id = 'ga_nakshatra'
   AND natural_key_partition IS NULL;
