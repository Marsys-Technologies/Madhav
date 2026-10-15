-- 1360_retire_bg_sarvatobhadra_grid.sql
--
-- RETIRE the unbuilt registry asset bg_sarvatobhadra_grid (SS ruling N-430: approved). DATA-ONLY, CATALOGUE-ONLY. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). No table or function is created, altered or dropped, so it runs as amjis_app on the routine
-- path. HELD FOR KALA COORDINATION: do not merge before Kala confirms (ka_vedha_gochara's own files are Kala's; see the PR body).
--
-- WHY. The asset was registered by migration 529 (ADJUDICATION-11) as a school-tagged 9x9 Sarvatobhadra grid, DELIBERATELY EMPTY: the grid geometry
-- varies by tradition, the one corpus source (the Phaladeepika diagram page) is OCR noise, and only 3 of 28 asterisms carry a full vedha set
-- (services/ka_vedha_gochara/logic.py docstring). It has no @register writer (has_writer = false), nothing inserts into it, and it has never held a
-- row. Seating a grid now would be fabrication (CLAUDE.md B.10, B.1). The asset is therefore RETIRED: a catalogue entry that promises an
-- activation nothing can perform is a signal without a detector behind it (CLAUDE.md N.8).
--
-- WHAT (three registry changes, nothing else):
--   (a) GUARD, before anything is written: the grid row exists; has_writer is false; the table exists and has ZERO rows (RAISE if it has any: a
--       populated grid is exactly the case this retirement must not silently orphan); no lifecycle declaration conflicts; dead_flag is not true
--       (the asset_registry_dead_flag_not_retired CHECK of migration 591 would refuse it anyway; named here so the message is readable); ka_vedha_gochara
--       exists; and NO asset other than ka_vedha_gochara depends on the grid (an edge left to an inactive asset turns that asset red on Build.dag).
--   (b) asset_registry row of bg_sarvatobhadra_grid: is_active = false, catalog_status = 'RETIRED', data_disposition = 'RETAINED_AS_CAPITAL'.
--       Column semantics are those of migrations 563 (RETIRED + is_active = false) and 593 (RETAINED_AS_CAPITAL: the data and table stay),
--       and migration 590's CHECKs (catalog_status IN CURRENT/DRAFT/RETIRED per 328; data_disposition IN RETAINED_AS_CAPITAL/SUPERSEDED_IN_PLACE/DROPPABLE).
--       superseded_by stays NULL: there is no successor (the 590 FK and not-self CHECK both allow NULL; the 590 comment makes it non-null only
--       "on" a RETIRED row, never required). The row, its history and the asset_throughput / asset_freshness sentinel rows (553, 911) are KEPT.
--   (c) ka_vedha_gochara.depends_on (text[]): array_remove(depends_on, 'bg_sarvatobhadra_grid'). Keeping the edge once the grid is inactive would fail
--       the `exists` clause of Build.dag ("every depends_on entry is an ACTIVE registry asset") and the orchestrator's dependency gate for
--       ka_vedha_gochara. Migration 911 had rejected this option (b) while the grid was a live, intentionally-empty asset; N-430 supersedes that.
--   (d) POST-CHECKS RAISE if any of it did not take (never trust a silent no-op, CLAUDE.md N.4): the grid row is retired/inactive/RETAINED with
--       superseded_by NULL and has_writer false; nothing depends on the grid; ka_vedha_gochara.depends_on is EXACTLY its pre-state minus the grid
--       edge (every other edge, in order); and no other asset_registry row version was written by this transaction (a supplementary check of visible
--       tuple versions, as in 1243; not proof that nothing else was touched).
--
-- KEPT, ON PURPOSE. The table bg_sarvatobhadra_grid itself (the ka_vedha_gochara writer reads it first and falls through to
-- l1_sarvatobhadra_vedha, then to the disclosed algorithmic opposition approximation, when it is empty: writer behaviour is unchanged); the
-- asset_throughput (553) and asset_freshness (911) rows; migration 632's evidence-server write guard list (the table still exists; 632 is applied
-- and is never edited). The TypeScript seed (asset_registry_seed.ts) is NOT edited: its upsert keeps a RETIRED row RETIRED and is_active false
-- (the MR-06 guard in ASSET_REGISTRY_UPSERT_SQL), keeps catalog_status CURRENT-or-RETIRED as it is, and does not overwrite depends_on once a row
-- exists, so a routine re-seed cannot undo this migration.
--
-- TRIGGER EFFECT (migration 596, nirmana_registry_receipt_invalidation: AFTER UPDATE OF depends_on, ..., is_active ...). It fires for two rows:
-- the grid (is_active) and ka_vedha_gochara (depends_on), and sets their asset_freshness rows to 'stale' with reason 'registry_changed'.
-- ka_vedha_gochara is a per-chart asset, so its freshness reads stale on EVERY chart until it rebuilds; it is rebuilt in the single rebuild.
-- That is the honest reading: its declared dependency set changed.
--
-- CENSUS. The population filter is `is_active AND NOT dead_flag`, so the retired grid reads `excluded_inactive`. The Build.dag reads-match clause
-- is unaffected: table owners are active WRITER-BACKED assets only (build_table_owners), the grid has none, and `bg_` tables are bedrock-exempt.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (never trust a deploy log). After the deploy, as the read-only role:
--   SELECT asset_id, is_active, catalog_status, data_disposition, superseded_by, has_writer FROM asset_registry WHERE asset_id = 'bg_sarvatobhadra_grid';
--     expect: false | RETIRED | RETAINED_AS_CAPITAL | NULL | false
--   SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_vedha_gochara';
--     expect: the pre-deploy array without 'bg_sarvatobhadra_grid'
--   SELECT asset_id FROM asset_registry WHERE depends_on @> ARRAY['bg_sarvatobhadra_grid']::text[];   expect: no rows
--   SELECT count(*) FROM bg_sarvatobhadra_grid;   expect: 0 (the table is kept)
--
-- ROLLBACK (not executed by migrate.ts; only valid while the table is still empty):
--   UPDATE asset_registry SET is_active = true, catalog_status = 'CURRENT', data_disposition = NULL WHERE asset_id = 'bg_sarvatobhadra_grid';
--   UPDATE asset_registry SET depends_on = array_append(depends_on, 'bg_sarvatobhadra_grid') WHERE asset_id = 'ka_vedha_gochara'
--     AND NOT depends_on @> ARRAY['bg_sarvatobhadra_grid']::text[];   -- the original position was fourth (after bg_transit_rules)

