-- state after the ownership preflight (builder SELECT-only on protected tables), grants per prod relacl
\set ON_ERROR_STOP on
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['chart_facts','chart_dashas','chart_divisionals','ga_condition_composite','ga_yoga_firings','chart_vichara','ga_transit_anchors','l1_tajik_varsha_year_lords','ga_medical','ga_vastu_planet_direction_map','ga_prashna_lagna','ga_prashna_judgment'] LOOP
  EXECUTE format('ALTER TABLE public.%I OWNER TO data_plane_l1_owner', t);
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC', t);
  EXECUTE format('GRANT SELECT ON public.%I TO data_plane_builder, data_plane_verifier, data_plane_migrator, data_plane_l2_owner, amjis_app', t);
 END LOOP;
END $$;
DO $$ DECLARE s regclass; BEGIN
 FOR s IN SELECT c.oid::regclass FROM pg_class c WHERE c.relkind='S' AND c.relnamespace='public'::regnamespace LOOP
  EXECUTE format('ALTER SEQUENCE %s OWNER TO data_plane_l1_owner', s);
 END LOOP;
END $$;
ALTER TABLE public.charts OWNER TO amjis_app;
ALTER TABLE public.build_runs OWNER TO amjis_app;
ALTER TABLE public.build_run_assets OWNER TO amjis_app;
ALTER TABLE public.asset_registry OWNER TO amjis_app;
ALTER TABLE public.fact_category_ownership OWNER TO amjis_app;
ALTER TABLE public.brahma_yoga_catalog OWNER TO amjis_app;
ALTER TABLE public.brahma_dosha_catalog OWNER TO amjis_app;
GRANT SELECT ON public.charts, public.build_runs, public.build_run_assets, public.asset_registry, public.fact_category_ownership TO data_plane_l1_owner;
GRANT SELECT ON public.charts, public.build_runs, public.build_run_assets, public.asset_registry TO data_plane_l2_owner;
GRANT SELECT ON public.charts TO data_plane_builder;
GRANT SELECT ON public.asset_registry TO data_plane_builder;
GRANT ALL ON public.build_runs, public.build_run_assets, public.brahma_yoga_catalog, public.brahma_dosha_catalog TO data_plane_builder, role_orchestrator;
-- schema
ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner, data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve;
GRANT CREATE ON SCHEMA public TO data_plane_l1_owner, data_plane_l2_owner;
