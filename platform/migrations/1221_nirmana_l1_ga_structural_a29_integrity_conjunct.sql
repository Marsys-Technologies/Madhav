-- 1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql  (the a29 conjunct, two corrected integrity conjuncts (bb) and (c9), AND the ga_structural output-digest spec swap)
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
-- LIVE READ (suvarna_reader, read-only, 2026-10-02): the ONLY non-internal trigger on asset_registry, asset_freshness,
-- asset_output_digest_specs, asset_provenance_receipts and fact_category_ownership is nirmana_registry_receipt_invalidation
-- on asset_registry; no rules (pg_rules) on them; row-level security off on all five; amjis_app (the runner role and owner)
-- holds INSERT/UPDATE/DELETE on fact_category_ownership, asset_output_digest_specs and asset_registry.
--
-- FINGERPRINT EFFECT (campaign control, not a serving state): integrity_check_sql is part of the Nirmana registry-contract fingerprint, so
-- ga_structural's frozen manifest goes to evidence_refresh_required, and this file merges immediately before the ga_structural launch; accepted W1/W2 evidence bound to the old fingerprint reads as not current, and lane C receipt validation refuses
-- a frozen manifest that no longer matches the live registry. The S-L1 runbook must therefore re-bind evidence (a refresh
-- of the affected frozen manifests) between this apply and that launch (and again after the rebuild).
--
-- REASON CODES: while a29's stale holds, served_generation.ts partitionDefect reports receipt_not_fresh first (it is checked
-- before the spec predicate); receipt_spec_retired is the reason once a receipt is fresh again but still names the retired
-- spec. Both are unresolved for serving; the behaviour is the same.
--
-- TWO PARTS, in order: (1) the a29 conjunct AND the (bb) / (c9) corrections on ga_structural's integrity_check_sql, one UPDATE; (2) the ga_structural output-digest
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
-- THREE CORRECTIONS RIDE WITH a29 (rehearsal findings and the #2969 review, 2026-10-02): (bb) and (c9) were found by the data-plane
-- rehearsal of a fresh ga_structural build on an anchor-matched chart: two TABLE-WIDE conjuncts of the live check that read FALSE
-- on a correct build. Both are check defects, not writer defects (evidence:
-- 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1221_A29_INTENT_v1_0.md sections 7 and 8):
--   * (bb) aspect_tajik orb_strength: the check recomputed 1 - orb_deg/deeptamsa_sum_deg from the STORED orb_deg, which the writer
--     rounds to 4 dp (round(orb, 4)), and demanded exact equality with the writer's value, which rounds the same quotient
--     computed from the UNROUNDED orb (ga_structural_writer.py, _build_aspect_rows: orb_strength = round(max(0.0, 1.0 - orb /
--     deeptamsa_sum), 4)). A quotient within 5e-5 of a 4 dp rounding boundary lands one unit (0.0001) apart: e.g. orb 13.4585
--     with deeptamsa_sum 22.0 stores 0.3882, the check expects 0.3883. Corrected to a tolerance of 0.0001 (one unit in the 4th
--     decimal; the worst-case disagreement of the two roundings is 16/3 * 1e-5 = 5.333e-5 < 1e-4); yamaya (1.0) and manaau (0.1)
--     stay exact.
--   * (c9) karakatva composite_strength domain: the check listed seven values, but the writer computes (karaka_strength +
--     house_strength) / 2 with karaka_strength in {1, 0.875, 0.5, 0.25} and house_strength in {1, 0.75, 0.5} (12 combinations =
--     9 distinct values, plus the 0.5 no-karaka fallback, already in the set). It omitted 0.6875 (own sign, house not kendra /
--     5 / 9) and 0.875 (exalted, house 5 or 9): a false RED on any chart that lands on them. Corrected to the nine values.
--   * (uu2) chandra_bala_natal_baseline classification: the check re-derived the birth Moon sign from
--     panchanga_nakshatra_moon.number as ((nak - 1) * 4) / 9 + 1 (a nakshatra that straddles two signs gets its FIRST sign).
--     PR #2969 (ga_panchanga) makes the writer READ the Moon sign from the ga_positions fact graha_position | MOON | sign of the
--     same ayanamsha instead (CLAUDE.md N.5), so after its rebuild the old re-derivation would call a correct baseline wrong.
--     Corrected to compare against that same position fact, selected as #2969's _read_birth_moon_signs selects it (latest
--     computed_at, then build_id; one generation per chart and ayanamsha in steady state). NO OR of the two derivations (it
--     would bless a baseline computed from the wrong sign). It is the ONLY live conjunct of ga_structural, and of any asset's
--     integrity text, that carries the nakshatra-to-sign formula (the 33 copies in migrations 790-819, 840, 841 and 904 are
--     historical restatements of this one text); (d) panchaka_flag and (v) tara_bala read the nakshatra NUMBER, which #2969 does
--     not change.
-- (uu2) is table-wide (not canonical-scoped) and stays TRUE for the other two charts, because on every ayanamsha their position-fact
-- and nakshatra-derived Moon signs agree. Measured (suvarna_reader, 2026-10-02): 9 of the 180 chandra_bala_natal_baseline rows
-- differ from the nakshatra-derived baseline, all of them the canonical chart's surya_siddhanta_classical rows (position fact
-- Pisces, nakshatra-derived Aquarius): the rows #2969 rewrites. So the corrected (uu2) is RED on those stale canonical rows from this
-- apply until the S-L1 ga_panchanga rebuild writes them, and TRUE after it: the same shape as (a29). ga_structural depends_on
-- ga_panchanga, so that rebuild precedes the ga_structural post-write gate; if the order were violated ga_structural would end
-- `error` on (uu2).
-- (bb) and (c9) are not chart-scoped either, and neither is RED on production today (0/76 and 0/450 violations on the three charts
-- that hold the rows); both would turn RED on the next build that lands on a tie or on one of the two omitted combinations. Each fix
-- is guarded like a29: each old conjunct must occur exactly once (refuse otherwise), and is a no-op when the correction is there.
-- Live text read 2026-10-02 (suvarna_reader): length 203539, md5 bb9803524a61427e7f4f179a59911e33, no (a29), all three old
-- conjuncts once.
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
-- WHAT IT DOES: (i) adds ONE conjunct, (a29) [SS N-61, AR-3; CLAUDE.md N.8], to ga_structural's
-- integrity_check_sql: for every argala-offset cell of argala_natal_matrix, NULL with fact_value_text
-- 'no_occupant' exactly when the source sign holds no graha, a non-NULL score with no text when it does.
-- Conjunct (e27) is vacuously true on a NULL score (NULL <> x is not true), so before this a NULL on an
-- occupied cell, or a stale 1.0 on an empty one, passed. Scoped to the canonical chart (migration 904's
-- disclosed tradeoff: the other charts still hold pre-AR-3 rows until they rebuild). (ii) corrects conjunct
-- (bb) (aspect_tajik orb_strength: tolerance 0.0001), conjunct (c9) (karakatva composite_strength: nine-value
-- domain), and (uu2) (chandra_bala birth Moon sign from the position fact), see THREE CORRECTIONS above.
--
-- HOW: guarded replace() of the live text, not a 200 KB re-statement of migration 904's text, all in ONE UPDATE
-- (so the registry trigger fires once). (a29) goes in at the single `AS integrity_passed` anchor: it refuses unless
-- (g28) is present and the anchor occurs exactly once. (bb), (c9) and (uu2) each replace the live conjunct text read on
-- 2026-10-02 (comment plus SQL, verbatim): it refuses unless that text occurs exactly once. Each of the four is skipped
-- when its marker is already there; the whole is a no-op when nothing changes; the result is asserted afterwards.
-- Live text this was written against: md5 bb9803524a61427e7f4f179a59911e33 (length 203539); the text after this file is md5
-- c56f9e12b2002269eb5f27a7abc42105 (length 207959), verified by applying this file to that real live text on a disposable Postgres.
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
--   SELECT position('Migration 1221 (bb tolerance)' in integrity_check_sql) > 0, position('Migration 1221 (c9 domain)' in integrity_check_sql) > 0,
--          position('Migration 1221 (uu2 moon sign)' in integrity_check_sql) > 0
--     FROM asset_registry WHERE asset_id = 'ga_structural';   -- t, t, t
--   SELECT md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_structural';
--     -- c56f9e12b2002269eb5f27a7abc42105, 207959 (holds only if the live text at apply was md5 bb9803524a61427e7f4f179a59911e33;
--     -- if another change to this text landed first, the guards above govern and the md5 differs by exactly that change)
--   Position proves the text changed, not that the whole composite parses and reads as intended: also run the
--   full integrity_check_sql read-only against the canonical chart. Expected integrity_passed = false (a29 red, and (uu2) red on
--   the stale canonical surya_siddhanta chandra_bala rows) until the S-L1 rebuilds (ga_panchanga, then ga_structural) write
--   them; true after it.

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
  -- (bb) aspect_tajik orb_strength: the live conjunct (read 2026-10-02) and its corrected text.
  old_bb constant text := $ob$  -- (bb) value_jsonb.orb_strength must equal the writer's own per-type formula: 1.0 for yamaya
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
$ob$;
  new_bb constant text := $nb$  -- (bb) value_jsonb.orb_strength must equal the writer's own per-type formula: 1.0 for yamaya
  -- (exact-degree case); 0.1 for manaau (the fixed "denial" weight); for ithasala/eesarpha,
  -- round(greatest(0, 1 - orb_deg/deeptamsa_sum_deg), 4) -- a genuine cross-field re-derivation
  -- combining two already-stored fields into a third, not a bare restatement. Migration 1221 (bb tolerance):
  -- the stored orb_deg is itself rounded to 4 dp while the writer rounds the quotient computed from the
  -- UNROUNDED orb, so for ithasala/eesarpha the two can differ by one unit in the 4th decimal at a rounding
  -- boundary (worst case 5e-5 + 5e-5/14 < 1e-4); compared with a tolerance of 0.0001. yamaya (1.0) and
  -- manaau (0.1) stay exact.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND abs((fact_value_jsonb->>'orb_strength')::numeric -
        CASE fact_key
          WHEN 'yamaya' THEN 1.0
          WHEN 'manaau' THEN 0.1
          ELSE GREATEST(0.0, 1.0 -
            (fact_value_jsonb->>'orb_deg')::numeric / (fact_value_jsonb->>'deeptamsa_sum_deg')::numeric)
        END) > CASE WHEN fact_key IN ('yamaya', 'manaau') THEN 0 ELSE 0.0001 END
  )
