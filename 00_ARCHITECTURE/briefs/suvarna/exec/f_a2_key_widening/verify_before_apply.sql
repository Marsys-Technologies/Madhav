-- READ-ONLY. Run as suvarna_reader (catalog + attestation-table reads only; no row of any snapshot table is read, none is writable here):
--   ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_before_apply.sql )
-- One row per check: ord | check | observed | expected | PASS/FAIL, then the summary row. Expected values are the plan's bound constants.
-- BEFORE the D6 apply: every row must read PASS (INFO rows are information).

WITH fn AS (
  SELECT p.oid, pg_get_functiondef(p.oid) AS d, pg_get_userbyid(p.proowner) AS owner, p.prosecdef AS secdef,
         COALESCE(p.proconfig::text, '') AS cfg, COALESCE(p.proacl::text, '') AS acl
  FROM pg_proc p WHERE p.oid = to_regprocedure('public.l1_data_plane_capture_row()')
), trg AS (
  SELECT pg_get_triggerdef(t.oid, true) AS d, t.tgenabled::text AS en
  FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
  WHERE c.relname = 'chart_divisionals' AND t.tgname = 'l1_data_plane_capture' AND NOT t.tgisinternal
), idx AS (
  SELECT i.indexdef AS d, x.indisunique, x.indisvalid, x.indnullsnotdistinct
  FROM pg_indexes i JOIN pg_class c ON c.relname = i.indexname JOIN pg_index x ON x.indexrelid = c.oid
  WHERE i.schemaname = 'public' AND i.indexname = 'chart_divisionals_unique_idx'
), l1m(sig, md5_before) AS (VALUES
    ('authorize_l1_chart_facts_delete(uuid,text[],text[],text[])','b81c9f63b322d567eb21054ac281fe29'),
    ('capture_l1_data_plane_dasha_partition(uuid,text,text,integer)','eee8d9d4f5fbbbbbd03a9abda7c62385'),
    ('complete_l1_data_plane_partition(uuid,text,text,text,integer)','dcab40cf524c39efca628517c14fd9e8'),
    ('l1_data_plane_capture_row()','1e079261aa42eb97a1885a48035e7520'),
    ('l1_data_plane_dasha_semantic_payload(chart_dashas)','0d4b33b09315cb3cffda146c3bed9de1'),
    ('l1_data_plane_fact_unit(text,text,jsonb)','cbe5275c6f03369835dcb9914f4e4263'),
    ('l1_data_plane_guard_active_mutation()','33b20202ec3571bc73a0e59b83591cef'),
    ('l1_data_plane_guard_generation_change()','5b83daa863c1c81ef8e1401556ffdc31'),
    ('l1_data_plane_install_active_guards(text,text[])','e9a61c49e56b9adda54ad2df4aafb996'),
    ('l1_data_plane_jsonb_has_nonfinite(jsonb)','876b4a5ccc248bb34d61dc698ba87b95'),
    ('l1_data_plane_material_fact_specs(text)','eb6b349e7dab96a2affc453d36443c85'),
    ('l1_data_plane_reject_immutable_change()','f077fd723a03353081fcfa2c5b10e8e7'),
    ('open_l1_data_plane_generation(uuid,text,text,text,integer,text,text,text,text,text,text)','ea6b50d97d2d88f8f1d20701abe37b14'),
    ('rollback_l1_data_plane_generation(uuid,text,text)','ed47c9ed9dbc723579d583b53702e04b'),
    ('select_l1_data_plane_generation(uuid,text,text)','94c08ee5d0b695ef9a2715b060270f3f')
), l2m(sig, md5_live) AS (VALUES
    ('assert_l2_msr_delete_safe(uuid,text[],text[],text[])','500ffdd7dd8808cc9937531da8099a3b'),
    ('bind_l2_exact_inputs(uuid,jsonb)','7bf8987517a7b76bd7ffae1c2bcf32ee'),
    ('complete_l2_data_plane_partition(uuid,text,text,text,text,bigint,bigint,bigint)','ee8ffbdde0c111067a6b86cae0494333'),
    ('l2_data_plane_capture_row()','8af0e24fac6953311680249934554b34'),
    ('l2_data_plane_dependency_topology_matches(text,jsonb)','b86a85310a0e310e04b21067f8e37711'),
    ('l2_data_plane_generation_is_compatible(uuid,text,text)','07085ae7a34e1795f63ae77928512ddb'),
    ('l2_data_plane_guard_active_mutation()','c6102b4bef2046ed4f71f5bb78d284f0'),
    ('l2_data_plane_guard_completed_run_rows()','aaf52b0aa3135787c46e5709066d623b'),
    ('l2_data_plane_guard_generation_change()','5be375550450929f3b820e42cc6aad13'),
    ('l2_data_plane_install_capture_trigger(text,text[])','647156a792f806bbc01c2bc6c00951c5'),
    ('l2_data_plane_jsonb_has_nonfinite(jsonb)','5573940554045eedbb3f6304ecba37e1'),
    ('l2_data_plane_reject_immutable_change()','e2bbd4db69822072be570cd664f052b0'),
    ('l2_data_plane_strip_volatile(jsonb)','6eff4cfb6395843b6da4f1b8d1155cd6'),
    ('open_l2_data_plane_generation(uuid,text,text,text,integer,text,text,text,text,jsonb,jsonb,text)','17e394454e917f996af266f8c599e14c'),
    ('rollback_l2_data_plane_generation(uuid,text,text)','a8d9156d0a66557c83f9a40666024b72'),
    ('select_l2_data_plane_generation(uuid,text,text)','44a5f09c8becc9a756bfa4bd2eecaa7e')
), cm AS (
  SELECT c.relname AS t, COALESCE(a.attname, '') AS col, d.description AS txt
  FROM pg_description d JOIN pg_class c ON c.oid = d.objoid AND d.classoid = 'pg_class'::regclass
  JOIN pg_namespace n ON n.oid = c.relnamespace LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.objsubid AND d.objsubid > 0
  WHERE n.nspname = 'public' AND c.relname IN ('l1_data_plane_row_snapshots', 'l1_data_plane_fact_snapshots')
), r(ord, chk, obs, exp) AS (
  SELECT 10, 'capture function exists, owner data_plane_l1_owner, SECURITY DEFINER, config, ACL',
         (SELECT owner || ' / ' || secdef::text || ' / ' || cfg || ' / ' || acl FROM fn),
         'data_plane_l1_owner / true / {"search_path=pg_catalog, public, pg_temp"} / {data_plane_l1_owner=X/data_plane_l1_owner}'
  UNION ALL SELECT 20, 'function attestation drift rows (the gate''s own function-digest join, all attested functions)',
         (SELECT count(*)::text FROM public.l1_data_plane_function_attestations a
            LEFT JOIN pg_proc p ON p.oid = to_regprocedure('public.' || a.function_signature)
            WHERE p.oid IS NULL OR a.definition_digest <> encode(public.digest(pg_get_functiondef(p.oid), 'sha256'), 'hex')
               OR a.owner_name <> pg_get_userbyid(p.proowner) OR a.security_definer <> p.prosecdef OR a.config IS DISTINCT FROM p.proconfig), '0'
  UNION ALL SELECT 21, 'trigger attestation drift rows (23 attested triggers: digest, type, enabled, function)',
         (SELECT count(*)::text FROM public.l1_data_plane_trigger_attestations a
            LEFT JOIN (SELECT c.relname AS table_name, t.tgname AS trigger_name, t.tgtype, t.tgenabled, t.tgfoid,
                              encode(public.digest(pg_get_triggerdef(t.oid, true), 'sha256'), 'hex') AS dd
                       FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace
                       WHERE NOT t.tgisinternal AND n.nspname = 'public') x USING (table_name, trigger_name)
            WHERE x.dd IS DISTINCT FROM a.definition_digest OR x.tgenabled <> a.enabled OR x.tgtype <> a.trigger_type OR x.tgfoid <> a.function_oid), '0'
  UNION ALL SELECT 22, 'attested triggers (rows) / attestation rows (functions)',
         (SELECT count(*)::text FROM public.l1_data_plane_trigger_attestations) || ' / ' || (SELECT count(*)::text FROM public.l1_data_plane_function_attestations), '23 / 15'
  UNION ALL SELECT 23, 'append-only (immutable) attestation triggers all enabled (11 of 11 on production)',
         (SELECT count(*) FILTER (WHERE tgenabled = 'O')::text || ' of ' || count(*)::text FROM pg_trigger WHERE tgname LIKE '%\_attestations\_immutable'),
         (SELECT count(*)::text || ' of ' || count(*)::text FROM pg_trigger WHERE tgname LIKE '%\_attestations\_immutable')
  UNION ALL SELECT 30, 'the 14 OTHER L1 lifecycle/helper functions keep their live md5 (mismatches among the 14)',
         (SELECT count(*)::text FROM l1m m LEFT JOIN pg_proc p ON p.oid = to_regprocedure('public.' || m.sig)
            WHERE m.sig <> 'l1_data_plane_capture_row()' AND md5(pg_get_functiondef(p.oid)) IS DISTINCT FROM m.md5_before), '0'
  UNION ALL SELECT 31, 'the L2 functions that exist keep their live md5 (mismatches; 0 expected, absent functions are not counted)',
         (SELECT count(*)::text FROM l2m m JOIN pg_proc p ON p.oid = to_regprocedure('public.' || m.sig)
            WHERE md5(pg_get_functiondef(p.oid)) <> m.md5_live), '0'
  UNION ALL SELECT 40, 'row counts of chart_divisionals (information only: the plan changes no row)', (SELECT count(*)::text FROM public.chart_divisionals), '(info)'
  UNION ALL SELECT 11, 'capture function md5 / length (BEFORE: the live pre-state)', (SELECT md5(d) || ' / ' || length(d)::text FROM fn), '1e079261aa42eb97a1885a48035e7520 / 19780'
  UNION ALL SELECT 12, 'function attestation digest = live sha256 of the definition = the pre-state digest',
         (SELECT a.definition_digest || ' / ' || (a.definition_digest = encode(public.digest(f.d, 'sha256'), 'hex'))::text FROM public.l1_data_plane_function_attestations a, fn f WHERE a.function_signature = 'l1_data_plane_capture_row()'),
         '0f8f42b6c93a9a5d2d25333cc2bd3cf52aed60e7cb7d51a87979ede92e74b9b8 / true'
  UNION ALL SELECT 13, 'patch A hunks absent (typed-choice hunk count / all-null hunk / v_typed_col declaration)',
         (SELECT (length(d) - length(replace(d, 'num_nonnulls(v_value_num, v_value_text, v_value_jsonb) > 1', ''))) / length('num_nonnulls(v_value_num, v_value_text, v_value_jsonb) > 1') || ' / ' ||
                 (position('THEN ''floored'' ELSE ''unavailable'' END' in d) > 0)::text || ' / ' || (position('v_typed_col TEXT' in d) > 0)::text FROM fn), '0 / false / false'
  UNION ALL SELECT 14, 'F-A2 function hunk absent (fact_subject= in the function)', (SELECT (position('fact_subject=' in d) > 0)::text FROM fn), 'false'
  UNION ALL SELECT 15, 'unique index is the 6-column NULLS NOT DISTINCT one', (SELECT d FROM idx),
         'CREATE UNIQUE INDEX chart_divisionals_unique_idx ON public.chart_divisionals USING btree (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT'
  UNION ALL SELECT 16, 'capture trigger has 6 arguments, enabled', (SELECT d || ' / ' || en FROM trg),
         'CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON chart_divisionals FOR EACH ROW EXECUTE FUNCTION l1_data_plane_capture_row(''chart_id'', ''graha'', ''ayanamsha_id'', ''varga'', ''fact_category'', ''fact_key'') / O'
  UNION ALL SELECT 17, 'capture trigger attestation digest = the pre-state digest', (SELECT definition_digest FROM public.l1_data_plane_trigger_attestations WHERE table_name = 'chart_divisionals' AND trigger_name = 'l1_data_plane_capture'),
         'd0064f5ed31f7db91cb239967f783af3a885f21b39aa7c833877989a713768b0'
  UNION ALL SELECT 18, 'snapshot-table comments: the two 1035 table comments, no column comment', (SELECT count(*) FILTER (WHERE col = '')::text || ' table / ' || count(*) FILTER (WHERE col <> '')::text || ' column' FROM cm), '2 table / 0 column'
  UNION ALL SELECT 19, 'the table comments do not yet state the precedence rule', (SELECT (count(*) FILTER (WHERE txt LIKE '%precedence%'))::text FROM cm), '0'
  UNION ALL SELECT 41, 'readiness: build_runs planned/running/paused on ANY chart', (SELECT count(*)::text FROM public.build_runs WHERE state IN ('planned','running','paused')), '0'
)
SELECT ord, chk, obs, exp, CASE WHEN exp = '(info)' THEN 'INFO' WHEN obs IS NOT DISTINCT FROM exp THEN 'PASS' ELSE 'FAIL' END AS verdict FROM r
UNION ALL SELECT 999, 'SUMMARY: checks that are not PASS/INFO', count(*) FILTER (WHERE exp <> '(info)' AND obs IS DISTINCT FROM exp)::text, '0',
       CASE WHEN count(*) FILTER (WHERE exp <> '(info)' AND obs IS DISTINCT FROM exp) = 0 THEN 'PASS' ELSE 'FAIL' END FROM r
ORDER BY 1;
