---
artifact: MIGRATION_1219_1221_INTENT
version: "1.0"
status: INTENT ONLY (owner hold: no file under platform/migrations/ is created or modified by this change)
produced_by: exec-suvarna
produced_on: 2026-10-02
for: PR #2851 (ga_structural argala) and design note DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md (#2850)
tests: platform/python-sidecar/tests/test_argala_migration_intent_sql.py executes both SQL blocks below against a disposable local Postgres
changelog:
  - "1.0 (2026-10-02): first version; replaces the pending edits to the 1219 draft and the 1221 split, held for the owner."
---

# Migration 1219 / 1221: intended text (held)

## 1. Status

By the owner hold, no migration file is created or modified. The 1219 draft already on branch `suvarna/land/TI-argala-l1-001` (commit `9c038a663`) stays exactly as pushed; it is **superseded by block A below** once the owner answers. Block B is the integrity conjunct, split out as SS decided (it was part of 1219 in that draft). When the owner relays the answer, block A becomes the text of 1219 (re-check the number is free), block B becomes the next free number (allocated: 1221), each applied with the normal runner and verified after (CLAUDE.md N.4).

## 2. What block A changes against the pushed 1219 draft

1. The integrity conjunct (a29) leaves 1219 (it is block B).
2. **No floor is touched** (`target_floor` is in the column list of the live trigger `nirmana_registry_receipt_invalidation`; floors are re-declared from achieved counts after S-L1 in one registry migration).
3. `ga_strength.count_sql` is narrowed so that no row is counted by two assets: it drops the 420 `bhava_bala_*` rows, the 35 `vimsopaka_bala_per_graha` rows and the 35 `graha_saptavargaja_bala_component` rows, which `ga_structural` emits and owns. Guard: md5 of the live text.
4. `ga_condition.count_sql`: only the stale `graha_yuddha` clause is removed (`ga_structural` emits and owns `graha_yuddha`; the clause double-counts it on charts that have it). The earlier draft cut it to the composite table (45); the independent review points out that this would hide the 2,925 `chart_facts` rows it owns (CLAUDE.md N.4, cockpit truth). **For SS:** Q-L1-04's text says "`count_sql` on the primary table"; I followed the review and left the multi-table count shape to I-30. One line to change if SS prefers the ruling's text.
5. Ownership: the five panchanga categories (216 rows) are **dropped from `ga_structural`** (it never emits them) and owned by `ga_panchanga`; the three categories a writer emits with no ownership row (`ashtakavarga_bindu_contributor`; `graha_degree_flags`, `nakshatra_exchange`) and the three inert `esoteric_point_trisphuta` / `chatushphuta` / `panchasphuta` are added. Derivation: `derive_q04_ownership.py` (predicate and live data) and `derive_writer_categories.py` (writer source), outside the repo in `/Users/Dev/suvarna-evidence/TrackI/argala_l1/`. After block A every live category (all charts) and every category a `ga_*` chart_facts writer emits has an owner (the 62 other writer-source hits are reads, GA3-overlap lists and `chart_divisionals` categories).

The live trigger `l1_data_plane_mutation_guard` refuses an L1 write to a `chart_facts` category with no ownership row for that asset, so block A is a hard prerequisite of the S-L1 `ga_structural` rebuild.

## 3. Canonical chart, chart_facts-based counts, before to after block A

  asset                 before    after    change
  ga_structural        102,037  106,707    +4,670  (+4,816 the 12 unowned categories, +70 vimsopaka_bala_per_graha
                                                     and graha_saptavargaja_bala_component, -216 the five panchanga
                                                     categories; equals its 106,707 build record)
  ga_strength           14,141   13,651      -490  (-420 bhava_bala_*, -70 vimsopaka / saptavarga component)
  ga_condition           2,970    2,970         0  (only the graha_yuddha clause leaves its predicate: 0 canonical rows)
  ga_panchanga             437      437         0  (the five categories were already inside its predicate)
  ga_nakshatra 2,847; ga_positions 1,205; ga_sade_sati 6,287; ga_sensitive 8,775; ga_sensitive_degree 335;
  ga_ayurdaya 130: unchanged.
The narrowed ga_strength predicate was also run as SQL against the live canonical chart (read-only): 13,651.

Before block A the double claims on the canonical chart are the 420 `bhava_bala_*` rows (`ga_structural` by ownership, `ga_strength` by predicate) and the 216 panchanga rows (`ga_structural` by ownership, `ga_panchanga` by predicate): 636 rows. After it, none (`count_claims_before_after.py`). `count_sql` is not in the trigger's column list, so no freshness is staled; it is in the Nirmana registry-contract fingerprint, so the frozen manifests of `ga_strength` and `ga_condition` go to `evidence_refresh_required` (design note, section 5).

## 4. Application order

- Block A applies before the S-L1 launch (it is a prerequisite of it).
- Block B ((a29), `integrity_check_sql`) applies as a **named step of S-L1, immediately before the `ga_structural` launch, with or after the writer deploy**: (a29) reads red on live canonical data until S-L1 writes the NULL cells; `UPDATE OF integrity_check_sql` stales `ga_structural`'s freshness (trigger 596); and after (a29) a `ga_structural` rebuild by the OLD writer image fails its post-write integrity check, so block B must never precede the writer deploy.

