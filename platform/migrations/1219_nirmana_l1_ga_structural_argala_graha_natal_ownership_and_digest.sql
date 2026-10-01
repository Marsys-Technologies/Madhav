-- 1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql
--
-- DRAFT, NOT APPLIED. Suvarna Track I (SS decision N-61, 2026-10-01, approved with changes
-- 2026-10-02; design note 00_ARCHITECTURE/briefs/suvarna/exec/DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md;
-- Q-L1-04 / I-30 of DECISION_SHEET_L1_v1_0.md). The reviewer/operator applies it through the PR and
-- verifies it (CLAUDE.md N.4: never trust a silent no-op). Re-check at arm time that 1219 is still free.
-- Transaction ownership belongs to platform/scripts/migrate.ts: no BEGIN/COMMIT here (1086 pattern).
--
-- THIS MIGRATION IS A HARD PREREQUISITE OF THE S-L1 ga_structural REBUILD, not registry tidiness.
-- The live trigger l1_data_plane_mutation_guard on chart_facts (function
-- l1_data_plane_guard_active_mutation, migration 1035) refuses any chart_facts INSERT / UPDATE /
-- DELETE by an L1 asset for a fact_category that has no fact_category_ownership row for THAT asset
-- ('L1 asset % cannot mutate chart_facts category %'). So the new category argala_graha_natal, the 22
-- categories the writer emits without an ownership row today, and every other L1 producer's categories
-- must be owned before the rebuild runs.
--
-- Four parts, in order:
--
--   1. fact_category_ownership (the mechanism of 410 / 842): 166 rows, ON CONFLICT DO NOTHING.
--      * argala_graha_natal -> ga_structural (the new category).
--      * Q-L1-04: ga_structural owns bhava_bala_* (already owned, 842) and every category its writer
--        emits that lacks a row: the 22 categories in migration 914's digest spec without an ownership
--        row (the 12 categories of the decision sheet, 4,816 canonical rows, plus 10 conditional or
--        predicate-claimed ones: ashtakavarga_anubindu, bhava_chalit_rasi_divergence,
--        combustion_relationship, dosha_fires, graha_saptavargaja_bala_component, graha_yuddha,
--        parivartana_pairs, retrograde_aspect_modification, vimsopaka_bala_per_graha, yoga_fires).
--      * Q-L1-04: the other producers' categories, assigned by their live count_sql predicate (138
--        categories; derivation and writer cross-check in
--        /Users/Dev/suvarna-evidence/TrackI/argala_l1/derive_q04_ownership.py). ga_panchanga is also given
--        the five categories 842-era ownership put on ga_structural alone (bhadra_flag,
--        chandra_bala_natal_baseline, eclipse_proximity_natal, panchaka_flag, tara_bala_natal_baseline).
--      A guard refuses the insert if a listed category is already owned by an asset other than the
--      ones named for it here, except the five ga_panchanga ones, which are deliberately dual-owned.
--
--   2. asset_registry (Q-L1-04). count_sql of ga_strength narrowed so it no longer claims the 420
--      ga_structural bhava_bala_* rows ('%bhava_bala%' to 'house_bhava_bala_%', 14,141 to 13,721 on the
--      canonical chart); ga_condition's count_sql moved to its primary table (ga_condition_composite)
--      only, and its aspirational target_floor re-declared from the achieved counts (13,721 and 45; floors
--      are aspirational, CLAUDE.md N.4). ga_structural's own count_sql already joins the ownership table
--      (410), so part 1 is its count change; its floor re-baselines after the S-L1 rebuild. Guards: each
--      UPDATE refuses to run unless the live text / floor is exactly what was read.
--      NOT done here (I-30 writer and declaration work): ga_condition's declared multi-table shape and
--      its rows_written counting everything it writes.
--
--   3. asset_output_digest_specs. ga_structural has ONE active spec (migration 914, sha b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6,
--      81 categories); a category outside its where_in is not digested, so a change to the new rows would
--      not move the output digest. This retires it and inserts the same spec plus argala_graha_natal (82).
--      spec_sha256 = canonical_digest (pipeline.orchestrator.provenance), which reproduces 914's stored
--      sha exactly. Retired, not deleted (609 / 1086 precedent).
--
--   4. ga_structural.integrity_check_sql: one new conjunct, (a29), argala NULL <=> empty source sign
--      (CLAUDE.md N.8: conjunct (e27) is vacuously true on a NULL score). Applied as a guarded
--      replace() of the live text at its single `AS integrity_passed` anchor, not a 200 KB re-statement
--      of migration 904's text; it refuses unless (g28) is present, the anchor occurs exactly once and
--      (a29) is not already there, and it asserts the result afterwards. (a29) is scoped to the canonical
--      chart (904's tradeoff) and is EXPECTED RED until the S-L1 rebuild writes the NULL cells.
--
-- Open for SS (flagged, not decided here): vimsopaka_bala_per_graha (35 rows) and
-- graha_saptavargaja_bala_component (35 rows) are emitted by ga_structural_writer but fall inside
-- ga_strength's count_sql predicate; here ga_structural owns them (the guard needs it) and both assets
-- count them until that predicate is narrowed further.
--
-- Post-apply verification (each should return the stated value):
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category = 'argala_graha_natal' AND owning_asset_id = 'ga_structural';            -- 1
--   SELECT spec_sha256 FROM asset_output_digest_specs
--    WHERE asset_id = 'ga_structural' AND retired_at IS NULL;                                     -- d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620
--   SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry
--    WHERE asset_id = 'ga_structural';                                                           -- t
--   SELECT count_sql NOT LIKE '%bhava_bala%' OR count_sql LIKE '%house_bhava_bala_%'
--     FROM asset_registry WHERE asset_id = 'ga_strength';                                         -- t

-- ── 1. ownership ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
  conflicting integer;
BEGIN
  CREATE TEMP TABLE _own_1219 (fact_category text NOT NULL, owning_asset_id text NOT NULL) ON COMMIT DROP;
  INSERT INTO _own_1219 (fact_category, owning_asset_id) VALUES
    ('graha_avastha_baladi_per_varga', 'ga_condition'),
    ('graha_avastha_deeptaadi_per_varga', 'ga_condition'),
    ('graha_avastha_jagradadi_per_varga', 'ga_condition'),
    ('graha_avastha_lajjitadi_per_varga', 'ga_condition'),
    ('graha_avastha_sayanadi_per_varga', 'ga_condition'),
    ('cusp_kp_lords', 'ga_nakshatra'),
    ('graha_gandanta', 'ga_nakshatra'),
    ('graha_kp_lords', 'ga_nakshatra'),
    ('graha_nakshatra_join', 'ga_nakshatra'),
    ('graha_pada_join', 'ga_nakshatra'),
    ('graha_tara_bala', 'ga_nakshatra'),
    ('kp_house_significators', 'ga_nakshatra'),
    ('kp_planet_significations', 'ga_nakshatra'),
    ('nakshatra_cogravity', 'ga_nakshatra'),
    ('nakshatra_conjunction', 'ga_nakshatra'),
    ('nakshatra_cross_ayanamsha', 'ga_nakshatra'),
    ('nakshatra_dispositor', 'ga_nakshatra'),
    ('nakshatra_statistics', 'ga_nakshatra'),
    ('bhadra_flag', 'ga_panchanga'),
    ('chandra_bala_natal_baseline', 'ga_panchanga'),
    ('eclipse_proximity_natal', 'ga_panchanga'),
    ('panchaka_flag', 'ga_panchanga'),
    ('panchanga_abhijit_muhurta', 'ga_panchanga'),
    ('panchanga_agni_vasa', 'ga_panchanga'),
    ('panchanga_brahma_muhurta', 'ga_panchanga'),
    ('panchanga_calendrical', 'ga_panchanga'),
    ('panchanga_choghadiya_birth', 'ga_panchanga'),
    ('panchanga_disha_shul', 'ga_panchanga'),
    ('panchanga_durmuhurta', 'ga_panchanga'),
    ('panchanga_godhuli_muhurta', 'ga_panchanga'),
    ('panchanga_gulika_kalam', 'ga_panchanga'),
    ('panchanga_hora_birth', 'ga_panchanga'),
    ('panchanga_karana', 'ga_panchanga'),
    ('panchanga_krakaca', 'ga_panchanga'),
    ('panchanga_madhyahna_sandhya', 'ga_panchanga'),
    ('panchanga_nakshatra_moon', 'ga_panchanga'),
    ('panchanga_nakshatra_shoonya_rashi', 'ga_panchanga'),
    ('panchanga_nishita_kala', 'ga_panchanga'),
    ('panchanga_panchaka_classification', 'ga_panchanga'),
    ('panchanga_pratah_sandhya', 'ga_panchanga'),
    ('panchanga_rahu_kalam', 'ga_panchanga'),
    ('panchanga_sashtighati', 'ga_panchanga'),
    ('panchanga_sayam_sandhya', 'ga_panchanga'),
    ('panchanga_solar_context', 'ga_panchanga'),
    ('panchanga_special_yoga_combinations', 'ga_panchanga'),
    ('panchanga_sun_moon_dynamics', 'ga_panchanga'),
    ('panchanga_tithi', 'ga_panchanga'),
    ('panchanga_tithi_shoonya_rashi', 'ga_panchanga'),
    ('panchanga_vara', 'ga_panchanga'),
    ('panchanga_varjyam', 'ga_panchanga'),
    ('panchanga_vijaya_muhurta', 'ga_panchanga'),
    ('panchanga_visha_ghati', 'ga_panchanga'),
    ('panchanga_yamaganda_kalam', 'ga_panchanga'),
    ('panchanga_yamakantaka', 'ga_panchanga'),
    ('panchanga_yoga', 'ga_panchanga'),
    ('tara_bala_natal_baseline', 'ga_panchanga'),
    ('bhava_cusps', 'ga_positions'),
    ('graha_position', 'ga_positions'),
    ('graha_sign_attributes', 'ga_positions'),
    ('house_chalit', 'ga_positions'),
    ('sandhi_flag', 'ga_positions'),
    ('anumukha_shani_period', 'ga_sade_sati'),
    ('ardha_ashtama_shani_period', 'ga_sade_sati'),
    ('ashtama_shani_period', 'ga_sade_sati'),
    ('dhaiya_period', 'ga_sade_sati'),
    ('janma_shani_period', 'ga_sade_sati'),
    ('kantaka_shani_period', 'ga_sade_sati'),
    ('sade_sati_cancellation_check', 'ga_sade_sati'),
    ('sade_sati_concurrent_dasha_overlay', 'ga_sade_sati'),
    ('sade_sati_cycle', 'ga_sade_sati'),
    ('sade_sati_downstream_cross_reference', 'ga_sade_sati'),
    ('sade_sati_modifier_overlay', 'ga_sade_sati'),
    ('sade_sati_phase', 'ga_sade_sati'),
    ('sade_sati_phase_quarter', 'ga_sade_sati'),
    ('sade_sati_saturn_retrograde_subset', 'ga_sade_sati'),
    ('vishakha_shani_period', 'ga_sade_sati'),
    ('aprakasha_position', 'ga_sensitive'),
    ('arudha_pada', 'ga_sensitive'),
    ('bhava_arudha', 'ga_sensitive'),
    ('bhrigu_nadi_point', 'ga_sensitive'),
    ('esoteric_point_avayogi', 'ga_sensitive'),
    ('esoteric_point_bhrigu_bindu', 'ga_sensitive'),
    ('esoteric_point_brahma', 'ga_sensitive'),
    ('esoteric_point_mrityu', 'ga_sensitive'),
    ('esoteric_point_pranapada_sphuta', 'ga_sensitive'),
    ('esoteric_point_shiva', 'ga_sensitive'),
    ('esoteric_point_sphuta_fertility', 'ga_sensitive'),
    ('esoteric_point_sri_yantra_position', 'ga_sensitive'),
    ('esoteric_point_trikona_dasha_sphuta', 'ga_sensitive'),
    ('esoteric_point_vishnu', 'ga_sensitive'),
    ('esoteric_point_yogi', 'ga_sensitive'),
    ('esoteric_point_yogi_system', 'ga_sensitive'),
    ('karaka_chara_position', 'ga_sensitive'),
    ('karakamsa_position', 'ga_sensitive'),
    ('kp_cuspal_significators', 'ga_sensitive'),
    ('kp_ruling_planets_natal', 'ga_sensitive'),
    ('lal_kitab_special_point', 'ga_sensitive'),
    ('maharsi_specific_point', 'ga_sensitive'),
    ('midpoint', 'ga_sensitive'),
    ('nakshatra_pada_sensitive', 'ga_sensitive'),
    ('saham_position', 'ga_sensitive'),
    ('saturn_derived_point', 'ga_sensitive'),
    ('sensitive_point_gulika_mandi', 'ga_sensitive'),
    ('special_lagna', 'ga_sensitive'),
    ('sun_derived_upagraha', 'ga_sensitive'),
    ('swamsa_position', 'ga_sensitive'),
    ('tajik_hadda_lord', 'ga_sensitive'),
    ('tajik_triraashipathi', 'ga_sensitive'),
    ('tajik_vargottama_specific', 'ga_sensitive'),
    ('upagraha_position', 'ga_sensitive'),
    ('sensitive_degree_check', 'ga_sensitive_degree'),
    ('sensitive_point_yogi', 'ga_sensitive_degree'),
    ('ashtakavarga_bindu', 'ga_strength'),
    ('ashtakavarga_bindu_per_varga', 'ga_strength'),
    ('ashtakavarga_bindu_sign', 'ga_strength'),
    ('ashtakavarga_ekadhipathya_shodhana', 'ga_strength'),
    ('ashtakavarga_kakshya_boundary', 'ga_strength'),
    ('ashtakavarga_pinda_bhinna', 'ga_strength'),
    ('ashtakavarga_pinda_raasi', 'ga_strength'),
    ('ashtakavarga_pinda_sarva', 'ga_strength'),
    ('ashtakavarga_pinda_sarva_per_varga', 'ga_strength'),
    ('ashtakavarga_pinda_sodhita', 'ga_strength'),
    ('ashtakavarga_trikona_shodhana', 'ga_strength'),
    ('graha_cheshta_bala_per_varga', 'ga_strength'),
    ('graha_drik_bala_per_varga', 'ga_strength'),
    ('graha_ishta_phala', 'ga_strength'),
    ('graha_kala_bala_per_varga', 'ga_strength'),
    ('graha_kashta_phala', 'ga_strength'),
    ('graha_shadbala_cheshta', 'ga_strength'),
    ('graha_shadbala_dig', 'ga_strength'),
    ('graha_shadbala_drik', 'ga_strength'),
    ('graha_shadbala_kala', 'ga_strength'),
    ('graha_shadbala_naisargika', 'ga_strength'),
    ('graha_shadbala_sthana', 'ga_strength'),
    ('graha_shadbala_total', 'ga_strength'),
    ('graha_sthana_bala_per_varga', 'ga_strength'),
    ('graha_vimsopaka_dasavarga', 'ga_strength'),
    ('graha_vimsopaka_saptavarga', 'ga_strength'),
    ('graha_vimsopaka_shadvarga', 'ga_strength'),
    ('graha_vimsopaka_shodasavarga', 'ga_strength'),
    ('house_bhava_bala_ratio', 'ga_strength'),
    ('house_bhava_bala_subscore', 'ga_strength'),
    ('house_bhava_bala_total', 'ga_strength'),
    ('argala_graha_natal', 'ga_structural'),
    ('ashtakavarga_anubindu', 'ga_structural'),
    ('bhava_chalit_rasi_divergence', 'ga_structural'),
    ('combustion_relationship', 'ga_structural'),
    ('conjunction_special_point', 'ga_structural'),
    ('dosha_fires', 'ga_structural'),
    ('dosha_label', 'ga_structural'),
    ('graha_saptavargaja_bala_component', 'ga_structural'),
    ('graha_yuddha', 'ga_structural'),
    ('karaka_web_per_varga', 'ga_structural'),
    ('kendradhipati_dosha', 'ga_structural'),
    ('nakshatra_co_tenancy', 'ga_structural'),
    ('nakshatra_lord_relationship', 'ga_structural'),
    ('panchadha_maitri', 'ga_structural'),
    ('parivartana_pairs', 'ga_structural'),
    ('retrograde_aspect_modification', 'ga_structural'),
    ('significator_path', 'ga_structural'),
    ('tara_bala', 'ga_structural'),
    ('upapada_lagna', 'ga_structural'),
    ('vimsopaka_bala_per_graha', 'ga_structural'),
    ('virupa_drishti', 'ga_structural'),
    ('yoga_fires', 'ga_structural'),
    ('yoga_label', 'ga_structural');

  SELECT count(*) INTO conflicting
  FROM _own_1219 n
  JOIN fact_category_ownership o ON o.fact_category = n.fact_category
  WHERE o.owning_asset_id <> n.owning_asset_id
    AND NOT (n.owning_asset_id = 'ga_panchanga' AND o.owning_asset_id = 'ga_structural');
  IF conflicting <> 0 THEN
    RAISE EXCEPTION 'ownership 1219 refused: % category(ies) already owned by a different asset', conflicting;
  END IF;

  INSERT INTO fact_category_ownership (fact_category, owning_asset_id)
  SELECT fact_category, owning_asset_id FROM _own_1219
  ON CONFLICT (fact_category, owning_asset_id) DO NOTHING;

  IF NOT EXISTS (SELECT 1 FROM fact_category_ownership
                  WHERE fact_category = 'argala_graha_natal' AND owning_asset_id = 'ga_structural') THEN
    RAISE EXCEPTION 'ownership 1219 failed: argala_graha_natal row missing';
  END IF;
END $$;

-- ── 2. count_sql / floors (Q-L1-04) ──────────────────────────────────────────────────────────
DO $$
DECLARE
  n integer;
BEGIN
  UPDATE asset_registry
     SET count_sql = replace(count_sql, '%bhava_bala%', 'house_bhava_bala_%'),
         target_floor = 13721
   WHERE asset_id = 'ga_strength'
     AND (length(count_sql) - length(replace(count_sql, 'LIKE ''%bhava_bala%''', ''))) = length('LIKE ''%bhava_bala%''')
     AND target_floor = 13621;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 AND NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ga_strength'
                              AND count_sql LIKE '%house_bhava_bala_%' AND target_floor = 13721) THEN
    RAISE EXCEPTION 'ga_strength count_sql narrowing refused: live count_sql / floor is not the one read (rows %)', n;
  END IF;

  UPDATE asset_registry
     SET count_sql = 'SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1',
         target_floor = 45
   WHERE asset_id = 'ga_condition'
     AND count_sql LIKE '%FROM ga_condition_composite%'
     AND count_sql LIKE '%FROM chart_facts%'
     AND target_floor = 2880;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 AND NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ga_condition'
                              AND count_sql = 'SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1'
                              AND target_floor = 45) THEN
    RAISE EXCEPTION 'ga_condition count_sql re-declaration refused: live count_sql / floor is not the one read (rows %)', n;
  END IF;
