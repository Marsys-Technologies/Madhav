-- fn_1235_evidence_readback.sql — READ-ONLY post-apply readback for migration
-- 1235_ka_gochara_staged_candidate_evidence_function.sql (PR #3018, protected-class).
--
-- Emits labeled TSV rows (check<TAB>value...) that fn-1235-readbacks.sh asserts one by one:
--   * the function exists with the expected identity arguments and result type;
--   * owner is amjis_app, SECURITY DEFINER, search_path pinned to pg_catalog, pg_temp;
--   * one row per ACL entry (grantee, privilege, grantable) so the runner can assert the
--     exact set: EXECUTE to amjis_app / nirmana_campaign_control_writer /
--     nirmana_evidence_ingress_writer, NO PUBLIC entry, NO grant option for any non-owner;
--   * the ledger row with the applied file's sha256.
-- A missing function yields the single row 'function	MISSING' and nothing else (the
-- runner STOPs on it); every statement is a SELECT and the runner forces a read-only session.

SELECT 'function', CASE WHEN to_regprocedure(
         'public.ka_gochara_staged_candidate_has_runtime_evidence(text)') IS NULL
       THEN 'MISSING' ELSE 'present' END;

SELECT 'signature', pg_get_function_identity_arguments(p.oid), pg_get_function_result(p.oid)
  FROM pg_proc p
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)');

SELECT 'owner', pg_get_userbyid(p.proowner)
  FROM pg_proc p
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)');

SELECT 'security_definer', CASE WHEN p.prosecdef THEN 't' ELSE 'f' END
  FROM pg_proc p
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)');

SELECT 'search_path', COALESCE(array_to_string(p.proconfig, ' '), '')
  FROM pg_proc p
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)');

SELECT 'acl', pg_get_userbyid(a.grantee), a.privilege_type,
       CASE WHEN a.is_grantable THEN 't' ELSE 'f' END
  FROM pg_proc p,
       LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)')
 ORDER BY 2, 3, 4;

SELECT 'acl_public_entries', count(*)::text
  FROM pg_proc p,
       LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)')
   AND a.grantee = 0;

SELECT 'acl_non_owner_grant_options', count(*)::text
  FROM pg_proc p,
       LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
 WHERE p.oid = to_regprocedure('public.ka_gochara_staged_candidate_has_runtime_evidence(text)')
   AND a.is_grantable AND a.grantee <> p.proowner;

SELECT 'ledger', m.filename, m.sha256
  FROM public._migrations_applied m
 WHERE m.filename = '1235_ka_gochara_staged_candidate_evidence_function.sql';
