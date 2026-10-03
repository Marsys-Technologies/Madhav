-- 1270_bg_cohort_count_scope.sql
--
-- Suvarna Track I, item TI-L0-30 (finding CF-02, SS ruling Q19 of 2026-10-01; number 1270 allocated by SS):
-- scope bg_cohort's count_sql to its PRIMARY table, and move the floor to match.
--
--   asset_registry, asset_id = 'bg_cohort':
--     count_sql     SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count
--               ->  SELECT COUNT(*) FROM bg_synthetic_cohort
--     target_floor  110000 -> 10000
--
-- Two cells of one row. Nothing else.
--
-- CONCERN
--   bg_cohort is a two-table asset: bg_synthetic_cohort (10,000 synthetic charts, one row per chart) and its child
--   bg_synthetic_cohort_md (100,000 Vimshottari mahadasha rows, 10 per chart). The registry count_sql SUMS both
--   (110,000), but the writer reports only the primary table in rows_written (10,000;
--   pipeline/orchestrator/writers/bg_cohort.py:525-575 keeps `rows_written` apart from `md_rows_written` and returns the first), so the
--   asset's counted volume and its recorded build volume disagree by a factor of eleven (Earn.build_record /
--   Count-vs-record reading). SS Q19: "scope count_sql to the primary table and declare the asset multi-table".
--   The precedent for a scoped count_sql is bg_class_lifetime_counts (seed L580-608).
--
-- WHAT STAYS TRUE (so nothing is lost by the scoping)
--   * The asset is ALREADY declared multi-table in the registry: natural_key_partition =
--     'bg_synthetic_cohort.synthetic_id; bg_synthetic_cohort_md.(synthetic_id,md_index)' (untouched here). The
--     declarations-file "multi-table" word is a #2984 file and is NOT done here.
--   * The child table remains fully covered: integrity_check_sql (untouched) asserts exactly 100,000 md rows, 10 per
--     chart, the age-chain continuity and a sha256 of both tables' content. Only the COUNT figure narrows.
--   * volume_explanation ("10,000 ... + 100,000 ...") stays accurate and is untouched.
--
-- SERVING EFFECT AT APPLY
--   * Fires nirmana_registry_receipt_invalidation (target_floor is a trigger column; the row changes): the
--     asset_freshness row of bg_cohort (fresh, 2026-09-07) becomes STALE (reason registry_changed).
--     Assets that go stale: bg_cohort ONLY. BUT bg_cohort has a declared dependent: ka_kshetra (L3 Kala) lists it in
--     depends_on, and asset_runner.deps_unsatisfied requires a DATA dependency's latest freshness to be 'fresh'.
--     Until bg_cohort is rebuilt (or its receipt otherwise re-emitted as fresh), a dispatch of ka_kshetra reads
--     "bg_cohort(receipt:stale)" and is BLOCKED. Proven in the test with the real gate function. This is the cost
--     of moving a trigger column; it cannot be avoided because a scoped count of 10,000 against the old floor of
--     110,000 would read Count.floor FAIL. ORDER the apply so that bg_cohort is re-built (or SS accepts the block)
--     before ka_kshetra is dispatched. Held; sequence with SS.
--   * Cockpit stats read count_sql (not asset_throughput): bg_cohort will show 10,000 (floor 10,000) instead of
--     110,000 (floor 110,000). No served tool reads count_sql or the floor; no data is touched.
--
-- GUARDS (every one raises rather than skip)
--   * bg_cohort must exist with target_table = 'bg_synthetic_cohort'; its count_sql must be EXACTLY the audited
--     two-table sum (md5 d8f9f0bfe7b996e5fd829bc3f5347632, read live 2026-10-03) and target_floor 110000; or already
--     EXACTLY the new pair (then skipped); anything else is DRIFT and raises.
--   * ROW_COUNT = 1 and a post-check that re-reads both cells. A missing row (fresh bootstrap) is a NOTICE skip.
--
-- PRIVILEGE (P2 rule, W1_PRIVILEGE_AUDIT): runs as amjis_app, OWNER of asset_registry, asset_freshness and the
-- trigger function; needs only UPDATE on asset_registry. No CREATE, no GRANT, no DDL. Proven as amjis_app
-- (NOSUPERUSER, NOINHERIT, no CREATE on schema public).
--
-- IDEMPOTENT: a second run finds the new pair and updates nothing (the trigger does not fire again).
--
-- NOT DONE HERE
--   * The seed literals (count_sql / target_floor of bg_cohort) in platform/scripts/seed/asset_registry_seed.ts and
--     the declarations-file multi-table declaration: both #2984 files. The seed's ON CONFLICT keeps count_sql and
--     target_floor migration-governed for an existing row, so a re-seed cannot revert this file.
--   * Any rebuild/re-receipt of bg_cohort (needed to clear the ka_kshetra gate, above); any change to the writer.
--   * The writer's own reporting of md_rows_written (CF-02 part 2, held with the writer-digest inventory).
--
-- ROLLBACK (ops reference, not executed): restore the audited count_sql text and target_floor 110000 with a new
-- reviewed migration against the then-current state; never edit this file after apply.
--
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103):
--   SELECT count_sql, target_floor FROM asset_registry WHERE asset_id = 'bg_cohort';
--     -- SELECT COUNT(*) FROM bg_synthetic_cohort | 10000
--   SELECT freshness_state, reasons FROM asset_freshness WHERE asset_id = 'bg_cohort';   -- stale, ["registry_changed"]
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $m1270$
DECLARE
    old_count_sql constant text :=
        'SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count';
    new_count_sql constant text := 'SELECT COUNT(*) FROM bg_synthetic_cohort';
    v_sql    text;
    v_floor  integer;
    v_target text;
    v_rows   bigint;
