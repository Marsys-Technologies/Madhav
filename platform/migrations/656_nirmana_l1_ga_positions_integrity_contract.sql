-- 656_nirmana_l1_ga_positions_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_positions: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- SCOPE. ga_positions owns exactly two fact_categories in the shared chart_facts table --
-- 'graha_position' and 'graha_sign_attributes' (ga_positions_writer.py's own module docstring
-- names both explicitly; confirmed live, no other fact_category appears with either writer's
-- source_calculation tag). This is the DAG root: zero declared dependencies, reads nothing from
-- the DB (D-L1-3), so it cannot inherit any other asset's error -- every conjunct here is a pure
-- self-consistency check on this writer's own output.
--
-- Standard: D-CND-03 -- chart-partitioned, attribution-preserving, no bare count pin (C12).
-- chart_facts_unique_null_formula / chart_facts_unique_with_formula are already DB-enforced and
-- match this writer's own ON CONFLICT target (ga_positions_writer.py:547) exactly, so no
-- distinctness conjunct appears here (D-CND-03 rule 4).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_positions integrity contract (graha_position + graha_sign_attributes fact_categories;
-- target table: chart_facts, shared with other L1 writers -- see this migration's header).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced; not re-asserted here (D-CND-03 rule 4).
SELECT
  -- (a) cross-category consistency: graha_position's own `sign` (text) must name the same sign
  -- as graha_sign_attributes' `sign_num` (1-indexed, confirmed live: LAGNA=1=Aries,
  -- JUP=9=Sagittarius) for the SAME (chart, ayanamsha, graha) -- two atomic facts the writer
  -- emits about the identical longitude, which must never disagree with each other.
  NOT EXISTS (
    SELECT 1 FROM (
      SELECT p.chart_id, p.ayanamsha_id, p.fact_subject, p.fact_value_text AS sign,
             a.fact_value_num AS sign_num
      FROM chart_facts p
      JOIN chart_facts a
        ON a.chart_id = p.chart_id AND a.ayanamsha_id = p.ayanamsha_id AND a.fact_subject = p.fact_subject
       AND a.fact_category = 'graha_sign_attributes' AND a.fact_key = 'sign_num'
      WHERE p.fact_category = 'graha_position' AND p.fact_key = 'sign'
    ) t
    WHERE t.sign IS DISTINCT FROM (ARRAY['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra',
                                          'Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'])[t.sign_num::int]
  )
  -- (b) longitude_sidereal (graha_position) must equal (sign_num-1)*30 + degree_in_sign
  -- (graha_sign_attributes) for the same (chart, ayanamsha, graha) -- the writer's own
  -- decomposition of one continuous longitude into sign + degree-within-sign must round-trip
  -- back to the whole-circle value it was decomposed from.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT lon.chart_id, lon.ayanamsha_id, lon.fact_subject, lon.fact_value_num AS lon_val,
             sn.fact_value_num AS sign_num, deg.fact_value_num AS deg_val
      FROM chart_facts lon
      JOIN chart_facts sn
        ON sn.chart_id = lon.chart_id AND sn.ayanamsha_id = lon.ayanamsha_id AND sn.fact_subject = lon.fact_subject
       AND sn.fact_category = 'graha_sign_attributes' AND sn.fact_key = 'sign_num'
      JOIN chart_facts deg
        ON deg.chart_id = lon.chart_id AND deg.ayanamsha_id = lon.ayanamsha_id AND deg.fact_subject = lon.fact_subject
       AND deg.fact_category = 'graha_sign_attributes' AND deg.fact_key = 'degree_in_sign'
      WHERE lon.fact_category = 'graha_position' AND lon.fact_key = 'longitude_sidereal'
    ) t
    WHERE abs(t.lon_val - ((t.sign_num - 1) * 30 + t.deg_val)) > 0.01
  )
  -- (c) FORENSIC gate, permanently re-asserted at the data layer (this asset's own module
  -- docstring: "FORENSIC gate MUST pass before any INSERT"; the writer enforces it at build
  -- time via forensic_gate(), but nothing previously re-checked it against what actually landed
  -- in the table afterward). Scoped to the canonical chart only -- these are native-specific
  -- birth facts, not a claim about any other chart.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'graha_position' AND fact_subject = 'SUN' AND fact_key = 'sign'
      AND fact_value_text <> 'Capricorn'
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'graha_position' AND fact_subject = 'MOON' AND fact_key = 'nakshatra'
      AND fact_value_text <> 'Purva Bhadrapada'
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'graha_position' AND fact_subject = 'LAGNA' AND fact_key = 'sign'
      AND fact_value_text <> 'Aries'
  )
  -- (d) range guard: chart_facts carries no CHECK on fact_value_num at all. pada (nakshatra
  -- quarter) is 1-4 by classical definition; house_d1 is 1-12.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_position' AND fact_key = 'pada'
      AND (fact_value_num < 1 OR fact_value_num > 4)
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_position' AND fact_key = 'house_d1'
      AND (fact_value_num < 1 OR fact_value_num > 12)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_positions';