$nb$;
  -- (c9) karakatva composite_strength domain: the live conjunct and its corrected text.
  old_c9 constant text := $oc$  -- (c9) composite_strength domain: must be one of the seven achievable values given the
  -- formula's four dignity tiers x three house tiers. 0/450 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karakatva_strength_per_significance' AND fact_key = 'composite_strength'
      AND fact_value_num NOT IN (0.375, 0.5, 0.625, 0.75, 0.8125, 0.9375, 1.0)
  )
$oc$;
  new_c9 constant text := $nc$  -- (c9) composite_strength domain: must be one of the nine achievable values given the formula's
  -- four karaka-dignity tiers {1, 0.875, 0.5, 0.25} x three house tiers {1, 0.75, 0.5}: (k + h) / 2 =
  -- 0.375, 0.5, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375, 1.0 (the writer's no-karaka fallback 0.5 is in
  -- the set). Migration 1221 (c9 domain): the list had seven values and omitted 0.6875 (own sign, house not
  -- kendra/5/9) and 0.875 (exalted, house 5 or 9). Value-for-value derivation is (d9) below.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karakatva_strength_per_significance' AND fact_key = 'composite_strength'
      AND fact_value_num NOT IN (0.375, 0.5, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375, 1.0)
  )
$nc$;
  -- (uu2) chandra_bala baseline classification: the live conjunct and its corrected text (Moon sign from the position fact).
  old_uu2 constant text := $ou$  -- (uu2) chandra_bala_natal_baseline.classification must equal the full re-derivation of the
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
$ou$;
  new_uu2 constant text := $nu$  -- (uu2) chandra_bala_natal_baseline.classification must equal the full re-derivation of the
  -- writer's own formula: transit sign_id is parsed from fact_subject's
  -- "TRANSIT_SIGN_{SANSKRIT_NAME}" suffix via the standard Sanskrit zodiac name table;
  -- the birth Moon sign is the L1 graha_position MOON `sign` fact of the SAME chart and ayanamsha
  -- (CLAUDE.md N.5: the authority, referenced and never re-derived), mapped from its English name; when
  -- several generations of that fact exist the latest one is taken (computed_at, then build_id, both
  -- descending), exactly as ga_panchanga's _read_birth_moon_signs selects it. Per D-L1-55, a +120
  -- (10*12) margin is added before the modulo, guaranteeing a positive dividend without changing the
  -- result mod 12. Migration 1221 (uu2 moon sign): the birth sign used to be re-derived from
  -- panchanga_nakshatra_moon.number as ((nak - 1) * 4) / 9 + 1, which gives a nakshatra that straddles
  -- two signs its FIRST sign (Purva Bhadrapada: Aquarius, although its fourth pada is in Pisces); the writer now
  -- reads the position fact, so the old re-derivation would call a correct baseline wrong. A baseline
  -- computed from any sign other than the position fact's is still FALSE (no OR of the two derivations).
  -- A chart with no position fact, or a sign name outside the twelve, is not checked here, as before.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    CROSS JOIN LATERAL (
      SELECT p.fact_value_text AS moon_sign
      FROM chart_facts p
      WHERE p.chart_id = a.chart_id AND p.ayanamsha_id = a.ayanamsha_id
        AND p.fact_category = 'graha_position' AND p.fact_subject = 'MOON' AND p.fact_key = 'sign'
      ORDER BY p.computed_at DESC, p.build_id DESC
      LIMIT 1
    ) mp
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
              - (CASE mp.moon_sign
                WHEN 'Aries' THEN 1 WHEN 'Taurus' THEN 2 WHEN 'Gemini' THEN 3 WHEN 'Cancer' THEN 4
                WHEN 'Leo' THEN 5 WHEN 'Virgo' THEN 6 WHEN 'Libra' THEN 7 WHEN 'Scorpio' THEN 8
                WHEN 'Sagittarius' THEN 9 WHEN 'Capricorn' THEN 10 WHEN 'Aquarius' THEN 11 WHEN 'Pisces' THEN 12
                ELSE NULL END)
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
$nu$;
  live text;
  patched text;
  n integer;