BEGIN
    IF md5(old_count_sql) <> 'd8f9f0bfe7b996e5fd829bc3f5347632' THEN
        RAISE EXCEPTION '1270: the audited count_sql literal does not match its pinned md5 (file corrupted)';
    END IF;

    SELECT count_sql, target_floor, target_table
      INTO v_sql, v_floor, v_target
      FROM asset_registry WHERE asset_id = 'bg_cohort' FOR UPDATE;
    IF NOT FOUND THEN
        RAISE NOTICE '1270: bg_cohort is not in asset_registry; skipped';
        RETURN;
    END IF;
    IF v_target IS DISTINCT FROM 'bg_synthetic_cohort' THEN
        RAISE EXCEPTION '1270: bg_cohort has drifted from the audited state (target_table=%); refusing to change count_sql', v_target;
    END IF;

    IF v_sql = new_count_sql AND v_floor = 10000 THEN
        RAISE NOTICE '1270: bg_cohort count_sql / target_floor are already scoped; skipped';
        RETURN;
    END IF;
    IF v_sql IS DISTINCT FROM old_count_sql OR v_floor IS DISTINCT FROM 110000 THEN
        RAISE EXCEPTION '1270: bg_cohort has drifted from the audited state (md5(count_sql)=%, target_floor=%); refusing to change count_sql / target_floor',
            md5(v_sql), v_floor;
    END IF;

    UPDATE asset_registry
       SET count_sql = new_count_sql, target_floor = 10000
     WHERE asset_id = 'bg_cohort' AND count_sql = old_count_sql AND target_floor = 110000;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN
        RAISE EXCEPTION '1270: bg_cohort update touched % rows, expected 1', v_rows;
    END IF;

    -- Post-check: re-read both cells, never trust a silent no-op.
    IF NOT EXISTS (SELECT 1 FROM asset_registry
                    WHERE asset_id = 'bg_cohort' AND count_sql = new_count_sql AND target_floor = 10000) THEN
        RAISE EXCEPTION '1270: bg_cohort count_sql / target_floor are not the scoped pair after the update';
    END IF;
END
$m1270$;
