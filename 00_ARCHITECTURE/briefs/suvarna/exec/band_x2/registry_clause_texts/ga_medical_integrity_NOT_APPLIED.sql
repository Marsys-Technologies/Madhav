-- INTENT ONLY, NOT APPLIED: migration 1252 (to be written at the owner's line). This file is the exact
-- text of `asset_registry.integrity_check_sql` for ga_medical that migration 1252 would set.
-- ORDERING RULE: apply BEFORE ga_medical is rebuilt in S-L1, and WITH OR AFTER the writer deploy. An OLD
-- writer under this NEW clause, or a NEW writer under the OLD clause, FAILS the post-write integrity gate.
-- (Band table / D1 fallback lane: BAND_X2_LANE_INTENT_v1_0.md section 9.)

-- ga_medical integrity contract (target table: ga_medical)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_medical_chart_id_ayanamsha_id_graha_key); not
-- re-asserted here (D-CND-03 rule 4).
SELECT
  -- (a) §A Ethical Framework, encoded as a data-layer invariant: this writer's own module
  -- docstring and inline comments mark indication_tier='jyotish_indication' and
  -- not_diagnosis=TRUE as "NON-NEGOTIABLE" (ga_medical_writer.py:18,28,331-332) -- the exact
  -- disclosure discipline the project's stated mission (probabilistic, calibrated, auditable
  -- outputs, "not a fortune-telling product") depends on for this asset's domain. No row may
  -- ever read otherwise.
  NOT EXISTS (
    SELECT 1 FROM ga_medical WHERE indication_tier <> 'jyotish_indication'
  )
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical WHERE not_diagnosis IS DISTINCT FROM true
  )
  -- (b) indication_strength must equal the writer's own threshold formula
  -- (indication_strength_from_score, ga_medical_writer.py: the ONE band table of I-28, 0.4 / 0.7) applied to the SAME
  -- (chart, ayanamsha, graha)'s condition_score in ga_condition_composite -- re-derived here
  -- directly, not restated. A row whose cross-table partner is missing entirely also fails
  -- this NOT EXISTS (an absent match can never satisfy the equality inside it).
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical m
    WHERE NOT EXISTS (
      SELECT 1 FROM ga_condition_composite c
      WHERE c.chart_id = m.chart_id AND c.ayanamsha_id = m.ayanamsha_id AND c.graha = m.graha
        AND m.indication_strength = (
          CASE
            WHEN c.condition_score IS NULL THEN 'unknown'
            WHEN c.condition_score < 0.4 THEN 'strong'
            WHEN c.condition_score < 0.7 THEN 'moderate'
            ELSE 'mild'
          END
        )
    )
  )
  -- (c) NONE. The Saturn conjunct (migration 740) and the Sun conjunct (migration 740) are both REMOVED
  -- (SS rulings 2026-10-02): each hard-coded one chart (482012f1-...), one ayanamsha and one graha and
  -- asserted a label about that one value. An asset's integrity clause must be true for ANY chart, so
  -- this clause is chart-independent: (a) tier/disclosure constants, (b) label = the band-table rule.
  -- Saturn's and Sun's canonical scores and bands are pinned by golden tests
  -- (tests/test_ga_medical_saturn_golden.py, tests/test_ga_medical_sun_golden.py) instead.
  AS integrity_passed

