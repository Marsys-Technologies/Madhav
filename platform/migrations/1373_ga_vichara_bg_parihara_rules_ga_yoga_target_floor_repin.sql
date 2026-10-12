-- 1373_ga_vichara_bg_parihara_rules_ga_yoga_target_floor_repin.sql   (number 1373: 1369 sits inside the protected applied range 1300-1370, so the owner's rule assigns the next free number)
--
-- Census Count.floor: three registry floors that no longer match the documented, INTENDED achieved counts. All three are floor RE-PINS to the live count after an intended change; no row is added,
-- removed or rewritten anywhere (CLAUDE.md N.4: floors are aspirational and never a reason to fabricate rows).
-- (1) ga_vichara 8249 -> 7774: lane #2970 (whole-row dedupe, S-L1 integration e9e96d759, 2026-10-03) removed 750 exact duplicate valence_pass rows (5 x 150; membership identical): 8,524 -> 7,774
--     (HOOKS_W7_HAND_READBACK_v1_0.md, the writer acceptance SQL). Migration 846's formula with the new valence term: 5 x (1500 + 35 + 9 + 9) + 9 = 7,774. Measured on the evaluation copy of on-demand backup 1791769727082 (taken 2026-10-12T01:50Z; restored copy, not the live database) through
--     the registered count_sql = 7,774 (chart 482012f1). The other two charts still hold older output (8,240 / 8,247) until replicated.
-- (2) bg_parihara_rules 449 -> 440: floor 449 = 61 + 329 + 59 (migration 644); migration 703 deleted 9 orphaned rows (1 parihara, 8 census) and re-pinned the check to 60 / 329 / 51 but not the floor.
--     The registered count_sql measured on the evaluation copy of on-demand backup 1791769727082 (taken 2026-10-12T01:50Z; restored copy, not the live database) = 60 + 329 + 51 = 440 (identical in every census since 2026-09-30).
-- (3) ga_yoga 63 -> 53: floor 63 was the native chart's count recorded by migration 650 (2026-09-05; min of 80 / 69 / 63). Now: 53 rows / 13 yogas (5 ayanamshas), every row fired: a delta of -10 firings
--     (measured on the evaluation copy of on-demand backup 1791769727082 (taken 2026-10-12T01:50Z; restored copy, not the live database)).
--     CAUSE NOT ISOLATED: the committed evidence shows the delta, not the per-yoga cause. The probable cause is the Nabhasa rule tightening (commit bdc27ccdf: chatra and ardhachandra, 2 yogas x 5 ayanamshas = 10),
--     which the Engine read on 2026-10-12 as an intended evaluator change, not lost rows; that attribution is plausible, not proven by a per-yoga count. PR #1298 merged 2026-08-15, before migration 650 recorded 63,
--     so it is NOT the explanation. The other two charts hold older output (69 / 80) until replicated.
-- GUARD: each UPDATE replaces only the exact old floor of its own asset row; a different live floor is a NOTICE-and-NO-OP; a floor already at the new value is an idempotent no-op; a silent no-op of an
-- UPDATE that should have matched RAISES. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT). Data-only.
-- TRIGGER EFFECT: nirmana_registry_receipt_invalidation fires for target_floor: the three assets' freshness becomes 'stale' (registry_changed) until their next build.
-- VERIFICATION: SELECT asset_id, target_floor FROM asset_registry WHERE asset_id IN ('ga_vichara','bg_parihara_rules','ga_yoga');  -- 7774, 440, 53
-- ROLLBACK: UPDATE asset_registry SET target_floor = 8249 WHERE asset_id='ga_vichara' AND target_floor=7774; ... = 449 WHERE asset_id='bg_parihara_rules' AND target_floor=440; ... = 63 WHERE asset_id='ga_yoga' AND target_floor=53;

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  v_floor bigint;
  v_rows  integer;
BEGIN
  SELECT target_floor INTO v_floor FROM asset_registry WHERE asset_id = 'ga_vichara' FOR UPDATE;
  IF NOT FOUND THEN RAISE NOTICE '1373: no ga_vichara registry row; nothing to do';
  ELSIF v_floor = 7774 THEN RAISE NOTICE '1373: ga_vichara target_floor already 7774; nothing to do';
  ELSIF v_floor IS DISTINCT FROM 8249 THEN RAISE NOTICE '1373: ga_vichara target_floor is % (not the 8249 this migration was written against); NO-OP', v_floor;
  ELSE
    UPDATE asset_registry SET target_floor = 7774 WHERE asset_id = 'ga_vichara' AND target_floor = 8249;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN RAISE EXCEPTION '1373: ga_vichara target_floor update did not take (rows %)', v_rows; END IF;
  END IF;

  SELECT target_floor INTO v_floor FROM asset_registry WHERE asset_id = 'bg_parihara_rules' FOR UPDATE;
  IF NOT FOUND THEN RAISE NOTICE '1373: no bg_parihara_rules registry row; nothing to do';
  ELSIF v_floor = 440 THEN RAISE NOTICE '1373: bg_parihara_rules target_floor already 440; nothing to do';
  ELSIF v_floor IS DISTINCT FROM 449 THEN RAISE NOTICE '1373: bg_parihara_rules target_floor is % (not the 449 this migration was written against); NO-OP', v_floor;
  ELSE
    UPDATE asset_registry SET target_floor = 440 WHERE asset_id = 'bg_parihara_rules' AND target_floor = 449;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN RAISE EXCEPTION '1373: bg_parihara_rules target_floor update did not take (rows %)', v_rows; END IF;
  END IF;

  SELECT target_floor INTO v_floor FROM asset_registry WHERE asset_id = 'ga_yoga' FOR UPDATE;
  IF NOT FOUND THEN RAISE NOTICE '1373: no ga_yoga registry row; nothing to do';
  ELSIF v_floor = 53 THEN RAISE NOTICE '1373: ga_yoga target_floor already 53; nothing to do';
  ELSIF v_floor IS DISTINCT FROM 63 THEN RAISE NOTICE '1373: ga_yoga target_floor is % (not the 63 this migration was written against); NO-OP', v_floor;
  ELSE
    UPDATE asset_registry SET target_floor = 53 WHERE asset_id = 'ga_yoga' AND target_floor = 63;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN RAISE EXCEPTION '1373: ga_yoga target_floor update did not take (rows %)', v_rows; END IF;
  END IF;
END $$;
