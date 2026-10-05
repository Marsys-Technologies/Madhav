-- 1288_ph_pramana_integrity_check_chart_scoped.sql
--
-- Suvarna (SS ruling N-120; principle N-99 / N-105: a check claims only what its own writer wrote, for the chart being built). Makes ph_pramana's
-- registered integrity_check_sql CHART-SCOPED. One md5-guarded UPDATE of one column of one asset_registry row. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no object is created (amjis_app has no CREATE on schema public; none is needed).
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1288-001). Routine path. Merge only on SS's review. Must be applied BEFORE the scoped delete of PR #3072
-- (the one-shot gated production DELETE of 8 contaminated phala_pramana rows of chart 1c826d5a) is EXECUTED, or at the latest before the next
-- ph_pramana build on any chart after it (see THE PROBLEM).
--
-- THE PROBLEM (REVIEW_3072.md MED-1). The orchestrator runs every registered integrity_check_sql after the writer, in the writer's transaction
-- (platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1200, _probe_asset), and a false result rolls the build back and errors the asset.
-- ph_pramana's check is GLOBAL: its tiling clause (one pramana row per anchor, both directions) quantifies over EVERY chart. Today it is TRUE on
-- production. After #3072 deletes the 8 contaminated life_event_miss rows of chart 1c826d5a, those chart's 8 spirituality anchors have no pramana row,
-- the check flips to FALSE, and then a ph_pramana build on ANY OTHER chart (e.g. the canonical 482012f1) fails its own post-write integrity gate for
-- a fact about a different chart's rows. (Evaluated read-only on production, below.)
--
-- HOW THE ORCHESTRATOR BINDS A CHART: IT DOES NOT. asset_runner.py runs `cur.execute(integrity_sql)` with NO parameters (also the census,
-- asset_census.py, and the freeze-time detector); migration 691 (D-CND-03) states "$1 placeholders are rejected outright". count_sql uses $1; integrity
-- SQL cannot. A text containing $1 would raise on every build. The orchestrator contract is FROZEN (CLAUDE.md N.2), so the scope is read from the
-- orchestrator's own COMMITTED state instead, no contract change:
--   chart in scope  =  the chart_id of a build_runs row with state 'running' that has a build_run_assets row for ph_pramana in state 'building'
--   (the run_asset 'building' upsert precedes the writer and is committed), AND ONLY IN A SESSION THAT HAS WRITTEN (txid_current_if_assigned() IS NOT
--   NULL). The orchestrator's probe runs on the writer's own connection, in the writer's transaction, after the writer and its asset_throughput
--   heartbeat wrote (asset_runner.py:_drive_substeps / _run_data_writer), so a txid is assigned there (verified with the real _probe_asset). The
--   freeze-time detector, the census and an operator's SELECT run read-only sessions: no txid, so for them the scope is never narrowed. (An xmin-based
--   scope is NOT used: the writer runs inside SAVEPOINT writer_exec, so its rows carry the subtransaction id.)
-- Inside a ph_pramana build the check therefore judges ONLY the pramana rows of the chart being built: its tiling against that chart's anchors in both
-- directions (a chart being built with anchors and no pramana rows at all is still judged: its anchors must each have one) and its one-row-per-anchor grain.
-- In EVERY read-only session (and any session that has written nothing), whatever runs are in flight or stuck, the scope is EVERY chart that HAS pramana rows:
-- the old global behaviour for built charts, so the detector and the census are never narrower than before and the check stays able to fail (CLAUDE.md N.8).
-- LOST DETECTION, stated plainly: in a read-only session a chart with anchors and ZERO pramana rows is not in scope (an unbuilt chart is not corruption;
-- the ph_pratikara precedent), so it reads TRUE where the old check read FALSE. It is still caught in-build (FALSE). ph_pramana has target_floor NULL, so
-- the census count-vs-floor comparison does not catch it either. A build whose session wrote nothing at all (a writer that deleted 0 rows and inserted none,
-- before any heartbeat row matched) also takes the all-charts scope, i.e. it behaves like the old check.
-- The schema clause (no numeric column: the D5 NO-SCORING gate) is chart-independent and unchanged.
--
-- THE TEXT. Live (suvarna_reader, 2026-10-03): 1,284 chars, md5 45f89d4853b157e22507ffccdb9af0e0; it is migration 681's ph_pramana check verbatim (reproduced by the tests).
-- New: 3,398 chars, md5 c3f1b7949ebfda27ab959e55c2a14898.
--
-- READBACKS, production, suvarna_reader, 2026-10-03, read-only (the whole texts run as the reader; the "scoped" rows substitute the chart for the
-- scope subquery, because the reader cannot create a running build; the real subquery is exercised on the mirror, below). "After delete" = the 8
-- life_event_miss rows of 1c826d5a excluded inside the query (nothing is written).
--                                        OLD check   NEW outside a build   NEW scoped to 482012f1   NEW scoped to 1c826d5a
--   today                                TRUE        TRUE                  TRUE                      TRUE
--   after the #3072 delete               FALSE       FALSE                 TRUE                      FALSE
--   (synthetic post-rebuild, mirror)     TRUE        TRUE                  TRUE                      TRUE
-- So after the delete a ph_pramana build on 482012f1 passes (it does not under the old check), and the incompleteness of 1c826d5a is still reported where
-- it is true: by every read-only session (the freeze-time detector, the census), honestly, until 1c826d5a's pramana is rebuilt. READ THE LAST COLUMN
-- CORRECTLY: "scoped to 1c826d5a = FALSE" is the PRE-WRITE state, which the orchestrator never evaluates for this asset. A build OF 1c826d5a IS the rebuild:
-- the probe runs after the writer has regenerated the 8 rows, so that build reads TRUE (tested with the real _probe_asset). Row counts: phala_pramana
-- 1c826d5a 56 (8 life_event_miss), 482012f1 4.
--
-- SERVING / FRESHNESS EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-03, suvarna_reader).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation (AFTER UPDATE OF depends_on, natural_key_partition,
--   health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table; FOR EACH ROW WHEN
--   (old.* IS DISTINCT FROM new.*); function nirmana_invalidate_registry_receipts() stales asset_freshness rows WHERE asset_id = NEW.asset_id).
--   Asset touched: ph_pramana only. asset_freshness holds 0 rows for ph_pramana (98 rows in the table, none for any ph_* asset; no RLS) and
--   asset_provenance_receipts 0, on every chart: 0 rows staled, no chart's freshness or served-generation state changes. Re-read at apply time.
--   The partition key (natural_key_partition) is not touched.
--
-- ACTIVE RUNS (ENFORCED): the first DO block RAISES, changing nothing, if any build_runs row in planned / running / paused has a build_run_assets row for
-- ph_pramana in queued / building. Zombie rows (a queued row in a failed / completed / stopped run: {1 stopped+queued, 18 failed+queued} on production today)
-- do NOT block. Active today: 0.
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly the base text (apply) or the target text (already applied: NOTICE); anything else, NULL included, RAISES.
-- The UPDATE is also guarded by the base md5. The post-check RAISES unless md5 + length + the exact text are stored and no other column of the row changed.
--
-- NOT DONE HERE: any change to the orchestrator (frozen); the same chart-scoping for other assets' global checks (ph_sodhana, ph_suddha_sodhana,
-- ph_sankrama, ph_muhurta, ph_pratikara and mimamsa_* have the same unbound-global shape: a ruling for SS; this one is the only check that #3072 breaks);
-- #3072 itself; 1259 (other columns/other assets).
--
-- KNOWN LIMITS (stated plainly).
--  1. TWO CONCURRENT ph_pramana BUILDS RE-COUPLE THE CHARTS. Both charts are in scope for each (each build's connection has a txid). With chart Y's COMMITTED
--     rows incomplete (1c826d5a after the #3072 delete), chart X's COMPLETE build reads FALSE and is rolled back (reproduced by the reviewer with the real
--     _probe_asset); Y's own build passes; X passes again once Y has committed. It fails closed and is transient, but it is exactly the cross-chart failure this
--     migration removes, for the overlap window. RUNBOOK RULE: NEVER RUN TWO ph_pramana BUILDS CONCURRENTLY (the orchestrator dispatches one chart at a time;
--     LIST FOREIGN build_runs BEFORE EVERY DISPATCH, running or paused, whatever the asset).
--  2. A stuck 'running' run with a 'building' ph_pramana row keeps its chart in scope for ORCHESTRATOR builds (stricter: another chart's build fails while that
--     chart's committed rows are incomplete) until the watchdog fails the run (a 'running' run with no asset progress for >30 minutes). It does NOT narrow any
--     read-only session (no txid), so for the detector and the census the check is never laxer than the old one.
--  3. The registry fingerprint the Nirmana dispatcher computes for ph_pramana moves (integrity_check_sql is part of it). No accepted Nirmana evidence exists
--     for ph_pramana (0 elevation campaign events): no effect.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103). After the deploy, as suvarna_reader, expect md5 c3f1b7949ebfda27ab959e55c2a14898, sha256 040cf925736b063b41b894812835d6c97fcc0083544c899efa2978020f46267f, length 3398:
--   SELECT md5(integrity_check_sql), encode(sha256(convert_to(integrity_check_sql, 'UTF8')), 'hex'), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ph_pramana';
--   SELECT count(*) FROM asset_freshness WHERE asset_id = 'ph_pramana';   -- 0
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 681's ph_pramana check, md5 45f89d4853b157e22507ffccdb9af0e0> WHERE asset_id = 'ph_pramana';
-- (same trigger; re-introduces the global behaviour).

SET LOCAL lock_timeout = '5s';

DO $runs$
DECLARE n_active int;
BEGIN
    SELECT count(DISTINCT r.id) INTO n_active
      FROM public.build_runs r JOIN public.build_run_assets b ON b.run_id = r.id
     WHERE b.asset_id = 'ph_pramana' AND r.state IN ('planned', 'running', 'paused') AND b.state IN ('queued', 'building');
    IF n_active > 0 THEN
        RAISE EXCEPTION '1288: % active build run(s) (planned/running/paused with a queued/building ph_pramana row); refusing to change its integrity check under a running build', n_active;
    END IF;
END
$runs$;

DO $pre$
DECLARE v_md5 text; v_n int;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ph_pramana';
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1288: expected exactly one ph_pramana registry row, found %', v_n;
  END IF;
  IF v_md5 = 'c3f1b7949ebfda27ab959e55c2a14898' THEN
    RAISE NOTICE '1288: ph_pramana integrity_check_sql already carries the chart-scoped text; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '45f89d4853b157e22507ffccdb9af0e0' THEN
    RAISE EXCEPTION '1288: ph_pramana integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;
  END IF;
END
$pre$;

CREATE TEMP TABLE _m1288_before ON COMMIT DROP AS
  SELECT to_jsonb(r) - 'integrity_check_sql' AS rest FROM asset_registry r WHERE asset_id = 'ph_pramana';

UPDATE asset_registry
SET integrity_check_sql = $ck$
-- Chart-scoped (migration 1288, SS N-120). The orchestrator runs this text UNBOUND (cur.execute(sql), no parameters, asset_runner.py:_probe_asset;
-- D-CND-03 forbids bind placeholders), so "the chart being built" is read from the orchestrator's own COMMITTED state: the chart_id of a RUNNING
-- build_runs row whose ph_pramana build_run_assets row is 'building' -- AND only in a session that has WRITTEN (txid_current_if_assigned() IS NOT NULL:
-- the orchestrator's probe runs in the writer's own transaction, after the writer and its heartbeat wrote, so it has a txid; a read-only detector /
-- census / operator session has none). Inside a ph_pramana build the check claims ONLY facts about the pramana rows of THAT chart. In every
-- read-only session, whatever runs are in flight or stuck, the scope is EVERY chart that HAS pramana rows (never narrower than the old global check;
-- an unbuilt chart, with anchors and no pramana rows, is not corruption there: the ph_pratikara precedent).
SELECT
  -- Exactly one pramana row per anchor, no orphan in either direction, for the chart(s) in scope.
  NOT EXISTS (SELECT 1 FROM phala_anchors a
      FULL OUTER JOIN phala_pramana p ON p.anchor_id = a.anchor_id AND p.chart_id = a.chart_id
     WHERE (a.anchor_id IS NULL OR p.anchor_id IS NULL)
       AND coalesce(a.chart_id, p.chart_id) IN (SELECT r.chart_id FROM build_runs r JOIN build_run_assets b ON b.run_id = r.id
              WHERE b.asset_id = 'ph_pramana' AND b.state = 'building' AND r.state = 'running' AND txid_current_if_assigned() IS NOT NULL
            UNION
            SELECT x.chart_id FROM phala_pramana x
             WHERE NOT EXISTS (SELECT 1 FROM build_runs r2 JOIN build_run_assets b2 ON b2.run_id = r2.id
                                WHERE b2.asset_id = 'ph_pramana' AND b2.state = 'building' AND r2.state = 'running' AND txid_current_if_assigned() IS NOT NULL))
     GROUP BY coalesce(a.chart_id, p.chart_id) HAVING count(*) > 0)
  -- Grain assertion: one row per anchor, per chart in scope.
  AND NOT EXISTS (SELECT 1 FROM phala_pramana
     WHERE chart_id IN (SELECT r.chart_id FROM build_runs r JOIN build_run_assets b ON b.run_id = r.id
              WHERE b.asset_id = 'ph_pramana' AND b.state = 'building' AND r.state = 'running' AND txid_current_if_assigned() IS NOT NULL
            UNION
            SELECT x.chart_id FROM phala_pramana x
             WHERE NOT EXISTS (SELECT 1 FROM build_runs r2 JOIN build_run_assets b2 ON b2.run_id = r2.id
                                WHERE b2.asset_id = 'ph_pramana' AND b2.state = 'building' AND r2.state = 'running' AND txid_current_if_assigned() IS NOT NULL))
     GROUP BY chart_id HAVING count(*) <> count(DISTINCT anchor_id))
  -- NOT CHART-PARTITIONABLE, and this is the D-CND-03 clause-2 exception with its reason:
  -- this is a SCHEMA invariant, not a data one. It re-asserts the D5 NO-SCORING gate
  -- structurally -- phala_pramana must carry no numeric column at all, because calibration
  -- belongs to L5 and is filled in from real outcome data, never invented here (§N.8).
  -- information_schema has no chart_id to partition on, and the claim is chart-independent
  -- by nature: a numeric column exists for every chart or for none.
  AND NOT EXISTS (SELECT 1 FROM information_schema.columns
     WHERE table_name = 'phala_pramana'
       AND data_type IN ('numeric','double precision','real'))$ck$
WHERE asset_id = 'ph_pramana'
  AND md5(integrity_check_sql) = '45f89d4853b157e22507ffccdb9af0e0';

DO $post$
DECLARE v_md5 text; v_len int; v_txt text; v_rest jsonb;
BEGIN
  SELECT md5(integrity_check_sql), length(integrity_check_sql), integrity_check_sql INTO v_md5, v_len, v_txt FROM asset_registry WHERE asset_id = 'ph_pramana';
  IF v_md5 IS DISTINCT FROM 'c3f1b7949ebfda27ab959e55c2a14898' OR v_len IS DISTINCT FROM 3398 THEN
    RAISE EXCEPTION '1288: the new ph_pramana integrity_check_sql did not take (md5 %, length %)', v_md5, v_len;
  END IF;
  IF v_txt NOT LIKE '%Chart-scoped (migration 1288%' OR v_txt NOT LIKE '%b.state = ''building''%' OR v_txt NOT LIKE '%r.state = ''running''%' OR v_txt NOT LIKE '%txid_current_if_assigned() IS NOT NULL%' OR position('$1' IN v_txt) > 0 THEN
    RAISE EXCEPTION '1288: the stored ph_pramana integrity_check_sql is not the chart-scoped text';
  END IF;
  SELECT to_jsonb(r) - 'integrity_check_sql' INTO v_rest FROM asset_registry r WHERE asset_id = 'ph_pramana';
  IF v_rest IS DISTINCT FROM (SELECT rest FROM _m1288_before) THEN
    RAISE EXCEPTION '1288: another column of the ph_pramana registry row changed';
  END IF;
END
$post$;
