-- Mirror of production's phala_pramana and the objects the executor reads, as read live (catalog metadata only: columns, constraints, indexes, owners, ACLs) as
-- suvarna_reader on 2026-10-03. Rows are SYNTHETIC (see 03_seed.sql). Run as the cluster superuser, AFTER 00_roles.sql (W1 roles.sql, verbatim) and
-- 01_schema_acl.sql (W1 schema_acl.sql, verbatim). The W1 pre.sql holds no phala_* DDL, so these tables are reconstructed from the catalog reads.
CREATE TABLE public.phala_anchors (
  anchor_id uuid NOT NULL,
  chart_id uuid,
  CONSTRAINT phala_anchors_pkey PRIMARY KEY (anchor_id)
);
CREATE TABLE public.phala_pramana (
  pramana_id uuid DEFAULT gen_random_uuid() NOT NULL,
  chart_id uuid NOT NULL,
  anchor_id uuid NOT NULL,
  evidence_type text NOT NULL,
  evidence_strength_label text NOT NULL,
  falsifier_text text NOT NULL,
  observable_criteria_jsonb jsonb NOT NULL,
  window_status text NOT NULL,
  lel_entry_id bigint,
  lel_entry_jsonb jsonb,
  linked_sodhana_id uuid,
  derivation_ledger_jsonb jsonb NOT NULL,
  source_citation text NOT NULL,
  computed_at timestamptz DEFAULT now() NOT NULL,
  CONSTRAINT phala_pramana_pkey PRIMARY KEY (pramana_id),
  CONSTRAINT phala_pramana_anchor_id_fkey FOREIGN KEY (anchor_id) REFERENCES public.phala_anchors(anchor_id) ON DELETE CASCADE,
  CONSTRAINT phala_pramana_evidence_strength_label_check CHECK (evidence_strength_label = ANY (ARRAY['direct', 'indirect', 'proxy'])),
  CONSTRAINT phala_pramana_evidence_type_check CHECK (evidence_type = ANY (ARRAY['life_event_match', 'life_event_miss', 'proxy_indicator', 'self_report', 'pending_observation', 'detector_unavailable'])),
  CONSTRAINT phala_pramana_window_status_check CHECK (window_status = ANY (ARRAY['pending', 'open', 'past_window']))
);
CREATE INDEX phala_pramana_chart_id ON public.phala_pramana USING btree (chart_id);
CREATE INDEX phala_pramana_anchor_id ON public.phala_pramana USING btree (anchor_id);
CREATE INDEX phala_pramana_window_status ON public.phala_pramana USING btree (chart_id, window_status);
CREATE UNIQUE INDEX phala_pramana_natural_key ON public.phala_pramana USING btree (anchor_id, evidence_type, COALESCE(lel_entry_id, ('-1'::integer)::bigint));

CREATE TABLE public.phala_pramana__ssv_20260728b (
  pramana_id uuid NOT NULL,
  chart_id uuid NOT NULL,
  evidence_type text NOT NULL,
  lel_entry_jsonb jsonb,
  CONSTRAINT phala_pramana__ssv_20260728b_pkey PRIMARY KEY (pramana_id)
);
CREATE TABLE public.build_runs (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  chart_id uuid NOT NULL,
  state text NOT NULL,
  CONSTRAINT build_runs_pkey PRIMARY KEY (id),
  CONSTRAINT build_runs_state_check CHECK (state = ANY (ARRAY['planned', 'running', 'paused', 'completed', 'stopped', 'failed']))
);
CREATE TABLE public.mimamsa_predictions (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  source_pramana_id text,
  body jsonb,
  CONSTRAINT mimamsa_predictions_pkey PRIMARY KEY (id)
);
CREATE TABLE public.mimamsa_predictions__ssv_20260728b (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  source_pramana_id text,
  body jsonb,
  CONSTRAINT mimamsa_predictions__ssv_20260728b_pkey PRIMARY KEY (id)
);
CREATE TABLE public.mimamsa_anchor_adjustment (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, derived_from_pramana_ids jsonb);
CREATE TABLE public.mimamsa_convergence_adjustment (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, derived_from_pramana_ids jsonb);
CREATE TABLE public.mimamsa_fact_adjustment (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, derived_from_pramana_ids jsonb);
CREATE TABLE public.mimamsa_signal_adjustment (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, derived_from_pramana_ids jsonb);

ALTER TABLE public.phala_anchors OWNER TO amjis_app;
ALTER TABLE public.phala_pramana OWNER TO amjis_app;
ALTER TABLE public.phala_pramana__ssv_20260728b OWNER TO amjis_app;
ALTER TABLE public.build_runs OWNER TO amjis_app;
ALTER TABLE public.mimamsa_predictions OWNER TO amjis_app;
ALTER TABLE public.mimamsa_predictions__ssv_20260728b OWNER TO amjis_app;
ALTER TABLE public.mimamsa_anchor_adjustment OWNER TO amjis_app;
ALTER TABLE public.mimamsa_convergence_adjustment OWNER TO amjis_app;
ALTER TABLE public.mimamsa_fact_adjustment OWNER TO amjis_app;
ALTER TABLE public.mimamsa_signal_adjustment OWNER TO amjis_app;

