-- 1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql  (the a29 conjunct AND the ga_structural output-digest spec swap)
--
-- Suvarna Track I (SS decision N-61; split out of migration 1219 by SS, 2026-10-02).
-- Design note 00_ARCHITECTURE/briefs/suvarna/exec/DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md, sections 1 and 5;
-- explanation: 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1221_A29_INTENT_v1_0.md.
--
-- HELD. This file lives in its own draft PR (suvarna/land/TI-mig-1221-a29-001), separate from the PR that carries the
-- ga_structural argala writer and migration 1219 (#2851), and it merges ONLY in the S-L1 window: after #2851's writer
-- image is deployed and verified (LC-1 digest equality), immediately before the ga_structural launch. Merge = apply:
-- the migrate job runs at the next deploy, before that deploy's images roll.
--
-- SERVING EFFECT AT APPLY: ga_structural freshness stale on every chart (a29 UPDATE OF integrity_check_sql) AND its
-- receipts read receipt_spec_retired until rebuilt; degraded set at W1 = ga_structural (and with 1222/1223/1226:
-- ga_vargas, ga_dashas, ga_yoga); all rebuilt in the window.
--
-- TWO PARTS, in order: (1) the a29 conjunct on ga_structural's integrity_check_sql; (2) the ga_structural output-digest
-- spec swap (retire the one active spec, migration 914, 81 categories, sha b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6; insert the
-- same spec plus argala_graha_natal, 82 categories sorted and unique, sha d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620 = canonical_digest,
-- which reproduces 914's stored sha exactly; retired, not deleted: 609 / 1086 precedent). The swap used to be part 3 of
-- migration 1219; it moved here because served_generation.ts (spec_active) reads a receipt whose
-- output_digest_spec_sha256 is not an ACTIVE spec as receipt_spec_retired, so retiring the spec from the integration's
-- deploy would leave ga_structural unresolved for serving until rebuilt. a29 already stales ga_structural at this step
-- (trigger nirmana_registry_receipt_invalidation fires on UPDATE OF integrity_check_sql), so the swap here adds nothing
-- to the degraded set.
--
-- THE GAP BEFORE THIS FILE (integration deployed: new argala writer live, 1219 applied, the OLD 81-category spec still
-- ACTIVE, W1 not yet reached) and its direction. Nothing builds ga_structural in that gap. If something did:
-- asset_runner.py computes the output digest by compute_output_digest(), which uses load_output_digest_spec = the ACTIVE
-- row (retired_at IS NULL) and filters each component by where_in (fact_category = ANY(...)); the old spec's where_in
-- does NOT contain argala_graha_natal. So the build SUCCEEDS; the receipt records the OLD spec sha and an output digest
-- that does NOT cover the argala rows: a SILENT coverage gap, not a loud failure (nothing compares written categories
-- with the spec). After this file applies, that receipt reads receipt_spec_retired anyway. The remedy is the same as for
-- every other W1 receipt: the rebuild in the S-L1 window, which writes the receipt against the new 82-category spec.
--
-- This is a real migration, applied through the normal runner: platform/scripts/migrate.ts owns the transaction,
-- so there is no BEGIN/COMMIT here. It must be VERIFIED by production structure after it applies (the post-apply
-- query below; CLAUDE.md N.4, Trap 103: never trust the deploy log, a run that reports success can still have
-- done nothing).
--
-- ORDERING (hard rule). 1221 must be applied as a NAMED STEP of the S-L1 stage, IMMEDIATELY BEFORE the ga_structural
-- launch, and NEVER BEFORE the ga_structural writer deploy. It is not applied with 1219 and it is not applied
-- independently of the S-L1 sequence: 1219 may apply on its own; 1221 may not.
--
-- RUNNER CONSEQUENCE (migration-guard review): platform/scripts/migrate.ts applies EVERY unapplied file on the next
-- deploy, and every deploy job needs the migrate job, so a merged 1221 applies BEFORE that deploy's images roll.
-- The runner itself therefore cannot enforce the rule above: this file must not merge in the same deploy as the
-- ga_structural writer change, and not before that writer image is live and verified (LC-1 digest equality). Merge it
-- only at the S-L1 step, in a deploy after the writer deploy has been confirmed.
--
-- 0 ACTIVE RUNS AT APPLY: before merging, and again at apply, no build run may be in flight for ga_structural (an
-- in-flight old-image build would hit the post-write integrity check). Read-only check, expected 0:
--   SELECT count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--    WHERE a.asset_id = 'ga_structural' AND r.state NOT IN ('completed', 'failed', 'stopped');
--
-- OTHER CHARTS: (a29) is scoped to the canonical chart, but the post-write integrity gate runs for every chart's
-- ga_structural build. From apply until the canonical S-L1 rebuild has written the NULL cells, no ga_structural build
-- for ANY chart may run (a build for another chart would evaluate (a29) against the canonical rows and fail its gate).
--
-- LOCK TIMEOUT. The first statement is SET LOCAL lock_timeout = '5s' (migration 1218 pattern): a blocked migrate
-- job must fail fast, not hang a shared deploy.
--
-- WHY THE ORDERING: 1221 is a named step of the S-L1 stage, immediately before the ga_structural rebuild launches,
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
--   * The spec swap sits in the same file, so the window during which ga_structural's receipts read receipt_spec_retired
--     is exactly the window during which a29 keeps it stale: both end with the S-L1 rebuild.
--
-- ORDERING HAZARD (independent review): after (a29), a ga_structural rebuild by the OLD writer image (which still
-- writes 1.0 on empty cells) fails the post-write integrity check. 1221 therefore NEVER applies before the ga_structural
-- writer deploy; it applies after it, immediately before the S-L1 launch.
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
-- Tests: platform/python-sidecar/tests/test_argala_migration_1221_sql.py runs this text and the conjunct
-- against a disposable local Postgres: six mutants are killed, including the one (e27) passes; the swap reproduces
-- both shas with the real canonical_digest and loads through the real output_digest._validate_spec; the combined effect
-- (freshness stale AND spec retired) is proved against the real trigger function body.
--
-- Post-apply verification:
--   SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry WHERE asset_id = 'ga_structural';  -- t
--   SELECT spec_sha256 FROM asset_output_digest_specs
--    WHERE asset_id = 'ga_structural' AND retired_at IS NULL;   -- d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620
--   SELECT count(*) FROM asset_output_digest_specs
--    WHERE asset_id = 'ga_structural' AND retired_at IS NOT NULL;   -- >= 1 (b2490646... retired, not deleted)
--   SELECT count(*) FROM asset_freshness WHERE asset_id = 'ga_structural' AND freshness_state = 'stale';   -- every ga_structural row
--   Position proves the text changed, not that the whole composite parses and reads as intended: also run the
--   full integrity_check_sql read-only against the canonical chart. Expected integrity_passed = false (a29 red)
--   until the S-L1 ga_structural rebuild writes the NULL cells; true after it.

SET LOCAL lock_timeout = '5s';

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

-- ── 2. ga_structural output-digest spec (after the a29 conjunct) ─────────────────────────────
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
