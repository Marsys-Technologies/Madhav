-- 759_nirmana_l1_ga_structural_integrity_contract_yuddha.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Fifth follow-up F-A14 widening pass for ga_structural.
-- Migration 745 covered graha_vargottama_amplification_factor; migration 755 added bhadra_flag/
-- panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
-- parivartana_per_varga; migration 758 added combustion_per_varga (6/57). This adds
-- graha_yuddha_per_varga, taking coverage to 7/57 -- this is migration 759, the LAST number in
-- the 752-759 range (adjudication #1972); the follow-up adjudication for the next range is filed
-- in the same cycle this migration lands, per the D-L1-59/D-L1-60 drill.
--
-- graha_yuddha_per_varga (_build_graha_yuddha_per_varga_rows) emits one row per (varga, graha
-- pair) when two of the five eligible classical grahas (excludes Sun/Rahu/Ketu -- graha-yuddha is
-- a planetary-war concept classically restricted to Mars/Mercury/Jupiter/Venus/Saturn) sit within
-- 1 degree of each other in the same varga.
--
-- Three conjuncts:
--   (j) orb_deg (stored in the row's own value_jsonb) must be <= 1.0 -- re-derives the writer's
--       own `if orb <= 1.0` emission filter as a domain check on what actually got stored (a row
--       existing at all is itself the classical claim "these two are in graha-yuddha"; an
--       orb > 1.0 row would silently misrepresent that). 0/116 violations live.
--   (k) graha1/graha2 (also in value_jsonb) must never be Sun, Rahu, or Ketu -- re-derives the
--       writer's own `grahas = [g for g in ALL_GRAHAS if ... not in ("Rahu","Ketu","Sun")]`
--       exclusion filter. 0/116 violations live.
--   (l) orb_deg (varga != 'D1' -- see migration 758's header note on the D1 dual-source
--       exclusion, which applies here identically) must equal the re-derived circular-arc
--       distance between graha1 and graha2, computed fresh from ga_vargas' own chart_divisionals
--       varga_position data for the SAME varga -- re-derived directly rather than restated.
--       Investigated unscoped first: 5/116 violations, ALL on D1 -- confirmed the same shape as
--       combustion_per_varga's own D1 exclusion (graha_yuddha_per_varga's D1 rows source
--       varga_state from _extract_chart_state(chart_output), never ga_vargas' own chart_
--       divisionals D1 rows) before scoping it out, not a fresh investigation. 0/111 violations
--       live once D1 is excluded (D2 onward).
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries migrations 745's/755's/756's/757's/758's nine original conjuncts (a) through (i)
-- forward VERBATIM, including conjuncts (b), (e), and (f), which remain GENUINELY RED TODAY
-- exactly as migration 758 already documented (F-A15/F-A17/F-157 fixes landed, tracked charts not
-- yet rebuilt). Because (b), (e), (f) are all red, the combined 12-conjunct SELECT evaluates to
-- false on live production today; conjuncts (j)/(k)/(l) were verified INDIVIDUALLY (their own NOT
-- EXISTS subquery in isolation) rather than via the full combined SELECT.
--
-- Every conjunct was EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_structural integrity contract (target: chart_facts, scoped to
-- graha_vargottama_amplification_factor / bhadra_flag / panchaka_flag / vargottama_per_varga /
-- parivartana_per_varga / combustion_per_varga / graha_yuddha_per_varga, 7 of 57 owned
-- categories). D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin
-- (C12). No distinctness conjunct -- none of these seven categories' natural key needs
-- re-asserting (chart_facts_unique_null_formula already covers it).
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
  -- (f) F-157: parivartana_per_varga.mutual_exchange must never pair a graha with itself --
  -- classically this is svakshetra (own-sign), a well-defined and entirely different dignity
  -- state from parivartana (mutual exchange, which by definition requires TWO DIFFERENT grahas).
  -- The writer's own `lord1 != g1` guard already prevents this for any FUTURE build; re-derived
  -- here as a data check on what is actually stored. GENUINELY RED TODAY on 439/624 rows -- see
  -- header note; tracked, expected, will clear once the affected charts next rebuild.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'parivartana_per_varga' AND fact_key = 'mutual_exchange'
      AND fact_value_jsonb->>'planet_a' = fact_value_jsonb->>'planet_b'
  )
  -- (g) For genuinely non-self-paired rows, the classical parivartana condition itself must hold
  -- in BOTH directions: sign_a's lord is planet_b, AND sign_b's lord is planet_a (SIGN_LORDS --
  -- the same 12-sign classical table the writer itself uses) -- re-derived directly from the
  -- stored sign_a/sign_b/planet_a/planet_b values, not restated. 0/185 violations live (checked
  -- against the 185 genuinely non-self-paired rows; self-paired rows are already covered by
  -- conjunct (f) and excluded here to avoid double-penalizing the same known F-157 residual).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'parivartana_per_varga' AND fact_key = 'mutual_exchange'
      AND fact_value_jsonb->>'planet_a' <> fact_value_jsonb->>'planet_b'
      AND NOT (
        (CASE fact_value_jsonb->>'sign_a'
           WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
           WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
           WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
           WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
           ELSE NULL END) = fact_value_jsonb->>'planet_b'
        AND
        (CASE fact_value_jsonb->>'sign_b'
           WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
           WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
           WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
           WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
           ELSE NULL END) = fact_value_jsonb->>'planet_a'
      )
  )
  -- (h) combustion_per_varga.is_combust must equal (arc_deg <= orb_limit) -- both values are
  -- already stored in the row's own value_jsonb. An internal self-consistency check: the stored
  -- boolean flag must actually match the threshold comparison it claims to represent, catching a
  -- future mismatch between the derived flag and the derived arc (e.g. a wrong comparison
  -- operator). 0/2175 violations live, across all vargas including D1.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'combustion_per_varga' AND fact_key = 'is_combust'
      AND (fact_value_num = 1.0) <>
          ((fact_value_jsonb->>'arc_deg')::numeric <= (fact_value_jsonb->>'orb_limit')::numeric)
  )
  -- (i) combustion_per_varga.arc_deg (varga != 'D1' -- see header note on the D1 dual-source
  -- exclusion) must equal the re-derived circular-arc distance between the graha and Sun,
  -- computed fresh from ga_vargas' own chart_divisionals varga_position sign_number/
  -- degree_in_sign for the SAME varga -- re-derived directly rather than restated. 0/2100
  -- violations live (D2 onward).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_divisionals sunp
      ON sunp.chart_id = a.chart_id AND sunp.ayanamsha_id = a.ayanamsha_id
     AND sunp.fact_category = 'varga_position' AND sunp.fact_key = 'degree_in_sign'
     AND sunp.graha = 'Sun' AND sunp.varga = split_part(a.fact_subject, '_', 1)
    JOIN chart_divisionals gp
      ON gp.chart_id = a.chart_id AND gp.ayanamsha_id = a.ayanamsha_id
     AND gp.fact_category = 'varga_position' AND gp.fact_key = 'degree_in_sign'
     AND gp.varga = split_part(a.fact_subject, '_', 1)
     AND gp.graha = CASE substring(a.fact_subject from length(split_part(a.fact_subject,'_',1))+2)
       WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
       WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
       WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
       ELSE NULL END
    WHERE a.fact_category = 'combustion_per_varga' AND a.fact_key = 'is_combust'
      AND split_part(a.fact_subject, '_', 1) <> 'D1'
      AND abs(
        (a.fact_value_jsonb->>'arc_deg')::numeric -
        LEAST(
          abs(((gp.sign_number-1)*30.0 + gp.degree_in_sign) - ((sunp.sign_number-1)*30.0 + sunp.degree_in_sign)),
          360.0 - abs(((gp.sign_number-1)*30.0 + gp.degree_in_sign) - ((sunp.sign_number-1)*30.0 + sunp.degree_in_sign))
        )
      ) > 0.01
  )
  -- (j) graha_yuddha_per_varga.orb_deg (stored in the row's own value_jsonb) must be <= 1.0 --
  -- re-derives the writer's own `if orb <= 1.0` emission filter as a domain check. A row's mere
  -- existence is itself the classical claim "these two grahas are in graha-yuddha"; an
  -- orb > 1.0 row would silently misrepresent that. 0/116 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_yuddha_per_varga' AND fact_key = 'within_1deg'
      AND (fact_value_jsonb->>'orb_deg')::numeric > 1.0
  )
  -- (k) graha_yuddha_per_varga.graha1/graha2 must never be Sun, Rahu, or Ketu -- re-derives the
  -- writer's own classical eligibility filter (graha-yuddha is restricted to the five
  -- Mars/Mercury/Jupiter/Venus/Saturn). 0/116 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_yuddha_per_varga' AND fact_key = 'within_1deg'
      AND (
        fact_value_jsonb->>'graha1' IN ('Sun', 'Rahu', 'Ketu')
        OR fact_value_jsonb->>'graha2' IN ('Sun', 'Rahu', 'Ketu')
      )
  )
  -- (l) graha_yuddha_per_varga.orb_deg (varga != 'D1' -- see migration 758's header note on the
  -- D1 dual-source exclusion, which applies identically here) must equal the re-derived
  -- circular-arc distance between graha1 and graha2, computed fresh from ga_vargas' own
  -- chart_divisionals varga_position data for the SAME varga -- re-derived directly rather than
  -- restated. 0/111 violations live (D2 onward).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_divisionals p1
      ON p1.chart_id = a.chart_id AND p1.ayanamsha_id = a.ayanamsha_id
     AND p1.fact_category = 'varga_position' AND p1.fact_key = 'degree_in_sign'
     AND p1.varga = split_part(a.fact_subject, '_', 1)
     AND p1.graha = a.fact_value_jsonb->>'graha1'
    JOIN chart_divisionals p2
      ON p2.chart_id = a.chart_id AND p2.ayanamsha_id = a.ayanamsha_id
     AND p2.fact_category = 'varga_position' AND p2.fact_key = 'degree_in_sign'
     AND p2.varga = split_part(a.fact_subject, '_', 1)
     AND p2.graha = a.fact_value_jsonb->>'graha2'
    WHERE a.fact_category = 'graha_yuddha_per_varga' AND a.fact_key = 'within_1deg'
      AND split_part(a.fact_subject, '_', 1) <> 'D1'
      AND abs(
        (a.fact_value_jsonb->>'orb_deg')::numeric -
        LEAST(
          abs(((p1.sign_number-1)*30.0 + p1.degree_in_sign) - ((p2.sign_number-1)*30.0 + p2.degree_in_sign)),
          360.0 - abs(((p1.sign_number-1)*30.0 + p1.degree_in_sign) - ((p2.sign_number-1)*30.0 + p2.degree_in_sign))
        )
      ) > 0.01
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
