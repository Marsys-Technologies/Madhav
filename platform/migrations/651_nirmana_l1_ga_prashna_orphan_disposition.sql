-- 651_nirmana_l1_ga_prashna_orphan_disposition.sql
--
-- NIRMĀṆA v2.1 · L1 Gaṇita · C13 disposition for `ga_prashna_judgment`'s no-FK
-- `chart_id` (F-E21/F-E22, L1_W1_ANALYSIS_BATCH_E.md; action recorded in
-- L1_W2_DECIDE_v1_0.md §4: "re-ground or remove the 5 orphaned rows, and
-- disambiguate the tool naming"). Naming disambiguation is separate,
-- non-DB, follow-up work -- this migration is the DB-level disposition only.
--
-- THE FINDING: 5 rows in ga_prashna_judgment (one prashna cast, 5 ayanamsha
-- variants, chart_id b35046d8-4131-4e0e-8548-3136678fc2bb) cite a chart_id
-- that does not exist in `charts` -- confirmed live before writing this
-- migration, not assumed. This predates the R-1 native ruling (dormant
-- facility) and is unrelated to it: R-1 says "don't build out or pad the
-- count" for the CANONICAL chart; it says nothing about tolerating dead rows
-- pointing at a chart that was never persisted (or was deleted) after a
-- manual test cast via POST /api/compute/prashna/cast on 2026-06-18.
--
-- WHY REMOVE, NOT RE-GROUND: re-grounding requires a real chart to attach the
-- judgment to. None exists -- `charts` has no row for this id, live or
-- historical, so there is nothing to re-ground to. Fabricating a
-- replacement chart_id to "fix" the join would be exactly the fabricated-
-- computation the campaign's hard floor forbids (§B.10) -- it would assert a
-- cast that never happened against a chart it never happened for.
--
-- WHY A REAL FK, NOT DOCUMENTED ORPHAN-TOLERANCE (C13's other permitted
-- disposition): unlike phala_anchors.signal_id (migration 683), where a
-- generation pointer legitimately survives its own rebuild and re-aiming it
-- would assert a derivation that never happened, ga_prashna_judgment.chart_id
-- has no such lifecycle -- a judgment's chart either exists or the judgment
-- is meaningless. There is no scenario where this table SHOULD hold a row
-- citing a nonexistent chart. A real FK is the honest disposition, and it
-- converts a class of defect that was silent (nothing detected these 5 rows
-- until a W1 read-only analysis found them by hand) into one Postgres itself
-- refuses to create again.
--
-- ON DELETE CASCADE mirrors the existing chart-scoped-child convention this
-- schema already uses (e.g. chart_fact_identity_fact_id_fkey): if a chart is
-- ever deleted, its prashna judgments are not orphans-in-waiting, they are
-- gone with it -- exactly the property this migration is restoring for the
-- data that predates it.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

-- ---------------------------------------------------------------------------
-- 1. Remove the confirmed-unregroundable rows, and only those rows.
-- ---------------------------------------------------------------------------
-- Guarded on the exact chart_id this migration was written against, not a
-- blanket "chart_id not in charts" delete -- if live data has drifted since
-- this was authored (more, fewer, or different orphans), this migration must
-- fail loudly rather than silently deleting rows nobody reviewed.
DO $$
DECLARE
  deleted_count int;
BEGIN
  IF EXISTS (SELECT 1 FROM charts WHERE id = 'b35046d8-4131-4e0e-8548-3136678fc2bb') THEN
    RAISE EXCEPTION
      'migration 651: chart b35046d8-4131-4e0e-8548-3136678fc2bb now EXISTS in charts -- '
      'the F-E21/F-E22 orphan finding no longer holds. Re-review before deleting.';
  END IF;

  DELETE FROM ga_prashna_judgment
   WHERE chart_id = 'b35046d8-4131-4e0e-8548-3136678fc2bb';
  GET DIAGNOSTICS deleted_count = ROW_COUNT;

  IF deleted_count <> 5 THEN
    RAISE EXCEPTION
      'migration 651: expected to delete exactly 5 orphaned ga_prashna_judgment rows '
      '(the F-E21/F-E22 measured count) but deleted %; live data has drifted from what '
      'this migration was written against -- refusing to proceed blind.', deleted_count;
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. Any OTHER orphaned chart_id must not survive either. Same guard style as
--    part 1's exact-count check, generalised: assert zero remain before the
--    FK is added, so the FK creation below cannot silently fail to protect
--    data this migration did not know to name.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  remaining_orphans int;
BEGIN
  SELECT count(*) INTO remaining_orphans
    FROM ga_prashna_judgment j
   WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = j.chart_id);

  IF remaining_orphans > 0 THEN
    RAISE EXCEPTION
      'migration 651: % additional orphaned ga_prashna_judgment row(s) exist beyond the '
      'named F-E21/F-E22 set -- this migration only accounted for one chart_id; '
      'investigate before adding the FK.', remaining_orphans;
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3. The real disposition: an FK that makes this defect class impossible.
-- ---------------------------------------------------------------------------
ALTER TABLE ga_prashna_judgment
  ADD CONSTRAINT ga_prashna_judgment_chart_id_fkey
  FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;

COMMENT ON CONSTRAINT ga_prashna_judgment_chart_id_fkey ON ga_prashna_judgment IS
  'C13 disposition (migration 651, F-E21/F-E22): a prashna judgment with no backing chart is '
  'meaningless, not a tolerated lifecycle state (contrast phala_anchors.signal_id, migration '
  '683, which documents genuine orphan-tolerance for a generation pointer). Added after '
  'removing 5 pre-existing rows that cited a chart_id absent from `charts` -- confirmed '
  'unregroundable (no historical chart row exists) before deletion, not assumed. ON DELETE '
  'CASCADE matches the existing chart-scoped-child convention (e.g. '
  'chart_fact_identity_fact_id_fkey).';
