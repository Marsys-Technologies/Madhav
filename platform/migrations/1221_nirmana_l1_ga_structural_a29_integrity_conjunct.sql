-- 1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql
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
-- against a disposable local Postgres: six mutants are killed, including the one (e27) passes.
--
-- Post-apply verification:
--   SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry WHERE asset_id = 'ga_structural';  -- t
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
