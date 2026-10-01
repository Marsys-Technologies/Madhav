-- 1218_suvarna_bodha_writer_timeouts.sql
--
-- Suvarna ruling R-25 (SS, 2026-10-01; value superseded by SS to 1800): raise
-- asset_registry.writer_timeout_seconds from 600 to 1800 (30 min) for bo_grounding and
-- bo_laksana_rerank ONLY. Transaction ownership belongs to platform/scripts/migrate.ts
-- (BEGIN/COMMIT around this file). Data-only: one UPDATE of two asset_registry rows, no DDL.
-- NOT applied by this change.
--
-- WHY THESE TWO. The in-process per-writer watchdog is the timeout that can actually FAIL an asset and
-- block a batch: runner.py execute_dag computes `deadlines[fut] = monotonic() + _timeout_for(asset)`
-- from asset_registry.writer_timeout_seconds (runner.py:679 `_timeout_for`, :726 deadline check), marks
-- the asset `error` on expiry, and cascade-blocks its dependents. Both assets are still on the 600 s
-- default. The N-59 L2 fixes add work to the bo_laksana_rerank pass, so its 600 s headroom is the
-- one that shrinks. bo_grounding is raised with it so the pair is not left as the only 600 s
-- members of the chain.
--
-- WHY 1800 AND NOT 10800. SS first ruled 10800 (the value 15 other bodha assets carry and
-- mi_bhara holds in production), then superseded it with 1800: (a) it covers the worst recorded runs
-- with margin (bo_laksana_rerank 1233 s, bo_grounding 1157 s; INVESTIGATION_R25_REAPER_VS_L2_v1_0.md
-- section 2); (b) it BOUNDS a real hang at 30 minutes instead of 3 hours, which matters because
-- bo_sangati depends directly on bo_laksana_rerank (live asset_registry.depends_on) and is blocked
-- until the rerank finishes or times out; (c) it matches the 30-minute idle-in-transaction cap the
-- orchestrator sets on its connections (pipeline/orchestrator/db.py:49-76, which also sets
-- statement_timeout = 0, so the writer timeout is the only wall-clock bound on a statement).
--
-- HONEST TRADE-OFFS (what 1800 does and does not fix):
--   * It changes only the in-process budget (P1). The 15-minute stuck-asset watchdog, clause 2
--     (platform/src/app/api/cockpit/watchdog/route.ts:216-394), never reads the registry. Any run of
--     either asset longer than 15 minutes is still exposed to it, and a light writer re-running over
--     existing data can be falsely promoted to `lit` while its worker is still running. A `lit` flip
--     seen while the worker is alive is a watchdog artefact: verify the final state after the worker
--     ends, do not trust the interim one.
--   * A larger timeout lengthens hang detection for bo_laksana_rerank (and bo_grounding) from 10
--     minutes to up to 30 minutes, and keeps bo_sangati blocked that long on a real hang.
--   * Neither writer has substeps (light writers), so substep-progress monitoring (the S-L2 12-minute
--     stop rule) cannot observe them; watch their wall time directly.
--
-- SCOPE. Exactly these two rows and exactly this one column. NOT touched: the other six bodha assets
-- that are still at 600 (bo_arudha, bo_nakshatra_semantic, bo_special_lagna, bo_sudarshana,
-- bo_vargottama_dhana, bo_yantra_mechanism; not part of the ruling), any other layer, the seed.
--
-- FROZEN-MANIFEST / FINGERPRINT SAFETY (read in code, not assumed):
--   * registryContractFingerprintInput (src/lib/nirmana-elevation/definitions.ts:135-157) hashes
--     asset_id, layer, depends_on and a registry_contract of sort_order, scope, asset_kind,
--     catalog_status, is_active, has_writer, target_table, count_sql, integrity_check_sql,
--     health_probe, natural_key_partition, superseded_by, data_disposition, dead_flag.
--     writer_timeout_seconds is NOT in it, and NirmanaRegistryContractRow (definitions.ts:71-92) and
--     the registry SELECT that feeds it (definitions.ts:615-621 and the three sibling queries) do not
--     even read the column. assertManifestMatchesRegistry (:354-376) and
--     assertManifestMatchesRegistryIdentity (:387-408, layer + depends_on only) therefore cannot see
--     this change. bo_laksana_rerank is Nirmana-frozen (t3); bo_grounding is a supporting writer
--     excluded from the elevation denominator (NIRMANA_SUPPORTING_WRITERS).
--   * The only trigger on asset_registry, nirmana_registry_receipt_invalidation, is AFTER UPDATE OF
--     depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind,
--     asset_type, scope, has_writer, is_active, target_table. writer_timeout_seconds is not in that
--     column list and this UPDATE sets only writer_timeout_seconds, so the trigger does not fire and
--     no asset_freshness row is marked stale.
--   * runner.py _verify_registry_still_matches_manifest (:343-382) compares scope, depends_on,
--     natural_key_partition and co-writer presence; not the timeout. The timeout is read live at run
--     start (runner.py:885-888), so a run dispatched after this applies picks it up with no replan.
--   * asset_registry_seed.ts carries writer_timeout_seconds for neither asset (it is written only on
--     INSERT, default 600, and the conflict clause preserves the live value: `writer_timeout_seconds =
--     asset_registry.writer_timeout_seconds`, pinned by asset_registry_seed_dag_parity.test.ts), so
--     seed and DB stay consistent with no seed edit and the capability census is unaffected.
--
-- RUNNER AUTHORITY. The routine migration runner connects as amjis_app (PROD_DATABASE_URL,
-- platform/scripts/validate-migration-database-routes.ts:12) and amjis_app OWNS asset_registry
-- (verified read-only: pg_class.relowner = amjis_app), so this UPDATE is issued by the owner.
--
-- BEHAVIOUR. Guarded and append-only. The UPDATE matches only rows still at 600, so it is idempotent
-- (a replay finds nothing to change) and never overwrites a different value. A target row that holds
-- any value other than 600 (already 1800, or a deliberate other value such as 10800) is LEFT ALONE
-- with a NOTICE and the migration STILL SUCCEEDS, so a green deploy does not by itself prove both
-- rows read 1800: run the post-apply check below. On a fresh bootstrap where neither row exists yet
-- it is a no-op (rows seeded later take the 600 default; that is a bootstrap-ordering matter for a
-- fresh environment, not for this live-registry fact). A snapshot of every asset_registry row's
-- writer_timeout_seconds is taken inside the transaction and compared afterwards: the migration
-- RAISEs unless exactly the rows it meant to change changed, to 1800, and no other row's value moved.
-- The snapshot is taken at READ COMMITTED without a table lock (a lock would block builders for no
-- benefit), so a concurrent committed writer_timeout_seconds edit on ANY row between the snapshot and
-- the verify is counted as a stray change and fails the migration closed; re-running it succeeds.
--
-- Tests: platform/tests/unit/migrations/suvarna_bodha_writer_timeouts_1218.test.ts (static) and
-- platform/tests/integration/suvarna_bodha_writer_timeouts_1218.db.test.ts (executes this file on a
-- throwaway Postgres with the real trigger; env-gated, wired into CI db-integration-tests).
--
-- Post-apply verification (CLAUDE.md N.4): expect 2 rows, both 1800.
--   SELECT asset_id, writer_timeout_seconds FROM asset_registry
--    WHERE asset_id IN ('bo_grounding','bo_laksana_rerank') ORDER BY asset_id;

SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _m1218_before ON COMMIT DROP AS
SELECT asset_id, writer_timeout_seconds
  FROM asset_registry;

-- Guard 1: both target rows exist (live) or neither does (fresh bootstrap). One of two is drift.
DO $$
DECLARE
    n integer;
BEGIN
    SELECT count(*) INTO n
      FROM _m1218_before
     WHERE asset_id IN ('bo_grounding', 'bo_laksana_rerank');
    IF n NOT IN (0, 2) THEN
        RAISE EXCEPTION '1218: expected both or neither of bo_grounding/bo_laksana_rerank in asset_registry, found %', n;
    END IF;
END $$;

UPDATE asset_registry
   SET writer_timeout_seconds = 1800
 WHERE asset_id IN ('bo_grounding', 'bo_laksana_rerank')
   AND writer_timeout_seconds = 600;

-- Guard 2: verify it actually applied (never trust a silent no-op) and that nothing else moved.
DO $$
DECLARE
    expected_changes integer;
    actual_changes   integer;
    stray            text;
    unmet            text;
BEGIN
    -- rows this migration was entitled to change: targets that were at 600 in the snapshot
    SELECT count(*) INTO expected_changes
      FROM _m1218_before
     WHERE asset_id IN ('bo_grounding', 'bo_laksana_rerank')
       AND writer_timeout_seconds = 600;

    -- every row whose writer_timeout_seconds differs from the snapshot (FULL JOIN: also catches a
    -- row that appeared or vanished inside this transaction)
    SELECT count(*) INTO actual_changes
      FROM _m1218_before b
      FULL JOIN asset_registry r ON r.asset_id = b.asset_id
     WHERE r.writer_timeout_seconds IS DISTINCT FROM b.writer_timeout_seconds;

    IF actual_changes <> expected_changes THEN
        RAISE EXCEPTION '1218: % asset_registry row(s) changed writer_timeout_seconds, expected exactly %',
            actual_changes, expected_changes;
    END IF;

    -- no changed row may be outside the two targets, and every changed row must now read 1800
    SELECT string_agg(coalesce(r.asset_id, b.asset_id), ', ' ORDER BY coalesce(r.asset_id, b.asset_id))
      INTO stray
      FROM _m1218_before b
      FULL JOIN asset_registry r ON r.asset_id = b.asset_id
     WHERE r.writer_timeout_seconds IS DISTINCT FROM b.writer_timeout_seconds
       AND (coalesce(r.asset_id, b.asset_id) NOT IN ('bo_grounding', 'bo_laksana_rerank')
            OR r.writer_timeout_seconds IS DISTINCT FROM 1800);
    IF stray IS NOT NULL THEN
        RAISE EXCEPTION '1218: unexpected writer_timeout_seconds change on: %', stray;
    END IF;

    -- every target that was at 600 must now read 1800; a target that held a different, deliberate
    -- value was correctly left alone by the 600 guard (reported below, not overwritten)
    SELECT string_agg(r.asset_id || '=' || coalesce(r.writer_timeout_seconds::text, 'NULL'), ', '
                      ORDER BY r.asset_id)
      INTO unmet
      FROM asset_registry r
      JOIN _m1218_before b ON b.asset_id = r.asset_id
     WHERE r.asset_id IN ('bo_grounding', 'bo_laksana_rerank')
       AND r.writer_timeout_seconds IS DISTINCT FROM 1800
       AND b.writer_timeout_seconds = 600;
    IF unmet IS NOT NULL THEN
        RAISE EXCEPTION '1218: target row(s) not at 1800 after update: %', unmet;
    END IF;

    IF expected_changes < (SELECT count(*) FROM _m1218_before
                            WHERE asset_id IN ('bo_grounding', 'bo_laksana_rerank')) THEN
        RAISE NOTICE '1218: a target row was not at 600 (already 1800, or a deliberate other value) and was left untouched';
    END IF;
END $$;

-- DOWN (ops reference, not executed by migrate.ts): restore exactly these two rows.
--   UPDATE asset_registry SET writer_timeout_seconds = 600
--    WHERE asset_id IN ('bo_grounding', 'bo_laksana_rerank') AND writer_timeout_seconds = 1800;
