-- Read-only post-apply readback for the protected-class migration 1235 (the staged-candidate evidence function) — run AFTER the protected window.
SELECT filename, sha256 FROM _migrations_applied WHERE filename = '1235_ka_gochara_staged_candidate_evidence_function.sql';   -- expect 1 row; sha256 = the PR's pinned value
SELECT pg_get_userbyid(proowner) AS proowner,            -- expect amjis_app
       prosecdef,                                        -- expect t
       proconfig,                                        -- expect {"search_path=pg_catalog, pg_temp"}
       provolatile,                                      -- expect s
       prorettype::regtype AS returns                    -- expect boolean
  FROM pg_proc WHERE oid = 'public.ka_gochara_staged_candidate_has_runtime_evidence(text)'::regprocedure;
SELECT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END AS grantee, a.privilege_type, a.is_grantable
  FROM pg_proc p, LATERAL aclexplode(p.proacl) a
 WHERE p.oid = 'public.ka_gochara_staged_candidate_has_runtime_evidence(text)'::regprocedure
 ORDER BY 1;   -- expect exactly: amjis_app, nirmana_campaign_control_writer, nirmana_evidence_ingress_writer — each EXECUTE, is_grantable f; NO PUBLIC row
SELECT public.ka_gochara_staged_candidate_has_runtime_evidence('ka_gochara_v4_41_candidate') AS v41, public.ka_gochara_staged_candidate_has_runtime_evidence('ka_gochara_v5') AS v5;   -- expect f | f while no evidence exists
SELECT has_schema_privilege('amjis_app', 'public', 'CREATE') AS amjis_app_can_create_in_public;   -- expect f (the window's bounded CREATE grant was revoked)
