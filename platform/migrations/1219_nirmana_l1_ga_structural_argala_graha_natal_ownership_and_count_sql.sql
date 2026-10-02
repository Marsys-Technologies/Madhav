-- 1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_count_sql.sql
--
-- Suvarna Track I (SS decision N-61, 2026-10-01, approved with changes 2026-10-02; design note
-- 00_ARCHITECTURE/briefs/suvarna/exec/DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md; explanation and before/after counts:
-- 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1219_INTENT_v1_0.md; Q-L1-04 / I-30 of DECISION_SHEET_L1_v1_0.md).
--
-- This is a real migration, applied through the normal runner: platform/scripts/migrate.ts owns the transaction,
-- so there is no BEGIN/COMMIT here (1086 pattern). It must be VERIFIED by production structure after it applies
-- (the post-apply queries below; CLAUDE.md N.4, Trap 103: never trust the deploy log, a run that reports success
-- can still have done nothing).
--
-- LOCK TIMEOUT. The first statement is SET LOCAL lock_timeout = '5s' (migration 1218 pattern): a blocked migrate
-- job must fail fast, not hang a shared deploy.
--
-- SERVING EFFECT AT APPLY: none: touches no trigger column of asset_registry (the trigger fires only on UPDATE OF
-- depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope,
-- has_writer, is_active, target_table: count_sql is not one of them) and retires no digest spec. No asset_freshness
-- row changes and no asset_output_digest_specs row is retired (proved by test_argala_migration_1219_sql.py against the
-- real trigger function body on a disposable Postgres). The frozen manifests of ga_strength and ga_condition read
-- evidence_refresh_required (count_sql is in the registry-contract fingerprint), which is not a serving state.
--
-- ORDERING. 1219 is a HARD PREREQUISITE of the S-L1 ga_structural rebuild: it must be applied BEFORE that rebuild
-- launches. It has no dependency on the writer deploy and MAY APPLY INDEPENDENTLY of it (before, with or after).
-- Its companion 1221 (the a29 integrity conjunct AND the ga_structural digest-spec swap) is a different matter and is a
-- SEPARATE, HELD PR: it is NOT applied with this file and never before the ga_structural writer deploy; see the header
-- of 1221.
--
-- THIS MIGRATION IS A HARD PREREQUISITE OF THE S-L1 ga_structural REBUILD, not registry tidiness.
-- The live trigger l1_data_plane_mutation_guard on chart_facts (function
-- l1_data_plane_guard_active_mutation, migration 1035) refuses any chart_facts INSERT / UPDATE /
-- DELETE by an L1 asset for a fact_category that has no fact_category_ownership row for THAT asset
-- ('L1 asset % cannot mutate chart_facts category %'). So the new category argala_graha_natal, the 22
-- categories the writer emits without an ownership row today, and every other L1 producer's categories
-- must be owned before the rebuild runs.
--
-- Two parts, in order. The integrity conjunct (a29) is NOT here: it is migration 1221 (own file, applied as a
-- named S-L1 step immediately before the ga_structural launch and never before the writer deploy). Floors are NOT touched here: target_floor is in the
-- columns of the live trigger nirmana_registry_receipt_invalidation (it would stale the asset's freshness),
-- and floors are re-declared from achieved counts after S-L1 in one registry migration.
--
--   1. fact_category_ownership (the mechanism of 410 / 842): 172 rows added, ON CONFLICT DO NOTHING.
--      * argala_graha_natal -> ga_structural (the new category).
--      * Q-L1-04: ga_structural owns bhava_bala_* (already owned, 842) and every category its writer
--        emits that lacks a row: the 22 categories in migration 914's digest spec without an ownership
--        row (the 12 categories of the decision sheet, 4,816 canonical rows, plus 10 conditional or
--        predicate-claimed ones: ashtakavarga_anubindu, bhava_chalit_rasi_divergence,
--        combustion_relationship, dosha_fires, graha_saptavargaja_bala_component, graha_yuddha,
--        parivartana_pairs, retrograde_aspect_modification, vimsopaka_bala_per_graha, yoga_fires).
--      * Q-L1-04: the other producers' categories, assigned by their live count_sql predicate (136
--        categories; derivation and writer cross-check in
--        /Users/Dev/suvarna-evidence/TrackI/argala_l1/derive_q04_ownership.py), plus six categories a
--        writer emits that no live row yet needs (independent review; derive_writer_categories.py):
--        ashtakavarga_bindu_contributor (ga_strength, not yet live), graha_degree_flags and
--        nakshatra_exchange (ga_nakshatra, conditional emission, named in migration 872's partition), and
--        esoteric_point_trisphuta / chatushphuta / panchasphuta (ga_sensitive, inert today because
--        sunrise_jd is never passed). Without a row the next build that emits one raises
--        'cannot mutate chart_facts category'. After 1219 every live category and every category a
--        ga_* chart_facts writer names as emitted has an owner.
--      * Five panchanga categories (bhadra_flag, chandra_bala_natal_baseline, eclipse_proximity_natal,
--        panchaka_flag, tara_bala_natal_baseline; 216 canonical rows) are written only by ga_panchanga
--        (ga_panchanga_writer.py) and inside its count_sql predicate, yet 410 owns them under
--        ga_structural, so both assets count them today. They move to ga_panchanga: the ga_structural
--        rows are DELETED here (the only deletion in this migration; guarded to exactly those five).
--      A guard refuses the insert if a listed category is already owned by an asset other than the one
--      named for it here (the five above excepted).
--
--   2. asset_registry.count_sql (Q-L1-04), so that NO ROW IS COUNTED BY TWO ASSETS after 1219:
--      * ga_strength: the 420 ga_structural bhava_bala_* rows ('%bhava_bala%' to 'house_bhava_bala_%'),
--        the 35 vimsopaka_bala_per_graha rows ('%vimsopaka%' to 'graha_vimsopaka_%') and the 35
--        graha_saptavargaja_bala_component rows (clause removed) leave its predicate: they are
--        ga_structural's (it is the emitter). So does ashtakavarga_anubindu: it is owned by ga_structural (its
--        writer emits it, 7 grahas x 12 houses per ayanamsha) but the retained 'ashtakavarga_%' clause would still
--        match it, so that clause becomes (LIKE 'ashtakavarga_%' AND <> 'ashtakavarga_anubindu'). Every other
--        ashtakavarga_* category the clause matched stays ga_strength's (the 11 live ones, all in its ownership
--        rows below, plus ashtakavarga_bindu_contributor). 0 anubindu rows exist on any chart today, so no
--        count moves; the exclusion closes the double count before S-L1 emits those rows.
--      * ga_condition: only the stale graha_yuddha clause leaves its predicate (ga_structural emits and owns
--        graha_yuddha; the clause double-counts it on charts that have it; 0 rows on the canonical chart).
--        It keeps counting the 2,925 chart_facts rows it owns (CLAUDE.md N.4 cockpit truth). NOTE for SS:
--        Q-L1-04's text says "count_sql on the primary table (45)"; counting only the composite table
--        would hide 2,925 rows it writes, so the multi-table count shape is left to I-30 (writer and
--        declaration work). Its floor is not touched.
--      * ga_structural: its count_sql already joins the ownership table (410), so part 1 is its change.
--      Each UPDATE refuses to run unless the live count_sql is exactly the text read (md5 guard).
--      count_sql is not in the columns of nirmana_registry_receipt_invalidation, so no freshness is staled;
--      it is in the Nirmana registry-contract fingerprint (definitions.ts), so the frozen manifests of
--      ga_strength and ga_condition go to evidence_refresh_required (design note, section 5).
--
--      Canonical chart (482012f1) chart_facts-based counts, from the live category table, before / after:
--        asset                 before    after    change
--        ga_structural        102,037  106,707    +4,670  (+4,816 the 12 unowned categories, +70 vimsopaka_bala_per_graha
--                                                           and graha_saptavargaja_bala_component, -216 the five panchanga
--                                                           categories; equals its 106,707 build record)
--        ga_strength           14,141   13,651      -490  (-420 bhava_bala_*, -70 vimsopaka / saptavarga component)
--        ga_condition           2,970    2,970         0  (only the graha_yuddha clause leaves its predicate: 0 canonical rows)
--        ga_panchanga             437      437         0  (the five categories were already inside its predicate)
--        ga_nakshatra 2,847; ga_positions 1,205; ga_sade_sati 6,287; ga_sensitive 8,775; ga_sensitive_degree 335;
--        ga_ayurdaya 130: unchanged.
--      The narrowed ga_strength predicate was also run as SQL against the live canonical chart (read-only): 13,651.
--      Before 1219 the double claims on the canonical chart are the 420 bhava_bala_* rows (ga_structural by
--      ownership, ga_strength by predicate) and the five panchanga categories (216 rows; ga_structural by
--      ownership, ga_panchanga by predicate): 636 rows. After 1219 no chart_facts row is claimed by two assets
--      (check: /Users/Dev/suvarna-evidence/TrackI/argala_l1/count_claims_before_after.py; without the
--      narrowing the 70 vimsopaka / saptavargaja rows owned here would have joined that list). Rows of the
--      new argala_graha_natal category appear after S-L1 (156 expected, pre-ephemeris estimate).
--
--   The ga_structural output-digest spec (81 -> 82 categories, adding argala_graha_natal) is NOT here: it moved to
--   migration 1221 (own HELD PR), because retiring the active spec makes ga_structural's receipts read
--   receipt_spec_retired for serving (served_generation.ts) until rebuilt, and that must happen only in the S-L1 window
--   together with the a29 freshness stale, not from the integration's deploy.
--
-- Post-apply verification (each should return the stated value):
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category = 'argala_graha_natal' AND owning_asset_id = 'ga_structural';            -- 1
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category IN ('bhadra_flag', 'panchaka_flag') AND owning_asset_id = 'ga_structural'; -- 0
--   SELECT count(*) FROM asset_output_digest_specs WHERE retired_at IS NOT NULL;                   -- unchanged by 1219
--   SELECT count(*) FROM asset_freshness WHERE reasons ? 'registry_changed';                       -- unchanged by 1219
--   SELECT count_sql LIKE '%house_bhava_bala_%' AND count_sql NOT LIKE '%saptavargaja%'
--     FROM asset_registry WHERE asset_id = 'ga_strength';                                         -- t
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category IN ('bhadra_flag', 'chandra_bala_natal_baseline', 'eclipse_proximity_natal',
--                            'panchaka_flag', 'tara_bala_natal_baseline') AND owning_asset_id = 'ga_panchanga'; -- 5
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category IN ('bhadra_flag', 'chandra_bala_natal_baseline', 'eclipse_proximity_natal',
--                            'panchaka_flag', 'tara_bala_natal_baseline') AND owning_asset_id = 'ga_structural'; -- 0
--   SELECT count_sql NOT LIKE '%graha_yuddha%' AND count_sql LIKE '%ga_condition_composite%'
--     FROM asset_registry WHERE asset_id = 'ga_condition';                                        -- t
--   SELECT count_sql LIKE '%<> ''ashtakavarga_anubindu''%' FROM asset_registry WHERE asset_id = 'ga_strength'; -- t