BEGIN
  SELECT integrity_check_sql INTO live FROM asset_registry WHERE asset_id = 'ga_structural' FOR UPDATE;
  IF live IS NULL THEN
    RAISE EXCEPTION 'ga_structural integrity patch refused: no integrity_check_sql';
  END IF;
  patched := live;

  -- (a29): add the conjunct at the single anchor (skipped when already there).
  IF position('(a29)' in patched) = 0 THEN
    IF position('(g28)' in patched) = 0 THEN
      RAISE EXCEPTION 'ga_structural integrity patch refused: live text lacks conjunct (g28)';
    END IF;
    IF (length(patched) - length(replace(patched, anchor, ''))) <> length(anchor) THEN
      RAISE EXCEPTION 'ga_structural integrity patch refused: anchor is not unique in the live text';
    END IF;
    patched := replace(patched, anchor, rtrim(conjunct, E'\n') || anchor);
  END IF;

  -- (bb): replace the exact-equality conjunct with the 0.0001-tolerance text (skipped when already corrected).
  IF position('Migration 1221 (bb tolerance)' in patched) = 0 THEN
    IF (length(patched) - length(replace(patched, old_bb, ''))) <> length(old_bb) THEN
      RAISE EXCEPTION 'ga_structural integrity patch refused: live conjunct (bb) is not present exactly once';
    END IF;
    patched := replace(patched, old_bb, new_bb);
  END IF;

  -- (c9): replace the seven-value domain with the nine-value domain (skipped when already corrected).
  IF position('Migration 1221 (c9 domain)' in patched) = 0 THEN
    IF (length(patched) - length(replace(patched, old_c9, ''))) <> length(old_c9) THEN
      RAISE EXCEPTION 'ga_structural integrity patch refused: live conjunct (c9) is not present exactly once';
    END IF;
    patched := replace(patched, old_c9, new_c9);
  END IF;

  -- (uu2): replace the nakshatra-derived birth Moon sign with the position fact's sign (skipped when already corrected).
  IF position('Migration 1221 (uu2 moon sign)' in patched) = 0 THEN
    IF (length(patched) - length(replace(patched, old_uu2, ''))) <> length(old_uu2) THEN
      RAISE EXCEPTION 'ga_structural integrity patch refused: live conjunct (uu2) is not present exactly once';
    END IF;
    patched := replace(patched, old_uu2, new_uu2);
  END IF;

  IF patched = live THEN
    RETURN;   -- already applied (idempotent re-run)
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = patched
   WHERE asset_id = 'ga_structural';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 OR NOT EXISTS (SELECT 1 FROM asset_registry
                            WHERE asset_id = 'ga_structural'
                              AND position('(a29)' in integrity_check_sql) > 0
                              AND position('(g28)' in integrity_check_sql) > 0
                              AND position('Migration 1221 (bb tolerance)' in integrity_check_sql) > 0
                              AND position('Migration 1221 (c9 domain)' in integrity_check_sql) > 0
                              AND position('Migration 1221 (uu2 moon sign)' in integrity_check_sql) > 0
                              AND position(old_bb in integrity_check_sql) = 0
                              AND position(old_c9 in integrity_check_sql) = 0
                              AND position(old_uu2 in integrity_check_sql) = 0) THEN
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
