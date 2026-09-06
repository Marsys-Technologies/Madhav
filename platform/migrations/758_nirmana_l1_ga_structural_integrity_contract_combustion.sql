-- 758_nirmana_l1_ga_structural_integrity_contract_combustion.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Fourth follow-up F-A14 widening pass for ga_structural.
-- Migration 745 covered graha_vargottama_amplification_factor; migration 755 added bhadra_flag/
-- panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
-- parivartana_per_varga (5/57). This adds combustion_per_varga, taking coverage to 6/57.
--
-- combustion_per_varga (_build_combustion_per_varga_rows) computes, per (varga, graha), whether
-- the graha's arc-distance from the Sun (in the SAME varga) is within COMBUSTION_ORBS' classical
-- threshold. Two conjuncts:
--
--   (h) is_combust must equal (arc_deg <= orb_limit) -- both already stored in the row's own
--       value_jsonb -- an internal self-consistency check (the stored flag must match the stored
--       threshold comparison it claims to represent). 0/2175 violations live, ALL vargas.
--   (i) arc_deg itself must equal the re-derived circular-arc distance between the graha and Sun,
--       computed fresh from ga_vargas' own chart_divisionals varga_position data (sign_number +
--       degree_in_sign) for the SAME varga -- re-derived directly rather than restated.
--
-- Conjunct (i) is DELIBERATELY SCOPED to varga != 'D1'. Investigated first without the scope and
-- found 75/2175 violations, ALL on D1 -- root-caused to the SAME dual-D1-source situation F-A17
-- already identified: for D1, _build_combustion_per_varga_rows receives varga_state =
-- _extract_chart_state(chart_output) (ga_structural's own in-memory chart_output, GA3-flavored),
-- never ga_vargas' own chart_divisionals varga='D1' rows -- a SEPARATE, independent PyJHora
-- computation from ga_vargas' own D9 issue F-A17 root-caused. Comparing D1's combustion arc
-- against ga_vargas' own D1 position data would be comparing across the same two known-divergent
-- D1 sources F-A17 already documented -- not a new defect, just an artifact of choosing the wrong
-- authority for D1 specifically. For D2 onward, _build_combustion_per_varga_rows correctly
-- receives varga_state = _load_varga_positions(conn, ...), which reads chart_divisionals fresh --
-- the SAME source this conjunct re-derives against, so the comparison is genuinely apples-to-
-- apples there. Confirmed clean (0/2100 violations) once D1 is excluded on that basis, matching
-- the same avoidance the F-A17 writer fix itself already applies (never mixing D1 sources).
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries migrations 745's/755's/756's/757's seven original conjuncts (a) through (g) forward
-- VERBATIM, including conjuncts (b), (e), and (f), which remain GENUINELY RED TODAY exactly as
-- migration 757 already documented (F-A15/F-A17/F-157 fixes landed, tracked charts not yet
-- rebuilt). Because (b), (e), (f) are all red, the combined 9-conjunct SELECT evaluates to false
-- on live production today; conjuncts (h)/(i) were verified INDIVIDUALLY (their own NOT EXISTS
-- subquery in isolation) rather than via the full combined SELECT.
--
-- Every conjunct was EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_structural integrity contract (target: chart_facts, scoped to
-- graha_vargottama_amplification_factor / bhadra_flag / panchaka_flag / vargottama_per_varga /
-- parivartana_per_varga / combustion_per_varga, 6 of 57 owned categories). D-CND-03:
-- chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12). No distinctness
-- conjunct -- none of these six categories' natural key needs re-asserting
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
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
