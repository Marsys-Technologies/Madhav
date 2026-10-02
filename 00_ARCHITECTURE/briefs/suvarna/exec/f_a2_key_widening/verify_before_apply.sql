-- READ-ONLY. Run as suvarna_reader (catalog + attestation-table reads only; no row of any snapshot table is read, none is writable here):
--   ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_before_apply.sql )
-- One row per check: ord | check | observed | expected | PASS/FAIL, then the summary row. Expected values are the plan's bound constants.
-- BEFORE the D6 apply: every row must read PASS (INFO rows are information).

WITH fn AS (
  SELECT p.oid, pg_get_functiondef(p.oid) AS d, pg_get_userbyid(p.proowner) AS owner, p.prosecdef AS secdef,
         COALESCE(p.proconfig::text, '') AS cfg, COALESCE(p.proacl::text, '') AS acl
  FROM pg_proc p WHERE p.oid = to_regprocedure('public.l1_data_plane_capture_row()')
), fb AS (
  SELECT pg_get_functiondef(p.oid) AS d, pg_get_userbyid(p.proowner) || ' / ' || p.prosecdef::text || ' / ' || COALESCE(p.proconfig::text, '') || ' / ' || COALESCE(p.proacl::text, '') AS meta
  FROM pg_proc p WHERE p.oid = to_regprocedure('public.capture_l1_data_plane_dasha_partition(uuid,text,text,integer)')
), fc AS (
  SELECT pg_get_functiondef(p.oid) AS d, pg_get_userbyid(p.proowner) || ' / ' || p.prosecdef::text || ' / ' || COALESCE(p.proconfig::text, '') || ' / ' || COALESCE(p.proacl::text, '') AS meta
  FROM pg_proc p WHERE p.oid = to_regprocedure('public.complete_l1_data_plane_partition(uuid,text,text,text,integer)')
), tv AS (
  SELECT pg_get_triggerdef(t.oid, true) AS d, t.tgenabled::text AS en
  FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
  WHERE c.relname = 'chart_vichara' AND t.tgname = 'l1_data_plane_capture' AND NOT t.tgisinternal
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
  UNION ALL SELECT 30, 'the 12 OTHER L1 lifecycle/helper functions (not the three patched ones) keep their live md5 (mismatches among the 12)',
         (SELECT count(*)::text FROM l1m m LEFT JOIN pg_proc p ON p.oid = to_regprocedure('public.' || m.sig)
            WHERE m.sig NOT IN ('l1_data_plane_capture_row()', 'capture_l1_data_plane_dasha_partition(uuid,text,text,integer)', 'complete_l1_data_plane_partition(uuid,text,text,text,integer)') AND md5(pg_get_functiondef(p.oid)) IS DISTINCT FROM m.md5_before), '0'
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
  UNION ALL SELECT 32, 'ITEM 2 patch B: dasha capture function owner / SECURITY DEFINER / config / ACL unchanged', (SELECT meta FROM fb), 'data_plane_l1_owner / true / {"search_path=pg_catalog, public, pg_temp"} / {data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner}'
  UNION ALL SELECT 33, 'ITEM 2 patch B (BEFORE: live pre-state): md5 / length', (SELECT md5(d) || ' / ' || length(d)::text FROM fb), 'eee8d9d4f5fbbbbbd03a9abda7c62385 / 5357'
  UNION ALL SELECT 34, 'ITEM 2 patch B: attestation digest = live sha256 = the pre-state digest', (SELECT a.definition_digest || ' / ' || (a.definition_digest = encode(public.digest(f.d, 'sha256'), 'hex'))::text FROM public.l1_data_plane_function_attestations a, fb f WHERE a.function_signature = 'capture_l1_data_plane_dasha_partition(uuid,text,text,integer)'), '166928dd4d72ef82ceafd6bc48c6b66784d70a8c4326f769237e9f3eef83276f / true'
  UNION ALL SELECT 35, 'ITEM 2 patch B hunks absent (v_systems occurrences)', (SELECT ((length(d) - length(replace(d, 'v_systems', ''))) / length('v_systems'))::text FROM fb), '0'
  UNION ALL SELECT 36, 'ITEM 3 patch C: completion function owner / SECURITY DEFINER / config / ACL unchanged', (SELECT meta FROM fc), 'data_plane_l1_owner / true / {"search_path=pg_catalog, public, pg_temp"} / {data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner}'
  UNION ALL SELECT 37, 'ITEM 3 patch C (BEFORE: live pre-state): md5 / length', (SELECT md5(d) || ' / ' || length(d)::text FROM fc), 'dcab40cf524c39efca628517c14fd9e8 / 8647'
  UNION ALL SELECT 38, 'ITEM 3 patch C: attestation digest = live sha256 = the pre-state digest', (SELECT a.definition_digest || ' / ' || (a.definition_digest = encode(public.digest(f.d, 'sha256'), 'hex'))::text FROM public.l1_data_plane_function_attestations a, fc f WHERE a.function_signature = 'complete_l1_data_plane_partition(uuid,text,text,text,integer)'), '93bcb4afee1d568e885d83cc8eb58c1122dc429bfa201f90226b162a18cf5b4c / true'
  UNION ALL SELECT 39, 'ITEM 3 patch C hunk absent (post-pass dasha block)', (SELECT ((length(d) - length(replace(d, 'the post-pass partition also INSERTS rows', ''))) / length('the post-pass partition also INSERTS rows'))::text FROM fc), '0'
  UNION ALL SELECT 50, 'ITEM 5 chart_vichara capture trigger BEFORE: eight arguments (live pre-state), enabled', (SELECT d || ' / ' || en FROM tv), 'CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON chart_vichara FOR EACH ROW EXECUTE FUNCTION l1_data_plane_capture_row(''chart_id'', ''ayanamsha_id'', ''vichara_family'', ''subject'', ''target'', ''domain'', ''varga_id'', ''formula_version'') / O'
  UNION ALL SELECT 51, 'ITEM 5 chart_vichara capture trigger attestation digest = the pre-state digest', (SELECT definition_digest FROM public.l1_data_plane_trigger_attestations WHERE table_name = 'chart_vichara' AND trigger_name = 'l1_data_plane_capture'), 'aa242e3b291de7460d09cbaed833cdf179e8f4f896f1bb0a931028c4708367a8'
  UNION ALL SELECT 52, 'ITEM 5 chart_vichara mutation-guard attestation row unchanged (only the capture trigger row is re-attested)', (SELECT definition_digest FROM public.l1_data_plane_trigger_attestations WHERE table_name = 'chart_vichara' AND trigger_name = 'l1_data_plane_mutation_guard'), '34e107e2120ea118ab18b2162a8344c92e4636e3011b62429e39ab795e765df3'
  UNION ALL SELECT 60, 'PREREQ migration 1255 (step 0): data_plane_l1_owner has SELECT on public.brahma_yoga_catalog (reads FAIL on production until 1255 is applied)',
         (COALESCE(to_regclass('public.brahma_yoga_catalog') IS NOT NULL AND has_table_privilege('data_plane_l1_owner', to_regclass('public.brahma_yoga_catalog'), 'SELECT'), false))::text, 'true'
  UNION ALL SELECT 61, 'PREREQ migration 1255 (step 0): reference tables the builder cannot SELECT (of the 7: yoga_family_members, reference_nakshatra, reference_nakshatra_pada, bg_shashtiamsha_deities, bg_graha_naisargika_friendship, bg_motion_state_thresholds, brahma_vichara_constants)',
         (SELECT count(*)::text FROM unnest(ARRAY['yoga_family_members','reference_nakshatra','reference_nakshatra_pada','bg_shashtiamsha_deities','bg_graha_naisargika_friendship','bg_motion_state_thresholds','brahma_vichara_constants']) t(n)
            WHERE NOT COALESCE(to_regclass('public.' || n) IS NOT NULL AND has_table_privilege('data_plane_builder', to_regclass('public.' || n), 'SELECT'), false)), '0'
)
SELECT ord, chk, obs, exp, CASE WHEN exp = '(info)' THEN 'INFO' WHEN obs IS NOT DISTINCT FROM exp THEN 'PASS' ELSE 'FAIL' END AS verdict FROM r
UNION ALL SELECT 999, 'SUMMARY: checks that are not PASS/INFO', count(*) FILTER (WHERE exp <> '(info)' AND obs IS DISTINCT FROM exp)::text, '0',
       CASE WHEN count(*) FILTER (WHERE exp <> '(info)' AND obs IS DISTINCT FROM exp) = 0 THEN 'PASS' ELSE 'FAIL' END FROM r
ORDER BY 1;
