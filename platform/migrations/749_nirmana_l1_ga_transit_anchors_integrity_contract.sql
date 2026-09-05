-- 749_nirmana_l1_ga_transit_anchors_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_transit_anchors: integrity_check_sql
-- was NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- LAST migration in L1's 740-749 continuation range (adjudication #1947) -- confirmed free via a
-- re-check of every open PR's branch plus main immediately before authoring.
--
-- Target table: ga_transit_anchors, a DEDICATED table with an existing UNIQUE
-- (chart_id, ayanamsha_id, graha) -- no distinctness conjunct here (D-CND-03 rule 4).
--
-- No FORENSIC gate re-encoded here: the writer's own build-time FORENSIC gate (fixed under F-D22,
-- cycle 28) asserts Moon's NAKSHATRA, which this table does not store (only natal_sign, which is
-- correctly ayanamsha-DEPENDENT and legitimately varies across ayanamshas -- re-asserting a single
-- expected sign value here would be exactly the F-D22 landmine this asset already had fixed).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_transit_anchors integrity contract (target table: ga_transit_anchors)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- UNIQUE (chart_id, ayanamsha_id, graha) already exactly matches the natural key -- not
-- re-asserted here (D-CND-03 rule 4).
SELECT
  -- (a) natal_degree_absolute must equal the SAME (chart, ayanamsha, graha)'s own
  -- graha_position.longitude_sidereal fact in chart_facts (§N.5, the writer's own source) --
  -- re-derived here directly rather than restated. 135/135 rows matched live.
  NOT EXISTS (
    SELECT 1 FROM ga_transit_anchors t
    JOIN chart_facts f ON f.chart_id = t.chart_id AND f.ayanamsha_id = t.ayanamsha_id
      AND f.fact_category = 'graha_position' AND f.fact_key = 'longitude_sidereal'
      AND f.fact_subject = (CASE t.graha
            WHEN 'sun' THEN 'SUN' WHEN 'moon' THEN 'MOON' WHEN 'mars' THEN 'MAR'
            WHEN 'mercury' THEN 'MER' WHEN 'jupiter' THEN 'JUP' WHEN 'venus' THEN 'VEN'
            WHEN 'saturn' THEN 'SAT' WHEN 'rahu' THEN 'RAH_MEAN' WHEN 'ketu' THEN 'KET_MEAN'
            ELSE upper(t.graha) END)
    WHERE abs(t.natal_degree_absolute - f.fact_value_num) > 0.001
  )
  -- (b) natal_house_from_moon must equal the writer's own _house_from_moon formula
  -- (ga_transit_anchors.py:58-67: 1-based house count from Moon's own sign) applied to the SAME
  -- (chart, ayanamsha)'s Moon row -- re-derived here directly rather than restated. 135/135 rows
  -- matched live (including Moon's own row, house=1).
  AND NOT EXISTS (
    SELECT 1 FROM ga_transit_anchors t
    JOIN ga_transit_anchors m ON m.chart_id = t.chart_id AND m.ayanamsha_id = t.ayanamsha_id
      AND m.graha = 'moon'
    JOIN (VALUES ('aries',1),('taurus',2),('gemini',3),('cancer',4),('leo',5),('virgo',6),
                 ('libra',7),('scorpio',8),('sagittarius',9),('capricorn',10),('aquarius',11),
                 ('pisces',12)) AS sn_p(sign, num) ON sn_p.sign = lower(t.natal_sign)
    JOIN (VALUES ('aries',1),('taurus',2),('gemini',3),('cancer',4),('leo',5),('virgo',6),
                 ('libra',7),('scorpio',8),('sagittarius',9),('capricorn',10),('aquarius',11),
                 ('pisces',12)) AS sn_m(sign, num) ON sn_m.sign = lower(m.natal_sign)
    WHERE t.natal_house_from_moon <> (((sn_p.num - sn_m.num) % 12 + 12) % 12) + 1
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_transit_anchors';
