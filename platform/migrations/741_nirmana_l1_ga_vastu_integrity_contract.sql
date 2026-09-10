-- 741_nirmana_l1_ga_vastu_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_vastu: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: ga_vastu_planet_direction_map, a DEDICATED table with an existing UNIQUE
-- (chart_id, ayanamsha_id, graha) -- no distinctness conjunct appears here (D-CND-03 rule 4).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_vastu integrity contract (target table: ga_vastu_planet_direction_map)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_vastu_planet_direction_map_chart_id_ayanamsha_id_graha_key);
-- not re-asserted here (D-CND-03 rule 4).
SELECT
  -- (a) indication_tier is a single spec-required constant (ga_vastu_writer.py:13:
  -- "indication_tier: 'traditional_vastu' (§N per-spec epistemic tier)"). No row may read
  -- otherwise.
  NOT EXISTS (
    SELECT 1 FROM ga_vastu_planet_direction_map WHERE indication_tier <> 'traditional_vastu'
  )
  -- (b) direction vocabulary: the eight classical Vastu compass points only.
  AND NOT EXISTS (
    SELECT 1 FROM ga_vastu_planet_direction_map
    WHERE direction NOT IN ('East', 'West', 'North', 'South',
                             'Northeast', 'Northwest', 'Southeast', 'Southwest')
  )
  -- (c) direction_impact must equal the writer's own threshold formula
  -- (compute_direction_impact, ga_vastu_writer.py:58-72: <0.4 -> 'weakened', 0.4-0.7 ->
  -- 'neutral', >=0.7 -> 'strengthened', NULL -> 'neutral') applied to the SAME
  -- (chart, ayanamsha, graha)'s condition_score in ga_condition_composite, re-derived here
  -- directly rather than restated. A row whose cross-table partner is missing entirely also
  -- fails this NOT EXISTS.
  AND NOT EXISTS (
    SELECT 1 FROM ga_vastu_planet_direction_map m
    WHERE NOT EXISTS (
      SELECT 1 FROM ga_condition_composite c
      WHERE c.chart_id = m.chart_id AND c.ayanamsha_id = m.ayanamsha_id AND c.graha = m.graha
        AND m.direction_impact = (
          CASE
            WHEN c.condition_score IS NULL THEN 'neutral'
            WHEN c.condition_score < 0.4 THEN 'weakened'
            WHEN c.condition_score < 0.7 THEN 'neutral'
            ELSE 'strengthened'
          END
        )
    )
  )
  -- (d) FORENSIC gate, re-asserted at the data layer for the writer's own build-time check
  -- (ga_vastu_writer.py:171-179, all five ayanamshas -- no ayanamsha scope, unlike ga_medical's
  -- lahiri-only check): Saturn exalted in Libra -> direction_impact must be 'strengthened' for
  -- the canonical chart. The writer's module docstring also documents a prior Sun assertion
  -- ("Sun debilitated in Capricorn") that was REMOVED as astrologically incorrect (Sun
  -- debilitates in Libra, not Capricorn) -- not re-encoded here, since it was never a real
  -- FORENSIC anchor to begin with.
  AND NOT EXISTS (
    SELECT 1 FROM ga_vastu_planet_direction_map
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND graha = 'Saturn' AND direction_impact <> 'strengthened'
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_vastu';