-- production ACLs, granted by the owner in production's order so the ACL text is byte-identical (asserted by test_the_mirror_is_production_shaped)
SET ROLE amjis_app;
-- phala_pramana: {amjis_app=arwdDxt/amjis_app,retrieval_census_ro=r/amjis_app,role_web_serve=r/amjis_app,role_orchestrator=arwd/amjis_app,role_jobs=r/amjis_app,
--                 role_sidecar=r/amjis_app,nirmana_evidence_ingress_writer=r/amjis_app,suvarna_reader=r/amjis_app,data_plane_builder=ard/amjis_app}
GRANT SELECT ON public.phala_pramana TO retrieval_census_ro;
GRANT SELECT ON public.phala_pramana TO role_web_serve;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.phala_pramana TO role_orchestrator;
GRANT SELECT ON public.phala_pramana TO role_jobs;
GRANT SELECT ON public.phala_pramana TO role_sidecar;
GRANT SELECT ON public.phala_pramana TO nirmana_evidence_ingress_writer;
GRANT SELECT ON public.phala_pramana TO suvarna_reader;
GRANT SELECT, INSERT, DELETE ON public.phala_pramana TO data_plane_builder;
-- phala_anchors: same shape as phala_pramana
GRANT SELECT ON public.phala_anchors TO retrieval_census_ro;
GRANT SELECT ON public.phala_anchors TO role_web_serve;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.phala_anchors TO role_orchestrator;
GRANT SELECT ON public.phala_anchors TO role_jobs;
GRANT SELECT ON public.phala_anchors TO role_sidecar;
GRANT SELECT ON public.phala_anchors TO nirmana_evidence_ingress_writer;
GRANT SELECT ON public.phala_anchors TO suvarna_reader;
GRANT SELECT, INSERT, DELETE ON public.phala_anchors TO data_plane_builder;
-- build_runs: {...,nirmana_campaign_control_writer=r,data_plane_l1_owner=r,data_plane_l2_owner=r,data_plane_builder=arwd,suvarna_reader=r}
GRANT SELECT ON public.build_runs TO retrieval_census_ro;
GRANT SELECT ON public.build_runs TO role_web_serve;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.build_runs TO role_orchestrator;
GRANT SELECT ON public.build_runs TO role_jobs;
GRANT SELECT ON public.build_runs TO role_sidecar;
GRANT SELECT ON public.build_runs TO nirmana_evidence_ingress_writer;
GRANT SELECT ON public.build_runs TO nirmana_campaign_control_writer;
GRANT SELECT ON public.build_runs TO data_plane_l1_owner;
GRANT SELECT ON public.build_runs TO data_plane_l2_owner;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.build_runs TO data_plane_builder;
GRANT SELECT ON public.build_runs TO suvarna_reader;
-- mimamsa_predictions: builder ard, role_ledger_write arw, owner WITHOUT TRUNCATE; the other mimamsa_*: owner arwdDxt, the reader r, the builder NOTHING
REVOKE TRUNCATE ON public.mimamsa_predictions FROM amjis_app;
GRANT SELECT ON public.mimamsa_predictions TO retrieval_census_ro;
GRANT SELECT ON public.mimamsa_predictions TO role_web_serve;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.mimamsa_predictions TO role_orchestrator;
GRANT SELECT, INSERT, UPDATE ON public.mimamsa_predictions TO role_ledger_write;
GRANT SELECT ON public.mimamsa_predictions TO role_jobs;
GRANT SELECT ON public.mimamsa_predictions TO role_sidecar;
GRANT SELECT ON public.mimamsa_predictions TO nirmana_evidence_ingress_writer;
GRANT SELECT ON public.mimamsa_predictions TO suvarna_reader;
GRANT SELECT, INSERT, DELETE ON public.mimamsa_predictions TO data_plane_builder;
GRANT SELECT ON public.mimamsa_predictions__ssv_20260728b TO suvarna_reader;
GRANT SELECT ON public.phala_pramana__ssv_20260728b TO suvarna_reader;
GRANT SELECT ON public.mimamsa_anchor_adjustment TO suvarna_reader;
GRANT SELECT ON public.mimamsa_convergence_adjustment TO suvarna_reader;
GRANT SELECT ON public.mimamsa_fact_adjustment TO suvarna_reader;
GRANT SELECT ON public.mimamsa_signal_adjustment TO suvarna_reader;
RESET ROLE;
