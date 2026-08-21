--
-- PostgreSQL database dump
--

\restrict 4xuld3J3FNrP071y0qFeGjIpYXCRPLktRaTPUR3vfMsiL3tn6AexdnEmLMe7iD8

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bodha_rm_remedy_prescriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bodha_rm_remedy_prescriptions (
    prescription_id uuid NOT NULL,
    chart_id uuid NOT NULL,
    ayanamsha_id text NOT NULL,
    build_id uuid NOT NULL,
    snapshot_type text NOT NULL,
    target_graha text NOT NULL,
    target_resonance_id uuid NOT NULL,
    tradition text NOT NULL,
    sub_tradition text,
    remedy_category text NOT NULL,
    remedy_id_g27 text NOT NULL,
    remedy_label_human text NOT NULL,
    prescription_detail_jsonb jsonb NOT NULL,
    classical_strength_rating text,
    classical_sources_jsonb jsonb NOT NULL,
    classical_source_text_jsonb jsonb,
    targets_motif_id uuid,
    targets_cell_id uuid,
    targets_dosha_class text,
    resonance_match_score numeric,
    match_score_formula_version text,
    counter_indications_array text[],
    incompatible_with_prescription_ids_array uuid[],
    prerequisite_prescription_ids_array uuid[],
    feasibility_score numeric,
    estimated_cost_inr_range_jsonb jsonb,
    estimated_time_minutes_daily numeric,
    ritual_complexity_class text,
    requires_acharya_review_flag boolean NOT NULL,
    acharya_review_reason_array text[],
    cross_tradition_corroboration_count integer,
    cross_tradition_corroborating_traditions_array text[],
    phase_sequence_class text,
    phase_duration_days integer,
    count_prescription_jsonb jsonb,
    substitute_options_jsonb jsonb,
    yantra_geometry_jsonb jsonb,
    pranapratishtha_required_flag boolean,
    pilgrimage_site_jsonb jsonb,
    pilgrimage_priority_rank integer,
    recommended_hora_lord_array text[],
    recommended_choghadiya_window_array text[],
    initiation_lunar_phase_recommendation_array text[],
    recommended_facing_direction text,
    outcome_tracking_placeholder_jsonb jsonb,
    prescription_embedding_vec public.vector(768),
    verification_pass_status text NOT NULL,
    citation_ref text NOT NULL,
    citation_human text NOT NULL,
    computed_at timestamp with time zone NOT NULL
);


--
-- Name: chart_facts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chart_facts (
    fact_id text NOT NULL,
    chart_id uuid NOT NULL,
    ayanamsha_id text NOT NULL,
    build_id uuid NOT NULL,
    fact_category text NOT NULL,
    fact_subject text NOT NULL,
    fact_key text NOT NULL,
    fact_value_text text,
    fact_value_num numeric,
    fact_value_jsonb jsonb,
    unit text,
    citation_ref text NOT NULL,
    citation_human text NOT NULL,
    source_calculation text NOT NULL,
    verification_pass_status text NOT NULL,
    engine_version text NOT NULL,
    salience_formula_ver text,
    computed_at timestamp with time zone NOT NULL,
    tolerance_arcsec double precision,
    near_sign_boundary_flag boolean DEFAULT false,
    near_nakshatra_boundary_flag boolean DEFAULT false,
    vargottama_flag_at_point boolean DEFAULT false,
    formula_provenance_text text,
    cross_ayanamsha_divergence_arcsec double precision DEFAULT 0.0,
    formula_id text
);


