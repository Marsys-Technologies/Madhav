-- 1235_ka_gochara_staged_candidate_evidence_function.sql   (PROTECTED-CLASS — applies ONLY in the protected public-schema window)
--
-- Pravāha B (steward M20261003T131532-b179; Suvarṇa-approved split of #2996). ONE narrow SECURITY DEFINER boolean function,
--   public.ka_gochara_staged_candidate_has_runtime_evidence(p_asset_id text) RETURNS boolean
-- answering "is there ANY asset_provenance_receipts / build_run_assets / asset_throughput row for this staged Gochara candidate" for the Nirmāṇa
-- elevation loaders, without granting any role SELECT on asset_throughput (the control writer and the ingress writer hold none). The routine rows
-- migration 1243 (two INERT asset_registry rows) lands first and its loaders use a receipts-OR-build_run_assets predicate (the cockpit watchdog prunes
-- build_run_assets, so that predicate has a documented limit); this function closes the limit, and a LATER routine code change switches the loaders to it.
--
-- WHY PROTECTED. Creating a function in schema public needs CREATE on public, which the ordinary migration role (amjis_app) does NOT hold
-- (USAGE only; deploy.yml protected-migration comment; data-plane-ownership-status.ts rejects a persistent CREATE for amjis_app). The protected window
-- (deploy.yml job "Apply Protected Public-Schema Migrations") grants amjis_app a bounded schema-CREATE capability, applies the exact --only list, and
-- revokes it. The file is declared in migrate.ts PROTECTED_PUBLIC_SCHEMA_MIGRATIONS so the routine runner refuses it by name.
-- NUMBER 1235: free everywhere; below 1240, so the window's --only predecessor rule (every unapplied file numbered <= the highest selected must be
-- selected) needs nothing beyond the files the window already applies. It must NOT reach `main` without its migrate.ts set entry.
--
-- THE FUNCTION. Owner amjis_app (the window's migration principal); SECURITY DEFINER; SET search_path = pg_catalog, pg_temp; tables schema-qualified;
-- STABLE; returns boolean only; ANY id other than ka_gochara_v4_41_candidate / ka_gochara_v5 (and NULL) RAISES invalid_parameter_value.
-- ACL: REVOKE ALL FROM PUBLIC; EXECUTE granted ONLY to amjis_app, nirmana_campaign_control_writer and nirmana_evidence_ingress_writer (each only if the
-- role exists — a fresh environment without it skips; production has all three and the readback asserts the ACL).
--
-- POST-CHECKS (each RAISE rolls the migration back whole): owner = amjis_app when that role exists; prosecdef; proconfig exactly
-- {"search_path=pg_catalog, pg_temp"}; the ACL has NO PUBLIC entry, no privilege other than EXECUTE, no grantee outside {owner, the three roles}, and NO
-- grant option for any non-owner (is_grantable — a pre-existing grant WITH GRANT OPTION, which CREATE OR REPLACE would preserve, is rejected); the
-- function runs and refuses a non-candidate id.
--
-- NOT: no table, no data, no table privilege, no other function. Rollback note: never REVOKE blindly — author a new reviewed migration.

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
  v_fn    regprocedure := 'public.ka_gochara_staged_candidate_has_runtime_evidence(text)'::regprocedure;
  v_owner name;
  v_bad   int;
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO amjis_app;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO nirmana_campaign_control_writer;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO nirmana_evidence_ingress_writer;
  END IF;

  SELECT pg_get_userbyid(proowner) INTO v_owner FROM pg_proc WHERE oid = v_fn;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') AND v_owner <> 'amjis_app' THEN
    RAISE EXCEPTION '1235: the evidence function is owned by %, expected amjis_app', v_owner;
  END IF;
  IF NOT (SELECT prosecdef FROM pg_proc WHERE oid = v_fn) THEN
    RAISE EXCEPTION '1235: the evidence function is not SECURITY DEFINER';
  END IF;
  IF (SELECT proconfig FROM pg_proc WHERE oid = v_fn) IS DISTINCT FROM ARRAY['search_path=pg_catalog, pg_temp']::text[] THEN
    RAISE EXCEPTION '1235: the evidence function search_path is not pinned to pg_catalog, pg_temp (found %)', (SELECT proconfig FROM pg_proc WHERE oid = v_fn);
  END IF;
  -- ACL: no PUBLIC entry, only EXECUTE, only {owner + the three loader roles}, and no grant option for any non-owner.
  SELECT count(*) INTO v_bad
    FROM pg_proc p, LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
   WHERE p.oid = v_fn
     AND (a.grantee = 0
          OR a.privilege_type <> 'EXECUTE'
          OR pg_get_userbyid(a.grantee) NOT IN (v_owner::text, 'amjis_app', 'nirmana_campaign_control_writer', 'nirmana_evidence_ingress_writer')
          OR (a.is_grantable AND a.grantee <> p.proowner));
  IF v_bad <> 0 THEN
    RAISE EXCEPTION '1235: the evidence function ACL has % unexpected entr(y/ies) (PUBLIC, a non-approved grantee, a non-EXECUTE privilege or a grant option)', v_bad;
  END IF;
  PERFORM public.ka_gochara_staged_candidate_has_runtime_evidence('ka_gochara_v5');
  BEGIN
    PERFORM public.ka_gochara_staged_candidate_has_runtime_evidence('bg_texts');
    RAISE EXCEPTION '1235: the evidence function accepted an id that is not a staged candidate';
  EXCEPTION WHEN invalid_parameter_value THEN
    NULL;
  END;
END
$acl$;