-- Fail fast: a migrate job blocked on a lock must fail, not hang a shared deploy (migration 1218 pattern).
SET LOCAL lock_timeout = '5s';

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
    ('graha_degree_flags', 'ga_nakshatra'),
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
    ('nakshatra_exchange', 'ga_nakshatra'),
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
    ('esoteric_point_chatushphuta', 'ga_sensitive'),
    ('esoteric_point_mrityu', 'ga_sensitive'),
    ('esoteric_point_panchasphuta', 'ga_sensitive'),
    ('esoteric_point_pranapada_sphuta', 'ga_sensitive'),
    ('esoteric_point_shiva', 'ga_sensitive'),
    ('esoteric_point_sphuta_fertility', 'ga_sensitive'),
    ('esoteric_point_sri_yantra_position', 'ga_sensitive'),
    ('esoteric_point_trikona_dasha_sphuta', 'ga_sensitive'),
    ('esoteric_point_trisphuta', 'ga_sensitive'),
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
    ('ashtakavarga_bindu_contributor', 'ga_strength'),
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
    AND NOT (n.owning_asset_id = 'ga_panchanga' AND o.owning_asset_id = 'ga_structural'
             AND n.fact_category IN ('bhadra_flag', 'chandra_bala_natal_baseline', 'eclipse_proximity_natal',
                                     'panchaka_flag', 'tara_bala_natal_baseline'));
  IF conflicting <> 0 THEN
    RAISE EXCEPTION 'ownership 1219 refused: % category(ies) already owned by a different asset', conflicting;
  END IF;

  INSERT INTO fact_category_ownership (fact_category, owning_asset_id)
  SELECT fact_category, owning_asset_id FROM _own_1219
  ON CONFLICT (fact_category, owning_asset_id) DO NOTHING;

  -- the five panchanga categories: ga_panchanga now owns them (inserted above), ga_structural does not
  DELETE FROM fact_category_ownership
   WHERE owning_asset_id = 'ga_structural'
     AND fact_category IN ('bhadra_flag', 'chandra_bala_natal_baseline', 'eclipse_proximity_natal',
                           'panchaka_flag', 'tara_bala_natal_baseline');

  IF NOT EXISTS (SELECT 1 FROM fact_category_ownership
                  WHERE fact_category = 'argala_graha_natal' AND owning_asset_id = 'ga_structural') THEN
    RAISE EXCEPTION 'ownership 1219 failed: argala_graha_natal row missing';
  END IF;
