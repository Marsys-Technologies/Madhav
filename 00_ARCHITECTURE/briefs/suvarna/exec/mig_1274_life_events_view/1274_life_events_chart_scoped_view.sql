-- 1274_life_events_chart_scoped_view.sql
--
-- HISTORY + OWNER-PATH ARTIFACT. THIS FILE IS NEVER RUN BY platform/scripts/migrate.ts.
-- It lives here, outside platform/migrations/ and platform/supabase/migrations/ (the only two folders migrate.ts reads, non-recursively),
-- on purpose: the routine runner role (amjis_app) has no CREATE on schema public, so a CREATE VIEW in it would fail the whole deploy.
-- It is applied by the gated owner-path executor in this folder (mig_1274_life_events_view_exec.py) under run_gated.sh, as one
-- transaction, after a dry run whose evidence digest the operator names. Design notes: this header and the PR description.
--
-- WHAT (SS rulings N-105, N-109, N-112): a chart-scoped, read-only, security-barrier VIEW over the people-entered, private `life_events`, granted
-- SELECT to data_plane_builder ONLY, AND, in the SAME transaction, the REVOCATION of the builder's EXISTING column-level SELECT on
-- life_events (production today: data_plane_builder holds SELECT on exactly id, event_date, category, description, outcome_observed, granted
-- by amjis_app under the builder-grants plan, so it can read those five columns of EVERY chart straight from the table, bypassing any view).
-- After this file the builder has NO direct privilege on the table (table or column) and exactly one door: the view. The view shows only the rows whose chart_id
-- equals app_chart_context() (the existing G1c accessor of the transaction-local GUC `app.chart_context`; NULL when the GUC is unset
-- or malformed, so an unset GUC yields ZERO rows: fail closed).
--
-- WHO OWNS IT, AND WHY NOT A SECOND GRANT: no role both owns/can SELECT life_events (owner amjis_app) AND can CREATE in schema public
-- (owners data_plane_schema_owner / data_plane_l1_owner / data_plane_l2_owner hold CREATE; none of them can read life_events). Giving
-- an owner role a standing SELECT on the private table would be a new direct grant; instead amjis_app (the table owner) gets CREATE on
-- public for the length of ONE statement inside this transaction (granted and revoked by the schema owner; schema ACL asserted
-- byte-for-byte unchanged afterwards) and creates the view itself. The view therefore reads the table with the table owner's rights
-- (no security_invoker), so the builder needs no table privilege.
--
-- COLUMNS (6, minimal; each one is read by an L4 reader; no other column of life_events is exposed):
--   id, event_date, category                    <- ph_pramana   (id = the reference stored in phala_pramana.lel_entry_jsonb)
--   event_id, event_date, category, domain      <- ph_rectification
--   chart_id                                    <- the explicit WHERE chart_id = %s of every reader + the runtime guard
-- NOT exposed: outcome_observed (SS N-112: read by nothing that matters), description (SS N-109, DATA MINIMISATION: private free text is never copied into a derived L4 row; ph_pramana stores the
--   life_events id reference and the text is resolved on demand, chart-scoped, by an entitled role), significance, chart_state, source_section, build_id, provenance, event_type, source_citation, recorded_at, pool_consent,
--   contributed_to_pool_at, shape, date_confidence, interval_*, chain_parent_event_id, milestone_label, date_tightened_*, superseded_by_chain_note.
--
-- ACCEPTED LIMIT (SS N-109): the scoping stops ACCIDENTAL cross-chart reads, not a HOSTILE builder session: app.chart_context is a session-settable GUC,
-- so a builder session that deliberately names another chart sees that chart's rows (those 6 columns, never free text). The builder is a shared pipeline
-- identity, not an untrusted one; this is documented, tested for the accidental case, and accepted.
--
-- N-46 untouched: the view is read-only for the builder (SELECT only; asserted), and nothing here changes or deletes a life_events row.
-- REVOKEs: (a) on the NEW view (the default-ACL grant to retrieval_census_ro and PUBLIC); (b) the transient CREATE this file itself granted;
-- (c) the builder's five column-level SELECT grants on life_events (SS N-112), issued by amjis_app, the grantor of every one of them, AFTER the view
-- exists and is granted, in the same transaction: no moment with neither path or with both. The rollback leg re-grants EXACTLY those five
-- (grantor amjis_app, not grantable) before it drops the view, and asserts the column ACL is restored. Nothing else on the table's ACL moves.
--
-- LANDING SEQUENCE (SS N-112): PR-A (the L4 readers, #3047) and this migration land in ONE slot, both after S-L1: deploy PR-A, then apply this file
-- right away with the active-run guard on (run_gated.sh) and NO build in between. Before this file, PR-A's ph_pramana query (it filters on chart_id,
-- which the builder cannot read) FAILS LOUDLY with a privilege error; it never reads unscoped. After it, the helper reads the view. The old
-- (pre-PR-A) ph_pramana query worked only through the five column grants this file revokes.
--
-- Statements are grouped in steps (`-- @@STEP name`), which the executor runs one by one; the file is also valid for `psql -1 -f` as a
-- role with CREATEROLE (the mirror test does exactly that). No BEGIN/COMMIT in the file: the caller owns the transaction.
--
-- @@STEP s1_assume_owner_roles
-- The administrator (Cloud SQL `postgres`: CREATEROLE, not a superuser, no USAGE on schema public) needs membership of the roles it SETs.
-- Only the memberships GRANTED HERE are revoked again in s9 (tracked in transaction-local GUCs).
DO $m1274$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['data_plane_schema_owner', 'amjis_app', 'data_plane_builder'] LOOP
    IF NOT pg_has_role(current_user, r, 'MEMBER') THEN
      EXECUTE format('GRANT %I TO %I', r, current_user);
      PERFORM set_config('madhav.m1274_granted_' || r, 'on', true);
    END IF;
  END LOOP;
