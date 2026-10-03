-- 1243_ka_gochara_inert_registry_rows.sql
--
-- Pravāha B (steward M20261003T020844-29ec): stage the two INERT Gochara asset_registry rows that exist
-- today ONLY in platform/scripts/seed/asset_registry_seed.ts —
--   ka_gochara_v4_41_candidate  (PR #2799, deployed; seed row asset_registry_seed.ts:2265)
--   ka_gochara_v5               (Pravāha A5.3, the a53 branch; seed row asset_registry_seed.ts:2306 on that branch)
-- so the orchestrator's writer-gap pre-flight stops failing every build run.
--
-- WHY. pipeline/orchestrator/runner.py (_check_writer_registry_gaps, :175-203; called at :1224-1243,
-- ORCHESTRATOR_WRITER_GAP_CHECK default 'enforce') selects every @register()'d writer id and requires an
-- asset_registry row with has_writer = true; ANY missing row marks the run 'failed' and sys.exit(1)s —
-- on any chart, before any asset is planned. ka_gochara_v4_41_candidate is @register()'d on main
-- (writers/ka_gochara_v4_41_candidate.py:287) but production has NO row for it: the seed is a manual script
-- (header: "Usage: DATABASE_URL=<url> npx tsx scripts/seed/asset_registry_seed.ts"), no workflow, package
-- script or migration runs it, and production's newest asset_registry.created_at is 2026-09-07 (bo_grounding),
-- i.e. the seed has not created a row there since #2799 deployed. The a53 train would add the same hazard for
-- ka_gochara_v5 (writers/ka_gochara_v5.py:280).
--
-- WHAT. Two INSERTs, ON CONFLICT (asset_id) DO NOTHING, in the seed upsert's own 28-column order
-- (ASSET_REGISTRY_UPSERT_SQL), every value taken from the seed entry by the seed's own derivation
-- (layer_name / layer_index / asset_type / asset_kind / catalog_status / writer governance as main() computes
-- them). Both rows are INERT: is_active = false (runPreparation.ts:183 and recalibrationEnqueue.ts:141 never
-- select them; the cockpit plan/stats routes filter is_active), depends_on = '{}' and nothing depends on them.
-- Columns the seed upsert does not name keep their table defaults (NULL / false), exactly as a seed run would.
-- ka_gochara_v5's row is the seed row AS IT IS (has_substeps = false, count over the 5.0 windows) — the A5.3
-- conformance gaps recorded in ka_gochara_v5_registry_conformance.test.ts are the activation step's to correct,
-- by a later routine migration; this one adds no judgment of its own.
--
-- SECOND PART (Codex R20-1; Suvarṇa's six conditions): ONE narrow SECURITY DEFINER boolean function,
--   public.ka_gochara_staged_candidate_has_runtime_evidence(p_asset_id text) RETURNS boolean
-- used by the Nirmāṇa elevation loaders (monitor, snapshot, the five definitions loaders) to decide whether a staged candidate still has the inert
-- shape. It answers "is there ANY receipt / build_run_assets / asset_throughput row for this id" without granting any role SELECT on those tables
-- (the control writer has none on asset_throughput; the watchdog PRUNES old build_run_assets, so build evidence alone is not permanent; a cockpit
-- refresh inserts throughput with no build run). Owner amjis_app; REVOKE ALL FROM PUBLIC; EXECUTE only amjis_app and
-- nirmana_campaign_control_writer; search_path pinned (pg_catalog, pg_temp) with schema-qualified tables; STABLE; returns boolean only; ANY id other
-- than ka_gochara_v4_41_candidate / ka_gochara_v5 RAISES. A role that does not exist in a fresh environment is skipped (production has both; the
-- readback asserts the ACL).
--
-- NOT (first part). No chart data, no other asset_registry row, no other table — that narrow write scope is established by the
-- single INSERT below (and the table's one UPDATE trigger), not by the post-checks. The post-checks raise (rolling the migration back) if
-- either row is missing or not inert, if anything depends on them, or if a SUPPLEMENTARY check of visible tuple versions (xmin = this
-- transaction's id) finds another asset_registry row version written by this transaction. That last check is NOT proof that nothing else was
-- touched (it cannot see deleted rows, subtransaction writes or other tables). A row that ALREADY exists is left exactly as it is (DO NOTHING)
-- and must satisfy the same inertness check. The second part's only objects are the one function and its ACL (no grant on any table).

DO $mig$
DECLARE
  v_touched_other int;
  v_ok int;
BEGIN
  INSERT INTO asset_registry (
    asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql, target_floor,
    expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, estimated_seconds,
    asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status,
    asset_kind, has_writer, has_substeps, writer_timeout_seconds
  ) VALUES
  (
    'ka_gochara_v4_41_candidate', -- asset_id
    'kala', -- layer
    141, -- sort_order
    'Gocara-Pratijñā 4.1', -- sanskrit_name
    'Gochara ''4.1'' Candidate (Pravāha A2.5)', -- english_name
    'PRAVĀHA A2.5 heavy writer: the ''4.1'' gochara CANDIDATE chain (step06 enumerate → candidate build → class context → windows projection, scripts/kala_gochara_cutover/) run inside the governed build pipeline. Substeps: manifest → body:<Body> ×8 → windows, each idempotent (delete-then-insert scoped chart × ''4.1'' × sub-span) on ctx.db_conn. Candidate-only: the ledger guards (_require_not_published) and the serving-side authority filter make ''4.1'' unreachable until a steward flip this asset cannot perform.', -- english_description
    'postgres_table', -- storage_type
    'kala_gochara_windows', -- target_table
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.1''', -- count_sql
    'SELECT pg_total_relation_size(''kala_gochara_windows'')', -- size_sql
    0, -- target_floor
    NULL, -- expected_volume_formula
    NULL, -- expected_volume_inputs
    '''4.1'' candidate windows over the narrowed scored horizon [1998-01-01, 2026-04-18) — era/month/day tiers per event class. Candidate-only generation; the count stays 0 until the steward-dispatched run lands.', -- volume_explanation
    '{}'::text[], -- depends_on
    'per_chart', -- scope
    false, -- is_active
    NULL, -- estimated_seconds
    'data', -- asset_type
    'Kāla', -- layer_name
    'L3', -- layer_index
    NULL, -- provides_apis
    NULL, -- health_probe
    'CURRENT', -- catalog_status
    'data', -- asset_kind
    true, -- has_writer
    true, -- has_substeps
    7200 -- writer_timeout_seconds
  ),
  (
    'ka_gochara_v5', -- asset_id
    'kala', -- layer
    142, -- sort_order
    'Gocara-Pratijñā 5.0', -- sanskrit_name
    'Gochara ''5.0'' Writer Skeleton (Pravāha A5.3, INERT)', -- english_name
    'PRAVĀHA A5.3 INERT skeleton: registered WriterBase writer ka_gochara_v5 (@register, asset_id pinned, light shape) with a hard chart-scope refusal (only chart 482012f1-710e-4a25-994a-93821f5871aa admitted) and every execution path raising NotImplementedError pending steward pins 3-7 (ruling M20261001T014547-357e pins 1-2). Never commits/rolls back/closes ctx.db_conn, opens no connection, writes no asset_throughput — no DB touch at all. Registration + inertness ONLY; the geometry/solver is a separate governed step.', -- english_description
    'postgres_table', -- storage_type
    'kala_gochara_windows', -- target_table
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''5.0''', -- count_sql
    'SELECT pg_total_relation_size(''kala_gochara_windows'')', -- size_sql
    0, -- target_floor
    NULL, -- expected_volume_formula
    NULL, -- expected_volume_inputs
    'Placeholder surface for the pending ''5.0'' generation — the skeleton writes NOTHING (every path raises NotImplementedError), so the count stays 0 until steward pins 3-7 land and the geometry/solver is implemented under a later governed step.', -- volume_explanation
    '{}'::text[], -- depends_on
    'per_chart', -- scope
    false, -- is_active
    NULL, -- estimated_seconds
    'data', -- asset_type
    'Kāla', -- layer_name
    'L3', -- layer_index
    NULL, -- provides_apis
    NULL, -- health_probe
    'CURRENT', -- catalog_status
    'data', -- asset_kind
    true, -- has_writer
    false, -- has_substeps
    600 -- writer_timeout_seconds
  )
  ON CONFLICT (asset_id) DO NOTHING;

  -- Post-check 1 (supplementary check of visible tuple versions, not proof that nothing else was touched): no other asset_registry row
  -- version in this transaction.
  SELECT count(*) INTO v_touched_other
    FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid
     AND asset_id NOT IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5');
  IF v_touched_other <> 0 THEN
    RAISE EXCEPTION '1243: % other asset_registry row(s) were modified by this migration', v_touched_other;
  END IF;

  -- Post-check 2: both rows exist and are inert writers with no dependencies.
  SELECT count(*) INTO v_ok
    FROM asset_registry
   WHERE asset_id IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5')
     AND is_active IS FALSE
     AND has_writer IS TRUE
     AND COALESCE(depends_on, '{}'::text[]) = '{}'::text[];
  IF v_ok <> 2 THEN
    RAISE EXCEPTION '1243: expected both ka_gochara_v4_41_candidate and ka_gochara_v5 to exist with is_active=false, has_writer=true, depends_on={} — found % matching row(s)', v_ok;
  END IF;

  -- Post-check 3: no asset depends on either (no DAG build can schedule them).
  SELECT count(*) INTO v_ok
    FROM asset_registry
   WHERE depends_on && ARRAY['ka_gochara_v4_41_candidate', 'ka_gochara_v5']::text[];
  IF v_ok <> 0 THEN
    RAISE EXCEPTION '1243: % asset(s) depend on the inert rows', v_ok;
  END IF;
END
$mig$;

-- ── Part 2: the evidence function ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(p_asset_id text)
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
BEGIN
  IF p_asset_id IS NULL OR p_asset_id NOT IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5') THEN
    RAISE EXCEPTION 'ka_gochara_staged_candidate_has_runtime_evidence: % is not a staged Gochara candidate', p_asset_id
      USING ERRCODE = 'invalid_parameter_value';
  END IF;
  RETURN EXISTS (SELECT 1 FROM public.asset_provenance_receipts WHERE asset_id = p_asset_id)
      OR EXISTS (SELECT 1 FROM public.build_run_assets WHERE asset_id = p_asset_id)
      OR EXISTS (SELECT 1 FROM public.asset_throughput WHERE asset_id = p_asset_id);
END
$fn$;

REVOKE ALL ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) FROM PUBLIC;

DO $acl$
DECLARE
  v_fn  regprocedure := 'public.ka_gochara_staged_candidate_has_runtime_evidence(text)'::regprocedure;
  v_owner name;
  v_bad int;
BEGIN
  -- EXECUTE for exactly amjis_app (the app / monitor / snapshot role) and nirmana_campaign_control_writer (the definitions loaders).
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO amjis_app;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO nirmana_campaign_control_writer;
  END IF;

  -- Post-checks (each raises, rolling the migration back whole).
  SELECT pg_get_userbyid(proowner) INTO v_owner FROM pg_proc WHERE oid = v_fn;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') AND v_owner <> 'amjis_app' THEN
    RAISE EXCEPTION '1243: the evidence function is owned by %, expected amjis_app', v_owner;
  END IF;
  IF NOT (SELECT prosecdef FROM pg_proc WHERE oid = v_fn) THEN
    RAISE EXCEPTION '1243: the evidence function is not SECURITY DEFINER';
  END IF;
  IF (SELECT proconfig FROM pg_proc WHERE oid = v_fn) IS DISTINCT FROM ARRAY['search_path=pg_catalog, pg_temp']::text[] THEN
    RAISE EXCEPTION '1243: the evidence function search_path is not pinned to pg_catalog, pg_temp (found %)', (SELECT proconfig FROM pg_proc WHERE oid = v_fn);
  END IF;
  -- ACL: no PUBLIC entry (grantee 0) and no grantee outside {owner, amjis_app, nirmana_campaign_control_writer}.
  SELECT count(*) INTO v_bad
    FROM pg_proc p, LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
   WHERE p.oid = v_fn
     AND (a.grantee = 0 OR a.privilege_type <> 'EXECUTE'
          OR pg_get_userbyid(a.grantee) NOT IN (v_owner::text, 'amjis_app', 'nirmana_campaign_control_writer'));
  IF v_bad <> 0 THEN
    RAISE EXCEPTION '1243: the evidence function ACL has % unexpected entr(y/ies) (PUBLIC or a non-approved grantee)', v_bad;
  END IF;
  -- It runs, and it refuses any other id.
  PERFORM public.ka_gochara_staged_candidate_has_runtime_evidence('ka_gochara_v5');
  BEGIN
    PERFORM public.ka_gochara_staged_candidate_has_runtime_evidence('bg_texts');
    RAISE EXCEPTION '1243: the evidence function accepted an id that is not a staged candidate';
  EXCEPTION WHEN invalid_parameter_value THEN
    NULL;
  END;
END
$acl$;