END $$;

-- ── 3. ga_structural output-digest spec ──────────────────────────────────────────────────────
DO $$
DECLARE
  unexpected_active_count integer;
  active_new_count integer;
BEGIN
  SELECT count(*)
  INTO unexpected_active_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_structural'
    AND retired_at IS NULL
    AND spec_sha256 NOT IN (
      'b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6',
      'd480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620'
    );

  IF unexpected_active_count <> 0 THEN
    RAISE EXCEPTION
      'ga_structural digest-spec revision refused: % unrecognised active row(s)',
      unexpected_active_count;
  END IF;

  UPDATE asset_output_digest_specs
  SET retired_at = now()
  WHERE asset_id = 'ga_structural'
    AND spec_sha256 = 'b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6'
    AND retired_at IS NULL;

  INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
  VALUES (
    'ga_structural',
    'd480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620',
    '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts","relation":"chart_facts","where_in":{"fact_category":["argala_graha_natal","argala_natal_matrix","ashtakavarga_anubindu","aspect_jaimini","aspect_jaimini_per_varga","aspect_matrix_summary","aspect_parashari_given","aspect_parashari_per_varga","aspect_parashari_received","aspect_received_by_special_point","aspect_tajik","bhava_bala_aspectual","bhava_bala_directional","bhava_bala_lord","bhava_bala_occupant","bhava_bala_positional","bhava_bala_temporal","bhava_bala_total_extended","bhava_chalit_rasi_divergence","bhava_significance_link","chart_center_of_gravity","chart_cluster","combustion_per_varga","combustion_relationship","composite_dispositor_strength","conjunction_per_varga","conjunction_special_point","conjunction_within_orb","contradiction_pair","convergence_count","dispositor_chain_per_varga","dispositor_tree","dosha_fires","dosha_label","graha_avastha_baladi","graha_avastha_deepta","graha_avastha_jagrad","graha_avastha_lifetime_exposure_summary","graha_centrality","graha_composite_state_classification","graha_dignity_per_varga","graha_dispositor_chain","graha_effective_dignity_modified_by_aspects","graha_functional_class_per_ascendant","graha_in_house_composite_strength","graha_saptavargaja_bala_component","graha_special_state_rollup","graha_tri_deva_role_strength","graha_vargottama_amplification_factor","graha_yoga_karaka_flag","graha_yuddha","graha_yuddha_per_varga","house_strength_classification_rollup","jaimini_tri_deva_role_per_graha","kala_sarpa_per_varga","karaka_bhava_concordance","karaka_house_lord_overlap_flag","karaka_web_per_varga","karakatva_strength_per_significance","kendradhipati_dosha","lord_aspects_lord_per_varga","lord_in_house_per_varga","nakshatra_co_tenancy","nakshatra_dispositor_chain","nakshatra_lord_relationship","net_argala_per_varga","nway_config_per_varga","panchadha_maitri","parivartana_pairs","parivartana_per_varga","pranic_strength_per_graha","retrograde_aspect_modification","sambandha_grade","significator_path","tara_bala","upapada_lagna","vargottama_per_varga","vimsopaka_bala_per_graha","virodha_argala_natal_matrix","virupa_drishti","yoga_fires","yoga_label"]},"key_columns":["fact_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"]}]}'::jsonb
  )
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

  SELECT count(*)
  INTO active_new_count
  FROM asset_output_digest_specs
  WHERE asset_id = 'ga_structural'
    AND spec_sha256 = 'd480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620'
    AND retired_at IS NULL;

  IF active_new_count <> 1 THEN
    RAISE EXCEPTION
      'ga_structural digest-spec revision failed: expected one active new row, got %',
      active_new_count;
  END IF;