## 5. Block A: intended text of 1219

```sql 1219-intent
-- 1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql  (INTENDED TEXT; see MIGRATION_1219_1221_INTENT_v1_0.md)
--
-- DRAFT, NOT APPLIED, NOT A FILE UNDER platform/migrations/ (owner hold). Suvarna Track I (SS decision N-61, 2026-10-01, approved with changes
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
-- Three parts, in order. The integrity conjunct (a29) is NOT here: it is migration 1221 (own file, applied
-- as a named step immediately before the S-L1 launch, with or after the writer deploy). Floors are NOT touched here: target_floor is in the
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
--        ga_structural's (it is the emitter).
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
--   3. asset_output_digest_specs. ga_structural has ONE active spec (migration 914, sha b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6,
--      81 categories); a category outside its where_in is not digested, so a change to the new rows would
--      not move the output digest. This retires it and inserts the same spec plus argala_graha_natal (82).
--      spec_sha256 = canonical_digest (pipeline.orchestrator.provenance), which reproduces 914's stored
--      sha exactly. Retired, not deleted (609 / 1086 precedent).
--
-- Post-apply verification (each should return the stated value):
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category = 'argala_graha_natal' AND owning_asset_id = 'ga_structural';            -- 1
--   SELECT count(*) FROM fact_category_ownership
--    WHERE fact_category IN ('bhadra_flag', 'panchaka_flag') AND owning_asset_id = 'ga_structural'; -- 0
--   SELECT spec_sha256 FROM asset_output_digest_specs
--    WHERE asset_id = 'ga_structural' AND retired_at IS NULL;                                     -- d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620
--   SELECT count_sql LIKE '%house_bhava_bala_%' AND count_sql NOT LIKE '%saptavargaja%'
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
      OR fact_category LIKE 'ashtakavarga_%'
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
```

## 6. Block B: intended text of 1221

```sql 1221-intent
-- 1221_nirmana_l1_ga_structural_integrity_a29_argala_null.sql  (INTENDED TEXT; see MIGRATION_1219_1221_INTENT_v1_0.md)
--
-- DRAFT, NOT APPLIED, NOT A FILE UNDER platform/migrations/ (owner hold). Suvarna Track I (SS decision N-61; split out of migration 1219 by SS, 2026-10-02).
-- Design note 00_ARCHITECTURE/briefs/suvarna/exec/DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md, sections 1 and 5.
-- Re-check at arm time that 1221 is still free. Transaction ownership belongs to platform/scripts/migrate.ts:
-- no BEGIN/COMMIT here. Verify after applying (CLAUDE.md N.4).
--
-- WHEN TO APPLY: as a NAMED STEP of the S-L1 stage, IMMEDIATELY BEFORE the ga_structural rebuild launches,
-- not with 1219. Reasons (design note, section 5):
--   * (a29) reads RED on the live canonical chart from the moment it applies until S-L1 writes the NULL
--     cells (every empty-source argala cell is stored 1.0 today). The integrity_check_sql is read at
--     build time (asset_runner post-write gate), by the Nirmana `integrity_verified` acceptance detector
--     (definitions.ts), and is part of the registry-contract fingerprint; nothing else gates on the verdict,
--     but a standing red on ga_structural for days is a false alarm with no purpose.
--   * UPDATE OF integrity_check_sql is in the column list of the live trigger
--     nirmana_registry_receipt_invalidation (migration 596): it marks ga_structural's asset_freshness
--     'stale' (reason registry_changed), so ga_structural's direct dependents fail DEP-ASSERT
--     ('ga_structural(receipt:stale)') until the next governed ga_structural receipt. Applied immediately
--     before S-L1 that costs nothing, because S-L1 rebuilds ga_structural anyway.
--
-- ORDERING HAZARD (independent review): after (a29), a ga_structural rebuild by the OLD writer image (which still
-- writes 1.0 on empty cells) fails the post-write integrity check. 1221 therefore applies only WITH or AFTER the writer
-- deploy, never before it.
--
-- WHAT IT DOES: adds ONE conjunct, (a29) [SS N-61, AR-3; CLAUDE.md N.8], to ga_structural's
-- integrity_check_sql: for every argala-offset cell of argala_natal_matrix, NULL with fact_value_text
-- 'no_occupant' exactly when the source sign holds no graha, a non-NULL score with no text when it does.
-- Conjunct (e27) is vacuously true on a NULL score (NULL <> x is not true), so before this a NULL on an
-- occupied cell, or a stale 1.0 on an empty one, passed. Scoped to the canonical chart (migration 904's
-- disclosed tradeoff: the other charts still hold pre-AR-3 rows until they rebuild).
--
-- HOW: a guarded replace() of the live text at its single `AS integrity_passed` anchor, not a 200 KB
-- re-statement of migration 904's text. It refuses unless (g28) is present and the anchor occurs exactly
-- once, is a no-op when (a29) is already there, and asserts the result afterwards.
--
-- Tests: platform/python-sidecar/tests/test_argala_migration_intent_sql.py runs this text and the conjunct
-- against a disposable local Postgres: six mutants are killed, including the one (e27) passes.
--
-- Post-apply verification:
--   SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry WHERE asset_id = 'ga_structural';  -- t

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
```