END
$m1274$;

-- @@STEP s2_preconditions
SET LOCAL ROLE data_plane_schema_owner;
DO $m1274$
DECLARE
  v_owner text;
  v_cols  text;
  v_bcols text;
BEGIN
  IF to_regclass('public.life_events') IS NULL THEN RAISE EXCEPTION 'm1274 precondition: public.life_events does not exist'; END IF;
  IF to_regclass('public.life_events_chart_scoped') IS NOT NULL THEN
    RAISE EXCEPTION 'm1274 precondition: public.life_events_chart_scoped already exists (already applied?)';
  END IF;
  SELECT pg_get_userbyid(relowner) INTO v_owner FROM pg_class WHERE oid = 'public.life_events'::regclass;
  IF v_owner <> 'amjis_app' THEN RAISE EXCEPTION 'm1274 precondition: life_events owner is %, expected amjis_app', v_owner; END IF;
  IF (SELECT relrowsecurity OR relforcerowsecurity FROM pg_class WHERE oid = 'public.life_events'::regclass) THEN
    RAISE EXCEPTION 'm1274 precondition: row level security is enabled on life_events; this plan was written for RLS off (re-review)';
  END IF;
  -- every exposed column exists with the expected type
  SELECT string_agg(a.attname || ':' || format_type(a.atttypid, a.atttypmod), ',' ORDER BY a.attname) INTO v_cols
    FROM pg_attribute a
   WHERE a.attrelid = 'public.life_events'::regclass AND a.attnum > 0 AND NOT a.attisdropped
     AND a.attname IN ('id','event_id','event_date','category','domain','chart_id');
  IF v_cols IS DISTINCT FROM 'category:text,chart_id:uuid,domain:text,event_date:date,event_id:text,id:uuid' THEN
    RAISE EXCEPTION 'm1274 precondition: life_events column set/type differs from the plan: %', v_cols;
  END IF;
  -- the accessor exists, is owned by amjis_app and still reads app.chart_context
  IF NOT EXISTS (SELECT 1 FROM pg_proc p WHERE p.oid = to_regprocedure('public.app_chart_context()')
                  AND pg_get_userbyid(p.proowner) = 'amjis_app' AND p.prorettype = 'uuid'::regtype AND NOT p.prosecdef
                  AND p.prosrc LIKE '%current_setting(''app.chart_context'', true)%') THEN
    RAISE EXCEPTION 'm1274 precondition: public.app_chart_context() missing or not the expected G1c accessor';
  END IF;
  -- the starting point read live (SS N-112): NO table-level privilege, and column-level SELECT on EXACTLY these five columns, each granted by amjis_app,
  -- none grantable; nothing else. Any other state is not the one this plan was approved for.
  IF has_table_privilege('data_plane_builder', 'public.life_events', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') THEN
    RAISE EXCEPTION 'm1274 precondition: data_plane_builder holds a table-level privilege on life_events';
  END IF;
  SELECT string_agg(a.attname || ':' || x.privilege_type || ':' || x.is_grantable::text || ':' || pg_get_userbyid(x.grantor), ',' ORDER BY a.attname, x.privilege_type)
    INTO v_bcols
    FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
   WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee = 'data_plane_builder'::regrole;
  IF v_bcols IS DISTINCT FROM 'category:SELECT:false:amjis_app,description:SELECT:false:amjis_app,event_date:SELECT:false:amjis_app,id:SELECT:false:amjis_app,outcome_observed:SELECT:false:amjis_app' THEN
    RAISE EXCEPTION 'm1274 precondition: the builder column ACL on life_events is not exactly the five production SELECT grants: %', v_bcols;
  END IF;
  -- the schema: owned by data_plane_schema_owner; amjis_app has no CREATE on it today
  IF (SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = 'public') <> 'data_plane_schema_owner' THEN
    RAISE EXCEPTION 'm1274 precondition: schema public is not owned by data_plane_schema_owner';
  END IF;
  IF has_schema_privilege('amjis_app', 'public', 'CREATE') THEN
    RAISE EXCEPTION 'm1274 precondition: amjis_app already has CREATE on schema public (unexpected state)';
  END IF;
  IF NOT has_schema_privilege('data_plane_builder', 'public', 'USAGE') THEN
    RAISE EXCEPTION 'm1274 precondition: data_plane_builder has no USAGE on schema public';
  END IF;
  -- pre-images, compared again in s8 (transaction-local; not persisted)
  PERFORM set_config('madhav.m1274_pre_schema_acl', (SELECT COALESCE(nspacl::text, 'NULL') FROM pg_namespace WHERE nspname = 'public'), true);
  PERFORM set_config('madhav.m1274_pre_table_acl',  (SELECT COALESCE(relacl::text, 'NULL') FROM pg_class WHERE oid = 'public.life_events'::regclass), true);
  PERFORM set_config('madhav.m1274_pre_fn_md5',     (SELECT md5(pg_get_functiondef(to_regprocedure('public.app_chart_context()')))), true);
  -- every OTHER role's column-level ACL on life_events (must be byte-for-byte the same afterwards)
  PERFORM set_config('madhav.m1274_pre_colacl_other', (SELECT COALESCE(md5(string_agg(a.attname || ':' || x.grantee::regrole::text || ':' || x.privilege_type || ':' || x.is_grantable::text || ':' || x.grantor::regrole::text,
                       ',' ORDER BY a.attname, x.grantee, x.privilege_type)), 'none')
                       FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
                      WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee <> 'data_plane_builder'::regrole), true);
END
$m1274$;
RESET ROLE;

-- @@STEP s3_transient_create_for_the_table_owner
SET LOCAL ROLE data_plane_schema_owner;
GRANT CREATE ON SCHEMA public TO amjis_app;
RESET ROLE;

-- @@STEP s4_create_view_as_table_owner
SET LOCAL ROLE amjis_app;
CREATE VIEW public.life_events_chart_scoped WITH (security_barrier = true) AS
  SELECT id, event_id, event_date, category, domain, chart_id
    FROM public.life_events
   WHERE chart_id = public.app_chart_context();
-- the default ACL of amjis_app in public grants SELECT on every new relation to retrieval_census_ro: not wanted on this view
REVOKE ALL ON public.life_events_chart_scoped FROM PUBLIC, retrieval_census_ro;
GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;
-- SS N-112: the view is granted FIRST, then the builder's direct column grants are revoked (same transaction, same grantor amjis_app as every one of them)
REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder;
COMMENT ON VIEW public.life_events_chart_scoped IS
  'Chart-scoped (chart_id = app_chart_context(); GUC app.chart_context; unset = zero rows), read-only, security-barrier window on life_events for the shared builder (SS ruling N-105, migration 1274). Only the 6 columns the L4 readers need (no free text). Owner amjis_app; SELECT granted to data_plane_builder only.';
RESET ROLE;

-- @@STEP s5_revoke_transient_create
SET LOCAL ROLE data_plane_schema_owner;
REVOKE CREATE ON SCHEMA public FROM amjis_app;
RESET ROLE;

-- @@STEP s6_behavioural_probe_as_owner
-- Pick the probe chart (the chart with the most events; ties by chart_id) and record COUNTS only, never content.
SET LOCAL ROLE amjis_app;
DO $m1274$
DECLARE
  v_chart uuid;
  v_n bigint;
  v_other uuid;
  v_other_n bigint;
BEGIN
  SELECT chart_id, count(*) INTO v_chart, v_n FROM public.life_events GROUP BY chart_id ORDER BY count(*) DESC, chart_id LIMIT 1;
  SELECT chart_id, count(*) INTO v_other, v_other_n FROM public.life_events WHERE chart_id IS DISTINCT FROM v_chart
    GROUP BY chart_id ORDER BY count(*) DESC, chart_id LIMIT 1;
  PERFORM set_config('madhav.m1274_probe_chart',   COALESCE(v_chart::text, ''), true);
  PERFORM set_config('madhav.m1274_probe_n',       COALESCE(v_n, 0)::text, true);
  PERFORM set_config('madhav.m1274_other_chart',   COALESCE(v_other::text, ''), true);
  PERFORM set_config('madhav.m1274_other_n',       COALESCE(v_other_n, 0)::text, true);
  PERFORM set_config('madhav.m1274_total_n',       (SELECT count(*) FROM public.life_events)::text, true);
END
$m1274$;
RESET ROLE;

-- @@STEP s7_behavioural_probe_as_builder
SET LOCAL ROLE data_plane_builder;
DO $m1274$
DECLARE
  v_chart  uuid := NULLIF(current_setting('madhav.m1274_probe_chart', true), '')::uuid;
  v_n      bigint := current_setting('madhav.m1274_probe_n', true)::bigint;
  v_other  uuid := NULLIF(current_setting('madhav.m1274_other_chart', true), '')::uuid;
  v_other_n bigint := current_setting('madhav.m1274_other_n', true)::bigint;
  v_cnt bigint;
  v_foreign bigint;
  v_col text;
BEGIN
  -- (1) the builder cannot read the table: not at all, and not through any of the five columns it used to hold or any other
  BEGIN
    PERFORM 1 FROM public.life_events LIMIT 1;
    RAISE EXCEPTION 'm1274 probe: data_plane_builder CAN read public.life_events directly';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  FOREACH v_col IN ARRAY ARRAY['id', 'event_date', 'category', 'description', 'outcome_observed', 'chart_id', 'event_id', 'domain'] LOOP
    BEGIN
      EXECUTE format('SELECT %I FROM public.life_events LIMIT 1', v_col);
      RAISE EXCEPTION 'm1274 probe: data_plane_builder CAN still read life_events.% directly', v_col;
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
  END LOOP;
  -- (2) GUC unset / empty / malformed / random chart -> zero rows (fail closed)
  PERFORM set_config('app.chart_context', '', true);
  SELECT count(*) INTO v_cnt FROM public.life_events_chart_scoped;
  IF v_cnt <> 0 THEN RAISE EXCEPTION 'm1274 probe: view returned % rows with the GUC unset', v_cnt; END IF;
  PERFORM set_config('app.chart_context', 'not-a-uuid', true);
  SELECT count(*) INTO v_cnt FROM public.life_events_chart_scoped;
  IF v_cnt <> 0 THEN RAISE EXCEPTION 'm1274 probe: view returned % rows with a malformed GUC', v_cnt; END IF;
  PERFORM set_config('app.chart_context', 'ffffffff-ffff-4fff-bfff-ffffffffffff', true);
  SELECT count(*) INTO v_cnt FROM public.life_events_chart_scoped;
  IF v_cnt <> 0 THEN RAISE EXCEPTION 'm1274 probe: view returned % rows for a chart that has none', v_cnt; END IF;
  -- (3) the probe chart: exactly its own rows, none of any other chart
  IF v_chart IS NOT NULL THEN
    PERFORM set_config('app.chart_context', v_chart::text, true);
    SELECT count(*), count(*) FILTER (WHERE chart_id <> v_chart) INTO v_cnt, v_foreign FROM public.life_events_chart_scoped;
    IF v_cnt <> v_n OR v_foreign <> 0 THEN
      RAISE EXCEPTION 'm1274 probe: view returned % rows (% foreign) for the probe chart, expected %', v_cnt, v_foreign, v_n;
    END IF;
  END IF;
  -- (4) a second chart, when the table holds one: exactly its own rows, none of the probe chart's
  IF v_other IS NOT NULL THEN
    PERFORM set_config('app.chart_context', v_other::text, true);
    SELECT count(*), count(*) FILTER (WHERE chart_id <> v_other) INTO v_cnt, v_foreign FROM public.life_events_chart_scoped;
    IF v_cnt <> v_other_n OR v_foreign <> 0 THEN
      RAISE EXCEPTION 'm1274 probe: view returned % rows (% foreign) for the second chart, expected %', v_cnt, v_foreign, v_other_n;
    END IF;
  END IF;
  -- (5) read-only for the builder
  BEGIN
    INSERT INTO public.life_events_chart_scoped (id) VALUES (gen_random_uuid());
    RAISE EXCEPTION 'm1274 probe: data_plane_builder CAN insert through the view';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    UPDATE public.life_events_chart_scoped SET category = category;
    RAISE EXCEPTION 'm1274 probe: data_plane_builder CAN update through the view';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    DELETE FROM public.life_events_chart_scoped;
    RAISE EXCEPTION 'm1274 probe: data_plane_builder CAN delete through the view';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  PERFORM set_config('app.chart_context', '', true);
END
$m1274$;
RESET ROLE;

-- @@STEP s8_post_assertions
-- ASSERTING: every check RAISES. A WARNING-and-commit would count as failure, so nothing here is a NOTICE or a WARNING.
SET LOCAL ROLE data_plane_schema_owner;
DO $m1274$
DECLARE
  v_col text;
  v_view regclass := to_regclass('public.life_events_chart_scoped');
  v_expected_owner_acl aclitem[] := acldefault('r', (SELECT oid FROM pg_roles WHERE rolname = 'amjis_app'));
  v_got aclitem[];
  v_opts text[];
BEGIN
  IF v_view IS NULL THEN RAISE EXCEPTION 'm1274 assert: the view does not exist'; END IF;
  -- the grant took (the one a bare GRANT can silently fail to make)
  IF NOT has_table_privilege('data_plane_builder', v_view, 'SELECT') THEN
    RAISE EXCEPTION 'm1274 assert: data_plane_builder has NO SELECT on the view (the GRANT did not take)';
  END IF;
  -- SELECT only, and no column-level extras
  IF has_table_privilege('data_plane_builder', v_view, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') THEN
    RAISE EXCEPTION 'm1274 assert: data_plane_builder holds more than SELECT on the view';
  END IF;
  -- the view ACL is EXACTLY {owner defaults, builder SELECT}: nothing for PUBLIC, retrieval_census_ro or any other role
  SELECT relacl INTO v_got FROM pg_class WHERE oid = v_view;
  IF EXISTS (
       (SELECT grantor, grantee, privilege_type, is_grantable FROM aclexplode(v_got)
        EXCEPT
        (SELECT grantor, grantee, privilege_type, is_grantable FROM aclexplode(v_expected_owner_acl)
         UNION ALL
         SELECT (SELECT oid FROM pg_roles WHERE rolname = 'amjis_app'), (SELECT oid FROM pg_roles WHERE rolname = 'data_plane_builder'), 'SELECT', false))
     ) OR EXISTS (
       (SELECT grantor, grantee, privilege_type, is_grantable FROM aclexplode(v_expected_owner_acl)
        UNION ALL
        SELECT (SELECT oid FROM pg_roles WHERE rolname = 'amjis_app'), (SELECT oid FROM pg_roles WHERE rolname = 'data_plane_builder'), 'SELECT', false)
        EXCEPT
        SELECT grantor, grantee, privilege_type, is_grantable FROM aclexplode(v_got)
     ) THEN
    RAISE EXCEPTION 'm1274 assert: the view ACL is not exactly {owner, data_plane_builder SELECT}: %', v_got::text;
  END IF;
  -- security barrier, definer semantics (no security_invoker), owner amjis_app, a plain view
  SELECT reloptions INTO v_opts FROM pg_class WHERE oid = v_view;
  IF v_opts IS DISTINCT FROM ARRAY['security_barrier=true']::text[] THEN RAISE EXCEPTION 'm1274 assert: reloptions are % (expected only security_barrier=true)', v_opts; END IF;
  IF (SELECT relkind FROM pg_class WHERE oid = v_view) <> 'v' THEN RAISE EXCEPTION 'm1274 assert: not a plain view'; END IF;
  IF (SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = v_view) <> 'amjis_app' THEN RAISE EXCEPTION 'm1274 assert: view owner is not amjis_app'; END IF;
  -- the view's own definition: chart-scoped by app_chart_context() and exposing exactly the six columns
  IF position('app_chart_context()' IN pg_get_viewdef(v_view)) = 0 OR position('chart_id' IN pg_get_viewdef(v_view)) = 0 THEN
    RAISE EXCEPTION 'm1274 assert: the view definition is not chart-scoped by app_chart_context()';
  END IF;
  IF (SELECT string_agg(attname, ',' ORDER BY attnum) FROM pg_attribute WHERE attrelid = v_view AND attnum > 0 AND NOT attisdropped)
       IS DISTINCT FROM 'id,event_id,event_date,category,domain,chart_id' THEN
    RAISE EXCEPTION 'm1274 assert: the view column list differs from the plan';
  END IF;
  -- the builder has NO direct privilege on the table any more: none at table level, none on ANY column (the five former ones named), no ACL entry left
  IF has_table_privilege('data_plane_builder', 'public.life_events', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
     OR has_any_column_privilege('data_plane_builder', 'public.life_events', 'SELECT,INSERT,UPDATE,REFERENCES') THEN
    RAISE EXCEPTION 'm1274 assert: data_plane_builder still holds a privilege on life_events';
  END IF;
  FOREACH v_col IN ARRAY ARRAY['id', 'event_date', 'category', 'description', 'outcome_observed'] LOOP
    IF has_column_privilege('data_plane_builder', 'public.life_events', v_col, 'SELECT') THEN
      RAISE EXCEPTION 'm1274 assert: data_plane_builder can still SELECT life_events.% (the REVOKE did not take)', v_col;
    END IF;
  END LOOP;
  IF EXISTS (SELECT 1 FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
              WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee = 'data_plane_builder'::regrole) THEN
    RAISE EXCEPTION 'm1274 assert: a column ACL entry of data_plane_builder remains on life_events';
  END IF;
  IF (SELECT COALESCE(md5(string_agg(a.attname || ':' || x.grantee::regrole::text || ':' || x.privilege_type || ':' || x.is_grantable::text || ':' || x.grantor::regrole::text,
                       ',' ORDER BY a.attname, x.grantee, x.privilege_type)), 'none')
        FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
       WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee <> 'data_plane_builder'::regrole)
     <> current_setting('madhav.m1274_pre_colacl_other') THEN
    RAISE EXCEPTION 'm1274 assert: another role''s column ACL on life_events changed';
  END IF;
  -- nothing else moved: the table ACL, the schema ACL, the accessor function
  IF (SELECT COALESCE(relacl::text, 'NULL') FROM pg_class WHERE oid = 'public.life_events'::regclass) <> current_setting('madhav.m1274_pre_table_acl') THEN
    RAISE EXCEPTION 'm1274 assert: the life_events ACL changed';
  END IF;
  IF (SELECT COALESCE(nspacl::text, 'NULL') FROM pg_namespace WHERE nspname = 'public') <> current_setting('madhav.m1274_pre_schema_acl') THEN
    RAISE EXCEPTION 'm1274 assert: the ACL of schema public is not byte-identical to its pre-state (the transient CREATE was not fully reverted)';
  END IF;
  IF has_schema_privilege('amjis_app', 'public', 'CREATE') THEN RAISE EXCEPTION 'm1274 assert: amjis_app still has CREATE on schema public'; END IF;
  IF md5(pg_get_functiondef(to_regprocedure('public.app_chart_context()'))) <> current_setting('madhav.m1274_pre_fn_md5') THEN
    RAISE EXCEPTION 'm1274 assert: app_chart_context() changed';
  END IF;
  -- the view's evidence is recorded for the executor (catalog facts only; counts are reported separately and are NOT part of the digest)
  PERFORM set_config('madhav.m1274_view_def_md5', md5(pg_get_viewdef(v_view)), true);
  PERFORM set_config('madhav.m1274_view_acl', (SELECT string_agg(grantee::regrole::text || ':' || privilege_type, ',' ORDER BY grantee::regrole::text, privilege_type)
                                                 FROM aclexplode(v_got)), true);
END
$m1274$;
RESET ROLE;

-- @@STEP s9_restore_memberships
DO $m1274$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['data_plane_schema_owner', 'amjis_app', 'data_plane_builder'] LOOP
    IF current_setting('madhav.m1274_granted_' || r, true) = 'on' THEN
      EXECUTE format('REVOKE %I FROM %I', r, current_user);
      IF pg_has_role(current_user, r, 'MEMBER') THEN
        RAISE EXCEPTION 'm1274 assert: the membership of % granted for this plan is still in place', r;
      END IF;
    END IF;
  END LOOP;
END
$m1274$;
