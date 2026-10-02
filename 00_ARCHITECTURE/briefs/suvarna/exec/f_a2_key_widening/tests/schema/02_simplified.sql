-- simplified control tables (only the columns the data-plane functions read), owner amjis_app
CREATE TABLE public.charts (
  id uuid PRIMARY KEY, chart_id uuid, client_id text, owner_id text,
  birth_date date, birth_time time, birth_lat double precision, birth_lng double precision,
  timezone_id text, house_system text
);
ALTER TABLE public.charts ENABLE ROW LEVEL SECURITY;
CREATE POLICY chart_service_policy ON public.charts AS PERMISSIVE FOR ALL USING ((current_setting('app.principal_id'::text, true) IS NULL) OR (current_setting('app.principal_id'::text, true) = ''::text));
CREATE POLICY chart_owner_policy ON public.charts AS PERMISSIVE FOR ALL USING (owner_id = current_setting('app.principal_id'::text, true));
CREATE TABLE public.build_runs (id uuid PRIMARY KEY, chart_id uuid, state text NOT NULL CHECK (state = ANY (ARRAY['planned','running','paused','completed','stopped','failed'])));
CREATE TABLE public.build_run_assets (run_id uuid NOT NULL REFERENCES public.build_runs(id), asset_id text NOT NULL, state text NOT NULL CHECK (state = ANY (ARRAY['queued','building','complete','skipped','error','aborted'])), PRIMARY KEY (run_id, asset_id));
CREATE TABLE public.asset_registry (asset_id text PRIMARY KEY, depends_on text[], target_floor integer, has_substeps boolean);
