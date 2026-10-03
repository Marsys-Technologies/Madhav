-- sd8_delete_life_event_miss_phala_pramana.sql
--
-- ONE-SHOT, SCOPED, IRREVERSIBLE DELETE. NOT A MIGRATION: THIS FILE IS NEVER RUN BY platform/scripts/migrate.ts.
-- It lives in exec/scoped_delete_8/, outside platform/migrations/ and platform/supabase/migrations/ (the only two folders migrate.ts reads,
-- non-recursively) and carries no migration number. It is applied only by scoped_delete_8_exec.py under exec/gate_v2/run_gated.sh, as ONE
-- transaction, after a dry run whose evidence digest the operator names.
--
-- WHY (SS ruling N-109): L4 step ph_pramana read `life_events` (people-entered, private, chart-scoped) WITHOUT a chart filter, so chart
-- 1c826d5a-41cb-4450-b4dc-59d440e5f75a (no life events of its own) holds 8 phala_pramana rows classified `life_event_miss` that can only have
-- been derived from ANOTHER chart's private events (PH_LIFEEVENTS_SCOPE_REPORT.md; the reader fix is PR #3047). SS APPROVED a one-shot,
-- scoped delete of exactly those 8 DERIVED rows (computed rows, so N-46 on people-entered data is untouched). They are regenerable: rebuilding
-- ph_pramana for 1c826d5a after PR #3047 yields `detector_unavailable` for them.
--
-- WHAT IT DELETES: DELETE FROM ONLY public.phala_pramana WHERE chart_id = <1c826d5a-...> AND pramana_id = ANY(<the 8 ids>) AND
-- evidence_type = 'life_event_miss'. Nothing else. No DDL, no grant of any privilege on any object, no other table written.
--
-- WHICH ROLE: data_plane_builder (the shared builder: table ACL `data_plane_builder=ard/amjis_app` = INSERT, SELECT, DELETE; no UPDATE) is the
-- LEAST-privileged role that can DELETE from phala_pramana (the others: owner amjis_app arwdDxt, role_orchestrator arwd). It is also the role whose
-- ph_pramana rebuild does the per-chart delete-then-insert. The administrator (Cloud SQL `postgres`: CREATEROLE, not a superuser, no USAGE on
-- public) is made a transient member of the two roles it SETs and the membership is revoked again in the last step (only what this file granted).
-- All reads (preconditions, post-checks, dependents) run as suvarna_reader (SELECT only, no write privilege on any table touched), so a
-- mistyped read can never write. Counts and ids only are read; no private column of any row is ever selected into a result.
--
-- IRREVERSIBLE BY DESIGN: there is NO rollback leg and the rows are NOT copied (their jsonb could be derived from private text). To restore:
-- rebuild ph_pramana for 1c826d5a after PR #3047.
--
-- Statements are grouped in steps (`-- @@STEP name`) that the executor runs one by one. No BEGIN/COMMIT in this file: the executor owns the
-- transaction. The executor also measures every precondition and postcondition INDEPENDENTLY of the assertions below (python, as suvarna_reader).
--
-- @@STEP s1_assume_roles
-- Only the memberships GRANTED HERE are revoked again in s5 (tracked in transaction-local GUCs). The bound chart and id list live HERE ONLY
-- (one literal, read by every later step through the GUC); the plan hash covers this file.
DO $sd8$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['suvarna_reader', 'data_plane_builder'] LOOP
    IF NOT pg_has_role(current_user, r, 'MEMBER') THEN
      EXECUTE format('GRANT %I TO %I', r, current_user);
      PERFORM set_config('madhav.sd8_granted_' || r, 'on', true);
    END IF;
  END LOOP;
  PERFORM set_config('madhav.sd8_chart', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', true);
  PERFORM set_config('madhav.sd8_ids', '649c5828-ba9c-4ca8-9a7f-6ace81fad2e3,767b84b4-4090-4383-a9a9-ada59a509b1d,a3c855bb-9698-4c43-bb6b-c85ad1ec0a84,adcfd0d2-e748-4741-9df5-619ad1e8d271,c4fd0d7c-7502-4b63-bb61-8b693c38375b,ccdf5abd-6339-48dc-adac-39d8877f2629,db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c,f44dea24-ada4-405d-bba7-fe094ce8e1e6', true);
  PERFORM set_config('madhav.sd8_fp', 'bf270a4b5b3612827e5ea85885538a99ca4147fd62f1a86882c831c0ff21a4b6', true);
END
$sd8$;

-- @@STEP s2_preconditions_as_reader
SET LOCAL ROLE suvarna_reader;
DO $sd8$
DECLARE
  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;
  v_ids   uuid[] := string_to_array(current_setting('madhav.sd8_ids'), ',')::uuid[];
  v_regex text := replace(current_setting('madhav.sd8_ids'), ',', '|');
  v_rel   oid := to_regclass('public.phala_pramana');
  v_n     bigint;
  v_got   uuid[];
  v_fp    text;
  v_payload bigint;
  v_x     bigint;
  v_ref   text;
BEGIN
  IF current_user <> 'suvarna_reader' THEN RAISE EXCEPTION 'sd8 precondition: preconditions must run as suvarna_reader, not %', current_user; END IF;
  IF cardinality(v_ids) <> 8 THEN RAISE EXCEPTION 'sd8 precondition: the bound id list holds % ids, expected 8', cardinality(v_ids); END IF;
  IF v_rel IS NULL THEN RAISE EXCEPTION 'sd8 precondition: public.phala_pramana does not exist'; END IF;
  IF (SELECT pg_get_userbyid(relowner) || ':' || relkind::text || ':' || relrowsecurity::text || ':' || relforcerowsecurity::text FROM pg_class WHERE oid = v_rel)
       IS DISTINCT FROM 'amjis_app:r:false:false' THEN
    RAISE EXCEPTION 'sd8 precondition: phala_pramana is not an ordinary table owned by amjis_app with row level security off';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_inherits WHERE inhparent = v_rel OR inhrelid = v_rel) THEN
    RAISE EXCEPTION 'sd8 precondition: phala_pramana takes part in table inheritance / partitioning (a DELETE could reach other relations)';
  END IF;
  -- dependents, by the catalog: no foreign key references phala_pramana; no trigger (user), rule or dependent view on it
  SELECT count(*) INTO v_x FROM pg_constraint WHERE confrelid = v_rel AND contype = 'f';
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % foreign key(s) reference phala_pramana (a delete could cascade)', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_trigger WHERE tgrelid = v_rel AND NOT tgisinternal;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % user trigger(s) on phala_pramana (re-review the freshness/receipt effect)', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_rewrite WHERE ev_class = v_rel AND rulename <> '_RETURN';
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % rule(s) on phala_pramana', v_x; END IF;
  SELECT count(*) INTO v_x FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid AND d.classid = 'pg_rewrite'::regclass
   WHERE d.refobjid = v_rel AND r.ev_class <> v_rel;
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % view/rule object(s) depend on phala_pramana', v_x; END IF;
  -- the roles: the delete role can DELETE, the read role cannot
  IF NOT (has_table_privilege('data_plane_builder', v_rel, 'SELECT') AND has_table_privilege('data_plane_builder', v_rel, 'DELETE'))
     OR has_table_privilege('data_plane_builder', v_rel, 'UPDATE,TRUNCATE') THEN
    RAISE EXCEPTION 'sd8 precondition: data_plane_builder must hold SELECT and DELETE and no UPDATE/TRUNCATE on phala_pramana';
  END IF;
  IF has_table_privilege('suvarna_reader', v_rel, 'INSERT,UPDATE,DELETE,TRUNCATE') THEN
    RAISE EXCEPTION 'sd8 precondition: suvarna_reader holds a write privilege on phala_pramana';
  END IF;
  -- the logical (non-FK) referencers of a pramana id are exactly the known set: a new column named like *pramana_id(s) fails closed
  SELECT string_agg(c.relname || '.' || a.attname, ',' ORDER BY c.relname COLLATE "C", a.attname COLLATE "C") INTO v_ref
    FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
   WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm', 'f') AND a.attnum > 0 AND NOT a.attisdropped
     AND a.attname ~ 'pramana_ids?$';
  IF v_ref IS DISTINCT FROM 'mimamsa_anchor_adjustment.derived_from_pramana_ids,mimamsa_convergence_adjustment.derived_from_pramana_ids,mimamsa_fact_adjustment.derived_from_pramana_ids,mimamsa_predictions.source_pramana_id,mimamsa_predictions__ssv_20260728b.source_pramana_id,mimamsa_signal_adjustment.derived_from_pramana_ids,phala_pramana.pramana_id,phala_pramana__ssv_20260728b.pramana_id' THEN
    RAISE EXCEPTION 'sd8 precondition: the set of columns that can refer to a pramana id changed: %', v_ref;
  END IF;
  -- dependents by VALUE (the id text anywhere in the referencing column / row): all must be 0
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
  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b t WHERE t.pramana_id = ANY (v_ids);
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % phala_pramana__ssv_20260728b row(s) carry a bound pramana id', v_x; END IF;
  -- no build in flight (the gate checks the same, once; this is in-transaction)
  SELECT count(*) INTO v_x FROM public.build_runs WHERE state IN ('planned', 'running', 'paused');
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % build_runs in flight on some chart', v_x; END IF;
  SELECT count(*) INTO v_x FROM public.build_runs WHERE chart_id = v_chart AND state IN ('planned', 'running', 'paused');
  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % build_runs in flight on the bound chart', v_x; END IF;
  -- the matching rows: EXACTLY the bound eight (chart + marker), their ids equal the bound list, their non-private fingerprint equals the pinned one,
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
  -- pre-images, compared again in s4 (transaction-local; not persisted): per-chart counts, the ids of every row that must SURVIVE
  PERFORM set_config('madhav.sd8_pre_chart_total', (SELECT count(*) FROM public.phala_pramana WHERE chart_id = v_chart)::text, true);
  PERFORM set_config('madhav.sd8_pre_other_by_chart', COALESCE((SELECT string_agg(chart_id::text || ':' || n::text, ',' ORDER BY chart_id)
                       FROM (SELECT chart_id, count(*) n FROM public.phala_pramana WHERE chart_id <> v_chart GROUP BY chart_id) s), ''), true);
  PERFORM set_config('madhav.sd8_pre_other_digest', encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id)
                       FROM public.phala_pramana WHERE chart_id <> v_chart), ''), 'UTF8')), 'hex'), true);
  PERFORM set_config('madhav.sd8_pre_chart_rest_digest', encode(sha256(convert_to(COALESCE((SELECT string_agg(pramana_id::text, ',' ORDER BY pramana_id)
                       FROM public.phala_pramana WHERE chart_id = v_chart AND NOT (pramana_id = ANY (v_ids))), ''), 'UTF8')), 'hex'), true);
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

-- @@STEP s4_post_assertions_as_reader
SET LOCAL ROLE suvarna_reader;
DO $sd8$
DECLARE
  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;
  v_ids   uuid[] := string_to_array(current_setting('madhav.sd8_ids'), ',')::uuid[];
  v_x     bigint;
BEGIN
  IF current_user <> 'suvarna_reader' THEN RAISE EXCEPTION 'sd8 post: assertions must run as suvarna_reader, not %', current_user; END IF;
  IF current_setting('madhav.sd8_deleted_ids', true) IS DISTINCT FROM current_setting('madhav.sd8_ids') THEN
    RAISE EXCEPTION 'sd8 post: the recorded deleted ids differ from the bound ids';
  END IF;
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
END
$sd8$;
RESET ROLE;

-- @@STEP s5_restore_memberships
DO $sd8$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['suvarna_reader', 'data_plane_builder'] LOOP
    IF current_setting('madhav.sd8_granted_' || r, true) = 'on' THEN
      EXECUTE format('REVOKE %I FROM %I', r, current_user);
    END IF;
  END LOOP;
END
$sd8$;
