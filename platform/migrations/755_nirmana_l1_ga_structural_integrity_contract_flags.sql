-- 755_nirmana_l1_ga_structural_integrity_contract_flags.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. First follow-up F-A14 widening pass for ga_structural.
-- Migration 745 (cycle 34) covered graha_vargottama_amplification_factor -- 1/57 of
-- ga_structural's owned categories (fact_category_ownership). This adds two more: bhadra_flag
-- and panchaka_flag, taking coverage to 3/57.
--
-- Cross-writer note: unlike graha_vargottama_amplification_factor, these two categories are
-- physically EMITTED by ga_panchanga_writer.py, not ga_structural_writer.py -- but they are
-- OWNED by ga_structural per fact_category_ownership, so ga_structural's integrity_check_sql is
-- the correct place to verify them (D-CND-03 scopes to the owning asset's registry row, not the
-- writer file). deliberately did NOT attempt eclipse_proximity_natal (ga_structural's third
-- remaining single-digit-row-count category): its one stored value is a fixed
-- EXTERNAL_COMPUTATION_REQUIRED placeholder string ("no_eclipse_±15d") on every chart/ayanamsha
-- today -- an honest B.10 floor, not yet a real computation, so there is no independent formula
-- to re-derive against (same disposition as D-L1-62's ga_prashna_judgment: an honest
-- absence-of-check, not a red or green one).
--
-- (c) bhadra_flag.active_at_birth_flag (ga_panchanga_writer.py's _emit_bhadra_flag, karana.id==7)
-- must agree with panchanga_karana.vishti_bhadra_flag (subj KARANA_BIRTH) for the same chart --
-- the SAME source computation (karana.id == 7), stored twice under different fact_categories/
-- subjects (and, in bhadra_flag's case, owned by a different asset than the one that emits it).
-- Separately stored rows from a shared source value -- a genuine cross-category consistency
-- check, not a tautology.
--
-- (d) panchaka_flag.active_at_birth_flag must equal (panchanga_nakshatra_moon.number IN
-- (23,24,25,26,27)) for the same (chart, ayanamsha) -- _emit_panchaka_flag's own PANCHAKA_NAKSHATRAS
-- set, re-derived here directly from the nakshatra number ga_panchanga's own
-- panchanga_nakshatra_moon category already stores, rather than restated.
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries migration 745's two original conjuncts (a)/(b) forward VERBATIM, including conjunct
-- (b), which remains GENUINELY RED TODAY exactly as documented in migration 745 and cycle 42's
-- F-A15 fix (PR #1981): the writer fix landed, but the 4 disagreeing rows on the 2 affected
-- charts will only correct themselves once those charts next rebuild. This migration does not
-- attempt to resolve that -- it is tracked, expected, and not a regression this migration
-- introduces or must fix. Because conjunct (b) is still red, the combined 4-conjunct SELECT
-- below evaluates to false on live production TODAY, exactly as migration 745 already did; the
-- two NEW conjuncts (c)/(d) were verified INDIVIDUALLY (their own NOT EXISTS subquery in
-- isolation) rather than via the full combined SELECT, since the whole conjunction cannot
-- currently read true regardless of what this migration adds. Each new conjunct was
-- EXECUTED against live production and MUTATION-PROVED before landing: re-run against a
-- corruption injected via a real transactional UPDATE inside BEGIN/ROLLBACK and shown to return
-- false; both individually pass clean (return true in isolation) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_structural integrity contract (target: chart_facts, scoped to
-- graha_vargottama_amplification_factor / bhadra_flag / panchaka_flag, 3 of 57 owned categories).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12). No
-- distinctness conjunct -- none of these three categories' natural key needs re-asserting
-- (chart_facts_unique_null_formula already covers it).
SELECT
  -- (a) amplification_factor domain: the writer's own inline comment states it is "1.25 if
  -- vargottama, 1.0 otherwise" -- no third value is ever legitimate.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_vargottama_amplification_factor'
      AND fact_value_num NOT IN (1.0, 1.25)
  )
  -- (b) F-A15: amplification_factor must agree with ga_vargas' own authoritative D9
  -- varga_vargottama_flag (chart_divisionals, §N.5) for the SAME (chart, ayanamsha, graha) --
  -- re-derived here directly rather than restated. STILL GENUINELY RED TODAY on 4/105 rows (2
  -- charts, surya_siddhanta_classical/raman ayanamshas): the underlying writer bug was fixed
  -- (PR #1981, cycle 42), but these 4 rows were computed by the pre-fix writer and will only
  -- self-correct once their 2 charts next rebuild. Carried forward verbatim, not re-scoped or
  -- weakened -- this is exactly migration 745's own tracked, expected RED, not a regression.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_divisionals v
      ON v.chart_id = a.chart_id AND v.ayanamsha_id = a.ayanamsha_id
     AND v.fact_category = 'varga_vargottama_flag' AND v.varga = 'D9'
     AND v.graha = initcap(
       CASE a.fact_subject
         WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
         WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
         WHEN 'SAT' THEN 'Saturn' ELSE a.fact_subject END
     )
    WHERE a.fact_category = 'graha_vargottama_amplification_factor'
      AND (a.fact_value_num = 1.25) <> v.vargottama
  )
  -- (c) bhadra_flag.active_at_birth_flag must agree exactly with panchanga_karana's own
  -- vishti_bhadra_flag (subj KARANA_BIRTH) for the same chart -- the same karana.id==7
  -- computation, stored twice. bhadra_flag carries one ayanamsha-INVARIANT row plus 5
  -- per-ayanamsha copies of the same value (ga_panchanga_writer.py's own comment: "Bhadra flag
  -- (ayanamsha-invariant for karana)") -- joined here on chart_id alone (not ayanamsha_id),
  -- matching that invariance rather than assuming a coincidental per-ayanamsha agreement.
  -- 0/18 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts b
    JOIN chart_facts k ON k.chart_id = b.chart_id
      AND k.fact_category = 'panchanga_karana' AND k.fact_subject = 'KARANA_BIRTH'
      AND k.fact_key = 'vishti_bhadra_flag'
    WHERE b.fact_category = 'bhadra_flag' AND b.fact_key = 'active_at_birth_flag'
      AND b.fact_value_text <> k.fact_value_text
  )
  -- (d) panchaka_flag.active_at_birth_flag must equal (panchanga_nakshatra_moon.number IN
  -- (23,24,25,26,27)) for the same (chart, ayanamsha) -- _emit_panchaka_flag's own
  -- PANCHAKA_NAKSHATRAS set (Roga/Raja/Agni/Chora/Mrityu, nakshatras 23-27), re-derived directly
  -- from the nakshatra number ga_panchanga's own panchanga_nakshatra_moon category already
  -- stores. 0/15 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts p
    JOIN chart_facts n ON n.chart_id = p.chart_id AND n.ayanamsha_id = p.ayanamsha_id
      AND n.fact_category = 'panchanga_nakshatra_moon' AND n.fact_subject = 'NAKSHATRA_MOON_BIRTH'
      AND n.fact_key = 'number'
    WHERE p.fact_category = 'panchaka_flag' AND p.fact_key = 'active_at_birth_flag'
      AND (p.fact_value_text = 'true') <> (n.fact_value_num::int = ANY(ARRAY[23,24,25,26,27]))
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
