-- sd8_delete_life_event_miss_phala_pramana.sql
--
-- ONE-SHOT, SCOPED, IRREVERSIBLE DELETE, TWO TABLES, ONE TRANSACTION (all-or-nothing): 8 rows of public.phala_pramana and 16 rows of its frozen
-- ŚUDDHA-VĀCA snapshot public.phala_pramana__ssv_20260728b (SS extension of the ruling: same contamination, same chart, derived data).
-- NOT A MIGRATION: THIS FILE IS NEVER RUN BY platform/scripts/migrate.ts.
-- It lives in exec/scoped_delete_8/, outside platform/migrations/ and platform/supabase/migrations/ (the only two folders migrate.ts reads,
-- non-recursively) and carries no migration number. It is applied only by scoped_delete_8_exec.py under exec/gate_v2/run_gated.sh, as ONE
-- transaction, after a dry run whose evidence digest the operator names.
--
-- WHY (SS ruling N-109): L4 step ph_pramana read `life_events` (people-entered, private, chart-scoped) WITHOUT a chart filter, so chart
-- 1c826d5a-41cb-4450-b4dc-59d440e5f75a (no life events of its own) holds 8 phala_pramana rows classified `life_event_miss` that can only have
-- been derived from ANOTHER chart's private events (PH_LIFEEVENTS_SCOPE_REPORT.md; the reader fix is PR #3047); the 2026-07-28 snapshot of that table holds 16 more.
-- SS APPROVED a one-shot, scoped delete of exactly those DERIVED rows (computed rows, so N-46 on people-entered data is untouched). The 8 live rows are regenerable: rebuilding
-- ph_pramana for 1c826d5a after PR #3047 yields `detector_unavailable` for them.
--
-- WHAT IT DELETES (two statements, nothing else):
--   (1) DELETE FROM ONLY public.phala_pramana WHERE chart_id = <1c826d5a-...> AND pramana_id = ANY(<the 8 ids>) AND evidence_type = 'life_event_miss'
--   (2) DELETE FROM ONLY public.phala_pramana__ssv_20260728b WHERE chart_id = <1c826d5a-...> AND pramana_id = ANY(<the 16 ids>) AND evidence_type = 'life_event_miss'
-- No DDL, no grant of any privilege on any object, no other table written.
--
-- WHICH ROLES (least privilege PER TABLE, from the catalog):
--   (1) data_plane_builder: phala_pramana ACL `data_plane_builder=ard/amjis_app` = INSERT, SELECT, DELETE; no UPDATE / TRUNCATE. The others that can delete are
--       the owner amjis_app (arwdDxt) and role_orchestrator (arwd). It is also the role whose ph_pramana rebuild does the per-chart delete-then-insert.
--   (2) amjis_app (the table owner): the shadow table's ACL gives data_plane_builder NOTHING. The roles holding DELETE on it are the owner amjis_app (arwdDxt) and
--       role_orchestrator (`arwd`), BUT role_orchestrator has NO USAGE on schema public (schema ACL: no entry, no PUBLIC, no membership), so it cannot even resolve
--       public.phala_pramana__ssv_20260728b and a DELETE by it fails; granting it USAGE would be a privilege change this file does not make. The only role that can
--       actually delete there is therefore amjis_app (NOINHERIT login, no CREATEROLE, no memberships; the same transient-membership route D6 uses for amjis_app).
--   The administrator (Cloud SQL `postgres`: CREATEROLE, not a superuser, no USAGE on public) is made a transient member of the roles it SETs and the memberships
--   are revoked again in the last step (only what this file granted). All reads (preconditions, post-checks, dependents) run as suvarna_reader (SELECT only,
--   no write privilege on any table touched), so a mistyped read can never write. Counts and ids only are read; no private column of any row is ever selected
--   into a result.
--
-- THE SHADOW TABLE is a plain CREATE TABLE AS snapshot (tag ssv_20260728b, the ŚUDDHA-VĀCA rollback baseline of 2026-07-28): no constraint, no index, no trigger,
-- no rule, no policy, no comment, no event trigger; so there is no freeze / immutability guard to refuse the delete. Its pramana_id is nullable and not unique by
-- constraint, so this file also requires that EXACTLY 16 rows of the whole table carry one of the 16 ids (the delete cannot reach a duplicate elsewhere).
--
-- IRREVERSIBLE BY DESIGN: there is NO rollback leg and the rows are NOT copied (their jsonb could be derived from private text). To restore: rebuild ph_pramana
-- for 1c826d5a after PR #3047 (the snapshot rows themselves are not regenerable; they are the contaminated rows and are deliberately dropped).
--
-- Statements are grouped in steps (`-- @@STEP name`) that the executor runs one by one. No BEGIN/COMMIT in this file: the executor owns the
-- transaction. The executor also measures every precondition and postcondition INDEPENDENTLY of the assertions below (python, as suvarna_reader).
--
-- @@STEP s1_assume_roles
-- Only the memberships GRANTED HERE are revoked again in s6 (tracked in transaction-local GUCs). The bound chart and id list live HERE ONLY
-- (one literal, read by every later step through the GUC); the plan hash covers this file.
DO $sd8$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['suvarna_reader', 'data_plane_builder', 'amjis_app'] LOOP
    IF NOT pg_has_role(current_user, r, 'MEMBER') THEN
      EXECUTE format('GRANT %I TO %I', r, current_user);
      PERFORM set_config('madhav.sd8_granted_' || r, 'on', true);
    END IF;
  END LOOP;
  PERFORM set_config('madhav.sd8_chart', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', true);
  PERFORM set_config('madhav.sd8_ids', '649c5828-ba9c-4ca8-9a7f-6ace81fad2e3,767b84b4-4090-4383-a9a9-ada59a509b1d,a3c855bb-9698-4c43-bb6b-c85ad1ec0a84,adcfd0d2-e748-4741-9df5-619ad1e8d271,c4fd0d7c-7502-4b63-bb61-8b693c38375b,ccdf5abd-6339-48dc-adac-39d8877f2629,db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c,f44dea24-ada4-405d-bba7-fe094ce8e1e6', true);
  PERFORM set_config('madhav.sd8_fp', 'bf270a4b5b3612827e5ea85885538a99ca4147fd62f1a86882c831c0ff21a4b6', true);
  PERFORM set_config('madhav.sd8_shadow_ids', '05a53e0a-54c9-4053-9ca2-b5a272d77019,12cf1a40-a44e-4cfa-8676-17de3f400a43,1fd500d1-e470-4059-95d7-15b7d318b96b,4649aa1b-20f4-4a7f-90a6-fbf43fb38574,60b833f7-0d0a-43ed-b904-a25450c3f114,7af4a789-5f28-4b36-82a7-644a182411f7,8b147ef7-3d7d-4657-9cf1-0dd652144ee9,a2138a26-3f37-480e-bf71-da03931b147b,ac243a04-6c4e-4c80-92b9-5ca8999bd644,c89c4d65-c928-4011-928c-fd2288049bc0,cdd0ef46-6290-4cae-9241-efd89bb109a8,d6a2f982-a44b-4b6c-92e0-bed3fe44e884,e05205a8-44ae-4329-b363-f28dd1c55fb3,e16bb71a-7b1b-4021-a4ac-8f286d6411b6,ef1d58d6-03a3-47bb-a2aa-e32c40d2c642,f9c0087b-529b-4673-a70f-dfc69dba2530', true);
  PERFORM set_config('madhav.sd8_shadow_fp', 'fe1dc5647a643981b4cfb170e5ded5082125b1bbbe0a1aa0a9c8a84e15264724', true);
END
$sd8$;

-- @@STEP s2_preconditions_as_reader
SET LOCAL ROLE suvarna_reader;
DO $sd8$
DECLARE
  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;
  v_ids   uuid[] := string_to_array(current_setting('madhav.sd8_ids'), ',')::uuid[];
  v_sids  uuid[] := string_to_array(current_setting('madhav.sd8_shadow_ids'), ',')::uuid[];
  v_regex text := replace(current_setting('madhav.sd8_ids') || ',' || current_setting('madhav.sd8_shadow_ids'), ',', '|');
  v_rel   oid := to_regclass('public.phala_pramana');
  v_srel  oid := to_regclass('public.phala_pramana__ssv_20260728b');
  v_n     bigint;
  v_got   uuid[];
  v_fp    text;
  v_payload bigint;
  v_x     bigint;
  v_ref   text;
BEGIN
  IF current_user <> 'suvarna_reader' THEN RAISE EXCEPTION 'sd8 precondition: preconditions must run as suvarna_reader, not %', current_user; END IF;
  IF cardinality(v_ids) <> 8 THEN RAISE EXCEPTION 'sd8 precondition: the bound id list holds % ids, expected 8', cardinality(v_ids); END IF;
  IF cardinality(v_sids) <> 16 THEN RAISE EXCEPTION 'sd8 precondition: the bound shadow id list holds % ids, expected 16', cardinality(v_sids); END IF;
  IF v_ids && v_sids THEN RAISE EXCEPTION 'sd8 precondition: the two bound id lists overlap'; END IF;
  IF v_rel IS NULL THEN RAISE EXCEPTION 'sd8 precondition: public.phala_pramana does not exist'; END IF;
  IF v_srel IS NULL THEN RAISE EXCEPTION 'sd8 precondition: public.phala_pramana__ssv_20260728b does not exist'; END IF;
  IF (SELECT pg_get_userbyid(relowner) || ':' || relkind::text || ':' || relrowsecurity::text || ':' || relforcerowsecurity::text FROM pg_class WHERE oid = v_rel)
       IS DISTINCT FROM 'amjis_app:r:false:false' THEN
    RAISE EXCEPTION 'sd8 precondition: phala_pramana is not an ordinary table owned by amjis_app with row level security off';
  END IF;
  IF (SELECT pg_get_userbyid(relowner) || ':' || relkind::text || ':' || relrowsecurity::text || ':' || relforcerowsecurity::text FROM pg_class WHERE oid = v_srel)
       IS DISTINCT FROM 'amjis_app:r:false:false' THEN
    RAISE EXCEPTION 'sd8 precondition: phala_pramana__ssv_20260728b is not an ordinary table owned by amjis_app with row level security off';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_inherits WHERE inhparent IN (v_rel, v_srel) OR inhrelid IN (v_rel, v_srel)) THEN
    RAISE EXCEPTION 'sd8 precondition: a target table takes part in table inheritance / partitioning (a DELETE could reach other relations)';
  END IF;
  -- dependents, by the catalog: no foreign key references either table; no trigger (user), rule, policy or dependent view on either; no event trigger
  SELECT count(*) INTO v_x FROM pg_constraint WHERE confrelid IN (v_rel, v_srel) AND contype = 'f';
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % foreign key(s) reference a target table (a delete could cascade)', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_trigger WHERE tgrelid IN (v_rel, v_srel) AND NOT tgisinternal;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % user trigger(s) on a target table (re-review the freshness/receipt effect)', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_rewrite WHERE ev_class IN (v_rel, v_srel) AND rulename <> '_RETURN';
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % rule(s) on a target table', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_policy WHERE polrelid IN (v_rel, v_srel);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % row level security policy(ies) on a target table', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_event_trigger;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % event trigger(s) exist (a guard on the snapshot tables? re-review)', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid AND d.classid = 'pg_rewrite'::regclass
   WHERE d.refobjid IN (v_rel, v_srel) AND r.ev_class NOT IN (v_rel, v_srel);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % view/rule object(s) depend on a target table', v_x; END IF;
  -- the roles: each delete role can SELECT and DELETE (tested one by one: a comma list means ANY) and cannot TRUNCATE/UPDATE where the plan says so; the read role cannot write
  IF NOT (has_table_privilege('data_plane_builder', v_rel, 'SELECT') AND has_table_privilege('data_plane_builder', v_rel, 'DELETE'))
     OR has_table_privilege('data_plane_builder', v_rel, 'UPDATE,TRUNCATE') THEN
    RAISE EXCEPTION 'sd8 precondition: data_plane_builder must hold SELECT and DELETE and no UPDATE/TRUNCATE on phala_pramana';
  END IF;
  IF NOT (has_table_privilege('amjis_app', v_srel, 'SELECT') AND has_table_privilege('amjis_app', v_srel, 'DELETE') AND has_schema_privilege('amjis_app', 'public', 'USAGE')) THEN
    RAISE EXCEPTION 'sd8 precondition: amjis_app must hold SELECT and DELETE on phala_pramana__ssv_20260728b and USAGE on schema public';
  END IF;
  IF NOT has_schema_privilege('data_plane_builder', 'public', 'USAGE') THEN
    RAISE EXCEPTION 'sd8 precondition: data_plane_builder has no USAGE on schema public';
  END IF;
  IF has_table_privilege('data_plane_builder', v_srel, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE') THEN
    RAISE EXCEPTION 'sd8 precondition: data_plane_builder unexpectedly holds a privilege on the shadow table (the plan assumes none; re-review the role choice)';
  END IF;
  IF has_table_privilege('suvarna_reader', v_rel, 'INSERT,UPDATE,DELETE,TRUNCATE') OR has_table_privilege('suvarna_reader', v_srel, 'INSERT,UPDATE,DELETE,TRUNCATE') THEN
    RAISE EXCEPTION 'sd8 precondition: suvarna_reader holds a write privilege on a target table';
  END IF;
  -- the logical (non-FK) referencers of a pramana id are exactly the known set: a new column named like *pramana_id(s) fails closed
  SELECT string_agg(c.relname || '.' || a.attname, ',' ORDER BY c.relname COLLATE "C", a.attname COLLATE "C") INTO v_ref
    FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
   WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm', 'f') AND a.attnum > 0 AND NOT a.attisdropped
     AND a.attname ~ 'pramana_ids?$';
  IF v_ref IS DISTINCT FROM 'mimamsa_anchor_adjustment.derived_from_pramana_ids,mimamsa_convergence_adjustment.derived_from_pramana_ids,mimamsa_fact_adjustment.derived_from_pramana_ids,mimamsa_predictions.source_pramana_id,mimamsa_predictions__ssv_20260728b.source_pramana_id,mimamsa_signal_adjustment.derived_from_pramana_ids,phala_pramana.pramana_id,phala_pramana__ssv_20260728b.pramana_id' THEN
    RAISE EXCEPTION 'sd8 precondition: the set of columns that can refer to a pramana id changed: %', v_ref;
  END IF;
  -- dependents by VALUE (any of the 24 bound ids anywhere in the referencing column / row): all must be 0
  SELECT count(*) INTO v_x FROM public.mimamsa_predictions t WHERE t.source_pramana_id ~ v_regex OR t::text ~ v_regex;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % mimamsa_predictions row(s) refer to a bound pramana id', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.mimamsa_predictions__ssv_20260728b t WHERE t.source_pramana_id ~ v_regex OR t::text ~ v_regex;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % mimamsa_predictions__ssv_20260728b row(s) refer to a bound pramana id', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.mimamsa_anchor_adjustment t WHERE t.derived_from_pramana_ids::text ~ v_regex;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % mimamsa_anchor_adjustment row(s) refer to a bound pramana id', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.mimamsa_convergence_adjustment t WHERE t.derived_from_pramana_ids::text ~ v_regex;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % mimamsa_convergence_adjustment row(s) refer to a bound pramana id', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.mimamsa_fact_adjustment t WHERE t.derived_from_pramana_ids::text ~ v_regex;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % mimamsa_fact_adjustment row(s) refer to a bound pramana id', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.mimamsa_signal_adjustment t WHERE t.derived_from_pramana_ids::text ~ v_regex;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % mimamsa_signal_adjustment row(s) refer to a bound pramana id', v_x; END IF;
  -- the two target tables must not carry each other's ids
  SELECT count(*) INTO v_x FROM public.phala_pramana t WHERE t.pramana_id = ANY (v_sids);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % phala_pramana row(s) carry a bound SHADOW pramana id', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b t WHERE t.pramana_id = ANY (v_ids);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % phala_pramana__ssv_20260728b row(s) carry a bound pramana id', v_x; END IF;
  -- no build in flight (the gate checks the same, once; this is in-transaction)
  SELECT count(*) INTO v_x FROM public.build_runs WHERE state IN ('planned', 'running', 'paused');
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % build_runs in flight on some chart', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.build_runs WHERE chart_id = v_chart AND state IN ('planned', 'running', 'paused');
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % build_runs in flight on the bound chart', v_x; END IF;
  -- TABLE 1, phala_pramana: EXACTLY the bound eight (chart + marker), their ids equal the bound list, their non-private fingerprint equals the pinned one,
  -- and none of them holds a life-event payload (lel_entry_id / lel_entry_jsonb NULL)
  SELECT count(*), array_agg(pramana_id ORDER BY pramana_id),
         encode(sha256(convert_to(string_agg(concat_ws('|', pramana_id::text, chart_id::text, anchor_id::text, evidence_type, evidence_strength_label, window_status,
                                                       (lel_entry_id IS NULL)::text, (lel_entry_jsonb IS NULL)::text, extract(epoch FROM computed_at)::text),
                                              E'\n' ORDER BY pramana_id), 'UTF8')), 'hex'),
         count(*) FILTER (WHERE lel_entry_id IS NOT NULL OR lel_entry_jsonb IS NOT NULL)
    INTO v_n, v_got, v_fp, v_payload
    FROM public.phala_pramana WHERE chart_id = v_chart AND evidence_type = 'life_event_miss';
  IF v_n <> 8 THEN RAISE EXCEPTION 'sd8 precondition: % rows match (chart, life_event_miss), expected exactly 8', v_n; END IF;
  IF v_got IS DISTINCT FROM (SELECT array_agg(i ORDER BY i) FROM unnest(v_ids) i) THEN
    RAISE EXCEPTION 'sd8 precondition: the ids of the matching rows differ from the bound id list';
  END IF;
  IF v_fp IS DISTINCT FROM current_setting('madhav.sd8_fp') THEN
    RAISE EXCEPTION 'sd8 precondition: the non-private fingerprint of the matching rows differs from the pinned one (%)', v_fp;
  END IF;
  IF v_payload <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % matching row(s) carry a life-event payload (lel_entry_id / lel_entry_jsonb); SS must re-decide', v_payload; END IF;
  -- TABLE 2, phala_pramana__ssv_20260728b: EXACTLY the bound sixteen, same four conditions; plus: no OTHER row of the whole table carries one of the 16 ids
  -- (pramana_id is nullable and not unique by constraint there)
  SELECT count(*), array_agg(pramana_id ORDER BY pramana_id),
         encode(sha256(convert_to(string_agg(concat_ws('|', pramana_id::text, chart_id::text, anchor_id::text, evidence_type, evidence_strength_label, window_status,
                                                       (lel_entry_id IS NULL)::text, (lel_entry_jsonb IS NULL)::text, extract(epoch FROM computed_at)::text),
                                              E'\n' ORDER BY pramana_id), 'UTF8')), 'hex'),
         count(*) FILTER (WHERE lel_entry_id IS NOT NULL OR lel_entry_jsonb IS NOT NULL)
    INTO v_n, v_got, v_fp, v_payload
    FROM public.phala_pramana__ssv_20260728b WHERE chart_id = v_chart AND evidence_type = 'life_event_miss';
  IF v_n <> 16 THEN RAISE EXCEPTION 'sd8 precondition: % shadow rows match (chart, life_event_miss), expected exactly 16', v_n; END IF;
  IF v_got IS DISTINCT FROM (SELECT array_agg(i ORDER BY i) FROM unnest(v_sids) i) THEN
    RAISE EXCEPTION 'sd8 precondition: the ids of the matching shadow rows differ from the bound shadow id list';
  END IF;
  IF v_fp IS DISTINCT FROM current_setting('madhav.sd8_shadow_fp') THEN
    RAISE EXCEPTION 'sd8 precondition: the non-private fingerprint of the matching shadow rows differs from the pinned one (%)', v_fp;
  END IF;
  IF v_payload <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % matching shadow row(s) carry a life-event payload; SS must re-decide', v_payload; END IF;
  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b WHERE pramana_id = ANY (v_sids);
  IF v_x <> 16 THEN RAISE EXCEPTION 'sd8 precondition: % shadow rows carry one of the 16 ids (a duplicate id outside the matching set), expected exactly 16', v_x; END IF;
  -- pre-images, compared again in s5 (transaction-local; not persisted): per-table chart totals, the other charts' counts and id digests, the surviving rows' id digest
  PERFORM set_config('madhav.sd8_pre_chart_total', (SELECT count(*) FROM public.phala_pramana WHERE chart_id = v_chart)::text, true);
  PERFORM set_config('madhav.sd8_pre_other_by_chart', COALESCE((SELECT string_agg(chart_id::text || ':' || n::text, ',' ORDER BY chart_id)
                       FROM (SELECT chart_id, count(*) n FROM public.phala_pramana WHERE chart_id <> v_chart GROUP BY chart_id) s), ''), true);
  PERFORM set_config('madhav.sd8_pre_other_digest', encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id)
                       FROM public.phala_pramana WHERE chart_id <> v_chart), ''), 'UTF8')), 'hex'), true);
  PERFORM set_config('madhav.sd8_pre_chart_rest_digest', encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id)
                       FROM public.phala_pramana WHERE chart_id = v_chart AND NOT (pramana_id = ANY (v_ids))), ''), 'UTF8')), 'hex'), true);
  PERFORM set_config('madhav.sd8_pre_s_chart_total', (SELECT count(*) FROM public.phala_pramana__ssv_20260728b WHERE chart_id = v_chart)::text, true);
  PERFORM set_config('madhav.sd8_pre_s_other_by_chart', COALESCE((SELECT string_agg(chart_id::text || ':' || n::text, ',' ORDER BY chart_id)
                       FROM (SELECT chart_id, count(*) n FROM public.phala_pramana__ssv_20260728b WHERE chart_id IS DISTINCT FROM v_chart GROUP BY chart_id) s), ''), true);
  PERFORM set_config('madhav.sd8_pre_s_other_digest', encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id)
                       FROM public.phala_pramana__ssv_20260728b WHERE chart_id IS DISTINCT FROM v_chart), ''), 'UTF8')), 'hex'), true);
  PERFORM set_config('madhav.sd8_pre_s_chart_rest_digest', encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id)
                       FROM public.phala_pramana__ssv_20260728b WHERE chart_id = v_chart AND NOT (pramana_id = ANY (v_sids))), ''), 'UTF8')), 'hex'), true);