END $$;

-- ── 4. integrity conjunct (a29) ──────────────────────────────────────────────────────────────
DO $$
DECLARE
  anchor constant text := E'\n  AS integrity_passed';
  conjunct constant text := $conj$
  -- (a29) [SS N-61, AR-3; CLAUDE.md N.8] argala NULL <=> empty source sign. For every argala-offset
  -- cell (2, 4, 5, 11) of argala_natal_matrix, the cell must be NULL with fact_value_text
  -- 'no_occupant' exactly when its source sign holds no graha, and a non-NULL score with no text
  -- when it does. Occupancy is cross-referenced from the sibling graha_dignity_per_varga category
  -- for the SAME (chart, ayanamsha, build, varga), as (e27) and (d28) do. This closes the vacuity
  -- of (e27): its `net_argala <> round(...)` is NULL, not true, for a NULL score, so a NULL on an
  -- occupied cell (or a stale 1.0 on an empty one) used to pass. SCOPED to the canonical chart
  -- (migration 904's disclosed tradeoff): the other charts still hold pre-AR-3 rows (1.0 on empty
  -- cells) until they rebuild. EXPECTED RED on the canonical chart until the one S-L1 ga_structural
  -- rebuild writes the NULL cells; it is read by the post-write gate of that build, not before.
  AND NOT EXISTS (
    WITH parsed AS (
      SELECT cf.chart_id, cf.ayanamsha_id, cf.build_id,
        split_part(cf.fact_subject, '_SIGN_', 1) AS varga,
        (split_part(substring(cf.fact_key from 11), '_offset_', 1))::int AS source_sign_num,
        (split_part(substring(cf.fact_key from 11), '_offset_', 2))::int AS argala_offset,
        cf.fact_value_num AS score,
        cf.fact_value_text AS score_text
      FROM chart_facts cf
      WHERE cf.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
        AND cf.fact_category = 'argala_natal_matrix'
    ),
    arows AS (
      SELECT * FROM parsed WHERE argala_offset IN (2, 4, 5, 11)
    ),
    sign_names(idx, sign) AS (VALUES
      (1, 'Aries'), (2, 'Taurus'), (3, 'Gemini'), (4, 'Cancer'), (5, 'Leo'), (6, 'Virgo'),
      (7, 'Libra'), (8, 'Scorpio'), (9, 'Sagittarius'), (10, 'Capricorn'), (11, 'Aquarius'),
      (12, 'Pisces')
    ),
    occ AS (
      SELECT ar.*,
        EXISTS (
          SELECT 1 FROM chart_facts gd
          JOIN sign_names sn ON sn.idx = ar.source_sign_num
          WHERE gd.chart_id = ar.chart_id AND gd.ayanamsha_id = ar.ayanamsha_id
            AND gd.build_id = ar.build_id AND gd.fact_category = 'graha_dignity_per_varga'
            AND gd.fact_value_jsonb->>'varga' = ar.varga AND gd.fact_value_jsonb->>'sign' = sn.sign
        ) AS has_occ
      FROM arows ar
    )
    SELECT 1 FROM occ
    WHERE (has_occ AND (score IS NULL OR score_text IS NOT NULL))
       OR (NOT has_occ AND (score IS NOT NULL OR score_text IS DISTINCT FROM 'no_occupant'))
  )
