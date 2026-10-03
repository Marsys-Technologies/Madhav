-- READ ONLY (run by the operator as suvarna_reader; hash-bound in the plan). Expected AFTER the 1265 plan applied (and unchanged after a rollback only for item 2-5).
-- 1. eleven triggers: the captured builder guard (O), the 8 new (A), the two existing repo triggers (O)
SELECT c.relname, t.tgname, t.tgenabled, t.tgtype FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
 WHERE c.relnamespace = 'public'::regnamespace AND NOT t.tgisinternal
   AND c.relname IN ('mimamsa_predictions', 'brahma_prospective_ledger', 'mimamsa_manifestation_sets', 'brahma_mimamsa_prediction_ledger') ORDER BY 1, 2;
-- 2. the six function bodies (expect the md5s bound in plan.txt), owners amjis_app, never SECURITY DEFINER, trigger guards not executable by PUBLIC
SELECT proname, md5(prosrc), pg_get_userbyid(proowner), prosecdef, proacl::text FROM pg_proc
 WHERE proname IN ('mimamsa_predictions_builder_guard', 'l5_frozen_withdrawal_authorizes', 'mimamsa_predictions_frozen_row_guard',
                   'brahma_prospective_ledger_frozen_row_guard', 'mimamsa_manifestation_sets_frozen_row_guard', 'brahma_mimamsa_prediction_ledger_delete_guard',
                   'l5_frozen_chart_cascade_authorizes') ORDER BY 1;
-- 3. the schema ACL is exactly as before (amjis_app has NO CREATE again)
SELECT has_schema_privilege('amjis_app', 'public', 'CREATE') AS amjis_app_can_create, (SELECT nspacl::text FROM pg_namespace WHERE nspname = 'public') AS schema_acl;
-- 4. no row changed: compare with verify_before_apply.sql item 5 and with before_state.json in the evidence directory
SELECT 'mimamsa_predictions' AS t, count(*) FROM mimamsa_predictions UNION ALL SELECT 'mimamsa_manifestation_sets', count(*) FROM mimamsa_manifestation_sets
UNION ALL SELECT 'brahma_prospective_ledger', count(*) FROM brahma_prospective_ledger UNION ALL SELECT 'brahma_mimamsa_prediction_ledger', count(*) FROM brahma_mimamsa_prediction_ledger;
-- 5. the deploy gate's role invariant (expect f)
SELECT has_schema_privilege('amjis_app', 'public', 'CREATE');
-- 6. STANDING CONSTRAINT: public.charts must not have FORCE ROW LEVEL SECURITY (run sql/verify_charts_rls_constraint.sql; expect verdict OK)
SELECT relforcerowsecurity AS charts_rls_forced, CASE WHEN relforcerowsecurity THEN 'FAIL: FORCE ROW LEVEL SECURITY on public.charts (revisit the 1265 guard)' ELSE 'OK' END AS verdict FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relname = 'charts';
-- 7. the two l5_frozen_* helpers are NOT executable by PUBLIC (expect false, false) and the cascade helper is SECURITY DEFINER (expect true)
SELECT has_function_privilege('public', to_regprocedure('public.l5_frozen_withdrawal_authorizes(uuid)'), 'EXECUTE') AS withdrawal_public_exec,
       has_function_privilege('public', to_regprocedure('public.l5_frozen_chart_cascade_authorizes(uuid)'), 'EXECUTE') AS cascade_public_exec,
       (SELECT prosecdef FROM pg_proc WHERE oid = to_regprocedure('public.l5_frozen_chart_cascade_authorizes(uuid)')) AS cascade_is_definer;
-- 8. INVARIANT: no non-owner, non-superuser role holds a write on the consent tables AND DELETE on a frozen table (expect 0 rows)
SELECT r.rolname FROM pg_roles r
 WHERE NOT r.rolsuper AND r.rolname NOT LIKE 'pg\_%' AND r.rolname <> 'amjis_app'
   AND (has_table_privilege(r.oid, 'public.chart_subject_consent', 'INSERT') OR has_table_privilege(r.oid, 'public.chart_subject_consent', 'UPDATE') OR has_table_privilege(r.oid, 'public.chart_subject_consent', 'DELETE')
     OR has_table_privilege(r.oid, 'public.chart_subject_deletion_disputes', 'INSERT') OR has_table_privilege(r.oid, 'public.chart_subject_deletion_disputes', 'UPDATE') OR has_table_privilege(r.oid, 'public.chart_subject_deletion_disputes', 'DELETE'))
   AND (has_table_privilege(r.oid, 'public.mimamsa_predictions', 'DELETE') OR has_table_privilege(r.oid, 'public.brahma_prospective_ledger', 'DELETE')
     OR has_table_privilege(r.oid, 'public.mimamsa_manifestation_sets', 'DELETE') OR has_table_privilege(r.oid, 'public.brahma_mimamsa_prediction_ledger', 'DELETE'));
