-- 1408_ka_vedha_gochara_writer_timeout_600.sql
--
-- SR-VEDHA-WRITER-BUDGET (owner surrogate, 2026-10-22, R2 (a)): raise asset_registry.writer_timeout_seconds of ka_vedha_gochara from 120 s to 600 s.
-- Data-only: ONE column of ONE asset_registry row, no DDL, no new object. Transaction ownership belongs to platform/scripts/migrate.ts
-- (no BEGIN/COMMIT here). Same pattern as migrations 1218, 1296, 1329 and 1395.
--
-- WHY. The K9 round-B rehearsal (K9B_REHEARSAL.md section 5) built ka_vedha_gochara in the same process as ka_yojaka on a loaded Mac. With the
-- production budget of 120 s the orchestrator watchdog (runner.py execute_dag, JL-023) marked it TIMEOUT and left ka_gochara, ka_sangam and
-- ka_vighnakara blocked_dependency. With the budget lifted the writer completed in 120.8 s (rep r3) and 196.3 s (rep r4), both upper bounds (machine load
-- 33-104 on 18 cores). 600 s is 3.06x the larger of the two. The audit of every other K9 / century-path writer budget is in
-- platform/python-sidecar/tests/l3/kala_db/writer_budget_audit_1408.json; no other writer has a recorded measurement that its budget falls
-- below 2x of, so this migration touches ka_vedha_gochara only.
--
-- GUARD (never a silent change, idempotent).  The row is read FOR UPDATE under the lock_timeout below.
--   * row absent                          -> RAISE, nothing changed;
--   * writer_timeout_seconds = 120        -> set 600 (the one transition this migration exists for);
--   * writer_timeout_seconds = 600        -> already landed (a fresh registry seeded at the seed value, or a replay): NOTICE, nothing is written;
--   * NULL or any other value             -> RAISE (ambiguous: somebody set it for a reason this migration cannot see), nothing changed.
-- After an UPDATE: ROW_COUNT must be exactly 1; the row re-read must show 600; the whole row minus writer_timeout_seconds must equal what was read
-- before; no OTHER asset_registry row version may have been written by this transaction (xmin check, the 1304/1395 pattern).
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation fires only AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table; writer_timeout_seconds is not among them.
--
-- NOT PROTECTED. A plain UPDATE: no public-schema DDL, so it is in neither PROTECTED_PUBLIC_SCHEMA_MIGRATIONS nor PROTECTED_DATA_PLANE_MIGRATIONS.
--
-- Seed: platform/scripts/seed/asset_registry_seed.ts carries writer_timeout_seconds: 600 explicitly for ka_vedha_gochara (its ON CONFLICT preserves
-- live values, so the seed only governs a fresh registry).
--
-- Post-apply verification (read-only):
--   SELECT asset_id, writer_timeout_seconds, is_active, has_writer, has_substeps FROM asset_registry WHERE asset_id = 'ka_vedha_gochara';
--     -- expect 600 | t | t | f
--
-- ROLLBACK (not executed by migrate.ts):
--   UPDATE asset_registry SET writer_timeout_seconds = 120 WHERE asset_id = 'ka_vedha_gochara' AND writer_timeout_seconds = 600;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $m1408$
DECLARE
  v_before  jsonb;
  v_after   jsonb;
  v_cur     integer;
  v_changed integer;
  v_other   integer;
BEGIN
  SELECT to_jsonb(r) INTO v_before
    FROM asset_registry r
   WHERE r.asset_id = 'ka_vedha_gochara'
     FOR UPDATE;
  IF v_before IS NULL THEN
    RAISE EXCEPTION '1408: ka_vedha_gochara has no asset_registry row; nothing was changed';
  END IF;

  v_cur := (v_before ->> 'writer_timeout_seconds')::integer;
  IF v_cur = 600 THEN
    RAISE NOTICE '1408: ka_vedha_gochara writer_timeout_seconds is already 600; nothing was changed';
    RETURN;
  END IF;
  IF v_cur IS DISTINCT FROM 120 THEN
    RAISE EXCEPTION '1408: refusing to change ka_vedha_gochara: writer_timeout_seconds is % (expected exactly 120, or 600 when already landed); nothing was changed', coalesce(v_cur::text, 'NULL');
  END IF;

  UPDATE asset_registry
     SET writer_timeout_seconds = 600
   WHERE asset_id = 'ka_vedha_gochara'
     AND writer_timeout_seconds = 120;

  GET DIAGNOSTICS v_changed = ROW_COUNT;
  IF v_changed <> 1 THEN
    RAISE EXCEPTION '1408: expected to update exactly one asset_registry row (ka_vedha_gochara), updated %', v_changed;
  END IF;

  SELECT to_jsonb(r) INTO v_after FROM asset_registry r WHERE r.asset_id = 'ka_vedha_gochara';
  IF (v_after ->> 'writer_timeout_seconds') IS DISTINCT FROM '600' THEN
    RAISE EXCEPTION '1408: ka_vedha_gochara writer_timeout_seconds update did not take (expected 600, found %)', coalesce(v_after ->> 'writer_timeout_seconds', 'NULL');
  END IF;
  IF (v_after - 'writer_timeout_seconds') IS DISTINCT FROM (v_before - 'writer_timeout_seconds') THEN
    RAISE EXCEPTION '1408: a column other than writer_timeout_seconds changed on ka_vedha_gochara; the migration must touch ONLY that column';
  END IF;

  SELECT count(*) INTO v_other
    FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid
     AND asset_id <> 'ka_vedha_gochara';
  IF v_other <> 0 THEN
    RAISE EXCEPTION '1408: % other asset_registry row version(s) were written by this transaction; the migration must touch ONLY ka_vedha_gochara', v_other;
  END IF;
END
$m1408$;