$conj$;
  live text;
  n integer;
BEGIN
  SELECT integrity_check_sql INTO live FROM asset_registry WHERE asset_id = 'ga_structural' FOR UPDATE;
  IF live IS NULL THEN
    RAISE EXCEPTION 'ga_structural integrity patch refused: no integrity_check_sql';
  END IF;
  IF position('(a29)' in live) > 0 THEN
    RETURN;   -- already applied (idempotent re-run)
  END IF;
  IF position('(g28)' in live) = 0 THEN
    RAISE EXCEPTION 'ga_structural integrity patch refused: live text lacks conjunct (g28)';
  END IF;
  IF (length(live) - length(replace(live, anchor, ''))) <> length(anchor) THEN
    RAISE EXCEPTION 'ga_structural integrity patch refused: anchor is not unique in the live text';
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = replace(integrity_check_sql, anchor, rtrim(conjunct, E'\n') || anchor)
   WHERE asset_id = 'ga_structural';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 OR NOT EXISTS (SELECT 1 FROM asset_registry
                            WHERE asset_id = 'ga_structural' AND position('(a29)' in integrity_check_sql) > 0
                              AND position('(g28)' in integrity_check_sql) > 0) THEN
    RAISE EXCEPTION 'ga_structural integrity patch failed to apply';
  END IF;
END $$;
