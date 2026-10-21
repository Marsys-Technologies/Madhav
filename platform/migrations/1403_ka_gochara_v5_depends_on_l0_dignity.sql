-- 1403_ka_gochara_v5_depends_on_l0_dignity.sql
--
-- K8 registry edge (owner surrogate SR-K8-EDGE-1403): add ONE element, bg_dignity_reference, to asset_registry.depends_on of ka_gochara_v5.
-- Data-only: ONE column (depends_on) of ONE asset_registry row, no DDL, no new object. Transaction ownership belongs to platform/scripts/migrate.ts
-- (no BEGIN/COMMIT here). Same guarded-DO pattern as migration 1395.
--
-- WHY. ka_gochara_v5 reads three L0 reference tables that its registry row did not declare: bg_dignity_reference, bg_graha_naisargika_friendship and
-- bg_combustion_orbs (services/gochara_kernel/p1_operands.py:109-111 and p1_operands_check.py:85-90, bound by input_vector.build_input_vector and
-- ka_gochara_v5._l0_consumed). Migration 1392 (K8-REG) declared {ga_positions, ga_dashas, bg_transit_rules} and missed them. depends_on drives Nirmana
-- receipt invalidation and the build order, so a later change to those L0 rows (for example migration 1401, node dignity / friendship) could not mark
-- ka_gochara_v5 stale. The platform/scripts/governance test test_k8_registry_reads.py found it (it derives the read set from the real writer SQL).
--
-- THE PRODUCER (exactly one, for all three tables). The registered L0 writer bg_dignity_reference
-- (pipeline/orchestrator/writers/bg_dignity_reference.py:386-390) seeds bg_dignity_reference, bg_graha_naisargika_friendship AND bg_combustion_orbs;
-- its registry row (asset_registry_seed.ts, bg_dignity_reference: target_table bg_dignity_reference, count_sql over all five sub-tables) is the only
-- active owner of each of the three (asset_census.build_table_owners). bg_combustion_orbs has no producer of its own.
--
-- GUARD (never a silent no-op, 1395 style). The row is read FOR UPDATE under the lock_timeout below. The migration changes the row ONLY when
-- depends_on is exactly the 1392 array {ga_positions,ga_dashas,bg_transit_rules} (order included). It also refuses, changing nothing, when:
--   * the ka_gochara_v5 row is absent;
--   * depends_on is any other array (the pre-1392 pair, a hand edit, anything);
--   * bg_dignity_reference is absent, inactive, has no writer or is not global (a dependency trap, as in 1226);
--   * bg_dignity_reference reaches ka_gochara_v5 through its own depends_on (the edge would close a cycle).
-- IDEMPOTENT: when depends_on already equals the four-element result the migration returns with a NOTICE and writes nothing (no row version, so the
-- trigger below cannot fire a second time). After the UPDATE: ROW_COUNT must be exactly 1; the row re-read must show the four-element array; the whole row
-- minus depends_on must be identical to what was read before (every other column, including any column added later); and no OTHER asset_registry row
-- version may have been written by this transaction (xmin check, the 1304/1395 pattern).
--
-- SERVING EFFECT AT APPLY (binding; measured, platform/python-sidecar/tests/l3/kala_db/test_k8_edge_1403.py on the prod-shaped local fixture).
-- nirmana_registry_receipt_invalidation (migration 596; AFTER UPDATE OF depends_on, ..., FOR EACH ROW WHEN OLD IS DISTINCT FROM NEW) runs
-- `UPDATE asset_freshness SET freshness_state='stale', reasons += 'registry_changed' WHERE asset_id = NEW.asset_id` with NO chart filter. So the moment
-- this UPDATE lands, every asset_freshness row of ka_gochara_v5 (one per chart that ever ran the v5 small test, at most the pinned candidate chart)
-- reads 'stale'. The last receipt row is kept; only the projection flips. NOTHING ELSE moves: no other asset's freshness or receipt row, no
-- asset_throughput row, no served generation head, no L2+ row, no build_runs row (the fixture compares every table before and after). ka_gochara_v5 is
-- inactive (is_active false), nothing depends on it, no served surface reads its freshness, and no code path reacts to the edit by rebuilding or
-- invalidating anything else: the trigger is the only reaction, no job polls asset_registry, and the seed's ON CONFLICT keeps the live depends_on. A governed
-- ka_gochara_v5 build is the only thing that restores 'fresh' (and the next dispatch sees a one-time upstream-digest change, by design).
-- LATER, NOT AT APPLY: bg_dignity_reference is now upstream of ka_gochara_v5, so a future governed BUILD of bg_dignity_reference marks the v5 asset_throughput
-- rows of the run's chart stale (staleness.propagate_downstream_staleness, runner.py on_complete) and its cascade/clear previews list v5; ka_vighnakara
-- already has the same edge. Deploy with no ka_gochara_v5 build in flight (a running build would hit the dependency gate on its next dispatch).
--
-- NOT PROTECTED. A plain UPDATE: no public-schema DDL, so it is in neither PROTECTED_PUBLIC_SCHEMA_MIGRATIONS nor PROTECTED_DATA_PLANE_MIGRATIONS and not in
-- kala_protected_migrations.txt. The routine deploy-time runner applies it.
--
-- Seed: platform/scripts/seed/asset_registry_seed.ts carries the same four-element depends_on for ka_gochara_v5 (its ON CONFLICT keeps live depends_on, so the seed
-- cannot apply this edge on its own). Nirmana: platform/src/lib/nirmana-elevation/definitions.ts declaredDependsOn for ka_gochara_v5 carries the same set, so the
-- staged-inert exclusion keeps matching the live row.
--
-- Post-apply verification (read-only):
--   SELECT asset_id, depends_on, is_active, has_writer, has_substeps, writer_timeout_seconds FROM asset_registry WHERE asset_id = 'ka_gochara_v5';
--     -- expect ka_gochara_v5 | {ga_positions,ga_dashas,bg_transit_rules,bg_dignity_reference} | f | t | t | 72000
--   Fingerprint of the row (the same 28-column md5 platform/scripts/gochara-window-readbacks.sh uses for the 1243 pin), computed in the guarded local fixture
--   by replaying the real 1243, 1304, 1395 and 1392 over the baseline registry DDL (the 1243 step reproduces the pinned 49995b52b7c416c8e0ef8f43b1158b57):
--     after 1395 8339e7adcbc90d0c62f50c4e62815b33 | after 1392 4806fad946bdc9b90f378e138278478c | after 1403 97b54242cb98bce22e0300654ba4b660
--   SELECT md5(row(asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql,
--     target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds, asset_type, layer_name,
--     layer_index, provides_apis, health_probe, catalog_status, asset_kind, has_writer, has_substeps, writer_timeout_seconds)::text)
--     FROM asset_registry WHERE asset_id = 'ka_gochara_v5';   -- expect 97b54242cb98bce22e0300654ba4b660
--
-- ROLLBACK (not executed by migrate.ts; it fires the same trigger and stales the same rows again):
--   UPDATE asset_registry SET depends_on = '{ga_positions,ga_dashas,bg_transit_rules}' WHERE asset_id = 'ka_gochara_v5'
--      AND depends_on = '{ga_positions,ga_dashas,bg_transit_rules,bg_dignity_reference}';

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $m1403$
DECLARE
  v_edge     constant jsonb := $k8_edge$
{"asset_id":"ka_gochara_v5","producer":"bg_dignity_reference","from":["ga_positions","ga_dashas","bg_transit_rules"],"to":["ga_positions","ga_dashas","bg_transit_rules","bg_dignity_reference"]}
$k8_edge$;
  v_target   constant text   := v_edge ->> 'asset_id';
  v_producer constant text   := v_edge ->> 'producer';
  v_from     text[] := ARRAY(SELECT jsonb_array_elements_text(v_edge -> 'from'));
  v_to       text[] := ARRAY(SELECT jsonb_array_elements_text(v_edge -> 'to'));
  v_before   jsonb;
  v_after    jsonb;
  v_cur      text[];
  v_changed  integer;
  v_other    integer;