END
$sd8$;
RESET ROLE;

-- @@STEP s3_delete_as_builder
SET LOCAL ROLE data_plane_builder;
DO $sd8$
DECLARE
  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;
  v_ids   uuid[] := string_to_array(current_setting('madhav.sd8_ids'), ',')::uuid[];
  v_n     bigint;
  v_got   uuid[];
BEGIN
  IF current_user <> 'data_plane_builder' THEN RAISE EXCEPTION 'sd8 delete: the delete must run as data_plane_builder, not %', current_user; END IF;
  WITH d AS (
    DELETE FROM ONLY public.phala_pramana
     WHERE chart_id = v_chart AND pramana_id = ANY (v_ids) AND evidence_type = 'life_event_miss'
    RETURNING pramana_id
  )
  SELECT count(*), array_agg(pramana_id ORDER BY pramana_id) INTO v_n, v_got FROM d;
  IF v_n <> 8 THEN RAISE EXCEPTION 'sd8 delete: % rows deleted, expected exactly 8', v_n; END IF;
  IF v_got IS DISTINCT FROM (SELECT array_agg(i ORDER BY i) FROM unnest(v_ids) i) THEN
    RAISE EXCEPTION 'sd8 delete: the deleted ids differ from the bound id list';
  END IF;
  PERFORM set_config('madhav.sd8_deleted_ids', array_to_string(v_got, ','), true);
