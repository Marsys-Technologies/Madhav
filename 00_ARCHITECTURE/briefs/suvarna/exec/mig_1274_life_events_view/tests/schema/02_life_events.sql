-- Mirror of production's life_events, its ACL, its policies (RLS DISABLED, as in production), the G1c accessor and the default ACL of amjis_app,
-- as read live as suvarna_reader on 2026-10-03 (catalog metadata only; the rows below are SYNTHETIC markers, never real life events).
-- Run as the cluster superuser, AFTER 00_roles.sql and 01_schema_acl.sql.
CREATE TABLE public.charts (id uuid PRIMARY KEY);
ALTER TABLE public.charts OWNER TO amjis_app;
CREATE TABLE public.life_events (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  event_id text NOT NULL,
  event_date date NOT NULL,
  category text NOT NULL,
  description text NOT NULL,
  significance text,
  chart_state jsonb NOT NULL,
  source_section text NOT NULL,
  build_id text NOT NULL,
  provenance jsonb NOT NULL,
  event_type text,
  domain text,
  source_citation text,
  outcome_observed boolean,
  chart_id uuid NOT NULL,
  recorded_at timestamptz DEFAULT now() NOT NULL,
  pool_consent boolean DEFAULT false NOT NULL,
  contributed_to_pool_at timestamptz,
  shape text DEFAULT 'point' NOT NULL,
  date_confidence text DEFAULT 'exact' NOT NULL,
  interval_start date,
  interval_end date,
  chain_parent_event_id text,
  milestone_label text,
  date_tightened_at timestamptz,
  date_tightened_by_source text,
  superseded_by_chain_note text,
  CONSTRAINT life_events_pkey PRIMARY KEY (id),
  CONSTRAINT life_events_chart_event_uq UNIQUE (chart_id, event_id),
  CONSTRAINT life_events_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id),
  CONSTRAINT life_events_date_confidence_check CHECK (date_confidence = ANY (ARRAY['exact','month_known','year_only'])),
  CONSTRAINT life_events_shape_check CHECK (shape = ANY (ARRAY['point','interval','chain']))
);
CREATE INDEX idx_life_events_date ON public.life_events USING btree (event_date);
CREATE INDEX idx_life_events_category ON public.life_events USING btree (category, event_date);
CREATE INDEX life_events_chart_id_idx ON public.life_events USING btree (chart_id);
ALTER TABLE public.life_events OWNER TO amjis_app;
-- production ACL: {amjis_app=arwdDxt/amjis_app, retrieval_census_ro=r/amjis_app, role_web_serve=r/amjis_app, role_orchestrator=arwd/amjis_app,
--                  role_jobs=r/amjis_app, nirmana_evidence_ingress_writer=r/amjis_app, suvarna_reader=r/amjis_app}
-- (role_sidecar is deliberately absent: it has a policy but no table privilege in production)
SET ROLE amjis_app;
GRANT SELECT ON public.life_events TO retrieval_census_ro;
GRANT SELECT ON public.life_events TO role_web_serve;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.life_events TO role_orchestrator;
GRANT SELECT ON public.life_events TO role_jobs;
GRANT SELECT ON public.life_events TO nirmana_evidence_ingress_writer;
GRANT SELECT ON public.life_events TO suvarna_reader;
-- PRODUCTION COLUMN ACL (pg_attribute.attacl, read live 2026-10-03): data_plane_builder holds SELECT on exactly these five columns, granted by amjis_app
-- (the builder-grants plan v1.3). The first mirror omitted this and was therefore not faithful (independent review HIGH-1).
GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder;
GRANT SELECT ON public.charts TO data_plane_builder;
RESET ROLE;
CREATE OR REPLACE FUNCTION public.app_chart_context()
 RETURNS uuid
 LANGUAGE plpgsql
 STABLE PARALLEL SAFE
AS $function$
DECLARE
  raw text;
BEGIN
  raw := nullif(current_setting('app.chart_context', true), '');
  IF raw IS NULL THEN
    RETURN NULL;
  END IF;
  BEGIN
    RETURN raw::uuid;
  EXCEPTION WHEN others THEN
    RETURN NULL;   -- malformed pin == no pin == deny
  END;
END
$function$;
ALTER FUNCTION public.app_chart_context() OWNER TO amjis_app;
CREATE POLICY life_events_g1c_chart_context ON public.life_events AS PERMISSIVE FOR ALL TO role_sidecar, role_web_serve
  USING (chart_id = app_chart_context()) WITH CHECK (chart_id = app_chart_context());
CREATE POLICY life_events_g1c_unscoped ON public.life_events AS PERMISSIVE FOR ALL TO role_jobs, role_ledger_write, role_orchestrator
  USING (true) WITH CHECK (true);
-- (RLS is NOT enabled on life_events in production: relrowsecurity = f. The policies exist and do nothing today.)
-- production pg_default_acl: amjis_app, schema public, relations: {retrieval_census_ro=r/amjis_app}
ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app IN SCHEMA public GRANT SELECT ON TABLES TO retrieval_census_ro;
-- SYNTHETIC rows: chart A (5), chart B (3). Markers only.
INSERT INTO public.charts VALUES ('aaaaaaaa-1111-4222-8333-00000000000a'), ('bbbbbbbb-1111-4222-8333-00000000000b'), ('cccccccc-1111-4222-8333-00000000000c');
INSERT INTO public.life_events (event_id, event_date, category, description, chart_state, source_section, build_id, provenance, domain, outcome_observed, chart_id)
SELECT 'EVT.A.' || n, DATE '2011-01-01' + n * 400, 'career', 'SYNTHETIC-A-' || n, '{}'::jsonb, 's', 'b', '{"src":"PRIVATE-PROVENANCE-A"}'::jsonb, 'career', (n % 2 = 0), 'aaaaaaaa-1111-4222-8333-00000000000a'
  FROM generate_series(1, 5) n;
INSERT INTO public.life_events (event_id, event_date, category, description, chart_state, source_section, build_id, provenance, domain, outcome_observed, chart_id)
SELECT 'EVT.B.' || n, DATE '2012-06-01' + n * 300, 'health', 'SYNTHETIC-B-' || n, '{}'::jsonb, 's', 'b', '{"src":"PRIVATE-PROVENANCE-B"}'::jsonb, 'health', NULL, 'bbbbbbbb-1111-4222-8333-00000000000b'
  FROM generate_series(1, 3) n;
