-- 657_nirmana_l1_ga_panchanga_forensic_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_panchanga: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- SCOPE. ga_panchanga writes 31 distinct fact_categories into the shared chart_facts table
-- (measured live: panchanga_tithi, panchanga_vara, panchanga_yoga, panchanga_karana,
-- panchanga_rahu_kalam, ... 27 more). This contract covers FOUR: panchanga_tithi,
-- panchanga_vara, panchanga_yoga, panchanga_karana -- the four whose `name` fact is one of
-- CLAUDE.md's own seven FORENSIC birth anchors (Tithi = Shukla Tritiya, Vara = Ravivara,
-- Yoga = Shiva, Karana = Garaja). The other 27 categories are NOT covered here and are a
-- separate future unit, not silently assumed clean.
--
-- Standard: D-CND-03 -- chart-partitioned, attribution-preserving, no bare count pin (C12).
-- chart_facts_unique_null_formula / chart_facts_unique_with_formula are already DB-enforced and
-- match this writer's own ON CONFLICT target (ga_panchanga_writer.py:1290) exactly, so no
-- distinctness conjunct appears here (D-CND-03 rule 4).
--
-- Note on ayanamsha_id: these four categories are written under the ayanamsha-independent
-- pseudo-value 'INVARIANT' (measured live), not any of the five real ayanamshas -- panchanga
-- elements (tithi/vara/yoga/karana) are computed from the Moon/Sun's TROPICAL positions and the
-- classical lunar calendar, genuinely ayanamsha-independent in this writer's model. A first-draft
-- mutation test filtered on ayanamsha_id='lahiri_chitrapaksha' and matched nothing at all --
-- confirmed the actual value before writing any conjunct that depends on it.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_panchanga integrity contract (panchanga_tithi / panchanga_vara / panchanga_yoga /
-- panchanga_karana ONLY -- the four FORENSIC-anchored categories; target table: chart_facts,
-- shared with other writers -- see this migration's header for the 27 categories NOT covered).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced; not re-asserted here (D-CND-03 rule 4).
SELECT
  -- (a) FORENSIC gate, permanently re-asserted at the data layer. This asset's own build-time
  -- forensic_gate() enforces these four anchors before INSERT (ga_panchanga_writer.py:239,
  -- 265-267); nothing previously re-checked them against what actually landed. Scoped to the
  -- canonical chart only -- these are native-specific birth facts, never a claim about any
  -- other chart.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'panchanga_tithi' AND fact_key = 'name'
      AND fact_value_text <> 'Shukla Tritiya'
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'panchanga_vara' AND fact_key = 'name'
      AND fact_value_text <> 'Ravivara'
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'panchanga_yoga' AND fact_key = 'name'
      AND fact_value_text <> 'Shiva'
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'panchanga_karana' AND fact_key = 'name'
      AND fact_value_text <> 'Garaja'
  )
  -- (b) tithi's own paksha/number_in_lunar_month relationship, re-derived from the writer's own
  -- definition (ga_panchanga_writer.py:337-340: paksha = "Shukla" if tithi_num<=15 else
  -- "Krishna"; num_in_paksha always 1-15 regardless of which half). Both halves use the same
  -- 1-15 range -- a number outside it, or a paksha outside the two-value vocabulary, cannot be
  -- a real classical tithi.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'panchanga_tithi' AND fact_key = 'paksha'
      AND fact_value_text NOT IN ('Shukla', 'Krishna')
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'panchanga_tithi' AND fact_key = 'number_in_lunar_month'
      AND (fact_value_num < 1 OR fact_value_num > 15)
  )
  -- (c) null/empty guard: chart_facts carries no CHECK on fact_value_text at all. The `name`
  -- fact is each of these four categories' one required identity field -- an empty or NULL
  -- name is a silently-dropped classical designation, not a valid absence.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category IN ('panchanga_tithi', 'panchanga_vara', 'panchanga_yoga', 'panchanga_karana')
      AND fact_key = 'name'
      AND (fact_value_text IS NULL OR fact_value_text = '')
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_panchanga';