END
$sd8$;
RESET ROLE;

-- @@STEP s4_delete_shadow_as_table_owner
SET LOCAL ROLE amjis_app;
DO $sd8$
DECLARE
  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;
  v_sids  uuid[] := string_to_array(current_setting('madhav.sd8_shadow_ids'), ',')::uuid[];
  v_n     bigint;
  v_got   uuid[];
BEGIN
  IF current_user <> 'amjis_app' THEN RAISE EXCEPTION 'sd8 shadow delete: the delete must run as amjis_app, not %', current_user; END IF;
  WITH d AS (
    DELETE FROM ONLY public.phala_pramana__ssv_20260728b
     WHERE chart_id = v_chart AND pramana_id = ANY (v_sids) AND evidence_type = 'life_event_miss'
    RETURNING pramana_id
  )
  SELECT count(*), array_agg(pramana_id ORDER BY pramana_id) INTO v_n, v_got FROM d;
  IF v_n <> 16 THEN RAISE EXCEPTION 'sd8 shadow delete: % rows deleted, expected exactly 16', v_n; END IF;
  IF v_got IS DISTINCT FROM (SELECT array_agg(i ORDER BY i) FROM unnest(v_sids) i) THEN
    RAISE EXCEPTION 'sd8 shadow delete: the deleted ids differ from the bound shadow id list';
  END IF;
  PERFORM set_config('madhav.sd8_deleted_shadow_ids', array_to_string(v_got, ','), true);
