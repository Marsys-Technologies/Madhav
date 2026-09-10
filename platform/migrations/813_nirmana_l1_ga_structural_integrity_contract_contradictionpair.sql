-- 813_nirmana_l1_ga_structural_integrity_contract_contradictionpair.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Thirty-ninth follow-up F-A14 widening pass for
-- ga_structural, fourteenth in the 800-819 range (adjudication #2057, continuation 4). Migration
-- 745 covered graha_vargottama_amplification_factor; migration 755 added
-- bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
-- parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
-- graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
-- kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
-- conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
-- graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
-- composite_dispositor_strength; migration 788 added the Group H avastha bundle; migration 789
-- added nakshatra_dispositor_chain; migration 790 added chandra_bala_natal_baseline; migration
-- 791 added the Group O tri-deva bundle; migration 792 added
-- graha_functional_class_per_ascendant; migration 793 added
-- graha_effective_dignity_modified_by_aspects; migration 794 added
-- graha_composite_state_classification; migration 795 added karaka_house_lord_overlap_flag;
-- migration 796 added the Group C Bhava Bala extended bundle; migration 797 added
-- aspect_matrix_summary; migration 798 added the aspect_parashari_given/received bundle;
-- migration 799 added graha_special_state_rollup, discovering F-A18; migration 800 added
-- chart_center_of_gravity; migration 801 added karakatva_strength_per_significance; migration
-- 802 added aspect_received_by_special_point; migration 803 added aspect_jaimini; migration 804
-- added conjunction_per_varga; migration 805 added lord_aspects_lord_per_varga; migration 806
-- added dispositor_chain_per_varga; migration 807 added graha_centrality; migration 808 added
-- chart_cluster; migration 809 added dispositor_tree; migration 810 added
-- graha_in_house_composite_strength; migration 811 added lord_in_house_per_varga; migration 812
-- added net_argala_per_varga (53/57 by the running tally -- see D-L1-105 for a governance-table
-- registry-gap finding that corrects this denominator). This adds contradiction_pair.
--
-- contradiction_pair (`_build_contradiction_pair_rows`) is a cross-category aggregation: for
-- every (fact_subject, family, varga) group across ALL of ga_structural's own emitted rows
-- (`all_rows`, a single pass over the whole build), it flags a "contradiction" when BOTH a
-- benefic-valence source and a malefic-valence source exist for the SAME key. The writer's own
-- `CATEGORY_FAMILY` dict maps FOUR possible source-category pairs to a family
-- (yoga/dosha/argala/net_argala), but only the argala family is live today: yoga_fires/
-- yoga_label are ga_yoga-owned (never present in `all_rows`, a single-asset build pass) and the
-- writer's own `"net_argala"` dict key is a dead reference (the real category is named
-- `net_argala_per_varga`, confirmed 0 live rows under the bare `net_argala` name) -- confirmed
-- live: 100% of contradiction_pair rows have family='argala'. Given the scale of the two source
-- categories this would fully re-derive from (`argala_natal_matrix`/`virodha_argala_natal_matrix`,
-- 62640 rows each, neither yet examined in this arc), this migration ships strong
-- self-consistency and domain conjuncts rather than a full cross-category row-count
-- re-derivation, per the established "don't always need to re-derive the full source algorithm"
-- precedent (migration 800).
--
--   (a20) fact_value_text domain: must equal the writer's own constant
--         "benefic_malefic_conflict" -- the only string this function ever emits.
--   (b20) fact_key format: must equal "opposed_{family}_{varga}" -- the writer's own
--         `f"opposed_{family}_{varga}"` construction, re-derived from the row's own stored
--         family/varga fields.
--   (c20) family domain: value_jsonb.family must be one of the writer's own CATEGORY_FAMILY
--         values (yoga/dosha/argala/net_argala) -- no fifth value is ever legitimate.
--   (d20) argala-family source consistency: when family='argala', benefic_sources must be
--         exactly ["argala_natal_matrix"] and malefic_sources must be exactly
--         ["virodha_argala_natal_matrix"] -- these are the ONLY two categories CATEGORY_FAMILY
--         maps to the argala family, so a genuine argala contradiction can never cite any other
--         source pair.
--   (e20) genuine-contradiction invariant: both benefic_count and malefic_count must be > 0 --
--         the writer's own `if has_benefic and has_malefic:` gate is the sole reason a row is
--         ever emitted at all, so a stored row with either count at zero would contradict its
--         own existence.
--   (f20) target self-consistency: value_jsonb.target must equal fact_subject -- the same
--         subject stored twice.
--   (g20) varga/subject consistency: fact_subject must begin with "{varga}_" -- the writer's own
--         `_varga_from_subject` parse, re-derived as the converse check on what actually got
--         stored (every subject the writer builds already carries its own varga prefix).
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries migrations 745's/755's/756's/757's/758's/759's/780's/781's/782's/783's/784's/785's/
-- 786's/787's/788's/789's/790's/791's/792's/793's/794's/795's/796's/797's/798's/799's/800's/
-- 801's/802's/803's/804's/805's/806's/807's/808's/809's/810's/811's/812's one-hundred-and-
-- seventy-nine original conjuncts (a) through (e19) forward VERBATIM, including conjuncts (b),
-- (e), (f), and (e7)/F-A18, which remain GENUINELY RED TODAY exactly as migration 812 already
-- documented. Because (b), (e), (f), and (e7) are all red, the combined 186-conjunct SELECT
-- evaluates to false on live production today; the new conjuncts were verified INDIVIDUALLY
-- (their own subquery in isolation) rather than via the full combined SELECT.
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
-- chandra_bala_natal_baseline / pranic_strength_per_graha / jaimini_tri_deva_role_per_graha /
-- graha_tri_deva_role_strength / graha_functional_class_per_ascendant /
-- graha_effective_dignity_modified_by_aspects / graha_composite_state_classification /
-- karaka_house_lord_overlap_flag / bhava_bala_positional / bhava_bala_directional /
-- bhava_bala_temporal / bhava_bala_aspectual / bhava_bala_occupant / bhava_bala_lord /
-- bhava_bala_total_extended / house_strength_classification_rollup / aspect_matrix_summary /
-- aspect_parashari_given / aspect_parashari_received / graha_special_state_rollup /
-- chart_center_of_gravity / karakatva_strength_per_significance /
-- aspect_received_by_special_point / aspect_jaimini / conjunction_per_varga, 45 of 57 owned
-- categories). D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count
-- pin (C12). No distinctness conjunct -- none of these forty-five categories' natural key
-- needs re-asserting
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
  -- (vv2) pranic_strength_per_graha.prana_score domain: must be within [0.3375, 1.2] -- the
  -- achievable range given the writer's own PRANIC_BASE_SCORES (0.50-0.80), dignity modifiers
  -- (0.75-1.25), and house modifiers (0.9-1.2), all multiplied together. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'pranic_strength_per_graha' AND fact_key = 'prana_score'
      AND (fact_value_num < 0.3375 OR fact_value_num > 1.2)
  )
  -- (ww2) jaimini_tri_deva_role_per_graha.tri_deva_role domain: must be one of the writer's own
  -- four values ('brahma', 'vishnu', 'shiva', 'neutral') -- no fifth value is ever legitimate.
  -- 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'jaimini_tri_deva_role_per_graha' AND fact_key = 'tri_deva_role'
      AND fact_value_text NOT IN ('brahma', 'vishnu', 'shiva', 'neutral')
  )
  -- (xx2) jaimini_tri_deva_role_per_graha.tri_deva_role full re-derivation: must equal the
  -- classical TRI_DEVA_ROLES membership table (Jaimini Sutram Ch.2) with the writer's own
  -- brahma-checked-first tie-break for Jupiter's dual membership (Jupiter is listed under both
  -- "brahma" and "vishnu", but Python's insertion-ordered dict iteration with the writer's own
  -- `break` always resolves it to "brahma" -- confirmed against all 135 live rows), re-derived
  -- directly from fact_subject rather than restated. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'jaimini_tri_deva_role_per_graha' AND fact_key = 'tri_deva_role'
      AND fact_value_text <> (
        CASE
          WHEN fact_subject IN ('JUP', 'VEN', 'MER') THEN 'brahma'
          WHEN fact_subject IN ('SUN', 'MOON') THEN 'vishnu'
          WHEN fact_subject IN ('MAR', 'SAT', 'RAH_MEAN') THEN 'shiva'
          ELSE 'neutral' END
      )
  )
  -- (yy2) graha_tri_deva_role_strength.role_strength cross-field re-derivation: must equal the
  -- SAME graha's own pranic_strength_per_graha.prana_score multiplied by the writer's own fixed
  -- per-role multiplier (brahma=1.1, vishnu=1.2, shiva=0.9, neutral=1.0) read from the SAME
  -- graha's own jaimini_tri_deva_role_per_graha.tri_deva_role -- a genuine two-category
  -- cross-reference, re-derived directly rather than restated. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts p
      ON p.chart_id = s.chart_id AND p.ayanamsha_id = s.ayanamsha_id AND p.build_id = s.build_id
     AND p.fact_subject = s.fact_subject
     AND p.fact_category = 'pranic_strength_per_graha' AND p.fact_key = 'prana_score'
    JOIN chart_facts r
      ON r.chart_id = s.chart_id AND r.ayanamsha_id = s.ayanamsha_id AND r.build_id = s.build_id
     AND r.fact_subject = s.fact_subject
     AND r.fact_category = 'jaimini_tri_deva_role_per_graha' AND r.fact_key = 'tri_deva_role'
    WHERE s.fact_category = 'graha_tri_deva_role_strength' AND s.fact_key = 'role_strength'
      AND abs(
        s.fact_value_num - round(
          p.fact_value_num * (
            CASE r.fact_value_text
              WHEN 'brahma' THEN 1.1 WHEN 'vishnu' THEN 1.2 WHEN 'shiva' THEN 0.9
              ELSE 1.0 END
          ), 4
        )
      ) > 0.0001
  )
  -- (zz2) graha_functional_class_per_ascendant fact_value_text domain: must be one of the 5
  -- values either branch of `_get_functional_class_dynamic` can ever produce
  -- ('functional_benefic', 'neutral', 'temporal_benefic', 'temporal_malefic', 'yogakaraka').
  -- 0/210 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_functional_class_per_ascendant'
      AND fact_value_text NOT IN
        ('functional_benefic', 'neutral', 'temporal_benefic', 'temporal_malefic', 'yogakaraka')
  )
  -- (aa3) bphs_canonical must equal raman_variant for the same (chart, ayanamsha, graha) -- the
  -- writer's own STAGE-2 comment confirms both are computed by the literal same function call
  -- with the same arguments. 0/105 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts b
      ON b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
     AND b.fact_subject = a.fact_subject
     AND b.fact_category = 'graha_functional_class_per_ascendant' AND b.fact_key = 'raman_variant'
    WHERE a.fact_category = 'graha_functional_class_per_ascendant' AND a.fact_key = 'bphs_canonical'
      AND a.fact_value_text <> b.fact_value_text
  )
  -- (bb3) full re-derivation: bphs_canonical must equal `_get_functional_class_dynamic`'s own
  -- two-branch formula -- for Aries lagna, the writer's own 7-entry FUNCTIONAL_CLASS_BPHS
  -- table; for any other lagna, the dynamic kendra/trikona/dusthana/upachaya classification of
  -- the houses each graha rules (via the classical _SIGN_LORDS_ORDERED table) from the chart's
  -- own lagna sign (graha_position.LAGNA.sign, the layer-root T0 asset's authoritative D1
  -- reference), computed via a LATERAL derivation of each graha's house(s)-from-lagna rather
  -- than a hand-flattened expression, so the intermediate kendra/trikona/dusthana/upachaya
  -- booleans exactly mirror the writer's own variable names. Confirmed both branches are
  -- genuinely exercised live (two charts Aries, one Cancer). 0/105 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts lg
      ON lg.chart_id = a.chart_id AND lg.ayanamsha_id = a.ayanamsha_id
     AND lg.fact_category = 'graha_position' AND lg.fact_subject = 'LAGNA' AND lg.fact_key = 'sign'
    CROSS JOIN LATERAL (
      SELECT
        (array_position(
          ARRAY['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'],
          lg.fact_value_text
        ) - 1) AS lagna_idx,
        (CASE a.fact_subject
          WHEN 'SUN' THEN 4 WHEN 'MOON' THEN 3 WHEN 'MAR' THEN 0 WHEN 'MER' THEN 2
          WHEN 'JUP' THEN 8 WHEN 'VEN' THEN 1 WHEN 'SAT' THEN 9 ELSE NULL END) AS sign_idx1,
        (CASE a.fact_subject
          WHEN 'MAR' THEN 7 WHEN 'MER' THEN 5 WHEN 'JUP' THEN 11 WHEN 'VEN' THEN 6
          WHEN 'SAT' THEN 10 ELSE NULL END) AS sign_idx2
    ) idx
    CROSS JOIN LATERAL (
      SELECT
        ((idx.sign_idx1 - idx.lagna_idx + 12) % 12) + 1 AS house1,
        CASE WHEN idx.sign_idx2 IS NOT NULL
          THEN ((idx.sign_idx2 - idx.lagna_idx + 12) % 12) + 1
          ELSE NULL END AS house2
    ) hs
    CROSS JOIN LATERAL (
      SELECT
        (hs.house1 IN (1,4,7,10) OR hs.house2 IN (1,4,7,10)) AS is_kendra,
        (hs.house1 IN (1,5,9) OR hs.house2 IN (1,5,9)) AS is_trikona,
        (hs.house1 IN (6,8,12) OR hs.house2 IN (6,8,12)) AS is_dusthana,
        (hs.house1 IN (3,11) OR hs.house2 IN (3,11)) AS is_upachaya,
        (a.fact_subject IN ('SUN', 'MAR', 'SAT')) AS is_malefic
    ) cls
    WHERE a.fact_category = 'graha_functional_class_per_ascendant' AND a.fact_key = 'bphs_canonical'
      AND a.fact_value_text <> (
        CASE WHEN lg.fact_value_text = 'Aries' THEN (
          CASE a.fact_subject
            WHEN 'SUN' THEN 'temporal_malefic' WHEN 'MOON' THEN 'functional_benefic'
            WHEN 'MAR' THEN 'yogakaraka' WHEN 'MER' THEN 'temporal_malefic'
            WHEN 'JUP' THEN 'temporal_benefic' WHEN 'VEN' THEN 'temporal_benefic'
            WHEN 'SAT' THEN 'temporal_malefic' ELSE 'neutral' END
        ) ELSE (
          CASE
            WHEN cls.is_kendra AND cls.is_trikona THEN 'yogakaraka'
            WHEN cls.is_trikona THEN 'temporal_benefic'
            WHEN cls.is_dusthana AND NOT cls.is_kendra THEN 'temporal_malefic'
            WHEN cls.is_kendra THEN (CASE WHEN cls.is_malefic THEN 'temporal_benefic' ELSE 'temporal_malefic' END)
            WHEN cls.is_upachaya THEN 'temporal_malefic'
            ELSE 'neutral'
          END
        ) END
      )
  )
  -- (cc3) graha_effective_dignity_modified_by_aspects.effective_dignity_score domain: must be
  -- within [0.0, 1.0] -- the writer's own clamp bounds (`min(max(...), 0.0), 1.0)`). 0/135
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_effective_dignity_modified_by_aspects'
      AND (fact_value_num < 0.0 OR fact_value_num > 1.0)
  )
  -- (dd3) value_jsonb.base_dignity domain: must be one of the writer's own dignity_scores dict
  -- values (exalted=1.0, own_sign=0.75, neutral=0.5, debilitated=0.25) -- no fifth value is ever
  -- legitimate. 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_effective_dignity_modified_by_aspects'
      AND (fact_value_jsonb->>'base_dignity')::numeric NOT IN (1.0, 0.75, 0.5, 0.25)
  )
  -- (ee3) full cross-field re-derivation: fact_value_num must equal
  -- round(clamp(base_dignity + sum(contributions[].delta) * 0.1, 0.0, 1.0), 4) -- the writer's
  -- own effective_dignity_score formula, re-derived directly from the row's own SELF-CONTAINED
  -- value_jsonb (no cross-category joins needed: base_dignity and every contribution's delta are
  -- already stored in the same row). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL (
      SELECT COALESCE(sum((c->>'delta')::numeric), 0.0) AS delta_sum
      FROM jsonb_array_elements(a.fact_value_jsonb->'contributions') c
    ) ds
    WHERE a.fact_category = 'graha_effective_dignity_modified_by_aspects'
      AND a.fact_value_num <> round(
        LEAST(GREATEST(
          (a.fact_value_jsonb->>'base_dignity')::numeric + ds.delta_sum * 0.1
        , 0.0), 1.0)
      , 4)
  )
  -- (ff3) per-contribution delta re-derivation: each contributions[] entry's delta must equal
  -- round(0.25 * aspect_strength, 4) when functional_class is benefic (functional_benefic/
  -- yogakaraka/temporal_benefic), round(-0.25 * aspect_strength, 4) when malefic
  -- (temporal_malefic/functional_malefic), else 0.0 -- the writer's own
  -- _BENEFIC_FUNCTIONAL_CLASSES / _MALEFIC_FUNCTIONAL_CLASSES bucket membership, re-derived
  -- directly rather than restated. 0/223 contribution entries checked (sum across all 135 rows),
  -- 0 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL jsonb_array_elements(a.fact_value_jsonb->'contributions') c
    WHERE a.fact_category = 'graha_effective_dignity_modified_by_aspects'
      AND (c->>'delta')::numeric <> (
        CASE
          WHEN (c->>'functional_class') IN ('functional_benefic', 'yogakaraka', 'temporal_benefic')
            THEN round(0.25 * (c->>'aspect_strength')::numeric, 4)
          WHEN (c->>'functional_class') IN ('temporal_malefic', 'functional_malefic')
            THEN round(-0.25 * (c->>'aspect_strength')::numeric, 4)
          ELSE 0.0
        END
      )
  )
  -- (a4) graha_composite_state_classification fact_value_text domain: must be one of the
  -- writer's own seven possible classification values -- 'debilitated' (plain, uncancelled) has
  -- 0 live rows today but remains a legitimate value in the writer's own decision tree. 0/135
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_composite_state_classification'
      AND fact_value_text NOT IN
        ('severely_afflicted', 'debilitated', 'debilitation_cancelled', 'afflicted',
         'well_placed', 'weak', 'neutral')
  )
  -- (b4) full first-principles re-derivation of the entire seven-way decision tree: dignity
  -- (exalted/debilitated/own_sign/neutral) re-derived from graha_position.sign against the
  -- classical exaltation/debilitation/own-sign tables (pyjhora_adapter/dignities.py's own
  -- _EXALT_SIGN/_DEBIL_SIGN/_OWN_SIGNS); combustion from graha_position.combustion_state;
  -- retrograde from graha_position.retrograde_flag; the debilitation_cancelled/debilitated
  -- split from ga_yoga's own authoritative ga_yoga_firings.neecha_bhanga_raja_yoga row
  -- (fired=true AND graha present in constituent_planets) -- a genuine cross-ASSET §N.5
  -- reference, not a restated local computation. Verified against ALL 135 live rows (not a
  -- sample). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN LATERAL (
      SELECT
        p_comb.fact_value_text AS combustion_state,
        p_retro.fact_value_text AS retrograde_flag,
        (CASE
          WHEN a.fact_subject = 'SUN' AND p_sign.fact_value_text = 'Aries' THEN 'exalted'
          WHEN a.fact_subject = 'SUN' AND p_sign.fact_value_text = 'Libra' THEN 'debilitated'
          WHEN a.fact_subject = 'SUN' AND p_sign.fact_value_text = 'Leo' THEN 'own_sign'
          WHEN a.fact_subject = 'MOON' AND p_sign.fact_value_text = 'Taurus' THEN 'exalted'
          WHEN a.fact_subject = 'MOON' AND p_sign.fact_value_text = 'Scorpio' THEN 'debilitated'
          WHEN a.fact_subject = 'MOON' AND p_sign.fact_value_text = 'Cancer' THEN 'own_sign'
          WHEN a.fact_subject = 'MAR' AND p_sign.fact_value_text = 'Capricorn' THEN 'exalted'
          WHEN a.fact_subject = 'MAR' AND p_sign.fact_value_text = 'Cancer' THEN 'debilitated'
          WHEN a.fact_subject = 'MAR' AND p_sign.fact_value_text IN ('Aries','Scorpio') THEN 'own_sign'
          WHEN a.fact_subject = 'MER' AND p_sign.fact_value_text = 'Virgo' THEN 'exalted'
          WHEN a.fact_subject = 'MER' AND p_sign.fact_value_text = 'Pisces' THEN 'debilitated'
          WHEN a.fact_subject = 'MER' AND p_sign.fact_value_text IN ('Gemini','Virgo') THEN 'own_sign'
          WHEN a.fact_subject = 'JUP' AND p_sign.fact_value_text = 'Cancer' THEN 'exalted'
          WHEN a.fact_subject = 'JUP' AND p_sign.fact_value_text = 'Capricorn' THEN 'debilitated'
          WHEN a.fact_subject = 'JUP' AND p_sign.fact_value_text IN ('Sagittarius','Pisces') THEN 'own_sign'
          WHEN a.fact_subject = 'VEN' AND p_sign.fact_value_text = 'Pisces' THEN 'exalted'
          WHEN a.fact_subject = 'VEN' AND p_sign.fact_value_text = 'Virgo' THEN 'debilitated'
          WHEN a.fact_subject = 'VEN' AND p_sign.fact_value_text IN ('Taurus','Libra') THEN 'own_sign'
          WHEN a.fact_subject = 'SAT' AND p_sign.fact_value_text = 'Libra' THEN 'exalted'
          WHEN a.fact_subject = 'SAT' AND p_sign.fact_value_text = 'Aries' THEN 'debilitated'
          WHEN a.fact_subject = 'SAT' AND p_sign.fact_value_text IN ('Capricorn','Aquarius') THEN 'own_sign'
          ELSE 'neutral'
        END) AS re_dignity
      FROM chart_facts p_sign
      JOIN chart_facts p_comb ON p_comb.chart_id=p_sign.chart_id AND p_comb.ayanamsha_id=p_sign.ayanamsha_id
        AND p_comb.fact_category='graha_position' AND p_comb.fact_subject=p_sign.fact_subject AND p_comb.fact_key='combustion_state'
      JOIN chart_facts p_retro ON p_retro.chart_id=p_sign.chart_id AND p_retro.ayanamsha_id=p_sign.ayanamsha_id
        AND p_retro.fact_category='graha_position' AND p_retro.fact_subject=p_sign.fact_subject AND p_retro.fact_key='retrograde_flag'
      WHERE p_sign.chart_id=a.chart_id AND p_sign.ayanamsha_id=a.ayanamsha_id
        AND p_sign.fact_category='graha_position' AND p_sign.fact_subject=a.fact_subject AND p_sign.fact_key='sign'
    ) re ON true
    WHERE a.fact_category = 'graha_composite_state_classification'
      AND a.fact_value_text <> (CASE
          WHEN re.re_dignity = 'debilitated' AND re.combustion_state = 'combust' THEN 'severely_afflicted'
          WHEN re.re_dignity = 'debilitated' AND EXISTS (
            SELECT 1 FROM ga_yoga_firings y
            WHERE y.chart_id = a.chart_id AND y.ayanamsha_id = a.ayanamsha_id
              AND y.yoga_canonical_id = 'neecha_bhanga_raja_yoga' AND y.fired = true
              AND lower(CASE a.fact_subject
                WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
                WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
                WHEN 'SAT' THEN 'Saturn' ELSE a.fact_subject END) = ANY (
                  SELECT jsonb_array_elements_text(y.constituent_planets)
                )
          ) THEN 'debilitation_cancelled'
          WHEN re.re_dignity = 'debilitated' THEN 'debilitated'
          WHEN re.combustion_state = 'combust' THEN 'afflicted'
          WHEN re.re_dignity IN ('exalted', 'own_sign') THEN 'well_placed'
          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'
          ELSE 'neutral'
        END)
  )
  -- (a5) karaka_house_lord_overlap_flag fact_value_text domain: must be 'true' or 'false' --
  -- no third value is ever legitimate for this boolean flag. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karaka_house_lord_overlap_flag'
      AND fact_value_text NOT IN ('true', 'false')
  )
  -- (b5) full re-derivation: is_overlap must equal (the significance's fixed classical natural
  -- karaka == the lord of the significance's fixed house, re-derived from Lagna sign via the
  -- same house-from-lagna arithmetic proven in migration 792's conjunct (bb3), then the
  -- classical SIGN_LORDS table). NATURAL_KARAKAS and significance_to_house are the writer's own
  -- fixed classical assignment dicts, hardcoded directly rather than re-derived from a further
  -- authority. Verified against ALL 180 live rows (not a sample), including all 50 true rows.
  -- 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts lg
      ON lg.chart_id = a.chart_id AND lg.ayanamsha_id = a.ayanamsha_id
     AND lg.fact_category = 'graha_position' AND lg.fact_subject = 'LAGNA' AND lg.fact_key = 'sign'
    CROSS JOIN LATERAL (
      SELECT
        (array_position(
          ARRAY['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'],
          lg.fact_value_text
        ) - 1) AS lagna_idx,
        (CASE a.fact_subject
          WHEN 'self' THEN 1 WHEN 'wealth' THEN 2 WHEN 'siblings' THEN 3 WHEN 'mother' THEN 4
          WHEN 'children' THEN 5 WHEN 'enemies' THEN 6 WHEN 'spouse' THEN 7 WHEN 'longevity' THEN 8
          WHEN 'luck' THEN 9 WHEN 'career' THEN 10 WHEN 'gains' THEN 11 WHEN 'losses' THEN 12
          ELSE NULL END) AS house_num,
        (CASE a.fact_subject
          WHEN 'self' THEN 'Sun' WHEN 'wealth' THEN 'Jupiter' WHEN 'siblings' THEN 'Mars'
          WHEN 'mother' THEN 'Moon' WHEN 'children' THEN 'Jupiter' WHEN 'enemies' THEN 'Saturn'
          WHEN 'spouse' THEN 'Venus' WHEN 'longevity' THEN 'Saturn' WHEN 'luck' THEN 'Jupiter'
          WHEN 'career' THEN 'Saturn' WHEN 'gains' THEN 'Jupiter' WHEN 'losses' THEN 'Saturn'
          ELSE NULL END) AS natural_karaka
    ) idx
    CROSS JOIN LATERAL (
      SELECT
        (ARRAY['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'])
          [((idx.lagna_idx + idx.house_num - 1) % 12) + 1] AS house_sign
    ) hs
    CROSS JOIN LATERAL (
      SELECT (CASE hs.house_sign
        WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
        WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
        WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
        WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
        ELSE NULL END) AS house_lord
    ) hl
    WHERE a.fact_category = 'karaka_house_lord_overlap_flag'
      AND (a.fact_value_text = 'true') <> (idx.natural_karaka = hl.house_lord)
  )
  -- (c) bhava_bala_positional full re-derivation: 1.0 for angular houses (1,4,7,10), 0.875 for
  -- trikona (5,9 -- house 1 checked first per the writer's own branch order), 0.375 for
  -- dusthana (6,8,12), 0.5 otherwise -- a pure function of house number, no chart data needed.
  -- 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_bala_positional'
      AND fact_value_num <> (CASE substring(fact_subject from 7)::int
          WHEN 1 THEN 1.0 WHEN 4 THEN 1.0 WHEN 7 THEN 1.0 WHEN 10 THEN 1.0
          WHEN 5 THEN 0.875 WHEN 9 THEN 0.875
          WHEN 6 THEN 0.375 WHEN 8 THEN 0.375 WHEN 12 THEN 0.375
          ELSE 0.5 END)
  )
  -- (d) bhava_bala_directional full re-derivation: the writer's own directional_map dict, a pure
  -- function of house number. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_bala_directional'
      AND fact_value_num <> (CASE substring(fact_subject from 7)::int
          WHEN 1 THEN 1.0 WHEN 4 THEN 1.0 WHEN 7 THEN 0.75 WHEN 10 THEN 0.75
          WHEN 2 THEN 0.5 WHEN 5 THEN 0.5 WHEN 8 THEN 0.5 WHEN 11 THEN 0.5
          WHEN 3 THEN 0.375 WHEN 6 THEN 0.375 WHEN 9 THEN 0.375 WHEN 12 THEN 0.375
          ELSE 0.5 END)
  )
  -- (e2) bhava_bala_temporal full re-derivation: 0.75 for angular houses, 0.5 otherwise -- a
  -- pure function of house number. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_bala_temporal'
      AND fact_value_num <> (CASE WHEN substring(fact_subject from 7)::int IN (1,4,7,10) THEN 0.75 ELSE 0.5 END)
  )
  -- (f2) bhava_bala_aspectual domain: must be one of {0.5, 0.625, 0.75, 0.875} -- the writer's
  -- own 0.5 + 0.125*n formula for n benefics (Jupiter/Venus/Mercury) aspecting, n in [0,3].
  -- 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_bala_aspectual'
      AND fact_value_num NOT IN (0.5, 0.625, 0.75, 0.875)
  )
  -- (g2) bhava_bala_occupant domain: must be 0.5 + 0.1*n for integer n in [0,9] (max grahas that
  -- could occupy one house) -- the writer's own formula, re-derived as a modulo-0.1 + range
  -- check rather than restated. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_bala_occupant'
      AND (fact_value_num < 0.5 OR fact_value_num > 1.4
           OR abs(((fact_value_num - 0.5) * 10) - round((fact_value_num - 0.5) * 10)) > 0.0001)
  )
  -- (h2) bhava_bala_lord domain: must be one of the writer's own four dignity-strength values
  -- {1.0, 0.875, 0.5, 0.25}. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'bhava_bala_lord'
      AND fact_value_num NOT IN (1.0, 0.875, 0.5, 0.25)
  )
  -- (i2) bhava_bala_total_extended self-consistency: total must equal the arithmetic mean of the
  -- SAME house's six sibling sub-score categories -- a genuine cross-category re-derivation
  -- within the same bundle, not a bare restatement. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts t
    JOIN chart_facts p ON p.chart_id=t.chart_id AND p.ayanamsha_id=t.ayanamsha_id AND p.build_id=t.build_id
      AND p.fact_subject=t.fact_subject AND p.fact_category='bhava_bala_positional'
    JOIN chart_facts d ON d.chart_id=t.chart_id AND d.ayanamsha_id=t.ayanamsha_id AND d.build_id=t.build_id
      AND d.fact_subject=t.fact_subject AND d.fact_category='bhava_bala_directional'
    JOIN chart_facts tm ON tm.chart_id=t.chart_id AND tm.ayanamsha_id=t.ayanamsha_id AND tm.build_id=t.build_id
      AND tm.fact_subject=t.fact_subject AND tm.fact_category='bhava_bala_temporal'
    JOIN chart_facts asp ON asp.chart_id=t.chart_id AND asp.ayanamsha_id=t.ayanamsha_id AND asp.build_id=t.build_id
      AND asp.fact_subject=t.fact_subject AND asp.fact_category='bhava_bala_aspectual'
    JOIN chart_facts occ ON occ.chart_id=t.chart_id AND occ.ayanamsha_id=t.ayanamsha_id AND occ.build_id=t.build_id
      AND occ.fact_subject=t.fact_subject AND occ.fact_category='bhava_bala_occupant'
    JOIN chart_facts lo ON lo.chart_id=t.chart_id AND lo.ayanamsha_id=t.ayanamsha_id AND lo.build_id=t.build_id
      AND lo.fact_subject=t.fact_subject AND lo.fact_category='bhava_bala_lord'
    WHERE t.fact_category = 'bhava_bala_total_extended'
      AND abs(t.fact_value_num - round(
        (p.fact_value_num + d.fact_value_num + tm.fact_value_num + asp.fact_value_num
         + occ.fact_value_num + lo.fact_value_num) / 6.0, 4)) > 0.0001
  )
  -- (j2) house_strength_classification_rollup full re-derivation: classification must equal the
  -- writer's own threshold function of the SAME house's bhava_bala_total_extended.total (>=0.75
  -- strong, >=0.5 normal, else weak) -- re-derived by reading the sibling category rather than
  -- restated. 0/180 violations live, confirmed non-vacuous across all three branches
  -- (strong=15, normal=111, weak=54).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts t ON t.chart_id=c.chart_id AND t.ayanamsha_id=c.ayanamsha_id AND t.build_id=c.build_id
      AND t.fact_subject=c.fact_subject AND t.fact_category='bhava_bala_total_extended'
    WHERE c.fact_category = 'house_strength_classification_rollup'
      AND c.fact_value_text <> (CASE
          WHEN t.fact_value_num >= 0.75 THEN 'strong'
          WHEN t.fact_value_num >= 0.5 THEN 'normal'
          ELSE 'weak' END)
  )
  -- (k) aspect_matrix_summary.aspects_received_count domain: must be a non-negative integer
  -- <= 9 -- the theoretical ceiling given ALL_GRAHAS has 9 members, each contributing at most
  -- one aspect per house per the writer's own per-graha aspect-offset loop. 0/180 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_matrix_summary'
      AND (fact_value_num < 0 OR fact_value_num > 9 OR fact_value_num <> round(fact_value_num))
  )
  -- (l) full re-derivation: aspects_received_count must equal the actual count of stored
  -- aspect_parashari_received rows for the SAME (chart, ayanamsha, build, house_key) --
  -- re-derived directly from the sibling category rather than restated. 0/180 violations live,
  -- confirmed non-vacuous (150/180 nonzero matches).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    LEFT JOIN (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, count(*) AS n
      FROM chart_facts
      WHERE fact_category = 'aspect_parashari_received'
      GROUP BY chart_id, ayanamsha_id, build_id, fact_subject
    ) r ON r.chart_id = a.chart_id AND r.ayanamsha_id = a.ayanamsha_id
       AND r.build_id = a.build_id AND r.fact_subject = a.fact_subject
    WHERE a.fact_category = 'aspect_matrix_summary'
      AND a.fact_value_num <> COALESCE(r.n, 0)
  )
  -- (a6) aspect_parashari_given.fact_value_num domain: must equal 1.0 -- the classical scheme
  -- has no fractional aspects (every offset in _GRAHA_PARASHARI_ASPECTS carries strength 1.0).
  -- 0/285 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_parashari_given' AND fact_value_num <> 1.0
  )
  -- (b6) aspect_parashari_given.fact_key format: must match house_(1-12). 0/285 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_parashari_given'
      AND fact_key !~ '^house_(1[0-2]|[1-9])$'
  )
  -- (c6) aspect_parashari_given full re-derivation, direction 1 (soundness): every stored target
  -- house must be a legitimate classical aspect of the graha's own house (from
  -- graha_position.house_d1) under its offset table (Mars 4/7/8; Jupiter/Rahu/Ketu 5/7/9;
  -- Saturn 3/7/10; all others the universal 7th). 0/285 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts hp ON hp.chart_id = a.chart_id AND hp.ayanamsha_id = a.ayanamsha_id
      AND hp.fact_category = 'graha_position' AND hp.fact_subject = a.fact_subject
      AND hp.fact_key = 'house_d1'
    WHERE a.fact_category = 'aspect_parashari_given'
      AND NOT EXISTS (
        SELECT 1 FROM unnest(CASE a.fact_subject
            WHEN 'MAR' THEN ARRAY[4,7,8]
            WHEN 'JUP' THEN ARRAY[5,7,9] WHEN 'RAH_MEAN' THEN ARRAY[5,7,9]
            WHEN 'KET_MEAN' THEN ARRAY[5,7,9]
            WHEN 'SAT' THEN ARRAY[3,7,10]
            ELSE ARRAY[7] END) AS off
        WHERE ((hp.fact_value_num::int - 1 + off - 1) % 12) + 1 = substring(a.fact_key from 7)::int
      )
  )
  -- (d6) aspect_parashari_given full re-derivation, direction 2 (completeness): every legitimate
  -- classical aspect must actually be stored -- no missing rows. 0/285 violations live
  -- (confirmed non-vacuous: 285/285 rows join-matched in the verification query).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts hp
    CROSS JOIN LATERAL unnest(CASE hp.fact_subject
        WHEN 'MAR' THEN ARRAY[4,7,8]
        WHEN 'JUP' THEN ARRAY[5,7,9] WHEN 'RAH_MEAN' THEN ARRAY[5,7,9]
        WHEN 'KET_MEAN' THEN ARRAY[5,7,9]
        WHEN 'SAT' THEN ARRAY[3,7,10]
        ELSE ARRAY[7] END) AS off
    WHERE hp.fact_category = 'graha_position' AND hp.fact_key = 'house_d1'
      AND hp.fact_subject IN ('SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN')
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts a
        WHERE a.chart_id = hp.chart_id AND a.ayanamsha_id = hp.ayanamsha_id
          AND a.fact_subject = hp.fact_subject AND a.fact_category = 'aspect_parashari_given'
          AND a.fact_key = 'house_' || (((hp.fact_value_num::int - 1 + off - 1) % 12) + 1)
      )
  )
  -- (e6) aspect_parashari_received.fact_value_num domain: must equal 1.0. 0/285 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_parashari_received' AND fact_value_num <> 1.0
  )
  -- (f6) aspect_parashari_received.fact_subject format: must match HOUSE_(1-12). 0/285
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_parashari_received'
      AND fact_subject !~ '^HOUSE_(1[0-2]|[1-9])$'
  )
  -- (g6) given -> received bidirectional correspondence: every aspect_parashari_given row must
  -- have a matching aspect_parashari_received row (subject=upper(given.key), key=
  -- "from_"||given.subject, same value) for the SAME (chart, ayanamsha, build) -- the writer's
  -- own same-loop dual-emission, re-derived as a genuine cross-row check rather than a bare
  -- restatement. 0/285 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts g
    WHERE g.fact_category = 'aspect_parashari_given'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts r
        WHERE r.chart_id = g.chart_id AND r.ayanamsha_id = g.ayanamsha_id AND r.build_id = g.build_id
          AND r.fact_category = 'aspect_parashari_received'
          AND r.fact_subject = upper(g.fact_key)
          AND r.fact_key = 'from_' || g.fact_subject
          AND r.fact_value_num = g.fact_value_num
      )
  )
  -- (h6) received -> given bidirectional correspondence: the reverse direction of (g6), closing
  -- the loop without re-deriving the classical formula a second time for the received side.
  -- 0/285 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts r
    WHERE r.fact_category = 'aspect_parashari_received'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts g
        WHERE g.chart_id = r.chart_id AND g.ayanamsha_id = r.ayanamsha_id AND g.build_id = r.build_id
          AND g.fact_category = 'aspect_parashari_given'
          AND g.fact_subject = substring(r.fact_key from 6)
          AND g.fact_key = lower(r.fact_subject)
          AND g.fact_value_num = r.fact_value_num
      )
  )
  -- (a7) graha_special_state_rollup fact_value_text domain: must be 'true' or 'false' across
  -- ALL five fact_keys -- no third value is ever legitimate for any of these boolean flags.
  -- 0/675 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_special_state_rollup'
      AND fact_value_text NOT IN ('true', 'false')
  )
  -- (b7) is_combust must equal ga_positions' own graha_position.combustion_state = 'combust'
  -- for the same (chart, ayanamsha, subject). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts p ON p.chart_id = a.chart_id AND p.ayanamsha_id = a.ayanamsha_id
      AND p.fact_category = 'graha_position' AND p.fact_subject = a.fact_subject
      AND p.fact_key = 'combustion_state'
    WHERE a.fact_category = 'graha_special_state_rollup' AND a.fact_key = 'is_combust'
      AND (a.fact_value_text = 'true') <> (p.fact_value_text = 'combust')
  )
  -- (c7) is_retrograde must equal ga_positions' own graha_position.retrograde_flag =
  -- 'retrograde' for the same (chart, ayanamsha, subject). 0/135 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts p ON p.chart_id = a.chart_id AND p.ayanamsha_id = a.ayanamsha_id
      AND p.fact_category = 'graha_position' AND p.fact_subject = a.fact_subject
      AND p.fact_key = 'retrograde_flag'
    WHERE a.fact_category = 'graha_special_state_rollup' AND a.fact_key = 'is_retrograde'
      AND (a.fact_value_text = 'true') <> (p.fact_value_text = 'retrograde')
  )
  -- (d7) is_debilitated / is_exalted must equal the classical exaltation/debilitation
  -- re-derivation from graha_position.sign (the same table already embedded since migration
  -- 794's conjunct (b4)). 0/270 violations live (135 rows x 2 keys).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts p_sign ON p_sign.chart_id = a.chart_id AND p_sign.ayanamsha_id = a.ayanamsha_id
      AND p_sign.fact_category = 'graha_position' AND p_sign.fact_subject = a.fact_subject
      AND p_sign.fact_key = 'sign'
    WHERE a.fact_category = 'graha_special_state_rollup' AND a.fact_key IN ('is_debilitated', 'is_exalted')
      AND (
        (a.fact_key = 'is_debilitated' AND (a.fact_value_text = 'true') <> (
          (CASE
            WHEN a.fact_subject = 'SUN' AND p_sign.fact_value_text = 'Libra' THEN true
            WHEN a.fact_subject = 'MOON' AND p_sign.fact_value_text = 'Scorpio' THEN true
            WHEN a.fact_subject = 'MAR' AND p_sign.fact_value_text = 'Cancer' THEN true
            WHEN a.fact_subject = 'MER' AND p_sign.fact_value_text = 'Pisces' THEN true
            WHEN a.fact_subject = 'JUP' AND p_sign.fact_value_text = 'Capricorn' THEN true
            WHEN a.fact_subject = 'VEN' AND p_sign.fact_value_text = 'Virgo' THEN true
            WHEN a.fact_subject = 'SAT' AND p_sign.fact_value_text = 'Aries' THEN true
            ELSE false END)
        ))
        OR
        (a.fact_key = 'is_exalted' AND (a.fact_value_text = 'true') <> (
          (CASE
            WHEN a.fact_subject = 'SUN' AND p_sign.fact_value_text = 'Aries' THEN true
            WHEN a.fact_subject = 'MOON' AND p_sign.fact_value_text = 'Taurus' THEN true
            WHEN a.fact_subject = 'MAR' AND p_sign.fact_value_text = 'Capricorn' THEN true
            WHEN a.fact_subject = 'MER' AND p_sign.fact_value_text = 'Virgo' THEN true
            WHEN a.fact_subject = 'JUP' AND p_sign.fact_value_text = 'Cancer' THEN true
            WHEN a.fact_subject = 'VEN' AND p_sign.fact_value_text = 'Pisces' THEN true
            WHEN a.fact_subject = 'SAT' AND p_sign.fact_value_text = 'Libra' THEN true
            ELSE false END)
        ))
      )
  )
  -- (e7) F-A18, GENUINELY RED TODAY: is_vargottama must equal ga_vargas' own authoritative D9
  -- chart_divisionals.varga_vargottama_flag for the same (chart, ayanamsha, graha) -- re-derived
  -- here directly rather than restated, mirroring migration 792's conjunct (b) exactly. The
  -- writer's own `_build_special_state_rows` still computes is_vargottama via the SAME buggy
  -- inline navamsha formula F-A15 already fixed in a DIFFERENT function
  -- (`_build_shadbala_extension_rows`'s graha_vargottama_amplification_factor) -- this second
  -- call site was never updated. GENUINELY RED on 4/105 rows -- the SAME 2 charts/4 graha-
  -- ayanamsha combinations as F-A15's own tracked residual, confirming the same underlying
  -- pre-fix computation duplicated into a still-unfixed second location. Will clear once the
  -- writer is fixed (mirroring F-A15's own fix) AND the affected charts next rebuild.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_divisionals v
      ON v.chart_id = a.chart_id AND v.ayanamsha_id = a.ayanamsha_id
     AND v.fact_category = 'varga_vargottama_flag' AND v.varga = 'D9'
     AND v.graha = initcap(CASE a.fact_subject
         WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
         WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
         WHEN 'SAT' THEN 'Saturn' ELSE a.fact_subject END)
    WHERE a.fact_category = 'graha_special_state_rollup' AND a.fact_key = 'is_vargottama'
      AND (a.fact_value_text = 'true') <> v.vargottama
  )
  -- (a8) chart_center_of_gravity.final_dispositor fact_value_text domain: must be one of the
  -- seven classical grahas that can ever be a SIGN_LORDS value -- Rahu/Ketu can never terminate
  -- a chain since they are never a sign lord. 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'chart_center_of_gravity' AND fact_key = 'final_dispositor'
      AND fact_value_text NOT IN ('SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT')
  )
  -- (b8) cluster_count / final_dispositor's own fact_value_num (chains_terminating_here)
  -- domain: both must be integers in [1, 9] -- the achievable range given exactly 9 walking
  -- grahas per varga. 0/435 + 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'chart_center_of_gravity' AND fact_key IN ('cluster_count', 'final_dispositor')
      AND (fact_value_num < 1 OR fact_value_num > 9 OR fact_value_num <> round(fact_value_num))
  )
  -- (c8) cluster_count self-consistency: must equal the count of distinct keys in the SAME
  -- row's own sibling final_dispositor row's value_jsonb.tally -- the writer's own len(tally)
  -- computation, re-derived by counting the stored JSON object's own keys rather than
  -- restated. 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts f ON f.chart_id = a.chart_id AND f.ayanamsha_id = a.ayanamsha_id
      AND f.build_id = a.build_id AND f.fact_subject = a.fact_subject
      AND f.fact_category = 'chart_center_of_gravity' AND f.fact_key = 'final_dispositor'
    WHERE a.fact_category = 'chart_center_of_gravity' AND a.fact_key = 'cluster_count'
      AND a.fact_value_num <> (SELECT count(*) FROM jsonb_object_keys(f.fact_value_jsonb->'tally'))
  )
  -- (d8) final_dispositor cross-field consistency: fact_value_num (chains_terminating_here)
  -- must equal value_jsonb.tally[fact_value_text] -- the writer's own tally[final_disp] lookup,
  -- re-derived directly from the row's own stored tally rather than restated. 0/435 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'chart_center_of_gravity' AND a.fact_key = 'final_dispositor'
      AND a.fact_value_num <> (a.fact_value_jsonb->'tally'->>a.fact_value_text)::numeric
  )
  -- (e8) final_dispositor genuine-argmax invariant: no OTHER entry in value_jsonb.tally may
  -- exceed fact_value_num -- re-derives the writer's own max(tally, key=lambda x: tally[x])
  -- selection as a real cross-entry comparison (ties are legitimate and not asserted away, only
  -- a strict violation of the max property is caught). 0/435 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL jsonb_each_text(a.fact_value_jsonb->'tally') t(k, v)
    WHERE a.fact_category = 'chart_center_of_gravity' AND a.fact_key = 'final_dispositor'
      AND t.v::numeric > a.fact_value_num
  )
  -- (f8) tally-sum invariant: the sum of ALL value_jsonb.tally entries must equal exactly 9 --
  -- every one of the 9 ALL_GRAHAS members walks to some terminus every time. 0/435 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT a.fact_id, sum((t.v)::int) AS total
      FROM chart_facts a
      CROSS JOIN LATERAL jsonb_each_text(a.fact_value_jsonb->'tally') t(k, v)
      WHERE a.fact_category = 'chart_center_of_gravity' AND a.fact_key = 'final_dispositor'
      GROUP BY a.fact_id
    ) x
    WHERE x.total <> 9
  )
  -- (a9) karakatva_strength_per_significance.natural_karaka fact_value_text domain: must be
  -- one of the 8 grahas that ever appear as a NATURAL_KARAKAS value. 0/450 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karakatva_strength_per_significance' AND fact_key = 'natural_karaka'
      AND fact_value_text NOT IN ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu')
  )
  -- (b9) natural_karaka full re-derivation: must equal the writer's own NATURAL_KARAKAS dict,
  -- hardcoded directly for all 30 significances. 0/450 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karakatva_strength_per_significance' AND fact_key = 'natural_karaka'
      AND fact_value_text <> (CASE fact_subject
          WHEN 'self' THEN 'Sun' WHEN 'wealth' THEN 'Jupiter' WHEN 'siblings' THEN 'Mars'
          WHEN 'mother' THEN 'Moon' WHEN 'children' THEN 'Jupiter' WHEN 'enemies' THEN 'Saturn'
          WHEN 'spouse' THEN 'Venus' WHEN 'longevity' THEN 'Saturn' WHEN 'luck' THEN 'Jupiter'
          WHEN 'career' THEN 'Saturn' WHEN 'gains' THEN 'Jupiter' WHEN 'losses' THEN 'Saturn'
          WHEN 'dharma' THEN 'Jupiter' WHEN 'artha' THEN 'Mercury' WHEN 'kama' THEN 'Venus'
          WHEN 'moksha' THEN 'Saturn' WHEN 'body' THEN 'Sun' WHEN 'courage' THEN 'Mars'
          WHEN 'intelligence' THEN 'Mercury' WHEN 'happiness' THEN 'Moon' WHEN 'education' THEN 'Mercury'
          WHEN 'travel' THEN 'Saturn' WHEN 'lineage' THEN 'Jupiter' WHEN 'spiritual_merit' THEN 'Sun'
          WHEN 'obstacles' THEN 'Saturn' WHEN 'foreign_travel' THEN 'Rahu' WHEN 'inner_strength' THEN 'Mars'
          WHEN 'creativity' THEN 'Venus' WHEN 'authority' THEN 'Sun' WHEN 'liberation' THEN 'Saturn'
          ELSE 'Jupiter' END)
  )
  -- (c9) composite_strength domain: must be one of the seven achievable values given the
  -- formula's four dignity tiers x three house tiers. 0/450 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karakatva_strength_per_significance' AND fact_key = 'composite_strength'
      AND fact_value_num NOT IN (0.375, 0.5, 0.625, 0.75, 0.8125, 0.9375, 1.0)
  )
  -- (d9) composite_strength full re-derivation: must equal round((karaka_strength +
  -- house_strength) / 2.0, 4), re-derived directly from the SAME significance's own natural
  -- karaka's graha_position.sign (via the classical dignity tables) and graha_position.house_d1
  -- -- a genuine two-source cross-field re-derivation, not a bare restatement. 0/450 violations
  -- live (confirmed non-vacuous: 450/450 rows join-matched).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL (
      SELECT (CASE a.fact_subject
          WHEN 'self' THEN 'SUN' WHEN 'wealth' THEN 'JUP' WHEN 'siblings' THEN 'MAR'
          WHEN 'mother' THEN 'MOON' WHEN 'children' THEN 'JUP' WHEN 'enemies' THEN 'SAT'
          WHEN 'spouse' THEN 'VEN' WHEN 'longevity' THEN 'SAT' WHEN 'luck' THEN 'JUP'
          WHEN 'career' THEN 'SAT' WHEN 'gains' THEN 'JUP' WHEN 'losses' THEN 'SAT'
          WHEN 'dharma' THEN 'JUP' WHEN 'artha' THEN 'MER' WHEN 'kama' THEN 'VEN'
          WHEN 'moksha' THEN 'SAT' WHEN 'body' THEN 'SUN' WHEN 'courage' THEN 'MAR'
          WHEN 'intelligence' THEN 'MER' WHEN 'happiness' THEN 'MOON' WHEN 'education' THEN 'MER'
          WHEN 'travel' THEN 'SAT' WHEN 'lineage' THEN 'JUP' WHEN 'spiritual_merit' THEN 'SUN'
          WHEN 'obstacles' THEN 'SAT' WHEN 'foreign_travel' THEN 'RAH_MEAN' WHEN 'inner_strength' THEN 'MAR'
          WHEN 'creativity' THEN 'VEN' WHEN 'authority' THEN 'SUN' WHEN 'liberation' THEN 'SAT'
          ELSE 'JUP' END) AS karaka_subj
    ) k
    JOIN chart_facts p_sign ON p_sign.chart_id = a.chart_id AND p_sign.ayanamsha_id = a.ayanamsha_id
      AND p_sign.fact_category = 'graha_position' AND p_sign.fact_subject = k.karaka_subj
      AND p_sign.fact_key = 'sign'
    JOIN chart_facts p_house ON p_house.chart_id = a.chart_id AND p_house.ayanamsha_id = a.ayanamsha_id
      AND p_house.fact_category = 'graha_position' AND p_house.fact_subject = k.karaka_subj
      AND p_house.fact_key = 'house_d1'
    WHERE a.fact_category = 'karakatva_strength_per_significance' AND a.fact_key = 'composite_strength'
      AND a.fact_value_num <> round((
        (CASE
          WHEN k.karaka_subj = 'SUN' AND p_sign.fact_value_text = 'Aries' THEN 1.0
          WHEN k.karaka_subj = 'SUN' AND p_sign.fact_value_text = 'Libra' THEN 0.25
          WHEN k.karaka_subj = 'SUN' AND p_sign.fact_value_text = 'Leo' THEN 0.875
          WHEN k.karaka_subj = 'MOON' AND p_sign.fact_value_text = 'Taurus' THEN 1.0
          WHEN k.karaka_subj = 'MOON' AND p_sign.fact_value_text = 'Scorpio' THEN 0.25
          WHEN k.karaka_subj = 'MOON' AND p_sign.fact_value_text = 'Cancer' THEN 0.875
          WHEN k.karaka_subj = 'MAR' AND p_sign.fact_value_text = 'Capricorn' THEN 1.0
          WHEN k.karaka_subj = 'MAR' AND p_sign.fact_value_text = 'Cancer' THEN 0.25
          WHEN k.karaka_subj = 'MAR' AND p_sign.fact_value_text IN ('Aries', 'Scorpio') THEN 0.875
          WHEN k.karaka_subj = 'MER' AND p_sign.fact_value_text = 'Virgo' THEN 1.0
          WHEN k.karaka_subj = 'MER' AND p_sign.fact_value_text = 'Pisces' THEN 0.25
          WHEN k.karaka_subj = 'MER' AND p_sign.fact_value_text IN ('Gemini', 'Virgo') THEN 0.875
          WHEN k.karaka_subj = 'JUP' AND p_sign.fact_value_text = 'Cancer' THEN 1.0
          WHEN k.karaka_subj = 'JUP' AND p_sign.fact_value_text = 'Capricorn' THEN 0.25
          WHEN k.karaka_subj = 'JUP' AND p_sign.fact_value_text IN ('Sagittarius', 'Pisces') THEN 0.875
          WHEN k.karaka_subj = 'VEN' AND p_sign.fact_value_text = 'Pisces' THEN 1.0
          WHEN k.karaka_subj = 'VEN' AND p_sign.fact_value_text = 'Virgo' THEN 0.25
          WHEN k.karaka_subj = 'VEN' AND p_sign.fact_value_text IN ('Taurus', 'Libra') THEN 0.875
          WHEN k.karaka_subj = 'SAT' AND p_sign.fact_value_text = 'Libra' THEN 1.0
          WHEN k.karaka_subj = 'SAT' AND p_sign.fact_value_text = 'Aries' THEN 0.25
          WHEN k.karaka_subj = 'SAT' AND p_sign.fact_value_text IN ('Capricorn', 'Aquarius') THEN 0.875
          ELSE 0.5
        END)
        +
        (CASE
          WHEN p_house.fact_value_num::int IN (1, 4, 7, 10) THEN 1.0
          WHEN p_house.fact_value_num::int IN (5, 9) THEN 0.75
          ELSE 0.5
        END)
      ) / 2.0, 4)
  )
  -- (a10) aspect_received_by_special_point.fact_value_num domain: must equal 1.0 -- the
  -- classical Parashari scheme has no fractional aspects. 0/1296 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_received_by_special_point' AND fact_value_num <> 1.0
  )
  -- (b10) fact_value_num must equal value_jsonb.strength -- the same strength value stored
  -- twice. 0/1296 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_received_by_special_point'
      AND fact_value_num <> (fact_value_jsonb->>'strength')::numeric
  )
  -- (c10) target_house full re-derivation: value_jsonb.target_house must equal
  -- ((graha_house - 1 + aspect_offset - 1) % 12) + 1, re-derived purely from the row's own
  -- stored graha_house/aspect_offset fields. 0/1296 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_received_by_special_point'
      AND (fact_value_jsonb->>'target_house')::int <>
          (((fact_value_jsonb->>'graha_house')::int - 1 + (fact_value_jsonb->>'aspect_offset')::int - 1) % 12) + 1
  )
  -- (d10) (aspecting_graha, aspect_offset) classical validity: must be a legitimate Parashari
  -- aspect pair per the hardcoded classical offset table (Mars 4/7/8; Jupiter/Rahu/Ketu 5/7/9;
  -- Saturn 3/7/10; all others only the universal 7th). 0/1296 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_received_by_special_point'
      AND NOT (
        (fact_value_jsonb->>'aspect_offset')::int = 7
        OR (fact_value_jsonb->>'aspecting_graha' = 'Mars' AND (fact_value_jsonb->>'aspect_offset')::int IN (4, 7, 8))
        OR (fact_value_jsonb->>'aspecting_graha' IN ('Jupiter', 'Rahu', 'Ketu') AND (fact_value_jsonb->>'aspect_offset')::int IN (5, 7, 9))
        OR (fact_value_jsonb->>'aspecting_graha' = 'Saturn' AND (fact_value_jsonb->>'aspect_offset')::int IN (3, 7, 10))
      )
  )
  -- (e10) fact_key format self-consistency: must equal 'aspected_by_' || the PLANET_TO_SUBJECT
  -- mapping of value_jsonb.aspecting_graha -- the writer's own f-string key construction,
  -- re-derived from the row's own stored aspecting_graha rather than restated. 0/1296
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_received_by_special_point'
      AND fact_key <> 'aspected_by_' || (CASE fact_value_jsonb->>'aspecting_graha'
          WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
          WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
          WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
          ELSE upper(fact_value_jsonb->>'aspecting_graha') END)
  )
  -- (f10) special_point self-consistency: value_jsonb.special_point must equal fact_subject --
  -- the same special-point name stored twice. 0/1296 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_received_by_special_point'
      AND fact_value_jsonb->>'special_point' <> fact_subject
  )
  -- (aa4) aspect_jaimini.fact_value_num domain: must equal 1.0 -- only true aspects are ever
  -- appended (the writer's own `if has_aspect:` guard); no row is ever emitted with a lesser
  -- strength. 0/1620 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_jaimini' AND fact_value_num <> 1.0
  )
  -- (bb4) no self-aspect: fact_key must never equal 'on_' || fact_subject -- the writer's own
  -- `if s1_idx == s2_idx: continue` guard, re-derived as a data check on what actually got
  -- stored. 0/1620 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_jaimini' AND fact_key = 'on_' || fact_subject
  )
  -- (cc4) adjacency exclusion, full classical re-derivation: for every stored (s1, s2) pair, the
  -- cyclic zodiacal distance between s1 and s2 -- re-derived purely from the 12 canonical sign
  -- names' fixed order (Aries=0 .. Pisces=11), not restated -- must be >= 2. Re-derives the
  -- writer's own `offset not in [1, 11]` exclusion directly. 0/1620 violations live.
  AND NOT EXISTS (
    SELECT 1
    FROM chart_facts cf
    JOIN (VALUES ('Aries',0),('Taurus',1),('Gemini',2),('Cancer',3),('Leo',4),('Virgo',5),('Libra',6),('Scorpio',7),('Sagittarius',8),('Capricorn',9),('Aquarius',10),('Pisces',11)) AS z1(sign1, idx1) ON z1.sign1 = cf.fact_subject
    JOIN (VALUES ('Aries',0),('Taurus',1),('Gemini',2),('Cancer',3),('Leo',4),('Virgo',5),('Libra',6),('Scorpio',7),('Sagittarius',8),('Capricorn',9),('Aquarius',10),('Pisces',11)) AS z2(sign2, idx2) ON 'on_' || z2.sign2 = cf.fact_key
    WHERE cf.fact_category = 'aspect_jaimini'
      AND LEAST(MOD(z2.idx2 - z1.idx1 + 12, 12), MOD(z1.idx1 - z2.idx2 + 12, 12)) < 2
  )
  -- (dd4) completeness: for every (chart, ayanamsha, build) combination and every (s1, s2) pair
  -- whose cyclic zodiacal distance is >= 2, a row MUST exist -- the converse of (cc4), confirming
  -- the writer never silently drops a legitimate pair. 0 missing pairs across all 15 combinations
  -- x 108 expected pairs = 1620 checked.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT DISTINCT chart_id, ayanamsha_id, build_id FROM chart_facts
      WHERE fact_category = 'aspect_jaimini'
    ) combos
    CROSS JOIN (VALUES ('Aries',0),('Taurus',1),('Gemini',2),('Cancer',3),('Leo',4),('Virgo',5),('Libra',6),('Scorpio',7),('Sagittarius',8),('Capricorn',9),('Aquarius',10),('Pisces',11)) AS z1(sign1, idx1)
    CROSS JOIN (VALUES ('Aries',0),('Taurus',1),('Gemini',2),('Cancer',3),('Leo',4),('Virgo',5),('Libra',6),('Scorpio',7),('Sagittarius',8),('Capricorn',9),('Aquarius',10),('Pisces',11)) AS z2(sign2, idx2)
    WHERE LEAST(MOD(z2.idx2 - z1.idx1 + 12, 12), MOD(z1.idx1 - z2.idx2 + 12, 12)) >= 2
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts cf
        WHERE cf.chart_id = combos.chart_id AND cf.ayanamsha_id = combos.ayanamsha_id
          AND cf.build_id = combos.build_id
          AND cf.fact_category = 'aspect_jaimini'
          AND cf.fact_subject = z1.sign1 AND cf.fact_key = 'on_' || z2.sign2
      )
  )
  -- (ee4) exact count invariant: each (chart, ayanamsha, build) combination must hold exactly 108
  -- rows (12 signs x 9 valid targets) -- a coarser but independent cross-check of (dd4)'s
  -- per-pair completeness. 0/15 combinations violate; 1620 total rows confirmed.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, ayanamsha_id, build_id, count(*) AS c FROM chart_facts
      WHERE fact_category = 'aspect_jaimini'
      GROUP BY chart_id, ayanamsha_id, build_id
    ) x WHERE x.c <> 108
  )
  -- (ff4) symmetric mutual invariant: if (s1, on_s2) is stored, (s2, on_s1) must also be stored
  -- for the SAME (chart, ayanamsha, build) -- re-derives the provable symmetry of the underlying
  -- rule (offset(s2,s1) = 12 - offset(s1,s2), and {1,11} is closed under that map) as a genuine
  -- row-to-row cross-check, independent of the classical zodiacal-order re-derivation (cc4)/(dd4)
  -- already establish. 0/1620 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts cf1
    WHERE cf1.fact_category = 'aspect_jaimini'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts cf2
        WHERE cf2.chart_id = cf1.chart_id AND cf2.ayanamsha_id = cf1.ayanamsha_id
          AND cf2.build_id = cf1.build_id
          AND cf2.fact_category = 'aspect_jaimini'
          AND cf2.fact_subject = substring(cf1.fact_key from 4)
          AND cf2.fact_key = 'on_' || cf1.fact_subject
      )
  )
  -- (a11) conjunction_per_varga.unit correlation: must equal 'deg' iff varga='D1', 'same_sign'
  -- iff varga<>'D1' -- the writer's own `unit="deg" if varga == "D1" else "same_sign"` ternary,
  -- re-derived as a data check on what actually got stored. 0/1719 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'conjunction_per_varga'
      AND (
        (fact_value_jsonb->>'varga' = 'D1' AND unit <> 'deg')
        OR (fact_value_jsonb->>'varga' <> 'D1' AND unit <> 'same_sign')
      )
  )
  -- (b11) value_num domain: for varga='D1', within [0, 10.0] (the writer's own `if orb > 10.0:
  -- continue` filter); for varga<>'D1', must equal exactly 0.0 (the writer's own hardcoded
  -- same-sign branch value). 0/1719 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'conjunction_per_varga'
      AND (
        (fact_value_jsonb->>'varga' = 'D1' AND (fact_value_num < 0 OR fact_value_num > 10.0))
        OR (fact_value_jsonb->>'varga' <> 'D1' AND fact_value_num <> 0.0)
      )
  )
  -- (c11) same_sign domain for non-D1: must be true for every varga<>'D1' row -- the writer's
  -- own `if sign1 != sign2: continue` guard. Deliberately excludes D1, where same_sign is not
  -- gating (5/30 D1 rows are genuinely same_sign=false -- a real classical possibility, not a
  -- defect). 0/1689 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'conjunction_per_varga' AND fact_value_jsonb->>'varga' <> 'D1'
      AND (fact_value_jsonb->>'same_sign')::boolean <> true
  )
  -- (d11) no self-pair: the two graha tokens parsed from fact_subject (after stripping the
  -- "{varga}_" prefix via the row's own stored value_jsonb.varga, then applying the same
  -- RAH_MEAN/KET_MEAN-aware split already established by migration 783's conjuncts (x)/(y)) must
  -- never be equal -- the writer's own `for g2 in ALL_GRAHAS[i+1:]` loop guarantees this.
  -- 0/1719 violations live.
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject,
        fact_value_jsonb->>'varga' AS varga,
        substring(fact_subject from length(fact_value_jsonb->>'varga') + 2) AS remainder
      FROM chart_facts WHERE fact_category = 'conjunction_per_varga'
    ),
    parsed2 AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, varga, remainder,
        CASE WHEN remainder LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
             WHEN remainder LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
             ELSE split_part(remainder, '_', 1) END AS s1_token
      FROM parsed
    ),
    parsed3 AS (
      SELECT *, substring(remainder from length(s1_token)+2) AS s2_token FROM parsed2
    )
    SELECT 1 FROM parsed3 WHERE s2_token = s1_token
  )
  -- (e11) no reversed-duplicate pair: for a stored "{VARGA}_{S1}_{S2}" row, "{VARGA}_{S2}_{S1}"
  -- must never also be stored for the same (chart, ayanamsha, build) -- re-derives the writer's
  -- own unordered-pair-emitted-once loop guarantee, the same invariant migration 783's conjunct
  -- (x) already established for conjunction_within_orb, now re-verified per-varga. 0/1719
  -- violations live.
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject,
        fact_value_jsonb->>'varga' AS varga,
        substring(fact_subject from length(fact_value_jsonb->>'varga') + 2) AS remainder
      FROM chart_facts WHERE fact_category = 'conjunction_per_varga'
    ),
    parsed2 AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, varga, remainder,
        CASE WHEN remainder LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
             WHEN remainder LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
             ELSE split_part(remainder, '_', 1) END AS s1_token
      FROM parsed
    ),
    parsed3 AS (
      SELECT *, substring(remainder from length(s1_token)+2) AS s2_token FROM parsed2
    )
    SELECT 1 FROM parsed3 a
    WHERE EXISTS (
      SELECT 1 FROM chart_facts b
      WHERE b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id AND b.build_id = a.build_id
        AND b.fact_category = 'conjunction_per_varga'
        AND b.fact_subject = a.varga || '_' || a.s2_token || '_' || a.s1_token
    )
  )
  -- (f11) pair ordering invariant: s1's index in the writer's own ALL_GRAHAS ordering
  -- (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) must strictly precede s2's index --
  -- the same invariant as migration 783's conjunct (y), re-verified per-varga. 0/1719 violations
  -- live.
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject,
        fact_value_jsonb->>'varga' AS varga,
        substring(fact_subject from length(fact_value_jsonb->>'varga') + 2) AS remainder
      FROM chart_facts WHERE fact_category = 'conjunction_per_varga'
    ),
    parsed2 AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, varga, remainder,
        CASE WHEN remainder LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
             WHEN remainder LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
             ELSE split_part(remainder, '_', 1) END AS s1_token
      FROM parsed
    ),
    parsed3 AS (
      SELECT *, substring(remainder from length(s1_token)+2) AS s2_token FROM parsed2
    )
    SELECT 1 FROM parsed3
    WHERE COALESCE(
        array_position(ARRAY['SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN'], s1_token), 999
      ) >= COALESCE(
        array_position(ARRAY['SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN'], s2_token), -1
      )
  )
  -- (g11) sign cross-reference, non-D1: value_jsonb.sign must equal ga_vargas' own authoritative
  -- chart_divisionals varga_position.sign for the SAME (chart, ayanamsha, varga, graha) --
  -- re-derived directly from the classical source table, catching any drift between the writer's
  -- own in-memory varga_state and the canonical chart_divisionals record. Excludes D1 per the
  -- established dual-source caveat. 0/1689 violations live (all 1689 non-D1 rows matched).
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id, cf.fact_subject,
        cf.fact_value_jsonb->>'varga' AS varga,
        cf.fact_value_jsonb->>'sign' AS jsonb_sign,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS remainder
      FROM chart_facts cf
      WHERE cf.fact_category = 'conjunction_per_varga' AND cf.fact_value_jsonb->>'varga' <> 'D1'
    ),
    parsed2 AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, varga, jsonb_sign, remainder,
        CASE WHEN remainder LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
             WHEN remainder LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
             ELSE split_part(remainder, '_', 1) END AS s1_token
      FROM parsed
    )
    SELECT 1
    FROM parsed2 p
    JOIN chart_divisionals cd
      ON cd.chart_id = p.chart_id AND cd.ayanamsha_id = p.ayanamsha_id
     AND cd.fact_category = 'varga_position' AND cd.fact_key = 'degree_in_sign'
     AND cd.varga = p.varga
     AND cd.graha = (CASE p.s1_token
         WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
         WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
         WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
         ELSE NULL END)
    WHERE cd.sign <> p.jsonb_sign
  )
  -- (h11) house cross-reference, non-D1: value_jsonb.house must equal ga_vargas' own
  -- authoritative chart_divisionals varga_position.house_from_varga_lagna for the SAME (chart,
  -- ayanamsha, varga, graha) -- re-derived directly rather than restated. Excludes D1 per the
  -- same dual-source caveat. 0/1689 violations live (all 1689 non-D1 rows matched).
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id, cf.fact_subject,
        cf.fact_value_jsonb->>'varga' AS varga,
        (cf.fact_value_jsonb->>'house')::int AS jsonb_house,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS remainder
      FROM chart_facts cf
      WHERE cf.fact_category = 'conjunction_per_varga' AND cf.fact_value_jsonb->>'varga' <> 'D1'
    ),
    parsed2 AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, varga, jsonb_house, remainder,
        CASE WHEN remainder LIKE 'RAH\_MEAN\_%' ESCAPE '\' THEN 'RAH_MEAN'
             WHEN remainder LIKE 'KET\_MEAN\_%' ESCAPE '\' THEN 'KET_MEAN'
             ELSE split_part(remainder, '_', 1) END AS s1_token
      FROM parsed
    )
    SELECT 1
    FROM parsed2 p
    JOIN chart_divisionals cd
      ON cd.chart_id = p.chart_id AND cd.ayanamsha_id = p.ayanamsha_id
     AND cd.fact_category = 'varga_position' AND cd.fact_key = 'house_from_varga_lagna'
     AND cd.varga = p.varga
     AND cd.graha = (CASE p.s1_token
         WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
         WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
         WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
         ELSE NULL END)
    WHERE cd.fact_value_num::int <> p.jsonb_house
  )
  -- (a12) lord_aspects_lord_per_varga.fact_value_num domain: must equal 1.0 -- the classical
  -- Parashari scheme has no fractional aspects. 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga' AND fact_value_num <> 1.0
  )
  -- (b12) fact_value_num must equal value_jsonb.strength -- the same strength value stored
  -- twice. 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND fact_value_num <> (fact_value_jsonb->>'strength')::numeric
  )
  -- (c12) no self-aspect: lord_a must never equal lord_b -- the writer's own `if lord_b ==
  -- lord_a: continue` guard, re-derived as a data check on what actually got stored. 0/2748
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND fact_value_jsonb->>'lord_a' = fact_value_jsonb->>'lord_b'
  )
  -- (d12) (lord_a, aspect_offset) classical validity: must be a legitimate Parashari aspect pair
  -- per the hardcoded classical offset table (Mars 4/7/8; Jupiter 5/7/9; Saturn 3/7/10; all
  -- others only the universal 7th) -- narrowed to the 7 classical grahas that can ever be a
  -- SIGN_LORDS value. 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND NOT (
        (fact_value_jsonb->>'aspect_offset')::int = 7
        OR (fact_value_jsonb->>'lord_a' = 'Mars' AND (fact_value_jsonb->>'aspect_offset')::int IN (4, 7, 8))
        OR (fact_value_jsonb->>'lord_a' IN ('Jupiter', 'Rahu', 'Ketu') AND (fact_value_jsonb->>'aspect_offset')::int IN (5, 7, 9))
        OR (fact_value_jsonb->>'lord_a' = 'Saturn' AND (fact_value_jsonb->>'aspect_offset')::int IN (3, 7, 10))
      )
  )
  -- (e12) lord_a/lord_b domain: both must be one of the seven classical grahas
  -- (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn) -- SIGN_LORDS never maps to a node, so neither
  -- lord_a nor lord_b can ever legitimately be Rahu or Ketu. 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND (
        fact_value_jsonb->>'lord_a' NOT IN ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
        OR fact_value_jsonb->>'lord_b' NOT IN ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
      )
  )
  -- (f12) target_house full re-derivation: lord_b_house must equal ((lord_a_house - 1 +
  -- aspect_offset - 1) % 12) + 1, re-derived purely from the row's own stored
  -- lord_a_house/aspect_offset fields. 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND (fact_value_jsonb->>'lord_b_house')::int <>
          (((fact_value_jsonb->>'lord_a_house')::int - 1 + (fact_value_jsonb->>'aspect_offset')::int - 1) % 12) + 1
  )
  -- (g12) fact_key format self-consistency: must equal 'aspects_' || the PLANET_TO_SUBJECT
  -- mapping of value_jsonb.lord_b -- the writer's own f-string key construction, re-derived from
  -- the row's own stored lord_b rather than restated. 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND fact_key <> 'aspects_' || (CASE fact_value_jsonb->>'lord_b'
          WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
          WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
          WHEN 'Saturn' THEN 'SAT' ELSE upper(fact_value_jsonb->>'lord_b') END)
  )
  -- (h12) fact_subject format self-consistency: must equal value_jsonb.varga || '_' || the
  -- PLANET_TO_SUBJECT mapping of value_jsonb.lord_a -- the writer's own f-string subject
  -- construction, re-derived from the row's own stored varga/lord_a rather than restated.
  -- 0/2748 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_aspects_lord_per_varga'
      AND fact_subject <> (fact_value_jsonb->>'varga') || '_' || (CASE fact_value_jsonb->>'lord_a'
          WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
          WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
          WHEN 'Saturn' THEN 'SAT' ELSE upper(fact_value_jsonb->>'lord_a') END)
  )
  -- (a13) dispositor_chain_per_varga.fact_value_text must equal the chain array joined with
  -- '→' -- the same chain stored twice (human-readable string + structured array). 0/3915
  -- violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts cf
    WHERE cf.fact_category = 'dispositor_chain_per_varga'
      AND cf.fact_value_text <> (
        SELECT string_agg(elem, '→') FROM jsonb_array_elements_text(cf.fact_value_jsonb->'chain') elem
      )
  )
  -- (b13) chain_length must equal the actual jsonb array length of "chain" -- the same count
  -- stored twice. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_chain_per_varga'
      AND (fact_value_jsonb->>'chain_length')::int <> jsonb_array_length(fact_value_jsonb->'chain')
  )
  -- (c13) chain[0] must equal the row's own graha (the writer's own `chain = [g_name]`
  -- initialization), re-derived from fact_subject rather than restated. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts cf
    WHERE cf.fact_category = 'dispositor_chain_per_varga'
      AND (cf.fact_value_jsonb->'chain'->>0) <> (
        CASE substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2)
          WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
          WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
          WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
          ELSE NULL END
      )
  )
  -- (d13) no duplicate elements in the chain array -- the writer's own `if lord in visited:
  -- break` guard (checked BEFORE appending) means a graha can never appear twice in a stored
  -- chain. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts cf
    WHERE cf.fact_category = 'dispositor_chain_per_varga'
      AND (
        SELECT count(DISTINCT elem) FROM jsonb_array_elements_text(cf.fact_value_jsonb->'chain') elem
      ) <> jsonb_array_length(cf.fact_value_jsonb->'chain')
  )
  -- (e13) chain_length domain: must be within [1, 9] -- the writer's own loop bound (1 initial
  -- member + at most 8 `for _ in range(8)` iterations). 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_chain_per_varga'
      AND ((fact_value_jsonb->>'chain_length')::int < 1 OR (fact_value_jsonb->>'chain_length')::int > 9)
  )
  -- (f13) start_sign cross-reference: must equal chain[0]'s own sign-in-this-varga, sourced from
  -- the sibling graha_dignity_per_varga category's own stored sign field for the SAME (chart,
  -- ayanamsha, build, varga, graha). 0/3915 violations live (all 3915 rows matched).
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        cf.fact_value_jsonb->>'start_sign' AS start_sign,
        cf.fact_value_jsonb->'chain'->>0 AS chain0
      FROM chart_facts cf
      WHERE cf.fact_category = 'dispositor_chain_per_varga'
    )
    SELECT 1
    FROM parsed p
    JOIN chart_facts gd
      ON gd.chart_id = p.chart_id AND gd.ayanamsha_id = p.ayanamsha_id AND gd.build_id = p.build_id
     AND gd.fact_category = 'graha_dignity_per_varga'
     AND gd.fact_value_jsonb->>'varga' = p.varga
     AND gd.fact_subject = p.varga || '_' || (CASE p.chain0
         WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
         WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
         WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
         ELSE NULL END)
    WHERE (gd.fact_value_jsonb->>'sign') <> p.start_sign
  )
  -- (g13) full classical chain-step re-derivation: for every consecutive pair in the stored
  -- chain, the next graha must equal SIGN_LORDS[the previous graha's sign-in-this-varga] --
  -- SIGN_LORDS is the same 12-sign classical table already used by migration 793's conjunct (g)
  -- and migration 786's conjunct (ll) -- where the previous graha's sign is sourced from the
  -- sibling graha_dignity_per_varga category, walked step-by-step via generate_series over the
  -- JSON array. 0/8179 pairs checked (sum of chain_length-1 across all 3915 rows), 0 violations
  -- live, all 8179 steps matched.
  AND NOT EXISTS (
    WITH steps AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        cf.fact_value_jsonb->'chain' AS chain,
        i AS idx
      FROM chart_facts cf
      CROSS JOIN LATERAL generate_series(0, jsonb_array_length(cf.fact_value_jsonb->'chain') - 2) AS i
      WHERE cf.fact_category = 'dispositor_chain_per_varga'
    )
    SELECT 1
    FROM steps s
    JOIN chart_facts gd
      ON gd.chart_id = s.chart_id AND gd.ayanamsha_id = s.ayanamsha_id AND gd.build_id = s.build_id
     AND gd.fact_category = 'graha_dignity_per_varga'
     AND gd.fact_value_jsonb->>'varga' = s.varga
     AND gd.fact_subject = s.varga || '_' || (CASE (s.chain->>s.idx)
         WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
         WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
         WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
         ELSE NULL END)
    WHERE (s.chain->>(s.idx+1)) <> (CASE (gd.fact_value_jsonb->>'sign')
        WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
        WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
        WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
        WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
        ELSE NULL END)
  )
  -- (a14) graha_centrality.fact_value_num must equal value_jsonb.degree_centrality -- the same
  -- count stored twice. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_centrality'
      AND fact_value_num <> (fact_value_jsonb->>'degree_centrality')::numeric
  )
  -- (b14) degree_centrality must equal the actual jsonb array length of "connected_to" -- the
  -- same count stored twice a different way. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_centrality'
      AND (fact_value_jsonb->>'degree_centrality')::int <> jsonb_array_length(fact_value_jsonb->'connected_to')
  )
  -- (c14) no self in connected_to: a graha must never list itself -- the writer's own `for g2 in
  -- present[i+1:]` loop guarantees g1 != g2 always. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts cf
    WHERE cf.fact_category = 'graha_centrality'
      AND (
        SELECT count(*) FROM jsonb_array_elements_text(cf.fact_value_jsonb->'connected_to') elem
        WHERE elem = (
          CASE substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2)
            WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
            WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
            WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
            ELSE NULL END
        )
      ) > 0
  )
  -- (d14) symmetric mutual invariant: if graha A's connected_to includes B, B's connected_to
  -- (same chart, ayanamsha, build, varga) must include A -- the writer's own undirected
  -- adjacency construction, re-derived as a genuine cross-row check. 0/11500 edge-endpoints
  -- checked, 0 violations live.
  AND NOT EXISTS (
    WITH pairs AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS g1_token,
        elem AS g2_name
      FROM chart_facts cf
      CROSS JOIN LATERAL jsonb_array_elements_text(cf.fact_value_jsonb->'connected_to') elem
      WHERE cf.fact_category = 'graha_centrality'
    ),
    g1_named AS (
      SELECT *, (CASE g1_token
          WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
          WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
          WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
          ELSE NULL END) AS g1_name,
        (CASE g2_name
          WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
          WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
          WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
          ELSE NULL END) AS g2_token
      FROM pairs
    )
    SELECT 1 FROM g1_named p
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_facts cf2
      WHERE cf2.chart_id = p.chart_id AND cf2.ayanamsha_id = p.ayanamsha_id AND cf2.build_id = p.build_id
        AND cf2.fact_category = 'graha_centrality'
        AND cf2.fact_subject = p.varga || '_' || p.g2_token
        AND cf2.fact_value_jsonb->'connected_to' @> to_jsonb(p.g1_name::text)
    )
  )
  -- (e14) degree_centrality domain: must be within [0, 8] -- ALL_GRAHAS has 9 members, so the
  -- maximum possible degree (all others connected) is 8. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_centrality'
      AND ((fact_value_jsonb->>'degree_centrality')::int < 0 OR (fact_value_jsonb->>'degree_centrality')::int > 8)
  )
  -- (f14) full classical edge re-derivation: for every stored (g1, g2) edge, the connection must
  -- be justified by g1 aspects g2's house, OR g2 aspects g1's house (both via the classical
  -- Parashari offset table, safe-wraparound arithmetic to avoid SQL's sign-following % operator),
  -- OR they share the same sign -- houses/signs sourced from the sibling graha_dignity_per_varga
  -- category for BOTH grahas. 0/11500 edges checked, 0 violations live, all 11500 matched.
  AND NOT EXISTS (
    WITH pairs AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS g1_token,
        elem AS g2_name
      FROM chart_facts cf
      CROSS JOIN LATERAL jsonb_array_elements_text(cf.fact_value_jsonb->'connected_to') elem
      WHERE cf.fact_category = 'graha_centrality'
    ),
    named AS (
      SELECT *, (CASE g1_token
          WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
          WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
          WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
          ELSE NULL END) AS g1_name,
        (CASE g2_name
          WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
          WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
          WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
          ELSE NULL END) AS g2_token
      FROM pairs
    ),
    joined AS (
      SELECT n.*, gd1.fact_value_jsonb->>'house' AS h1, gd1.fact_value_jsonb->>'sign' AS s1,
        gd2.fact_value_jsonb->>'house' AS h2, gd2.fact_value_jsonb->>'sign' AS s2
      FROM named n
      LEFT JOIN chart_facts gd1
        ON gd1.chart_id = n.chart_id AND gd1.ayanamsha_id = n.ayanamsha_id AND gd1.build_id = n.build_id
       AND gd1.fact_category = 'graha_dignity_per_varga' AND gd1.fact_value_jsonb->>'varga' = n.varga
       AND gd1.fact_subject = n.varga || '_' || n.g1_token
      LEFT JOIN chart_facts gd2
        ON gd2.chart_id = n.chart_id AND gd2.ayanamsha_id = n.ayanamsha_id AND gd2.build_id = n.build_id
       AND gd2.fact_category = 'graha_dignity_per_varga' AND gd2.fact_value_jsonb->>'varga' = n.varga
       AND gd2.fact_subject = n.varga || '_' || n.g2_token
    )
    SELECT 1
    FROM joined j
    LEFT JOIN LATERAL (
      SELECT 1.0 AS strength WHERE
        (MOD(j.h2::int - j.h1::int + 120, 12) + 1) IN (
          SELECT unnest(CASE j.g1_name
            WHEN 'Mars' THEN ARRAY[4,7,8]
            WHEN 'Jupiter' THEN ARRAY[5,7,9]
            WHEN 'Rahu' THEN ARRAY[5,7,9]
            WHEN 'Ketu' THEN ARRAY[5,7,9]
            WHEN 'Saturn' THEN ARRAY[3,7,10]
            ELSE ARRAY[7] END)
        )
    ) get_asp ON true
    LEFT JOIN LATERAL (
      SELECT 1.0 AS strength WHERE
        (MOD(j.h1::int - j.h2::int + 120, 12) + 1) IN (
          SELECT unnest(CASE j.g2_name
            WHEN 'Mars' THEN ARRAY[4,7,8]
            WHEN 'Jupiter' THEN ARRAY[5,7,9]
            WHEN 'Rahu' THEN ARRAY[5,7,9]
            WHEN 'Ketu' THEN ARRAY[5,7,9]
            WHEN 'Saturn' THEN ARRAY[3,7,10]
            ELSE ARRAY[7] END)
        )
    ) get_asp2 ON true
    WHERE j.h1 IS NOT NULL AND j.h2 IS NOT NULL
      AND NOT (
        (get_asp.strength IS NOT NULL) OR (get_asp2.strength IS NOT NULL) OR (j.s1 = j.s2)
      )
  )
  -- (a15) chart_cluster.fact_value_num must equal value_jsonb.cluster_id -- the same id stored
  -- twice. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'chart_cluster'
      AND fact_value_num <> (fact_value_jsonb->>'cluster_id')::numeric
  )
  -- (b15) cluster_id domain: must be within [0, total_clusters - 1] -- a valid zero-based index
  -- into the writer's own cluster_counter. 0/3915 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'chart_cluster'
      AND (
        (fact_value_jsonb->>'cluster_id')::int < 0
        OR (fact_value_jsonb->>'cluster_id')::int >= (fact_value_jsonb->>'total_clusters')::int
      )
  )
  -- (c15) total_clusters consistency: every row within the SAME (chart, ayanamsha, build, varga)
  -- group must report the identical total_clusters value -- it is a chart-varga-wide constant
  -- computed once by the writer, not a per-graha value.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, ayanamsha_id, build_id, fact_value_jsonb->>'varga' AS varga,
        count(DISTINCT fact_value_jsonb->>'total_clusters') AS distinct_totals
      FROM chart_facts WHERE fact_category = 'chart_cluster'
      GROUP BY 1, 2, 3, 4
    ) x WHERE x.distinct_totals <> 1
  )
  -- (d15) total_clusters completeness: the declared total_clusters must equal the actual count
  -- of DISTINCT cluster_id values present in that (chart, ayanamsha, build, varga) group --
  -- confirms no gap or phantom count between the writer's counter and what actually got stored.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, ayanamsha_id, build_id, fact_value_jsonb->>'varga' AS varga,
        max((fact_value_jsonb->>'total_clusters')::int) AS declared,
        count(DISTINCT (fact_value_jsonb->>'cluster_id')::int) AS actual
      FROM chart_facts WHERE fact_category = 'chart_cluster'
      GROUP BY 1, 2, 3, 4
    ) x WHERE x.declared <> x.actual
  )
  -- (e15) direct-edge-implies-same-cluster: for every direct edge in the sibling
  -- graha_centrality category's own connected_to array, both endpoint grahas must share the same
  -- cluster_id in chart_cluster for the SAME (chart, ayanamsha, build, varga) -- a genuine
  -- cross-category invariant from the two categories sharing one union-find input graph.
  -- 0/11500 edge-endpoints checked, 0 violations live.
  AND NOT EXISTS (
    WITH pairs AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS g1_token,
        elem AS g2_name
      FROM chart_facts cf
      CROSS JOIN LATERAL jsonb_array_elements_text(cf.fact_value_jsonb->'connected_to') elem
      WHERE cf.fact_category = 'graha_centrality'
    ),
    named AS (
      SELECT *,
        (CASE g2_name
          WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
          WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
          WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN'
          ELSE NULL END) AS g2_token
      FROM pairs
    )
    SELECT 1
    FROM named p
    JOIN chart_facts cc1
      ON cc1.chart_id = p.chart_id AND cc1.ayanamsha_id = p.ayanamsha_id AND cc1.build_id = p.build_id
     AND cc1.fact_category = 'chart_cluster' AND cc1.fact_subject = p.varga || '_' || p.g1_token
    JOIN chart_facts cc2
      ON cc2.chart_id = p.chart_id AND cc2.ayanamsha_id = p.ayanamsha_id AND cc2.build_id = p.build_id
     AND cc2.fact_category = 'chart_cluster' AND cc2.fact_subject = p.varga || '_' || p.g2_token
    WHERE (cc1.fact_value_jsonb->>'cluster_id') <> (cc2.fact_value_jsonb->>'cluster_id')
  )
  -- (f15) isolated-implies-singleton-cluster: if the sibling graha_centrality category reports
  -- degree_centrality=0 for a graha (no direct edge to anyone), no OTHER graha in the SAME
  -- (chart, ayanamsha, build, varga) group may share its cluster_id -- a zero-degree node can
  -- only ever form its own singleton connected component. 0/164 isolated grahas violate.
  AND NOT EXISTS (
    WITH isolated AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS g_token
      FROM chart_facts cf
      WHERE cf.fact_category = 'graha_centrality' AND (cf.fact_value_jsonb->>'degree_centrality')::int = 0
    )
    SELECT 1
    FROM isolated i
    WHERE EXISTS (
      SELECT 1 FROM chart_facts cc2
      WHERE cc2.chart_id = i.chart_id AND cc2.ayanamsha_id = i.ayanamsha_id AND cc2.build_id = i.build_id
        AND cc2.fact_category = 'chart_cluster'
        AND cc2.fact_value_jsonb->>'varga' = i.varga
        AND cc2.fact_subject <> i.varga || '_' || i.g_token
        AND cc2.fact_value_jsonb->>'cluster_id' = (
          SELECT cc1.fact_value_jsonb->>'cluster_id' FROM chart_facts cc1
          WHERE cc1.chart_id = i.chart_id AND cc1.ayanamsha_id = i.ayanamsha_id AND cc1.build_id = i.build_id
            AND cc1.fact_category = 'chart_cluster' AND cc1.fact_subject = i.varga || '_' || i.g_token
        )
    )
  )
  -- (a16) dispositor_tree.fact_value_text (the parent subject) must equal the classical
  -- SIGN_LORDS lookup of value_jsonb.sign, re-derived purely from the row's own stored field.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_tree' AND fact_key = 'tree_position'
      AND fact_value_text <> (CASE fact_value_jsonb->>'sign'
          WHEN 'Aries' THEN 'MAR' WHEN 'Taurus' THEN 'VEN' WHEN 'Gemini' THEN 'MER'
          WHEN 'Cancer' THEN 'MOON' WHEN 'Leo' THEN 'SUN' WHEN 'Virgo' THEN 'MER'
          WHEN 'Libra' THEN 'VEN' WHEN 'Scorpio' THEN 'MAR' WHEN 'Sagittarius' THEN 'JUP'
          WHEN 'Capricorn' THEN 'SAT' WHEN 'Aquarius' THEN 'SAT' WHEN 'Pisces' THEN 'JUP'
          ELSE NULL END)
  )
  -- (b16) fact_value_text must equal value_jsonb.parent -- the same parent stored twice.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_tree' AND fact_key = 'tree_position'
      AND fact_value_text <> (fact_value_jsonb->>'parent')
  )
  -- (c16) is_root domain: must equal (parent == the row's own graha, parsed from fact_subject) --
  -- the writer's own self-disposing-root definition, re-derived rather than restated.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_tree' AND fact_key = 'tree_position'
      AND (fact_value_jsonb->>'is_root')::boolean <> (
        (fact_value_jsonb->>'parent') = (
          CASE substring(fact_subject from length(fact_value_jsonb->>'varga') + 2)
            WHEN 'SUN' THEN 'SUN' WHEN 'MOON' THEN 'MOON' WHEN 'MAR' THEN 'MAR'
            WHEN 'MER' THEN 'MER' WHEN 'JUP' THEN 'JUP' WHEN 'VEN' THEN 'VEN'
            WHEN 'SAT' THEN 'SAT' WHEN 'RAH_MEAN' THEN 'RAH_MEAN' WHEN 'KET_MEAN' THEN 'KET_MEAN'
            ELSE NULL END
        )
      )
  )
  -- (d16) value_num domain: must be NULL iff value_jsonb.depth = -1 (a cycle member with no
  -- reachable own-sign root) -- the writer's own `float(depth) if depth >= 0 else None` branch.
  -- When not NULL, value_num must equal value_jsonb.depth exactly.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_tree' AND fact_key = 'tree_position'
      AND (
        ((fact_value_num IS NULL) <> ((fact_value_jsonb->>'depth')::int = -1))
        OR (fact_value_num IS NOT NULL AND fact_value_num <> (fact_value_jsonb->>'depth')::numeric)
      )
  )
  -- (e16) is_root implies depth=0 -- a self-disposing root is, by the writer's own BFS
  -- initialization, always depth 0.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_tree' AND fact_key = 'tree_position'
      AND (fact_value_jsonb->>'is_root')::boolean = true
      AND (fact_value_jsonb->>'depth')::int <> 0
  )
  -- (f16) mutual parent-child invariant: for every non-root graha, its declared parent's own
  -- children array must list it back -- the writer's own single children_map built in the same
  -- pass, re-derived as a cross-row check within dispositor_tree itself.
  AND NOT EXISTS (
    WITH children_of AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS g_token,
        cf.fact_value_jsonb->>'parent' AS parent_token
      FROM chart_facts cf
      WHERE cf.fact_category = 'dispositor_tree' AND cf.fact_key = 'tree_position'
        AND cf.fact_value_jsonb->>'parent' <> substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2)
    )
    SELECT 1 FROM children_of c
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_facts p
      WHERE p.chart_id = c.chart_id AND p.ayanamsha_id = c.ayanamsha_id AND p.build_id = c.build_id
        AND p.fact_category = 'dispositor_tree' AND p.fact_key = 'tree_position'
        AND p.fact_subject = c.varga || '_' || c.parent_token
        AND p.fact_value_jsonb->'children' @> to_jsonb(c.g_token::text)
    )
  )
  -- (g16) CHART summary root_count must equal the actual jsonb array length of "roots" -- the
  -- same count stored twice.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'dispositor_tree' AND fact_key = 'summary'
      AND (fact_value_jsonb->>'root_count')::int <> jsonb_array_length(fact_value_jsonb->'roots')
  )
  -- (h16) every graha named in a CHART summary's "roots" array must have is_root=true in its own
  -- per-graha row, for the SAME (chart, ayanamsha, build, varga) -- round-trip completeness in
  -- one direction.
  AND NOT EXISTS (
    WITH chart_roots AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id, cf.fact_value_jsonb->>'varga' AS varga, elem AS root_token
      FROM chart_facts cf
      CROSS JOIN LATERAL jsonb_array_elements_text(cf.fact_value_jsonb->'roots') elem
      WHERE cf.fact_category = 'dispositor_tree' AND cf.fact_key = 'summary'
    )
    SELECT 1 FROM chart_roots r
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_facts p
      WHERE p.chart_id = r.chart_id AND p.ayanamsha_id = r.ayanamsha_id AND p.build_id = r.build_id
        AND p.fact_category = 'dispositor_tree' AND p.fact_key = 'tree_position'
        AND p.fact_subject = r.varga || '_' || r.root_token
        AND (p.fact_value_jsonb->>'is_root')::boolean = true
    )
  )
  -- (i16) every per-graha row with is_root=true must be named in the CHART summary's "roots"
  -- array, for the SAME (chart, ayanamsha, build, varga) -- round-trip completeness in the other
  -- direction.
  AND NOT EXISTS (
    WITH is_roots AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        substring(cf.fact_subject from length(cf.fact_value_jsonb->>'varga') + 2) AS g_token
      FROM chart_facts cf
      WHERE cf.fact_category = 'dispositor_tree' AND cf.fact_key = 'tree_position'
        AND (cf.fact_value_jsonb->>'is_root')::boolean = true
    )
    SELECT 1 FROM is_roots ir
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_facts c
      WHERE c.chart_id = ir.chart_id AND c.ayanamsha_id = ir.ayanamsha_id AND c.build_id = ir.build_id
        AND c.fact_category = 'dispositor_tree' AND c.fact_key = 'summary'
        AND c.fact_subject = ir.varga || '_CHART'
        AND c.fact_value_jsonb->'roots' @> to_jsonb(ir.g_token::text)
    )
  )
  -- (a17) graha_in_house_composite_strength.cross_formula_divergence must equal
  -- abs(bphs_weighted - simple_multiplication) for the SAME comp_subject -- the writer's own
  -- `divergence = abs(bphs_score - simple_score)` definition, re-derived directly from the two
  -- sibling rows rather than restated.
  AND NOT EXISTS (
    WITH piv AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject,
        max(fact_value_num) FILTER (WHERE fact_key = 'bphs_weighted') AS bphs,
        max(fact_value_num) FILTER (WHERE fact_key = 'simple_multiplication') AS simple,
        max(fact_value_num) FILTER (WHERE fact_key = 'cross_formula_divergence') AS div
      FROM chart_facts
      WHERE fact_category = 'graha_in_house_composite_strength'
      GROUP BY 1, 2, 3, 4
    )
    SELECT 1 FROM piv
    WHERE bphs IS NOT NULL AND simple IS NOT NULL AND div IS NOT NULL
      AND abs(div - abs(bphs - simple)) > 0.0001
  )
  -- (b17) bphs_weighted must never exceed simple_multiplication -- a genuine algebraic
  -- certainty from the writer's own formula relationship (bphs = simple x shadbala_ratio x
  -- aspect_modifier, both factors <= 1), not a bare restatement.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject,
        max(fact_value_num) FILTER (WHERE fact_key = 'bphs_weighted') AS bphs,
        max(fact_value_num) FILTER (WHERE fact_key = 'simple_multiplication') AS simple
      FROM chart_facts
      WHERE fact_category = 'graha_in_house_composite_strength'
      GROUP BY 1, 2, 3, 4
    ) x WHERE x.bphs > x.simple + 0.0001
  )
  -- (c17) value_num domain: must never be negative -- every factor in both formulas (dignity
  -- sthana, shadbala_ratio, bhava_ratio, aspect_modifier) is non-negative by construction.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_in_house_composite_strength' AND fact_value_num < 0
  )
  -- (d17) row-count tiling per comp_subject: each (chart, ayanamsha, build, fact_subject) group
  -- must contain EXACTLY 3 rows with no floored member, OR exactly 1 floored row -- no partial
  -- state is ever legitimate, re-deriving the writer's own all-three-or-floored-alone emission
  -- structure.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, ayanamsha_id, build_id, fact_subject, count(*) AS n,
        count(*) FILTER (WHERE verification_pass_status = 'floored') AS n_floored
      FROM chart_facts
      WHERE fact_category = 'graha_in_house_composite_strength'
      GROUP BY 1, 2, 3, 4
    ) x WHERE NOT ((x.n = 3 AND x.n_floored = 0) OR (x.n = 1 AND x.n_floored = 1))
  )
  -- (e17) fact_subject format: must match "{GRAHA_TOKEN}_IN_HOUSE_{1-12}" -- the writer's own
  -- `f"{subject}_IN_{house_key}"` construction, re-derived as a domain check on what actually
  -- got stored.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_in_house_composite_strength'
      AND fact_subject !~ '^[A-Z_]+_IN_HOUSE_(1[0-2]|[1-9])$'
  )
  -- (f17) floored-row invariant: value_num must be NULL if and only if
  -- verification_pass_status='floored' -- the writer's own canonical-or-floor branch, re-derived
  -- as a data check on what actually got stored.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_in_house_composite_strength'
      AND ((fact_value_num IS NULL) <> (verification_pass_status = 'floored'))
  )
  -- (a18) lord_in_house_per_varga.lord must equal the classical SIGN_LORDS lookup of
  -- value_jsonb.sign, re-derived purely from the row's own stored sign field.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_in_house_per_varga'
      AND fact_value_jsonb->>'lord' <> (CASE fact_value_jsonb->>'sign'
          WHEN 'Aries' THEN 'Mars' WHEN 'Taurus' THEN 'Venus' WHEN 'Gemini' THEN 'Mercury'
          WHEN 'Cancer' THEN 'Moon' WHEN 'Leo' THEN 'Sun' WHEN 'Virgo' THEN 'Mercury'
          WHEN 'Libra' THEN 'Venus' WHEN 'Scorpio' THEN 'Mars' WHEN 'Sagittarius' THEN 'Jupiter'
          WHEN 'Capricorn' THEN 'Saturn' WHEN 'Aquarius' THEN 'Saturn' WHEN 'Pisces' THEN 'Jupiter'
          ELSE NULL END)
  )
  -- (b18) fact_value_text must equal the writer's own f-string reconstruction:
  -- "{lord}_in_H{lord_house_in_varga}" when lord_house_in_varga != 0, else "{lord}_unknown".
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_in_house_per_varga'
      AND fact_value_text <> (CASE WHEN (fact_value_jsonb->>'lord_house_in_varga')::int <> 0
          THEN (fact_value_jsonb->>'lord') || '_in_H' || (fact_value_jsonb->>'lord_house_in_varga')
          ELSE (fact_value_jsonb->>'lord') || '_unknown' END)
  )
  -- (c18) fact_value_num must equal value_jsonb.lord_house_in_varga -- the same placement value
  -- stored twice.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_in_house_per_varga'
      AND fact_value_num <> (fact_value_jsonb->>'lord_house_in_varga')::numeric
  )
  -- (d18) fact_subject format: must equal "{varga}_H{house}" -- the writer's own
  -- `f"{varga_prefix}H{house_num}"` construction, re-derived from the row's own stored
  -- varga/house fields.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_in_house_per_varga'
      AND fact_subject <> (fact_value_jsonb->>'varga') || '_H' || (fact_value_jsonb->>'house')
  )
  -- (e18) varga-independent sign invariant: for the SAME (chart, ayanamsha, build, house_num),
  -- value_jsonb.sign must be IDENTICAL across every varga -- house_sign(h) is computed from the
  -- D1 lagna alone and never varies by varga, a genuine structural certainty of the writer's own
  -- single house_sign() closure shared by every varga call.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, ayanamsha_id, build_id, (fact_value_jsonb->>'house')::int AS house_num,
        count(DISTINCT fact_value_jsonb->>'sign') AS distinct_signs
      FROM chart_facts WHERE fact_category = 'lord_in_house_per_varga'
      GROUP BY 1, 2, 3, 4
    ) x WHERE x.distinct_signs <> 1
  )
  -- (f18) house domain: value_jsonb.house must be within [1, 12].
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_in_house_per_varga'
      AND ((fact_value_jsonb->>'house')::int < 1 OR (fact_value_jsonb->>'house')::int > 12)
  )
  -- (g18) lord domain: value_jsonb.lord must be one of the seven classical grahas
  -- (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn) -- SIGN_LORDS never maps to a node, the same
  -- domain already established for migration 805's lord_a/lord_b.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'lord_in_house_per_varga'
      AND fact_value_jsonb->>'lord' NOT IN ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
  )
  -- (a19) net_argala_per_varga.fact_value_num must equal value_jsonb.net_argala -- the same
  -- count stored twice.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'net_argala_per_varga'
      AND fact_value_num <> (fact_value_jsonb->>'net_argala')::numeric
  )
  -- (b19) fact_subject format: must equal "{varga}_HOUSE_{house}" -- the writer's own
  -- `f"{varga}_HOUSE_{tgt_h}"` construction, re-derived from the row's own stored varga/house
  -- fields.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'net_argala_per_varga'
      AND fact_subject <> (fact_value_jsonb->>'varga') || '_HOUSE_' || (fact_value_jsonb->>'house')
  )
  -- (c19) house domain: value_jsonb.house must be within [1, 12].
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'net_argala_per_varga'
      AND ((fact_value_jsonb->>'house')::int < 1 OR (fact_value_jsonb->>'house')::int > 12)
  )
  -- (d19) net_argala domain: |value_jsonb.net_argala| must be <= 9 -- the maximum possible net
  -- (all 9 grahas concentrated at argala-only or virodha-only offset houses).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'net_argala_per_varga'
      AND abs((fact_value_jsonb->>'net_argala')::numeric) > 9
  )
  -- (e19) full cross-category re-derivation: net_argala must equal the sum of graha occupancy at
  -- the 4 classical argala-offset houses minus the sum at the 4 virodha-offset houses, sourced
  -- from the sibling graha_dignity_per_varga category's own house field for the SAME (chart,
  -- ayanamsha, build, varga) -- PLUS Lagna's own house-1 occupancy, but ONLY for varga='D1' (see
  -- header note: for D1, varga_state always includes a LAGNA pseudo-entry at house=1, absent
  -- from graha_dignity_per_varga's graha-only scope; every other varga's loader is graha-only,
  -- needing no adjustment). 0/5220 violations live.
  AND NOT EXISTS (
    WITH house_counts AS (
      SELECT chart_id, ayanamsha_id, build_id, fact_value_jsonb->>'varga' AS varga,
        (fact_value_jsonb->>'house')::int AS house_num, count(*) AS graha_count
      FROM chart_facts
      WHERE fact_category = 'graha_dignity_per_varga'
      GROUP BY 1, 2, 3, 4, 5
    ),
    target AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        cf.fact_value_jsonb->>'varga' AS varga,
        (cf.fact_value_jsonb->>'house')::int AS tgt_h,
        (cf.fact_value_jsonb->>'net_argala')::numeric AS stored_net
      FROM chart_facts cf
      WHERE cf.fact_category = 'net_argala_per_varga'
    ),
    recomputed AS (
      SELECT t.chart_id, t.ayanamsha_id, t.build_id, t.varga, t.tgt_h, t.stored_net,
        COALESCE((SELECT sum(hc.graha_count) FROM house_counts hc
          WHERE hc.chart_id = t.chart_id AND hc.ayanamsha_id = t.ayanamsha_id AND hc.build_id = t.build_id
            AND hc.varga = t.varga
            AND hc.house_num = ANY(ARRAY[
              ((t.tgt_h-1+2-1)%12)+1, ((t.tgt_h-1+4-1)%12)+1, ((t.tgt_h-1+5-1)%12)+1, ((t.tgt_h-1+11-1)%12)+1
            ])
        ), 0)
        + (CASE WHEN t.varga = 'D1' THEN
            (SELECT count(*) FROM unnest(ARRAY[
              ((t.tgt_h-1+2-1)%12)+1, ((t.tgt_h-1+4-1)%12)+1, ((t.tgt_h-1+5-1)%12)+1, ((t.tgt_h-1+11-1)%12)+1
            ]) x(h) WHERE x.h = 1)
          ELSE 0 END)
        - COALESCE((SELECT sum(hc.graha_count) FROM house_counts hc
          WHERE hc.chart_id = t.chart_id AND hc.ayanamsha_id = t.ayanamsha_id AND hc.build_id = t.build_id
            AND hc.varga = t.varga
            AND hc.house_num = ANY(ARRAY[
              ((t.tgt_h-1+3-1)%12)+1, ((t.tgt_h-1+10-1)%12)+1, ((t.tgt_h-1+9-1)%12)+1, ((t.tgt_h-1+12-1)%12)+1
            ])
        ), 0)
        - (CASE WHEN t.varga = 'D1' THEN
            (SELECT count(*) FROM unnest(ARRAY[
              ((t.tgt_h-1+3-1)%12)+1, ((t.tgt_h-1+10-1)%12)+1, ((t.tgt_h-1+9-1)%12)+1, ((t.tgt_h-1+12-1)%12)+1
            ]) x(h) WHERE x.h = 1)
          ELSE 0 END) AS recomputed_net
      FROM target t
    )
    SELECT 1 FROM recomputed WHERE stored_net <> recomputed_net
  )
  -- (a20) contradiction_pair.fact_value_text domain: must equal the writer's own constant
  -- "benefic_malefic_conflict" -- the only string this function ever emits.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair' AND fact_value_text <> 'benefic_malefic_conflict'
  )
  -- (b20) fact_key format: must equal "opposed_{family}_{varga}" -- the writer's own
  -- `f"opposed_{family}_{varga}"` construction, re-derived from the row's own stored
  -- family/varga fields.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair'
      AND fact_key <> 'opposed_' || (fact_value_jsonb->>'family') || '_' || (fact_value_jsonb->>'varga')
  )
  -- (c20) family domain: value_jsonb.family must be one of the writer's own CATEGORY_FAMILY
  -- values (yoga/dosha/argala/net_argala) -- no fifth value is ever legitimate.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair'
      AND fact_value_jsonb->>'family' NOT IN ('yoga', 'dosha', 'argala', 'net_argala')
  )
  -- (d20) argala-family source consistency: when family='argala', benefic_sources must be
  -- exactly ["argala_natal_matrix"] and malefic_sources must be exactly
  -- ["virodha_argala_natal_matrix"] -- these are the ONLY two categories CATEGORY_FAMILY maps to
  -- the argala family, so a genuine argala contradiction can never cite any other source pair.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair' AND fact_value_jsonb->>'family' = 'argala'
      AND NOT (
        fact_value_jsonb->'benefic_sources' = '["argala_natal_matrix"]'::jsonb
        AND fact_value_jsonb->'malefic_sources' = '["virodha_argala_natal_matrix"]'::jsonb
      )
  )
  -- (e20) genuine-contradiction invariant: both benefic_count and malefic_count must be > 0 --
  -- the writer's own `if has_benefic and has_malefic:` gate is the sole reason a row is ever
  -- emitted at all, so a stored row with either count at zero would contradict its own
  -- existence.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair'
      AND NOT ((fact_value_jsonb->>'benefic_count')::int > 0 AND (fact_value_jsonb->>'malefic_count')::int > 0)
  )
  -- (f20) target self-consistency: value_jsonb.target must equal fact_subject -- the same
  -- subject stored twice.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair' AND fact_value_jsonb->>'target' <> fact_subject
  )
  -- (g20) varga/subject consistency: fact_subject must begin with "{varga}_" -- the writer's own
  -- `_varga_from_subject` parse, re-derived as the converse check on what actually got stored.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'contradiction_pair'
      AND fact_subject NOT LIKE (fact_value_jsonb->>'varga') || '\_%' ESCAPE '\'
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
