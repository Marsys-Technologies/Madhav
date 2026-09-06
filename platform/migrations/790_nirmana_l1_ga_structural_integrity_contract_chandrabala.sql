-- 790_nirmana_l1_ga_structural_integrity_contract_chandrabala.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Sixteenth follow-up F-A14 widening pass for ga_structural,
-- eleventh in the 780-799 range (adjudication #2012). Migration 745 covered graha_vargottama_
-- amplification_factor; migration 755 added bhadra_flag/panchaka_flag; migration 756 added
-- vargottama_per_varga; migration 757 added parivartana_per_varga; migration 758 added
-- combustion_per_varga; migration 759 added graha_yuddha_per_varga; migration 780 added
-- nway_config_per_varga; migration 781 added kala_sarpa_per_varga; migration 782 added
-- tara_bala_natal_baseline; migration 783 added conjunction_within_orb; migration 784 added
-- aspect_tajik; migration 785 added graha_yoga_karaka_flag; migration 786 added
-- graha_dispositor_chain; migration 787 added composite_dispositor_strength; migration 788
-- added the Group H avastha bundle; migration 789 added nakshatra_dispositor_chain (20/57).
-- This adds chandra_bala_natal_baseline, taking coverage to 21/57.
--
-- chandra_bala_natal_baseline is a THIRD cross-writer-owned category (like migration 755's
-- bhadra_flag/panchaka_flag and migration 782's tara_bala_natal_baseline): physically EMITTED by
-- ga_panchanga_writer.py's `_emit_chandra_bala_baseline`, not ga_structural_writer.py -- but
-- OWNED by ga_structural per fact_category_ownership. It stores 12 rows per (chart, ayanamsha) --
-- one per transit Moon sign (fact_subject = "TRANSIT_SIGN_{SANSKRIT_NAME}", Sanskrit zodiac
-- names Mesha..Meena in the standard order) -- classified via:
--   birth_moon_sign_id = ((birth_nak_id - 1) * 4) // 9 + 1   (integer floor division; safe in
--     Postgres integer division since both operands are always non-negative here)
--   position = (sign_id - birth_moon_sign_id) % 12 + 1        (Python-semantics modulo -- CAN go
--     negative under Postgres's %, since sign_id - birth_moon_sign_id ranges from -11 to +11)
-- mapped through the writer's own fixed _CHANDRA_BALA 12-entry dict, with birth_nak_id sourced
-- from ga_panchanga's own panchanga_nakshatra_moon category (the same authoritative
-- birth-nakshatra reference already used by migration 782's tara_bala_natal_baseline and
-- migration 755's panchaka_flag conjuncts). Per D-L1-55, a +120 (10*12) safety margin is added
-- before the modulo to guarantee a positive dividend without changing the result mod 12 --
-- reused directly from the same precedent as migration 782, this time on a mod-12 formula
-- rather than mod-27/mod-9.
--
--   (tt2) fact_value_text domain: must be one of the 3 classical classifications ('favorable',
--         'unfavorable', 'neutral') -- the writer's own _CHANDRA_BALA dict, no fourth value ever
--         legitimate. 0/180 violations live.
--   (uu2) fact_value_text must equal the full re-derivation of the writer's own formula:
--         transit sign_id is parsed from fact_subject's "TRANSIT_SIGN_{SANSKRIT_NAME}" suffix
--         via the standard Sanskrit zodiac name table; birth_nak_id is sourced from
--         panchanga_nakshatra_moon.number for the same chart/ayanamsha -- re-derived directly
--         rather than restated. 0/180 violations live.
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries migrations 745's/755's/756's/757's/758's/759's/780's/781's/782's/783's/784's/785's/
-- 786's/787's/788's/789's fifty-five original conjuncts (a) through (ss2) forward VERBATIM,
-- including conjuncts (b), (e), and (f), which remain GENUINELY RED TODAY exactly as migration
-- 789 already documented (F-A15/F-A17/F-157 fixes landed, tracked charts not yet rebuilt).
-- Because (b), (e), (f) are all red, the combined 57-conjunct SELECT evaluates to false on live
-- production today; conjuncts (tt2)/(uu2) were verified INDIVIDUALLY (their own subquery in
-- isolation) rather than via the full combined SELECT.
--
-- Every conjunct was EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_structural integrity contract (target: chart_facts, scoped to
-- graha_vargottama_amplification_factor / bhadra_flag / panchaka_flag / vargottama_per_varga /
-- parivartana_per_varga / combustion_per_varga / graha_yuddha_per_varga / nway_config_per_varga /
-- kala_sarpa_per_varga / tara_bala_natal_baseline / conjunction_within_orb / aspect_tajik /
-- graha_yoga_karaka_flag / graha_dispositor_chain / composite_dispositor_strength /
-- graha_avastha_baladi / graha_avastha_jagrad / graha_avastha_deepta /
-- graha_avastha_lifetime_exposure_summary / nakshatra_dispositor_chain /
-- chandra_bala_natal_baseline, 21 of 57 owned categories). D-CND-03: chart-partitioned /
-- row-wise, attribution-preserving. No bare count pin (C12). No distinctness conjunct -- none of
-- these twenty-one categories' natural key needs re-asserting (chart_facts_unique_null_formula
-- already covers it).
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
  -- (m) nway_config_per_varga.stellium's fact_value_num (the graha count) must be >= 3 --
  -- re-derives the writer's own `if len(grahas) >= 3` filter as a domain check on what actually
  -- got stored. 0/223 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'nway_config_per_varga' AND fact_key = 'stellium'
      AND fact_value_num < 3
  )
  -- (n) fact_value_num must equal the length of the value_jsonb.grahas array -- internal
  -- self-consistency between the two places this same count is stored. 0/223 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'nway_config_per_varga' AND fact_key = 'stellium'
      AND fact_value_num <> jsonb_array_length(fact_value_jsonb->'grahas')
  )
  -- (o) every graha named in value_jsonb.grahas (varga != 'D1' -- see migration 758's header note
  -- on the D1 dual-source exclusion, which applies identically here) must actually sit in the
  -- stellium's own claimed sign, per ga_vargas' own chart_divisionals varga_position data for the
  -- SAME varga -- re-derived directly rather than restated. 0/746 violations live (D2 onward).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL jsonb_array_elements_text(a.fact_value_jsonb->'grahas') AS g(graha_name)
    JOIN chart_divisionals gp
      ON gp.chart_id = a.chart_id AND gp.ayanamsha_id = a.ayanamsha_id
     AND gp.fact_category = 'varga_position' AND gp.fact_key = 'sign'
     AND gp.varga = split_part(a.fact_subject, '_', 1)
     AND gp.graha = g.graha_name
    WHERE a.fact_category = 'nway_config_per_varga' AND a.fact_key = 'stellium'
      AND split_part(a.fact_subject, '_', 1) <> 'D1'
      AND gp.fact_value_text <> (a.fact_value_jsonb->>'sign')
  )
  -- (p) kala_sarpa_per_varga.ks_detection's fact_value_num (1.0/0.0) must match
  -- value_jsonb.fires (boolean) -- the same detection result stored twice. 0/435 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'
      AND (fact_value_num = 1.0) <> (fact_value_jsonb->>'fires')::boolean
  )
  -- (q) fact_value_text must equal value_jsonb.variant -- same value stored twice. 0/435
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'
      AND fact_value_text <> fact_value_jsonb->>'variant'
  )
  -- (r) fact_value_text domain: must be one of 'none'/'kala_sarpa'/'kala_amrita' -- the writer's
  -- own three-way classification, no fourth value ever legitimate. 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'
      AND fact_value_text NOT IN ('none', 'kala_sarpa', 'kala_amrita')
  )
  -- (s) fires (fact_value_num=1.0) must hold if and only if variant != 'none' -- a genuine
  -- cross-field consistency the writer's own return statements guarantee but never state
  -- explicitly as one claim. 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'
      AND (fact_value_num = 1.0) <> (fact_value_text <> 'none')
  )
  -- (t) value_jsonb.variant_name must equal the writer's own naming convention re-derived from
  -- variant + rahu_house ("KALA_SARPA_RAHU_H{n}" / "KALA_AMRITA_RAHU_H{n}" / "") -- combines two
  -- already-stored fields into what should equal a third, re-derived directly rather than
  -- restated. 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'
      AND fact_value_jsonb->>'variant_name' <> (
        CASE fact_value_text
          WHEN 'kala_sarpa' THEN 'KALA_SARPA_RAHU_H' || (fact_value_jsonb->>'rahu_house')
          WHEN 'kala_amrita' THEN 'KALA_AMRITA_RAHU_H' || (fact_value_jsonb->>'rahu_house')
          ELSE ''
        END
      )
  )
  -- (u) tara_bala_natal_baseline.tara_class domain: must be one of the writer's own 9 classical
  -- Tara quality names (_TARA_QUALITY dict) -- no tenth value ever legitimate. 0/405 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'tara_bala_natal_baseline' AND fact_key = 'tara_class'
      AND fact_value_text NOT IN
        ('Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak', 'Sadhaka', 'Vadha', 'Mitra', 'Atimitra')
  )
  -- (v) tara_bala_natal_baseline.tara_class must equal the full re-derivation of the writer's own
  -- two-step modulo formula (_emit_tara_bala_baseline): transit_nak_id is parsed from
  -- fact_subject's "TRANSIT_NAK_{code}" suffix via the writer's own NAKSHATRA_SHORT table;
  -- birth_nak_id is sourced from ga_panchanga's own panchanga_nakshatra_moon.number (subj
  -- NAKSHATRA_MOON_BIRTH) for the same chart/ayanamsha -- the same authoritative birth-nakshatra
  -- reference already used by conjunct (d)'s panchaka_flag re-derivation. Per D-L1-55, a +270
  -- (10*27) margin is added before the first modulo and +90 (10*9) before the second, guaranteeing
  -- a positive dividend without changing the result mod 27 / mod 9. 0/405 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts n ON n.chart_id = a.chart_id AND n.ayanamsha_id = a.ayanamsha_id
      AND n.fact_category = 'panchanga_nakshatra_moon' AND n.fact_subject = 'NAKSHATRA_MOON_BIRTH'
      AND n.fact_key = 'number'
    WHERE a.fact_category = 'tara_bala_natal_baseline' AND a.fact_key = 'tara_class'
      AND a.fact_value_text <> (
        CASE (
          (
            (
              (CASE substring(a.fact_subject from 13)
                WHEN 'ASH' THEN 1 WHEN 'BHA' THEN 2 WHEN 'KRI' THEN 3 WHEN 'ROH' THEN 4 WHEN 'MRI' THEN 5
                WHEN 'ARD' THEN 6 WHEN 'PUN' THEN 7 WHEN 'PUS' THEN 8 WHEN 'ASL' THEN 9 WHEN 'MAG' THEN 10
                WHEN 'PPH' THEN 11 WHEN 'UPH' THEN 12 WHEN 'HAS' THEN 13 WHEN 'CHI' THEN 14 WHEN 'SWA' THEN 15
                WHEN 'VIS' THEN 16 WHEN 'ANU' THEN 17 WHEN 'JYE' THEN 18 WHEN 'MOO' THEN 19 WHEN 'PAS' THEN 20
                WHEN 'UAS' THEN 21 WHEN 'SHR' THEN 22 WHEN 'DHA' THEN 23 WHEN 'SHA' THEN 24 WHEN 'PPB' THEN 25
                WHEN 'UPB' THEN 26 WHEN 'REV' THEN 27 ELSE NULL END)
              - n.fact_value_num::int + 270
            ) % 27 + 90
          ) % 9 + 1
        )
          WHEN 1 THEN 'Janma' WHEN 2 THEN 'Sampat' WHEN 3 THEN 'Vipat' WHEN 4 THEN 'Kshema'
          WHEN 5 THEN 'Pratyak' WHEN 6 THEN 'Sadhaka' WHEN 7 THEN 'Vadha' WHEN 8 THEN 'Mitra'
          WHEN 9 THEN 'Atimitra' ELSE NULL END
      )
  )
  -- (w) conjunction_within_orb.orb_deg domain: must be within [0, 10.0] -- re-derives the writer's
  -- own `if orb <= 10.0` emission filter (and the physical non-negativity of an orb) as a domain
  -- check on what actually got stored. 0/30 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'conjunction_within_orb' AND fact_key = 'orb_deg'
      AND (fact_value_num < 0 OR fact_value_num > 10.0)
  )
  -- (x) no reversed-duplicate pair: for a stored "{s1}_{s2}" row, "{s2}_{s1}" must never also be
  -- stored for the same (chart, ayanamsha, build) -- re-derives the writer's own `for g2 in
  -- ALL_GRAHAS[i+1:]` loop guarantee (each unordered pair emitted exactly once) as a genuine
  -- cross-row consistency check. s1 is parsed by checking the RAH_MEAN_/KET_MEAN_ prefix first
  -- (both PLANET_TO_SUBJECT tokens themselves contain an underscore, so a naive split_part would
  -- mis-parse e.g. "SAT_KET_MEAN"), falling back to split_part otherwise; s2 is the remainder.
  -- 0/30 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'conjunction_within_orb' AND a.fact_key = 'orb_deg'
      AND EXISTS (
        SELECT 1 FROM chart_facts b
        WHERE b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
          AND b.fact_category = 'conjunction_within_orb' AND b.fact_key = 'orb_deg'
          AND b.fact_subject =
            substring(
              a.fact_subject from
              length(CASE WHEN a.fact_subject LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
                           WHEN a.fact_subject LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
                           ELSE split_part(a.fact_subject, '_', 1) END) + 2
            )
            || '_' ||
            (CASE WHEN a.fact_subject LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
                  WHEN a.fact_subject LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
                  ELSE split_part(a.fact_subject, '_', 1) END)
      )
  )
  -- (y) pair ordering invariant: s1's index in the writer's own ALL_GRAHAS ordering
  -- (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) must strictly precede s2's index --
  -- re-derives the writer's own `i, g1` / `ALL_GRAHAS[i+1:]` loop structure (a genuine invariant
  -- the loop guarantees, not a bare restatement) as a domain check on what actually got stored.
  -- Same s1/s2 parse as conjunct (x). 0/30 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'conjunction_within_orb' AND a.fact_key = 'orb_deg'
      AND COALESCE(
        array_position(
          ARRAY['SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN'],
          CASE WHEN a.fact_subject LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
               WHEN a.fact_subject LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
               ELSE split_part(a.fact_subject, '_', 1) END
        ), 999
      ) >=
      COALESCE(
        array_position(
          ARRAY['SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN'],
          substring(
            a.fact_subject from
            length(CASE WHEN a.fact_subject LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
                         WHEN a.fact_subject LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
                         ELSE split_part(a.fact_subject, '_', 1) END) + 2
          )
        ), -1
      )
  )
  -- (z) aspect_tajik fact_key domain: must be one of the four live Tajik types ('yamaya',
  -- 'ithasala', 'eesarpha', 'manaau') -- Nakta is retained in the writer's vocabulary for schema
  -- stability but the writer's own comment confirms it never fires from this pairwise loop.
  -- 0/76 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND fact_key NOT IN ('yamaya', 'ithasala', 'eesarpha', 'manaau')
  )
  -- (aa) fact_value_num must equal value_jsonb.orb_deg -- the same orb value stored twice.
  -- 0/76 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND fact_value_num <> (fact_value_jsonb->>'orb_deg')::numeric
  )
  -- (bb) value_jsonb.orb_strength must equal the writer's own per-type formula: 1.0 for yamaya
  -- (exact-degree case); 0.1 for manaau (the fixed "denial" weight); for ithasala/eesarpha,
  -- round(greatest(0, 1 - orb_deg/deeptamsa_sum_deg), 4) -- a genuine cross-field re-derivation
  -- combining two already-stored fields into a third, not a bare restatement. 0/76 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND (fact_value_jsonb->>'orb_strength')::numeric <>
        CASE fact_key
          WHEN 'yamaya' THEN 1.0
          WHEN 'manaau' THEN 0.1
          ELSE round(
            GREATEST(0.0, 1.0 -
              (fact_value_jsonb->>'orb_deg')::numeric / (fact_value_jsonb->>'deeptamsa_sum_deg')::numeric
            ), 4
          )
        END
  )
  -- (cc) value_jsonb.applying must match the writer's own per-type motion constraint: ithasala and
  -- manaau both only ever fire on the writer's `applying` branch; eesarpha only fires on the
  -- separating branch. yamaya is unconstrained (fires regardless of motion) and is intentionally
  -- excluded from this conjunct. 0/76 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND (
        (fact_key = 'ithasala' AND (fact_value_jsonb->>'applying')::boolean <> true)
        OR (fact_key = 'eesarpha' AND (fact_value_jsonb->>'applying')::boolean <> false)
        OR (fact_key = 'manaau' AND (fact_value_jsonb->>'applying')::boolean <> true)
      )
  )
  -- (dd) value_jsonb.salience must equal the writer's own fixed per-type mapping
  -- ({"yamaya":"high","ithasala":"high","eesarpha":"medium","manaau":"low"}) -- re-derived
  -- directly from fact_key rather than restated. 0/76 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND (fact_value_jsonb->>'salience') <>
        CASE fact_key
          WHEN 'yamaya' THEN 'high' WHEN 'ithasala' THEN 'high'
          WHEN 'eesarpha' THEN 'medium' WHEN 'manaau' THEN 'low'
        END
  )
  -- (ee) orb_deg must satisfy the writer's own per-type threshold, re-deriving the exact
  -- if/elif/elif branch structure that decides which taj_type a row gets: <= 1.0 for yamaya; in
  -- (1.0, deeptamsa_sum_deg] for ithasala/eesarpha; > deeptamsa_sum_deg for manaau (the writer's
  -- own `continue` on separating-beyond-deeptamsa guarantees no row ever violates this for any
  -- live taj_type). 0/76 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND NOT (
        (fact_key = 'yamaya' AND (fact_value_jsonb->>'orb_deg')::numeric <= 1.0)
        OR (fact_key IN ('ithasala', 'eesarpha')
            AND (fact_value_jsonb->>'orb_deg')::numeric > 1.0
            AND (fact_value_jsonb->>'orb_deg')::numeric <= (fact_value_jsonb->>'deeptamsa_sum_deg')::numeric)
        OR (fact_key = 'manaau'
            AND (fact_value_jsonb->>'orb_deg')::numeric > (fact_value_jsonb->>'deeptamsa_sum_deg')::numeric)
      )
  )
  -- (ff) graha_yoga_karaka_flag.is_yoga_karaka domain: must be 'true' or 'false' -- no third value
  -- is ever legitimate for a boolean flag. 0/105 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_yoga_karaka_flag' AND fact_key = 'is_yoga_karaka'
      AND fact_value_text NOT IN ('true', 'false')
  )
  -- (gg) at most one graha per (chart, ayanamsha, build) may have is_yoga_karaka='true' -- a
  -- genuine cross-row invariant the writer's own equality-chain formula
  -- (`g_name == lord_9 == lord_10`) guarantees: only the one graha literally equal to both lord_9
  -- and lord_10, if such a graha exists at all, can ever satisfy the condition. 0/105 violations
  -- live (vacuously satisfied by today's all-'false' data -- none of the three live charts has a
  -- Taurus lagna, the only lagna under classical SIGN_LORDS where lord_9==lord_10 -- but a real,
  -- mutation-provable detector regardless).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_yoga_karaka_flag' AND fact_key = 'is_yoga_karaka'
      AND fact_value_text = 'true'
    GROUP BY chart_id, ayanamsha_id, build_id
    HAVING count(*) > 1
  )
  -- (hh) graha_dispositor_chain's chain[0] must equal the row's own graha (the writer's own
  -- `chain: list[str] = [g_name]` initialization) -- re-derived from fact_subject rather than
  -- restated. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_dispositor_chain' AND fact_key = 'chain_jsonb_atomic'
      AND (fact_value_jsonb->'chain'->>0) <> (
        CASE fact_subject
          WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
          WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
          WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
          ELSE NULL END
      )
  )
  -- (ii) length must equal the actual length of the chain array -- the same count stored twice.
  -- 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_dispositor_chain' AND fact_key = 'chain_jsonb_atomic'
      AND (fact_value_jsonb->>'length')::int <> jsonb_array_length(fact_value_jsonb->'chain')
  )
  -- (jj) the chain array and signs array must have equal length -- the writer's own loop appends
  -- to both in lockstep. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_dispositor_chain' AND fact_key = 'chain_jsonb_atomic'
      AND jsonb_array_length(fact_value_jsonb->'chain') <> jsonb_array_length(fact_value_jsonb->'signs')
  )
  -- (kk) when cycle_detected_at_step is not null, it must equal length exactly -- re-derives the
  -- writer's own loop arithmetic (cycle_at = step+1 at the exact break point, and length is the
  -- array size at that same point). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_dispositor_chain' AND fact_key = 'chain_jsonb_atomic'
      AND fact_value_jsonb->'cycle_detected_at_step' <> 'null'::jsonb
      AND (fact_value_jsonb->>'length')::int <> (fact_value_jsonb->>'cycle_detected_at_step')::int
  )
  -- (ll) full classical re-derivation: for every consecutive pair in the stored chain, the next
  -- graha must equal SIGN_LORDS[the previous graha's stored sign] (SIGN_LORDS -- the same
  -- 12-sign classical table already used by conjunct (g)) -- re-derives the actual dispositor
  -- rule, walked step-by-step via generate_series over the JSON array rather than restated.
  -- 0/318 pairs checked (sum of length-1 across all 135 rows), 0 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL generate_series(0, jsonb_array_length(a.fact_value_jsonb->'chain') - 2) AS i
    WHERE a.fact_category = 'graha_dispositor_chain' AND a.fact_key = 'chain_jsonb_atomic'
      AND (a.fact_value_jsonb->'chain'->>(i+1)) <> (
        CASE (a.fact_value_jsonb->'signs'->>i)
          WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
          WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
          WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
          WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
          ELSE NULL END
      )
  )
  -- (mm) terminal cycle-closure: the classical dispositor of the LAST stored sign must already be
  -- a member of the stored chain -- confirms the writer's own claim that a cycle was genuinely
  -- detected, re-derived directly from the classical table rather than trusting
  -- cycle_detected_at_step alone. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'graha_dispositor_chain' AND a.fact_key = 'chain_jsonb_atomic'
      AND NOT (
        (CASE (a.fact_value_jsonb->'signs'->>(jsonb_array_length(a.fact_value_jsonb->'signs')-1))
          WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
          WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
          WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
          WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
          ELSE NULL END) IN (SELECT jsonb_array_elements_text(a.fact_value_jsonb->'chain'))
      )
  )
  -- (nn) composite_dispositor_strength.terminal_strength domain: must be within [0.25, 1.0] --
  -- the achievable range of a mean over one or more values drawn from the writer's fixed
  -- four-value dignity-strength set (no chain is ever empty; the writer's own
  -- `chain: list[str] = [g_name]` guarantees at least one member). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'composite_dispositor_strength' AND fact_key = 'terminal_strength'
      AND (fact_value_num < 0.25 OR fact_value_num > 1.0)
  )
  -- (oo) bidirectional row correspondence with graha_dispositor_chain -- both categories are
  -- emitted by the SAME `for g in grahas_data:` loop in `_build_structural_relationship_rows`
  -- (a genuine cross-category invariant, not a bare restatement): every
  -- composite_dispositor_strength row must have a matching graha_dispositor_chain row for the
  -- same (chart, ayanamsha, build, subject), and vice versa. 0/135 violations live in either
  -- direction.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'composite_dispositor_strength' AND a.fact_key = 'terminal_strength'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts b
        WHERE b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id
          AND b.build_id = a.build_id AND b.fact_subject = a.fact_subject
          AND b.fact_category = 'graha_dispositor_chain' AND b.fact_key = 'chain_jsonb_atomic'
      )
    UNION ALL
    SELECT 1 FROM chart_facts b
    WHERE b.fact_category = 'graha_dispositor_chain' AND b.fact_key = 'chain_jsonb_atomic'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts a
        WHERE a.chart_id = b.chart_id AND a.ayanamsha_id = b.ayanamsha_id
          AND a.build_id = b.build_id AND a.fact_subject = b.fact_subject
          AND a.fact_category = 'composite_dispositor_strength' AND a.fact_key = 'terminal_strength'
      )
  )
  -- (pp) cross-category re-derivation: composite_strength * chain_length (from the sibling
  -- graha_dispositor_chain row's own `length` field) must be within a length-scaled tolerance of
  -- an exact multiple of 0.125 -- every one of the writer's four dignity-strength values
  -- (0.25/0.5/0.875/1.0) is itself a multiple of 0.125, so a genuine mean over `length` such
  -- values, once multiplied back by `length`, must reconstruct to a multiple of 0.125. The
  -- tolerance (0.0001 * length) is sized to the writer's own round(mean, 4) storage precision.
  -- 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts b
      ON b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
     AND b.fact_subject = a.fact_subject
     AND b.fact_category = 'graha_dispositor_chain' AND b.fact_key = 'chain_jsonb_atomic'
    WHERE a.fact_category = 'composite_dispositor_strength' AND a.fact_key = 'terminal_strength'
      AND abs(
        (a.fact_value_num * (b.fact_value_jsonb->>'length')::numeric)
        - round((a.fact_value_num * (b.fact_value_jsonb->>'length')::numeric) / 0.125) * 0.125
      ) > (0.0001 * (b.fact_value_jsonb->>'length')::numeric)
  )
  -- (qq) graha_avastha_baladi.baladi_state domain: must be one of the writer's own BALADI_STATES
  -- five values ('bal','kumar','yuva','vriddha','mrit') -- no sixth value is ever legitimate.
  -- 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_avastha_baladi' AND fact_key = 'baladi_state'
      AND fact_value_text NOT IN ('bal', 'kumar', 'yuva', 'vriddha', 'mrit')
  )
  -- (rr) graha_avastha_jagrad.jagrad_state domain: must be one of the writer's own three
  -- consciousness-avastha values ('jagrad','swapna','sushupta'). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_avastha_jagrad' AND fact_key = 'jagrad_state'
      AND fact_value_text NOT IN ('jagrad', 'swapna', 'sushupta')
  )
  -- (ss) graha_avastha_deepta.deepta_state domain: must be one of the writer's own seven literal
  -- branch outcomes ('deepta','svastha','mudita','shanta','vikala','kopa','dina') -- confirmed
  -- against all 135 live rows before fixing the domain at seven rather than trusting the
  -- writer's own "9 states" comment. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_avastha_deepta' AND fact_key = 'deepta_state'
      AND fact_value_text NOT IN ('deepta', 'svastha', 'mudita', 'shanta', 'vikala', 'kopa', 'dina')
  )
  -- (tt) graha_avastha_lifetime_exposure_summary.value_jsonb.current_baladi must equal the SAME
  -- graha's own graha_avastha_baladi.baladi_state for the same (chart, ayanamsha, build) -- the
  -- writer's own same-loop-iteration copy, re-derived rather than restated. 0/135 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts b
      ON b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
     AND b.fact_subject = a.fact_subject
     AND b.fact_category = 'graha_avastha_baladi' AND b.fact_key = 'baladi_state'
    WHERE a.fact_category = 'graha_avastha_lifetime_exposure_summary'
      AND (a.fact_value_jsonb->>'current_baladi') <> b.fact_value_text
  )
  -- (uu) graha_avastha_lifetime_exposure_summary.value_jsonb.current_jagrad must equal the SAME
  -- graha's own graha_avastha_jagrad.jagrad_state for the same (chart, ayanamsha, build) -- the
  -- writer's own same-loop-iteration copy, re-derived rather than restated. 0/135 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts b
      ON b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
     AND b.fact_subject = a.fact_subject
     AND b.fact_category = 'graha_avastha_jagrad' AND b.fact_key = 'jagrad_state'
    WHERE a.fact_category = 'graha_avastha_lifetime_exposure_summary'
      AND (a.fact_value_jsonb->>'current_jagrad') <> b.fact_value_text
  )
  -- (vv) graha_avastha_lifetime_exposure_summary.value_jsonb.current_deepta must equal the SAME
  -- graha's own graha_avastha_deepta.deepta_state for the same (chart, ayanamsha, build) -- the
  -- writer's own same-loop-iteration copy, re-derived rather than restated. 0/135 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts b
      ON b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
     AND b.fact_subject = a.fact_subject
     AND b.fact_category = 'graha_avastha_deepta' AND b.fact_key = 'deepta_state'
    WHERE a.fact_category = 'graha_avastha_lifetime_exposure_summary'
      AND (a.fact_value_jsonb->>'current_deepta') <> b.fact_value_text
  )
  -- (ww) full cross-branch-logic re-derivation: jagrad_state='jagrad' if and only if
  -- deepta_state IN ('deepta','svastha') -- both functions check the SAME dignity condition
  -- (dignity IN ('exalted','own_sign')) as their very first branch, verified by hand-tracing
  -- both branch chains (this is deliberately an iff only for the 'jagrad' case -- the
  -- 'sushupta'/'swapna' split does not map to a single deepta value each, since a debilitated
  -- graha can still hit an earlier house/retro branch in the deepta chain, so no analogous
  -- broader iff was attempted). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts b
      ON b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
     AND b.fact_subject = a.fact_subject
     AND b.fact_category = 'graha_avastha_deepta' AND b.fact_key = 'deepta_state'
    WHERE a.fact_category = 'graha_avastha_jagrad' AND a.fact_key = 'jagrad_state'
      AND (a.fact_value_text = 'jagrad') <> (b.fact_value_text IN ('deepta', 'svastha'))
  )
  -- (nn2) nakshatra_dispositor_chain.chain[0] must equal the row's own graha/Lagna name (the
  -- writer's own `chain: list[str] = [planet_name]` initialization) -- re-derived from
  -- fact_subject rather than restated. 0/150 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'nakshatra_dispositor_chain'
      AND (fact_value_jsonb->'chain'->>0) <> (
        CASE fact_subject
          WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
          WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
          WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
          WHEN 'LAGNA' THEN 'Lagna'
          ELSE NULL END
      )
  )
  -- (oo2) length must equal the actual length of the chain array -- the same count stored
  -- twice. 0/150 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'nakshatra_dispositor_chain'
      AND (fact_value_jsonb->>'length')::int <> jsonb_array_length(fact_value_jsonb->'chain')
  )
  -- (pp2) cycle_at_step must equal length-1 -- a structural invariant of the writer's own loop
  -- that holds unconditionally, whether a genuine cycle was detected or the effective_cycle
  -- fallback fired. 0/150 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'nakshatra_dispositor_chain'
      AND (fact_value_jsonb->>'cycle_at_step')::int <> (fact_value_jsonb->>'length')::int - 1
  )
  -- (qq2) the nakshatras array must have length-1 entries for graha subjects, but length-2 for
  -- Lagna specifically -- Lagna has no graha_position.nakshatra entry (the writer's own
  -- `if nak:` guard silently skips appending it), an honest, explained gap in the writer's own
  -- data availability, not a defect. 0/150 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'nakshatra_dispositor_chain'
      AND jsonb_array_length(fact_value_jsonb->'nakshatras') <>
        (fact_value_jsonb->>'length')::int - (CASE WHEN fact_subject = 'LAGNA' THEN 2 ELSE 1 END)
  )
  -- (rr2) full re-derivation against the writer's own authoritative source: for every
  -- consecutive pair in the stored chain, the next name must equal the CURRENT step's own
  -- graha_nakshatra_join.nakshatra_lord value (capitalized per the writer's own Rahu/Ketu
  -- special-casing) -- re-reading the SAME L1-authority table the writer itself consults.
  -- 0/693 pairs checked, 0 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL generate_series(0, jsonb_array_length(a.fact_value_jsonb->'chain') - 2) AS i
    LEFT JOIN chart_facts n
      ON n.chart_id = a.chart_id AND n.ayanamsha_id = a.ayanamsha_id
     AND n.fact_category = 'graha_nakshatra_join' AND n.fact_key = 'nakshatra_lord'
     AND n.fact_subject = (
       CASE (a.fact_value_jsonb->'chain'->>i)
         WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
         WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
         WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
         WHEN 'Lagna' THEN 'LAGNA'
         ELSE NULL END
     )
    WHERE a.fact_category = 'nakshatra_dispositor_chain'
      AND (a.fact_value_jsonb->'chain'->>(i+1)) <> (
        CASE lower(n.fact_value_text)
          WHEN 'rahu' THEN 'Rahu' WHEN 'rahu_mean' THEN 'Rahu'
          WHEN 'ketu' THEN 'Ketu' WHEN 'ketu_mean' THEN 'Ketu'
          WHEN 'sun' THEN 'Sun' WHEN 'moon' THEN 'Moon' WHEN 'mars' THEN 'Mars'
          WHEN 'mercury' THEN 'Mercury' WHEN 'jupiter' THEN 'Jupiter' WHEN 'venus' THEN 'Venus'
          WHEN 'saturn' THEN 'Saturn'
          ELSE NULL END
      )
  )
  -- (ss2) constituent_fact_ids[0], when present, must resolve to an ACTUAL
  -- graha_nakshatra_join.nakshatra_lord row for the SAME (chart, ayanamsha, subject) -- the
  -- §N.5 constituent-facts-must-resolve concern, verified directly. 0/150 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'nakshatra_dispositor_chain'
      AND jsonb_array_length(a.fact_value_jsonb->'constituent_fact_ids') > 0
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts n
        WHERE n.chart_id = a.chart_id AND n.ayanamsha_id = a.ayanamsha_id
          AND n.fact_category = 'graha_nakshatra_join' AND n.fact_key = 'nakshatra_lord'
          AND n.fact_subject = a.fact_subject
          AND n.fact_id = (a.fact_value_jsonb->'constituent_fact_ids'->>0)
      )
  )
  -- (tt2) chandra_bala_natal_baseline.classification domain: must be one of the 3 classical
  -- classifications ('favorable', 'unfavorable', 'neutral') -- the writer's own _CHANDRA_BALA
  -- dict, no fourth value ever legitimate. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'chandra_bala_natal_baseline' AND fact_key = 'classification'
      AND fact_value_text NOT IN ('favorable', 'unfavorable', 'neutral')
  )
  -- (uu2) chandra_bala_natal_baseline.classification must equal the full re-derivation of the
  -- writer's own formula: transit sign_id is parsed from fact_subject's
  -- "TRANSIT_SIGN_{SANSKRIT_NAME}" suffix via the standard Sanskrit zodiac name table;
  -- birth_nak_id is sourced from panchanga_nakshatra_moon.number for the same chart/ayanamsha --
  -- the same authoritative birth-nakshatra reference already used by tara_bala_natal_baseline
  -- (migration 782) and panchaka_flag (migration 755). Per D-L1-55, a +120 (10*12) margin is
  -- added before the modulo, guaranteeing a positive dividend without changing the result
  -- mod 12. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts n ON n.chart_id = a.chart_id AND n.ayanamsha_id = a.ayanamsha_id
      AND n.fact_category = 'panchanga_nakshatra_moon' AND n.fact_subject = 'NAKSHATRA_MOON_BIRTH'
      AND n.fact_key = 'number'
    WHERE a.fact_category = 'chandra_bala_natal_baseline' AND a.fact_key = 'classification'
      AND a.fact_value_text <> (
        CASE (
          (
            (
              (CASE substring(a.fact_subject from 14)
                WHEN 'MESHA' THEN 1 WHEN 'VRISHABHA' THEN 2 WHEN 'MITHUNA' THEN 3 WHEN 'KARKA' THEN 4
                WHEN 'SIMHA' THEN 5 WHEN 'KANYA' THEN 6 WHEN 'TULA' THEN 7 WHEN 'VRISHCHIKA' THEN 8
                WHEN 'DHANU' THEN 9 WHEN 'MAKARA' THEN 10 WHEN 'KUMBHA' THEN 11 WHEN 'MEENA' THEN 12
                ELSE NULL END)
              - ( ((n.fact_value_num::int - 1) * 4) / 9 + 1 )
              + 120
            ) % 12
          ) + 1
        )
          WHEN 1 THEN 'favorable' WHEN 2 THEN 'unfavorable' WHEN 3 THEN 'favorable'
          WHEN 4 THEN 'unfavorable' WHEN 5 THEN 'unfavorable' WHEN 6 THEN 'favorable'
          WHEN 7 THEN 'favorable' WHEN 8 THEN 'unfavorable' WHEN 9 THEN 'neutral'
          WHEN 10 THEN 'favorable' WHEN 11 THEN 'favorable' WHEN 12 THEN 'unfavorable'
          ELSE NULL END
      )
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
