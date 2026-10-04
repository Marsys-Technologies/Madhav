-- READ ONLY (run by the operator as suvarna_reader; hash-bound in the plan). Expected BEFORE the 1265 plan applies.
-- 1. none of the new objects exists (expect 0 and 0)
SELECT (SELECT count(*) FROM pg_proc WHERE proname IN ('l5_frozen_withdrawal_authorizes', 'mimamsa_predictions_frozen_row_guard',
          'brahma_prospective_ledger_frozen_row_guard', 'mimamsa_manifestation_sets_frozen_row_guard', 'brahma_mimamsa_prediction_ledger_delete_guard')) AS new_functions,
       (SELECT count(*) FROM pg_trigger WHERE tgname LIKE '%frozen_row_guard%' OR tgname LIKE 'brahma_mimamsa_prediction_ledger_delete_guard%') AS new_triggers;
-- 2. the captured live-only builder guard is live as captured (expect md5 46c23854275c2712b30860a2b174adb2, 1084, amjis_app, {amjis_app=X/amjis_app}, tgtype 15, enabled O)
SELECT md5(p.prosrc), length(convert_to(p.prosrc, 'UTF8')), pg_get_userbyid(p.proowner), p.proacl::text, p.proconfig::text,
       (SELECT tgtype || '/' || tgenabled FROM pg_trigger WHERE tgname = 'mimamsa_predictions_builder_guard')
  FROM pg_proc p WHERE p.proname = 'mimamsa_predictions_builder_guard';
-- 3. the recorded builder grants (expect DELETE,INSERT,SELECT / amjis_app on both tables)
SELECT c.relname, string_agg(a.privilege_type, ',' ORDER BY a.privilege_type), min(pg_get_userbyid(a.grantor))
  FROM pg_class c, aclexplode(c.relacl) a
 WHERE c.relname IN ('mimamsa_predictions', 'mimamsa_manifestation_sets') AND c.relnamespace = 'public'::regnamespace AND a.grantee = 'data_plane_builder'::regrole
 GROUP BY 1 ORDER BY 1;
-- 4. schema public: amjis_app has USAGE and NO CREATE (expect f), and the schema ACL text (kept; compare after)
SELECT has_schema_privilege('amjis_app', 'public', 'CREATE') AS amjis_app_can_create, (SELECT nspacl::text FROM pg_namespace WHERE nspname = 'public') AS schema_acl;
-- 5. frozen-set baseline (row counts per table; the executor binds the md5s)
SELECT 'mimamsa_predictions' AS t, count(*) FROM mimamsa_predictions UNION ALL SELECT 'mimamsa_manifestation_sets', count(*) FROM mimamsa_manifestation_sets
UNION ALL SELECT 'brahma_prospective_ledger', count(*) FROM brahma_prospective_ledger UNION ALL SELECT 'brahma_mimamsa_prediction_ledger', count(*) FROM brahma_mimamsa_prediction_ledger;
-- 6. STANDING CONSTRAINT: public.charts must not have FORCE ROW LEVEL SECURITY (run sql/verify_charts_rls_constraint.sql; expect verdict OK)
SELECT relforcerowsecurity AS charts_rls_forced, CASE WHEN relforcerowsecurity THEN 'FAIL: FORCE ROW LEVEL SECURITY on public.charts (revisit the 1265 guard)' ELSE 'OK' END AS verdict FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relname = 'charts';
-- 7. INVARIANT (the script's gate RAISES on it): no non-owner, non-superuser role holds a write on the consent tables AND DELETE on a frozen table (expect 0 rows)
SELECT r.rolname FROM pg_roles r
 WHERE NOT r.rolsuper AND r.rolname NOT LIKE 'pg\_%' AND r.rolname <> 'amjis_app'
   AND (has_table_privilege(r.oid, 'public.chart_subject_consent', 'INSERT') OR has_table_privilege(r.oid, 'public.chart_subject_consent', 'UPDATE') OR has_table_privilege(r.oid, 'public.chart_subject_consent', 'DELETE')
     OR has_table_privilege(r.oid, 'public.chart_subject_deletion_disputes', 'INSERT') OR has_table_privilege(r.oid, 'public.chart_subject_deletion_disputes', 'UPDATE') OR has_table_privilege(r.oid, 'public.chart_subject_deletion_disputes', 'DELETE'))
   AND (has_table_privilege(r.oid, 'public.mimamsa_predictions', 'DELETE') OR has_table_privilege(r.oid, 'public.brahma_prospective_ledger', 'DELETE')
     OR has_table_privilege(r.oid, 'public.mimamsa_manifestation_sets', 'DELETE') OR has_table_privilege(r.oid, 'public.brahma_mimamsa_prediction_ledger', 'DELETE'));
-- 8. the administrator can see other sessions (expect true for the role the executor connects as: pg_read_all_stats member)
SELECT pg_has_role('postgres', 'pg_read_all_stats', 'MEMBER') AS postgres_is_pg_read_all_stats_member;
