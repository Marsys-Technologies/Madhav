-- 756_nirmana_l1_ga_structural_integrity_contract_vargottama_varga.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Second follow-up F-A14 widening pass for ga_structural.
-- Migration 745 (cycle 34) covered graha_vargottama_amplification_factor; migration 755 (cycle
-- 46) added bhadra_flag/panchaka_flag (3/57). This adds vargottama_per_varga, taking coverage to
-- 4/57.
--
-- vargottama_per_varga (ga_structural_writer.py's _build_varga_relationship_rows) computes, for
-- every varga except D1, `is_vargottama = (d1_sign == varga_sign)` where varga_sign is read via
-- the get_sign()/varga_state closure -- itself backed by _load_varga_positions(), which reads
-- chart_divisionals' fact_category='varga_position' rows (GA6/ga_vargas' own sign data). This is
-- a legitimate §N.5 citation of ga_vargas' sign data, unlike the OLD graha_vargottama_
-- amplification_factor bug (F-A15) which used its own hardcoded navamsha-degree formula and never
-- read ga_vargas' data at all.
--
-- Discovered a NEW, genuine, previously-untracked defect while authoring this contract, filed as
-- F-A17 (see conjunct (e) below): ga_structural's re-derivation of the vargottama BOOLEAN from
-- ga_vargas' own sign data disagrees with ga_vargas' own PRE-COMPUTED vargottama_flag boolean
-- (chart_divisionals, fact_category='varga_vargottama_flag' -- confirmed present for ALL 29
-- vargas, not just D9 as F-A15's migration 745 conjunct (b) scoped to) on 13/3780 rows, spanning
-- both the canonical chart (482012f1, raman ayanamsha, Moon, 3 vargas: D3/D14/D27) and a
-- non-canonical chart (1c826d5a, surya_siddhanta_classical, 8 grahas across D8/D12/D14/D20/D24/
-- D27/D32/D40/D45). Root cause NOT investigated this cycle (a genuinely new writer/cross-asset
-- question -- whether ga_vargas' own varga_position.sign and varga_vargottama_flag.vargottama
-- columns can themselves disagree, or whether ga_structural's re-derivation has its own bug) --
-- following the F-C8/F-A15 precedent: shipped as a real, mutation-tested detector rather than
-- suppressed or narrowed to hide the finding. Confirmed genuine (not a stale-build-id artifact):
-- both sides hold exactly one build_id per (chart, ayanamsha, varga, graha) -- no plurality
-- violation on either side.
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries migrations 745's/755's four original conjuncts (a) through (d) forward VERBATIM,
-- including conjunct (b), which remains GENUINELY RED TODAY exactly as migration 755 already
-- documented (F-A15's fix hasn't propagated to its 2 affected charts' stored rows yet). This
-- migration does not attempt to resolve that. Because conjunct (b) is already red, and conjunct
-- (e) below is ALSO genuinely red (F-A17), the combined 5-conjunct SELECT evaluates to false on
-- live production today; conjuncts (c)/(d)/(e) were each verified INDIVIDUALLY (their own NOT
-- EXISTS subquery in isolation) rather than via the full combined SELECT.
--
-- Every conjunct was EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_structural integrity contract (target: chart_facts, scoped to
-- graha_vargottama_amplification_factor / bhadra_flag / panchaka_flag / vargottama_per_varga, 4
-- of 57 owned categories). D-CND-03: chart-partitioned / row-wise, attribution-preserving. No
-- bare count pin (C12). No distinctness conjunct -- none of these four categories' natural key
-- needs re-asserting (chart_facts_unique_null_formula already covers it).
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
  -- (e) F-A17: vargottama_per_varga.is_vargottama (fact_subject "{VARGA}_{SUBJECT}", e.g.
  -- "D9_SUN") must agree with ga_vargas' own authoritative varga_vargottama_flag
  -- (chart_divisionals, §N.5) for the SAME (chart, ayanamsha, varga, graha) -- re-derived here
  -- directly rather than restated. GENUINELY RED TODAY on 13/3780 rows: 3 rows on the canonical
  -- chart (482012f1, raman, Moon, vargas D3/D14/D27) and 10 rows on a non-canonical chart
  -- (1c826d5a, surya_siddhanta_classical, 8 distinct grahas across D8/D12/D14/D20/D24/D27/D32/
  -- D40/D45). Verified as a genuine detector, not a stale-build-id artifact: both sides hold
  -- exactly one build_id per (chart, ayanamsha, varga, graha) today. Root cause not yet
  -- investigated (whether ga_vargas' own varga_position.sign and varga_vargottama_flag.vargottama
  -- columns disagree with each other, or ga_structural's re-derivation has its own bug) -- tracked
  -- for a future pass, per the F-C8/F-A15 precedent of shipping a real red detector rather than
  -- suppressing the finding.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_divisionals v
      ON v.chart_id = a.chart_id AND v.ayanamsha_id = a.ayanamsha_id
     AND v.fact_category = 'varga_vargottama_flag'
     AND v.varga = split_part(a.fact_subject, '_', 1)
     AND v.graha = CASE substring(a.fact_subject from length(split_part(a.fact_subject,'_',1))+2)
       WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
       WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
       WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
       ELSE NULL END
    WHERE a.fact_category = 'vargottama_per_varga' AND a.fact_key = 'is_vargottama'
      AND (a.fact_value_num = 1.0) <> v.vargottama
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
