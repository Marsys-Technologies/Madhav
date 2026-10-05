-- 1274_life_events_chart_scoped_view_ROLLBACK.sql -- the exact inverse of 1274_life_events_chart_scoped_view.sql.
-- NEVER run by migrate.ts. Applied only by mig_1274_life_events_view_exec.py --rollback (gated, same transaction discipline).
-- Dropping the view removes its ACL with it. The forward leg also REVOKED the builder's five column-level SELECT grants on life_events (SS N-112);
-- this leg RE-GRANTS EXACTLY those five (id, event_date, category, description, outcome_observed; grantor amjis_app, not grantable) BEFORE it drops
-- the view (no moment with neither path), and asserts the builder's column ACL is exactly that again. Nothing else is touched.
-- Refused unless the live view is exactly the one the forward leg created (so a later, different object of that name is never dropped).
--
-- @@STEP r1_assume_owner_roles
DO $m1274$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['data_plane_schema_owner', 'amjis_app'] LOOP
    IF NOT pg_has_role(current_user, r, 'MEMBER') THEN
      EXECUTE format('GRANT %I TO %I', r, current_user);
      PERFORM set_config('madhav.m1274_granted_' || r, 'on', true);
    END IF;
  END LOOP;
END
$m1274$;

-- @@STEP r2_preconditions
SET LOCAL ROLE data_plane_schema_owner;
DO $m1274$
DECLARE v regclass := to_regclass('public.life_events_chart_scoped');
BEGIN
  -- the state the forward leg leaves: the builder holds NOTHING on life_events (table or column)
  IF has_table_privilege('data_plane_builder', 'public.life_events', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
     OR has_any_column_privilege('data_plane_builder', 'public.life_events', 'SELECT,INSERT,UPDATE,REFERENCES') THEN
    RAISE EXCEPTION 'm1274 rollback precondition: data_plane_builder holds a privilege on life_events (not the state the forward leg leaves)';
  END IF;
  IF v IS NULL THEN RAISE EXCEPTION 'm1274 rollback precondition: the view does not exist (nothing to roll back)'; END IF;
  IF (SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = v) <> 'amjis_app'
     OR (SELECT relkind FROM pg_class WHERE oid = v) <> 'v'
     OR (SELECT reloptions FROM pg_class WHERE oid = v) IS DISTINCT FROM ARRAY['security_barrier=true']::text[] THEN
    RAISE EXCEPTION 'm1274 rollback precondition: the live object is not the view the forward leg created (owner/kind/options differ)';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid
              WHERE d.refobjid = v AND d.classid = 'pg_rewrite'::regclass AND r.ev_class <> v) THEN
    RAISE EXCEPTION 'm1274 rollback precondition: another object depends on the view; refusing to drop it';
  END IF;
  PERFORM set_config('madhav.m1274_pre_schema_acl', (SELECT COALESCE(nspacl::text, 'NULL') FROM pg_namespace WHERE nspname = 'public'), true);
  PERFORM set_config('madhav.m1274_pre_table_acl',  (SELECT COALESCE(relacl::text, 'NULL') FROM pg_class WHERE oid = 'public.life_events'::regclass), true);
  PERFORM set_config('madhav.m1274_pre_fn_md5',     (SELECT md5(pg_get_functiondef(to_regprocedure('public.app_chart_context()')))), true);
  PERFORM set_config('madhav.m1274_pre_colacl_other', (SELECT COALESCE(md5(string_agg(a.attname || ':' || x.grantee::regrole::text || ':' || x.privilege_type || ':' || x.is_grantable::text || ':' || x.grantor::regrole::text,
                       ',' ORDER BY a.attname, x.grantee, x.privilege_type)), 'none')
                       FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
                      WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee <> 'data_plane_builder'::regrole), true);
END
$m1274$;
RESET ROLE;

-- @@STEP r3_drop_view_as_owner
SET LOCAL ROLE amjis_app;
GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder;
DROP VIEW public.life_events_chart_scoped RESTRICT;
RESET ROLE;

-- @@STEP r4_post_assertions
SET LOCAL ROLE data_plane_schema_owner;
DO $m1274$
DECLARE v_bcols text;
BEGIN
  IF to_regclass('public.life_events_chart_scoped') IS NOT NULL THEN RAISE EXCEPTION 'm1274 rollback assert: the view still exists'; END IF;
  -- the original production state, exactly: no table-level privilege; column-level SELECT on exactly the five columns, grantor amjis_app, not grantable
  IF has_table_privilege('data_plane_builder', 'public.life_events', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') THEN
    RAISE EXCEPTION 'm1274 rollback assert: data_plane_builder holds a table-level privilege on life_events';
  END IF;
  SELECT string_agg(a.attname || ':' || x.privilege_type || ':' || x.is_grantable::text || ':' || pg_get_userbyid(x.grantor), ',' ORDER BY a.attname, x.privilege_type)
    INTO v_bcols
    FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
   WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee = 'data_plane_builder'::regrole;
  IF v_bcols IS DISTINCT FROM 'category:SELECT:false:amjis_app,description:SELECT:false:amjis_app,event_date:SELECT:false:amjis_app,id:SELECT:false:amjis_app,outcome_observed:SELECT:false:amjis_app' THEN
    RAISE EXCEPTION 'm1274 rollback assert: the builder column ACL on life_events is not exactly the original five SELECT grants: %', v_bcols;
  END IF;
  IF (SELECT COALESCE(md5(string_agg(a.attname || ':' || x.grantee::regrole::text || ':' || x.privilege_type || ':' || x.is_grantable::text || ':' || x.grantor::regrole::text,
                       ',' ORDER BY a.attname, x.grantee, x.privilege_type)), 'none')
        FROM pg_attribute a, LATERAL aclexplode(a.attacl) x
       WHERE a.attrelid = 'public.life_events'::regclass AND a.attacl IS NOT NULL AND x.grantee <> 'data_plane_builder'::regrole)
     <> current_setting('madhav.m1274_pre_colacl_other') THEN
    RAISE EXCEPTION 'm1274 rollback assert: another role''s column ACL on life_events changed';
  END IF;
  IF (SELECT COALESCE(relacl::text, 'NULL') FROM pg_class WHERE oid = 'public.life_events'::regclass) <> current_setting('madhav.m1274_pre_table_acl') THEN
    RAISE EXCEPTION 'm1274 rollback assert: the life_events ACL changed';
  END IF;
  IF (SELECT COALESCE(nspacl::text, 'NULL') FROM pg_namespace WHERE nspname = 'public') <> current_setting('madhav.m1274_pre_schema_acl') THEN
    RAISE EXCEPTION 'm1274 rollback assert: the ACL of schema public changed';
  END IF;
  IF md5(pg_get_functiondef(to_regprocedure('public.app_chart_context()'))) <> current_setting('madhav.m1274_pre_fn_md5') THEN
    RAISE EXCEPTION 'm1274 rollback assert: app_chart_context() changed';
  END IF;
END
$m1274$;
RESET ROLE;

-- @@STEP r5_restore_memberships
DO $m1274$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['data_plane_schema_owner', 'amjis_app'] LOOP
    IF current_setting('madhav.m1274_granted_' || r, true) = 'on' THEN
      EXECUTE format('REVOKE %I FROM %I', r, current_user);
      IF pg_has_role(current_user, r, 'MEMBER') THEN
        RAISE EXCEPTION 'm1274 rollback assert: the membership of % granted for this plan is still in place', r;
      END IF;
    END IF;
  END LOOP;
END
$m1274$;