BEGIN
  SELECT to_jsonb(r), r.depends_on INTO v_before, v_cur
    FROM asset_registry r
   WHERE r.asset_id = v_target
     FOR UPDATE;
  IF v_before IS NULL THEN
    RAISE EXCEPTION '1403: % has no asset_registry row; nothing was changed', v_target;
  END IF;

  IF v_cur IS NOT DISTINCT FROM v_to THEN
    RAISE NOTICE '1403: % depends_on already holds %; nothing to do', v_target, v_to;
    RETURN;
  END IF;
  IF v_cur IS DISTINCT FROM v_from THEN
    RAISE EXCEPTION '1403: refusing to change %: depends_on is % (expected exactly %, the migration-1392 value); nothing was changed', v_target, coalesce(v_cur::text, 'NULL'), v_from;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM asset_registry p WHERE p.asset_id = v_producer AND p.is_active IS TRUE AND p.has_writer IS TRUE AND p.scope = 'global') THEN
    RAISE EXCEPTION '1403: refusing: producer % is missing, inactive, has no writer or is not global; nothing was changed', v_producer;
  END IF;
  IF v_producer = v_target OR EXISTS (
    WITH RECURSIVE up(asset_id) AS (
      SELECT unnest(p.depends_on) FROM asset_registry p WHERE p.asset_id = v_producer
      UNION
      SELECT unnest(r.depends_on) FROM asset_registry r JOIN up ON r.asset_id = up.asset_id
    )
    SELECT 1 FROM up WHERE up.asset_id = v_target
  ) THEN
    RAISE EXCEPTION '1403: refusing: % depends on % (directly or through its own depends_on), the edge would close a cycle; nothing was changed', v_producer, v_target;
  END IF;

  UPDATE asset_registry
     SET depends_on = v_to
   WHERE asset_id = v_target
     AND depends_on = v_from;

  GET DIAGNOSTICS v_changed = ROW_COUNT;
  IF v_changed <> 1 THEN
    RAISE EXCEPTION '1403: expected to update exactly one asset_registry row (%), updated %', v_target, v_changed;
  END IF;

  SELECT to_jsonb(r) INTO v_after FROM asset_registry r WHERE r.asset_id = v_target;
  IF (v_after -> 'depends_on') IS DISTINCT FROM to_jsonb(v_to) THEN
    RAISE EXCEPTION '1403: % depends_on update did not take (expected %, found %)', v_target, v_to, coalesce(v_after ->> 'depends_on', 'NULL');
  END IF;
  IF (v_after - 'depends_on') IS DISTINCT FROM (v_before - 'depends_on') THEN
    RAISE EXCEPTION '1403: a column other than depends_on changed on %; the migration must touch ONLY that column', v_target;
  END IF;

  -- Supplementary check of visible tuple versions: no OTHER asset_registry row version was written by this transaction.
  SELECT count(*) INTO v_other
    FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid
     AND asset_id <> v_target;
  IF v_other <> 0 THEN
    RAISE EXCEPTION '1403: % other asset_registry row version(s) were written by this transaction; the migration must touch ONLY %', v_other, v_target;
  END IF;
END
$m1403$;