END
$sd8$;
RESET ROLE;

-- @@STEP s5_post_assertions_as_reader
SET LOCAL ROLE suvarna_reader;
DO $sd8$
DECLARE
  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;
  v_ids   uuid[] := string_to_array(current_setting('madhav.sd8_ids'), ',')::uuid[];
  v_sids  uuid[] := string_to_array(current_setting('madhav.sd8_shadow_ids'), ',')::uuid[];
  v_x     bigint;
BEGIN
  IF current_user <> 'suvarna_reader' THEN RAISE EXCEPTION 'sd8 post: assertions must run as suvarna_reader, not %', current_user; END IF;
  IF current_setting('madhav.sd8_deleted_ids', true) IS DISTINCT FROM current_setting('madhav.sd8_ids') THEN
    RAISE EXCEPTION 'sd8 post: the recorded deleted ids differ from the bound ids';
  END IF;
  IF current_setting('madhav.sd8_deleted_shadow_ids', true) IS DISTINCT FROM current_setting('madhav.sd8_shadow_ids') THEN
    RAISE EXCEPTION 'sd8 post: the recorded deleted shadow ids differ from the bound shadow ids';
  END IF;
  -- phala_pramana
  SELECT count(*) INTO v_x FROM public.phala_pramana WHERE pramana_id = ANY (v_ids);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 post: % of the 8 bound ids are still present', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.phala_pramana WHERE chart_id = v_chart AND evidence_type = 'life_event_miss';
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 post: % (chart, life_event_miss) rows remain', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.phala_pramana WHERE chart_id = v_chart;
  IF v_x <> current_setting('madhav.sd8_pre_chart_total')::bigint - 8 THEN
    RAISE EXCEPTION 'sd8 post: the chart total is %, expected pre (%) - 8', v_x, current_setting('madhav.sd8_pre_chart_total');
  END IF;
  IF COALESCE((SELECT string_agg(chart_id::text || ':' || n::text, ',' ORDER BY chart_id)
                 FROM (SELECT chart_id, count(*) n FROM public.phala_pramana WHERE chart_id <> v_chart GROUP BY chart_id) s), '')
       IS DISTINCT FROM current_setting('madhav.sd8_pre_other_by_chart') THEN
    RAISE EXCEPTION 'sd8 post: the per-chart counts of the OTHER charts changed';
  END IF;
  IF encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id) FROM public.phala_pramana WHERE chart_id <> v_chart), ''), 'UTF8')), 'hex')
       IS DISTINCT FROM current_setting('madhav.sd8_pre_other_digest') THEN
    RAISE EXCEPTION 'sd8 post: the id set of the OTHER charts changed';
  END IF;
  IF encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id) FROM public.phala_pramana WHERE chart_id = v_chart), ''), 'UTF8')), 'hex')
       IS DISTINCT FROM current_setting('madhav.sd8_pre_chart_rest_digest') THEN
    RAISE EXCEPTION 'sd8 post: the surviving rows of the bound chart are not exactly the pre-image minus the 8';
  END IF;
  -- phala_pramana__ssv_20260728b
  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b WHERE pramana_id = ANY (v_sids);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 post: % of the 16 bound shadow ids are still present', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b WHERE chart_id = v_chart AND evidence_type = 'life_event_miss';
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 post: % shadow (chart, life_event_miss) rows remain', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b WHERE chart_id = v_chart;
  IF v_x <> current_setting('madhav.sd8_pre_s_chart_total')::bigint - 16 THEN
    RAISE EXCEPTION 'sd8 post: the shadow chart total is %, expected pre (%) - 16', v_x, current_setting('madhav.sd8_pre_s_chart_total');
  END IF;
  IF COALESCE((SELECT string_agg(chart_id::text || ':' || n::text, ',' ORDER BY chart_id)
                 FROM (SELECT chart_id, count(*) n FROM public.phala_pramana__ssv_20260728b WHERE chart_id IS DISTINCT FROM v_chart GROUP BY chart_id) s), '')
       IS DISTINCT FROM current_setting('madhav.sd8_pre_s_other_by_chart') THEN
    RAISE EXCEPTION 'sd8 post: the per-chart counts of the OTHER charts changed in the shadow table';
  END IF;
  IF encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id) FROM public.phala_pramana__ssv_20260728b WHERE chart_id IS DISTINCT FROM v_chart), ''), 'UTF8')), 'hex')
       IS DISTINCT FROM current_setting('madhav.sd8_pre_s_other_digest') THEN
    RAISE EXCEPTION 'sd8 post: the id set of the OTHER charts changed in the shadow table';
  END IF;
  IF encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id) FROM public.phala_pramana__ssv_20260728b WHERE chart_id = v_chart), ''), 'UTF8')), 'hex')
       IS DISTINCT FROM current_setting('madhav.sd8_pre_s_chart_rest_digest') THEN
    RAISE EXCEPTION 'sd8 post: the surviving shadow rows of the bound chart are not exactly the pre-image minus the 16';
  END IF;
END
$sd8$;
RESET ROLE;

-- @@STEP s6_restore_memberships
DO $sd8$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['suvarna_reader', 'data_plane_builder', 'amjis_app'] LOOP
    IF current_setting('madhav.sd8_granted_' || r, true) = 'on' THEN
      EXECUTE format('REVOKE %I FROM %I', r, current_user);
    END IF;
  END LOOP;
END
$sd8$;
