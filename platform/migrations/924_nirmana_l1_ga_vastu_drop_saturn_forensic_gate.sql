-- 924_nirmana_l1_ga_vastu_drop_saturn_forensic_gate.sql
--
-- NIRMĀṆA L1 Gaṇita — issue #2421 RULED (Conductor cycle 140, native-authorized D-NATIVE-12):
-- drop conjunct (d) from ga_vastu's integrity_check_sql (migration 741). Mirrors the Sun
-- FORENSIC guard's earlier removal from the same writer for the same reason: a hardcoded
-- "graha X must have direction_impact = Y" assertion is structurally in tension with
-- direction_impact's own threshold-derived formula (compute_direction_impact,
-- ga_vastu_writer.py) — Saturn's condition_score on the canonical chart (482012f1) is
-- 0.68-0.697 across all 5 ayanamshas, just under the writer's own >=0.7 "strengthened"
-- threshold, so the writer correctly computes 'neutral' while the hardcoded gate demanded
-- 'strengthened'. ga_vastu_writer.py's matching Saturn assertion block removed in the same
-- change (companion PR).
--
-- Conjuncts (a)/(b)/(c) are unchanged: (c) already fully re-derives and verifies every
-- graha's direction_impact (including Saturn's) from live ga_condition_composite data via
-- the writer's own formula — Saturn's derived value remains covered, just no longer subject
-- to an independent hardcoded override.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before
-- landing (same discipline as migration 741).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
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
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_vastu';
