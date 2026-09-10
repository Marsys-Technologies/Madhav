-- 740_nirmana_l1_ga_medical_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_medical: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- First migration in L1's newly-granted continuation range (740-749, adjudication #1947,
-- Conductor ruling) -- the original 650-659 range was fully consumed at migration 659.
--
-- Target table: ga_medical, a DEDICATED table with an existing UNIQUE (chart_id, ayanamsha_id,
-- graha) -- no distinctness conjunct appears here (D-CND-03 rule 4).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
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
  -- (indication_strength_from_score, ga_medical_writer.py:71-90) applied to the SAME
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
            WHEN c.condition_score <= 0.6 THEN 'moderate'
            ELSE 'mild'
          END
        )
    )
  )
  -- (c) FORENSIC gate, re-asserted at the data layer for the canonical chart's own build-time
  -- check (ga_medical_writer.py:275-300, lahiri_chitrapaksha only): Sun debilitated in
  -- Capricorn -> condition_score<0.4 -> 'strong'; Saturn exalted in Libra ->
  -- condition_score>0.6 -> 'mild'. This is the SAME classical claim F-E5 (cycle 9) corrected;
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
      AND graha = 'Saturn' AND indication_strength <> 'mild'
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_medical';