--
-- Name: mimamsa_insight_units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mimamsa_insight_units (
    chart_id uuid NOT NULL,
    insight_id text NOT NULL,
    insight_type text NOT NULL,
    domain text,
    horizon text,
    question_lens text,
    statement text NOT NULL,
    rank_consequence numeric NOT NULL,
    confidence_band numrange,
    n_support integer NOT NULL,
    leakage_status text NOT NULL,
    evidence_grade text NOT NULL,
    freshness_lel_version text NOT NULL,
    last_calibrated_at timestamp with time zone,
    provenance_chain jsonb NOT NULL,
    is_negative_knowledge boolean NOT NULL,
    surface_formula_version text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: mimamsa_manifestation_grammar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mimamsa_manifestation_grammar (
    chart_id uuid NOT NULL,
    origin_kind text NOT NULL,
    origin_ref text NOT NULL,
    channel_id text NOT NULL,
    domain text NOT NULL,
    fire_count integer NOT NULL,
    opportunity_count integer NOT NULL,
    channel_propensity numeric,
    prior_propensity numeric NOT NULL,
    propensity_delta numeric,
    n_support integer NOT NULL,
    confidence_band numrange,
    evidence_grade text NOT NULL,
    citation_ref jsonb NOT NULL,
    grammar_formula_version text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    scored_count integer DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN mimamsa_manifestation_grammar.evidence_grade; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_manifestation_grammar.evidence_grade IS '''empirical''|''assignment_only''|''prior_only'' — empirical requires scored_count >= 5 (confirmed/partial/denied outcomes), not just opportunity_count >= 5 assignments. See F-35 (00_ARCHITECTURE/briefs/parisesa/lanes/F-35/).';


--
-- Name: bodha_rm_remedy_prescriptions bodha_rm_remedy_prescriptions_chart_id_ayanamsha_id_build_i_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_rm_remedy_prescriptions
    ADD CONSTRAINT bodha_rm_remedy_prescriptions_chart_id_ayanamsha_id_build_i_key UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, target_graha, tradition, sub_tradition, remedy_category, remedy_id_g27);


--
-- Name: bodha_rm_remedy_prescriptions bodha_rm_remedy_prescriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_rm_remedy_prescriptions
    ADD CONSTRAINT bodha_rm_remedy_prescriptions_pkey PRIMARY KEY (prescription_id);


--
-- Name: chart_facts chart_facts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_facts
    ADD CONSTRAINT chart_facts_pkey PRIMARY KEY (fact_id);


--
-- Name: chart_facts chart_facts_verification_pass_status_check; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.chart_facts
    ADD CONSTRAINT chart_facts_verification_pass_status_check CHECK ((verification_pass_status = ANY (ARRAY['two_pass_verified'::text, 'classical_match'::text, 'divergent_flagged'::text, 'single'::text, 'single_pass'::text, 'documented_approximation'::text, 'computed_extension'::text, 'floored'::text, 'not_defined_for_nodes'::text, 'scope_cap_sentinel'::text, 'skipped_malformed_source'::text, 'external_computation_required'::text, 'pending_w3_verification'::text]))) NOT VALID;


--
-- Name: mimamsa_insight_units mimamsa_insight_units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_insight_units
    ADD CONSTRAINT mimamsa_insight_units_pkey PRIMARY KEY (chart_id, insight_id);


--
-- Name: mimamsa_manifestation_grammar mimamsa_manifestation_grammar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_manifestation_grammar
    ADD CONSTRAINT mimamsa_manifestation_grammar_pkey PRIMARY KEY (chart_id, origin_kind, origin_ref, channel_id);


--
-- Name: chart_facts_ayanamsha_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_ayanamsha_idx ON public.chart_facts USING btree (chart_id, ayanamsha_id);


--
-- Name: chart_facts_build_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_build_idx ON public.chart_facts USING btree (build_id);


--
-- Name: chart_facts_category_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_category_idx ON public.chart_facts USING btree (chart_id, fact_category);


--
-- Name: chart_facts_chart_aya_cat_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_chart_aya_cat_idx ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_category);


--
-- Name: chart_facts_chart_aya_sub_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_chart_aya_sub_idx ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_subject);


--
-- Name: chart_facts_chart_cat_sub_key_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_chart_cat_sub_key_idx ON public.chart_facts USING btree (chart_id, fact_category, fact_subject, fact_key);


--
-- Name: chart_facts_chart_computed_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_chart_computed_idx ON public.chart_facts USING btree (chart_id, computed_at DESC);


--
-- Name: chart_facts_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_chart_id_idx ON public.chart_facts USING btree (chart_id);


--
-- Name: chart_facts_jsonb_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_jsonb_gin ON public.chart_facts USING gin (fact_value_jsonb);


--
-- Name: chart_facts_subject_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_subject_idx ON public.chart_facts USING btree (chart_id, fact_subject);


--
-- Name: chart_facts_unique_null_formula; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX chart_facts_unique_null_formula ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id) WHERE (formula_id IS NULL);


--
-- Name: chart_facts_unique_with_formula; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX chart_facts_unique_with_formula ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id, formula_id) WHERE (formula_id IS NOT NULL);


--
-- Name: chart_facts_verification_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_facts_verification_idx ON public.chart_facts USING btree (verification_pass_status) WHERE (verification_pass_status <> 'single'::text);


--
-- Name: idx_bodha_rm_remedy_target_resonance_fk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bodha_rm_remedy_target_resonance_fk ON public.bodha_rm_remedy_prescriptions USING btree (target_resonance_id);


--
-- Name: idx_mimamsa_insight_units_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mimamsa_insight_units_chart_id ON public.mimamsa_insight_units USING btree (chart_id);


--
-- Name: idx_mimamsa_insight_units_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mimamsa_insight_units_domain ON public.mimamsa_insight_units USING btree (chart_id, domain);


--
-- Name: idx_mimamsa_insight_units_negative; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mimamsa_insight_units_negative ON public.mimamsa_insight_units USING btree (chart_id, is_negative_knowledge);


--
-- Name: idx_mimamsa_insight_units_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mimamsa_insight_units_type ON public.mimamsa_insight_units USING btree (chart_id, insight_type);


--
-- Name: idx_mimamsa_manifestation_grammar_channel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mimamsa_manifestation_grammar_channel ON public.mimamsa_manifestation_grammar USING btree (chart_id, channel_id);


--
-- Name: idx_mimamsa_manifestation_grammar_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mimamsa_manifestation_grammar_chart_id ON public.mimamsa_manifestation_grammar USING btree (chart_id);


--
-- Name: rm_prescriptions_category_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_category_idx ON public.bodha_rm_remedy_prescriptions USING btree (chart_id, ayanamsha_id, remedy_category);


--
-- Name: rm_prescriptions_chart_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_chart_idx ON public.bodha_rm_remedy_prescriptions USING btree (chart_id, ayanamsha_id);


--
-- Name: rm_prescriptions_counter_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_counter_gin ON public.bodha_rm_remedy_prescriptions USING gin (counter_indications_array);


--
-- Name: rm_prescriptions_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_embedding_hnsw ON public.bodha_rm_remedy_prescriptions USING hnsw (prescription_embedding_vec public.vector_cosine_ops);


--
-- Name: rm_prescriptions_match_score_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_match_score_idx ON public.bodha_rm_remedy_prescriptions USING btree (chart_id, ayanamsha_id, resonance_match_score DESC);


--
-- Name: rm_prescriptions_review_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_review_idx ON public.bodha_rm_remedy_prescriptions USING btree (chart_id, ayanamsha_id) WHERE (requires_acharya_review_flag = true);


--
-- Name: rm_prescriptions_target_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_target_idx ON public.bodha_rm_remedy_prescriptions USING btree (chart_id, ayanamsha_id, target_graha);


--
-- Name: rm_prescriptions_tradition_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rm_prescriptions_tradition_idx ON public.bodha_rm_remedy_prescriptions USING btree (chart_id, ayanamsha_id, tradition);


--
-- Name: ux_chart_facts_sade_sati_cycle_end_value; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_chart_facts_sade_sati_cycle_end_value ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_value_text) WHERE ((fact_category = 'sade_sati_cycle'::text) AND (fact_key = 'cycle_end_iso'::text));


--
-- Name: ux_chart_facts_sade_sati_cycle_start_value; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_chart_facts_sade_sati_cycle_start_value ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_value_text) WHERE ((fact_category = 'sade_sati_cycle'::text) AND (fact_key = 'cycle_start_iso'::text));


--
-- Name: bodha_rm_remedy_prescriptions bodha_rm_remedy_prescriptions_target_resonance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_rm_remedy_prescriptions
    ADD CONSTRAINT bodha_rm_remedy_prescriptions_target_resonance_id_fkey FOREIGN KEY (target_resonance_id) REFERENCES public.bodha_rm_resonances(resonance_id);


--
-- PostgreSQL database dump complete
--

\unrestrict 4xuld3J3FNrP071y0qFeGjIpYXCRPLktRaTPUR3vfMsiL3tn6AexdnEmLMe7iD8