END $$;

-- ── 2. count_sql (Q-L1-04) ───────────────────────────────────────────────────────────────────
DO $$
DECLARE
  n integer;
  strength_new constant text := $cs$
  SELECT count(*) AS count FROM chart_facts
  WHERE chart_id = $1
    AND (
      fact_category LIKE 'graha_shadbala_%'
      OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala')
      OR fact_category LIKE 'graha_vimsopaka_%'
      OR (fact_category LIKE 'ashtakavarga_%' AND fact_category <> 'ashtakavarga_anubindu')
      OR fact_category LIKE 'house_bhava_bala_%'
      OR fact_category LIKE 'graha_%_bala_per_varga'
    )
$cs$;
  condition_new constant text := $cc$SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1)
       + (SELECT count(*) FROM chart_facts
          WHERE chart_id = $1
            AND (fact_category LIKE 'graha_avastha_%_per_varga'
                 OR fact_category = 'graha_avastha_sayanadi'
                 OR fact_category = 'graha_avastha_lajjitadi')) AS count$cc$;
BEGIN
  UPDATE asset_registry SET count_sql = strength_new
   WHERE asset_id = 'ga_strength' AND md5(count_sql) = '1660f637c6e08c1ffe1f944776fd1618';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 AND NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ga_strength' AND count_sql = strength_new) THEN
    RAISE EXCEPTION 'ga_strength count_sql narrowing refused: live count_sql is not the text read (rows %)', n;
  END IF;

  UPDATE asset_registry SET count_sql = condition_new
   WHERE asset_id = 'ga_condition' AND md5(count_sql) = '75de1a479cbfeba37383aefdbfd83355';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 AND NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'ga_condition' AND count_sql = condition_new) THEN
    RAISE EXCEPTION 'ga_condition count_sql re-declaration refused: live count_sql is not the text read (rows %)', n;
  END IF;
END $$;
