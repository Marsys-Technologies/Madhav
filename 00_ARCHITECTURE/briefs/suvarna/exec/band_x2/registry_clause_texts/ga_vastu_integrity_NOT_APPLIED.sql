-- INTENT ONLY, NOT APPLIED: migration 1252 (to be written at the owner's line). This file is the exact
-- text of `asset_registry.integrity_check_sql` for ga_vastu that migration 1252 would set.
-- ORDERING RULE: apply BEFORE ga_vastu is rebuilt in S-L1, and WITH OR AFTER the writer deploy. An OLD
-- writer under this NEW clause, or a NEW writer under the OLD clause, FAILS the post-write integrity gate.
-- (Band table / D1 fallback lane: BAND_X2_LANE_INTENT_v1_0.md section 9.)

-- ga_vastu integrity contract (target table: ga_vastu_planet_direction_map)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_vastu_planet_direction_map_chart_id_ayanamsha_id_graha_key);
-- not re-asserted here (D-CND-03 rule 4).
--
-- Conjunct (d) (FORENSIC Saturn hard-gate) removed per issue #2421 ruling: a hardcoded
-- "Saturn must be 'strengthened'" assertion was structurally in tension with conjunct (c)'s
-- own threshold-derived formula for a boundary-case condition_score (0.68-0.697, just under
-- the writer's 0.7 threshold). Saturn's direction_impact remains fully covered by (c).
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
  -- (compute_direction_impact, ga_vastu_writer.py: <0.4 -> 'weakened', 0.4-0.7 ->
  -- 'neutral', >=0.7 -> 'strengthened', NULL -> 'unknown' (I-28: never 'neutral')) applied to the SAME
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
            WHEN c.condition_score IS NULL THEN 'unknown'
            WHEN c.condition_score < 0.4 THEN 'weakened'
            WHEN c.condition_score < 0.7 THEN 'neutral'
            ELSE 'strengthened'
          END
        )
    )
  )
  AS integrity_passed

