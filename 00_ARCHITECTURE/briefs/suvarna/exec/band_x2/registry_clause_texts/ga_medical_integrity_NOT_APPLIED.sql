
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
  -- (c) FORENSIC gate, re-asserted at the data layer for the canonical chart's own build-time
  -- check (ga_medical_writer.py:275-300, lahiri_chitrapaksha only): Sun debilitated in
  -- Capricorn -> condition_score<0.4 -> 'strong'; Saturn exalted in Libra ->
  -- condition_score must not be in the LOW band (I-28: the cut moved to 0.7; the canonical Saturn
  -- scores 0.680-0.697 = MID/'moderate'). This is the SAME classical claim F-E5 (cycle 9) corrected;
  -- nothing previously re-checked the writer's own build-time assertion against what actually
  -- landed in the table afterward.
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id = 'lahiri_chitrapaksha'
      AND graha = 'Sun' AND indication_strength <> 'strong'
  )
  AND NOT EXISTS (
    SELECT 1 FROM ga_medical
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id = 'lahiri_chitrapaksha'
      AND graha = 'Saturn' AND (indication_strength IS NULL OR indication_strength IN ('strong', 'unknown'))
  )
  AS integrity_passed