SET LOCAL lock_timeout = '5s';

DO $mig$
DECLARE
  c_grid    constant text := 'bg_sarvatobhadra_grid';
  c_vedha   constant text := 'ka_vedha_gochara';
  v_n         int;
  v_has_writer boolean;
  v_active    boolean;
  v_status    text;
  v_succ      text;
  v_disp      text;
  v_dead      boolean;
  v_rows      bigint;
  v_pre_deps  text[];
  v_post_deps text[];
  v_other     text;
  v_touched   int;
BEGIN
  -- ---- (a) GUARD ------------------------------------------------------------------------------------------------------------------
  SELECT count(*), bool_or(has_writer), bool_or(is_active), max(catalog_status), max(superseded_by), max(data_disposition), bool_or(dead_flag)
    INTO v_n, v_has_writer, v_active, v_status, v_succ, v_disp, v_dead
    FROM asset_registry WHERE asset_id = c_grid;
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1360: expected exactly one asset_registry row for % (migration 529 creates it), found %', c_grid, v_n;
  END IF;
  IF v_has_writer IS DISTINCT FROM false THEN
    RAISE EXCEPTION '1360: % has has_writer = % (expected false): an asset with a writer is not an unbuilt asset; refusing to retire it', c_grid, v_has_writer;
  END IF;
  IF to_regclass('public.bg_sarvatobhadra_grid') IS NULL THEN
    RAISE EXCEPTION '1360: table bg_sarvatobhadra_grid does not exist (migration 529 creates it); refusing to retire an asset whose emptiness cannot be checked';
  END IF;
  EXECUTE 'SELECT count(*) FROM public.bg_sarvatobhadra_grid' INTO v_rows;
  IF v_rows <> 0 THEN
    RAISE EXCEPTION '1360: bg_sarvatobhadra_grid has % row(s) (expected 0, deliberately empty per ADJUDICATION-11). Content has landed: this retirement is obsolete; re-evaluate rather than applying', v_rows;
  END IF;
  IF v_succ IS NOT NULL THEN
    RAISE EXCEPTION '1360: % already declares superseded_by = % (this retirement has no successor); refusing to overwrite a lifecycle declaration', c_grid, v_succ;
  END IF;
  IF v_disp IS NOT NULL AND v_disp <> 'RETAINED_AS_CAPITAL' THEN
    RAISE EXCEPTION '1360: % carries a conflicting data_disposition = %; refusing', c_grid, v_disp;
  END IF;
  IF v_dead IS TRUE THEN
    RAISE EXCEPTION '1360: % has dead_flag = true, which the asset_registry_dead_flag_not_retired CHECK (migration 591) does not allow on a RETIRED row; resolve the dead_flag disposition first', c_grid;
  END IF;

  SELECT depends_on INTO v_pre_deps FROM asset_registry WHERE asset_id = c_vedha;
  IF NOT FOUND THEN
    RAISE EXCEPTION '1360: no asset_registry row for % (migration 526 creates it); its depends_on edge to % cannot be removed', c_vedha, c_grid;
  END IF;

  SELECT string_agg(asset_id, ', ' ORDER BY asset_id) INTO v_other
    FROM asset_registry WHERE depends_on @> ARRAY[c_grid]::text[] AND asset_id <> c_vedha;
  IF v_other IS NOT NULL THEN
    RAISE EXCEPTION '1360: asset(s) other than % depend on %: % ; retiring it would leave a dangling edge on each. Remove those edges by their own owners first', c_vedha, c_grid, v_other;
  END IF;

  -- ---- (b) retire the grid row (a retry on an already-retired row rewrites nothing) ---------------------------------------------------
  IF v_active IS FALSE AND v_status = 'RETIRED' AND v_disp = 'RETAINED_AS_CAPITAL' THEN
    RAISE NOTICE '1360: % is already RETIRED / inactive / RETAINED_AS_CAPITAL; row left as is', c_grid;
  ELSE
    UPDATE asset_registry
       SET is_active = false, catalog_status = 'RETIRED', data_disposition = 'RETAINED_AS_CAPITAL'
     WHERE asset_id = c_grid;
  END IF;

  -- ---- (c) remove the edge ------------------------------------------------------------------------------------------------------------
  IF v_pre_deps @> ARRAY[c_grid]::text[] THEN
    UPDATE asset_registry SET depends_on = array_remove(depends_on, c_grid) WHERE asset_id = c_vedha;
  ELSE
    RAISE NOTICE '1360: % no longer lists % in depends_on; edge already removed', c_vedha, c_grid;
  END IF;

  -- ---- (d) POST-CHECKS (each RAISEs, rolling the migration back) --------------------------------------------------------------------
  SELECT count(*) INTO v_n FROM asset_registry
   WHERE asset_id = c_grid AND is_active IS FALSE AND catalog_status = 'RETIRED' AND data_disposition = 'RETAINED_AS_CAPITAL'
     AND superseded_by IS NULL AND has_writer IS FALSE;
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1360: the retirement of % did not take (expected is_active=false, catalog_status=RETIRED, data_disposition=RETAINED_AS_CAPITAL, superseded_by NULL, has_writer=false)', c_grid;
  END IF;

  SELECT string_agg(asset_id, ', ' ORDER BY asset_id) INTO v_other FROM asset_registry WHERE depends_on @> ARRAY[c_grid]::text[];
  IF v_other IS NOT NULL THEN
    RAISE EXCEPTION '1360: asset(s) still depend on the retired %: %', c_grid, v_other;
  END IF;

  SELECT depends_on INTO v_post_deps FROM asset_registry WHERE asset_id = c_vedha;
  IF v_post_deps IS DISTINCT FROM array_remove(v_pre_deps, c_grid) THEN
    RAISE EXCEPTION '1360: % depends_on is % (expected the pre-state % without %)', c_vedha, v_post_deps, v_pre_deps, c_grid;
  END IF;

  SELECT count(*) INTO v_touched FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid AND asset_id NOT IN (c_grid, c_vedha);
  IF v_touched <> 0 THEN
    RAISE EXCEPTION '1360: % other asset_registry row(s) were modified by this migration', v_touched;
  END IF;
END
$mig$;
