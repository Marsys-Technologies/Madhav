--
-- PostgreSQL database dump
--


-- Dumped from database version 15.17
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
-- Name: chart_divisionals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chart_divisionals (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    chart_id uuid NOT NULL,
    graha text,
    ayanamsha_id text NOT NULL,
    varga text NOT NULL,
    sign text,
    sign_number smallint,
    degree_in_sign numeric(8,4),
    house smallint,
    vargottama boolean,
    source_citation text DEFAULT 'PyJHora DE441 / MARSYS-engine v1'::text NOT NULL,
    build_id text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    fact_category text,
    fact_key text,
    fact_value_text text,
    fact_value_num numeric,
    fact_subject text,
    build_id_uuid uuid,
    verification_pass_status text,
    engine_version text,
    citation_ref text,
    citation_human text,
    source_calculation text,
    computed_at timestamp with time zone,
    tolerance_arcsec numeric,
    near_sign_boundary_flag boolean,
    near_nakshatra_boundary_flag boolean,
    vargottama_flag_at_point boolean,
    formula_provenance_text text,
    cross_ayanamsha_divergence_arcsec numeric,
    CONSTRAINT chart_divisionals_degree_in_sign_check CHECK (((degree_in_sign >= (0)::numeric) AND (degree_in_sign < (30)::numeric))),
    CONSTRAINT chart_divisionals_house_check CHECK (((house >= 1) AND (house <= 12))),
    CONSTRAINT chart_divisionals_sign_number_check CHECK (((sign_number >= 1) AND (sign_number <= 12))),
    CONSTRAINT chart_divisionals_verification_pass_status_check CHECK ((verification_pass_status = ANY (ARRAY['two_pass_verified'::text, 'classical_match'::text, 'divergent_flagged'::text, 'single'::text])))
);


--
-- Name: chart_fact_identity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chart_fact_identity (
    fact_id text NOT NULL,
    chart_id uuid NOT NULL,
    entity_kind text NOT NULL,
    graha_code text,
    graha_code_secondary text,
    house_num smallint,
    house_num_secondary smallint,
    varga_id text,
    sign_num smallint,
    parse_rule text NOT NULL,
    parsed_from text NOT NULL,
    build_id uuid,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chart_fact_identity_house_num_check CHECK (((house_num >= 1) AND (house_num <= 12))),
    CONSTRAINT chart_fact_identity_house_num_secondary_check CHECK (((house_num_secondary >= 1) AND (house_num_secondary <= 12))),
    CONSTRAINT chart_fact_identity_sign_num_check CHECK (((sign_num >= 1) AND (sign_num <= 12)))
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
-- Name: charts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.charts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_id text,
    name text NOT NULL,
    birth_date date NOT NULL,
    birth_time time without time zone NOT NULL,
    birth_place text NOT NULL,
    birth_lat numeric,
    birth_lng numeric,
    ayanamsa text DEFAULT 'lahiri'::text,
    house_system text DEFAULT 'sripathi'::text,
    created_at timestamp with time zone DEFAULT now(),
    native_id character varying(64) DEFAULT 'abhisek'::character varying NOT NULL,
    owner_id text,
    subject_name text,
    chart_id uuid DEFAULT gen_random_uuid(),
    role text DEFAULT 'native'::text NOT NULL,
    created_at_iso timestamp with time zone DEFAULT now() NOT NULL,
    preferred_name text,
    timezone_id text,
    chart_type text DEFAULT 'natal'::text NOT NULL,
    CONSTRAINT charts_chart_type_check CHECK ((chart_type = ANY (ARRAY['natal'::text, 'prashna'::text, 'synastry'::text, 'varshaphala'::text]))),
    CONSTRAINT charts_role_check CHECK ((role = ANY (ARRAY['native'::text, 'tertiary'::text, 'fixture'::text])))
);


--
-- Name: COLUMN charts.preferred_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.charts.preferred_name IS 'Display name for the native; defaults to first word of name.';


--
-- Name: COLUMN charts.timezone_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.charts.timezone_id IS 'IANA timezone identifier e.g. Asia/Kolkata. Sourced from explicit TZ select.';


--
-- Name: COLUMN charts.chart_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.charts.chart_type IS 'Chart category: natal (birth) | prashna (query) | synastry (relationship) | varshaphala (solar return). Default natal.';


--
-- Name: reference_planets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reference_planets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    planet_id text NOT NULL,
    canonical_name_en text NOT NULL,
    canonical_name_sa text NOT NULL,
    exaltation_sign smallint,
    exaltation_degree numeric(5,2),
    debilitation_sign smallint,
    mooltrikona_sign smallint,
    own_signs smallint[] DEFAULT '{}'::smallint[] NOT NULL,
    natural_benefic boolean NOT NULL,
    karak_domains text[] DEFAULT '{}'::text[] NOT NULL,
    dasha_years numeric(4,1),
    source_citation text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT reference_planets_debilitation_sign_check CHECK (((debilitation_sign >= 1) AND (debilitation_sign <= 12))),
    CONSTRAINT reference_planets_exaltation_sign_check CHECK (((exaltation_sign >= 1) AND (exaltation_sign <= 12))),
    CONSTRAINT reference_planets_mooltrikona_sign_check CHECK (((mooltrikona_sign >= 1) AND (mooltrikona_sign <= 12)))
);


--
-- Name: TABLE reference_planets; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.reference_planets IS 'BRAHMA L0 Brahmagyan: classical planetary attributes per BPHS. Exaltation/debilitation/mooltrikona/own-signs per Parashari tradition. Gate: BG-0-2. WS-2 depth build.';


--
-- Name: chart_divisionals chart_divisionals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_divisionals
    ADD CONSTRAINT chart_divisionals_pkey PRIMARY KEY (id);


--
-- Name: chart_fact_identity chart_fact_identity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_fact_identity
    ADD CONSTRAINT chart_fact_identity_pkey PRIMARY KEY (fact_id);


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
-- Name: charts charts_chart_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_chart_id_key UNIQUE (chart_id);


--
-- Name: charts charts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_pkey PRIMARY KEY (id);


--
-- Name: reference_planets reference_planets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reference_planets
    ADD CONSTRAINT reference_planets_pkey PRIMARY KEY (id);


--
-- Name: reference_planets reference_planets_planet_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reference_planets
    ADD CONSTRAINT reference_planets_planet_id_key UNIQUE (planet_id);


--
-- Name: cd_ga6_build_uuid_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cd_ga6_build_uuid_idx ON public.chart_divisionals USING btree (build_id_uuid);


--
-- Name: cd_ga6_cat_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cd_ga6_cat_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id, varga, fact_category);


--
-- Name: cd_ga6_key_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cd_ga6_key_idx ON public.chart_divisionals USING btree (chart_id, varga, fact_category, fact_key);


--
-- Name: cd_ga6_subject_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cd_ga6_subject_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id, fact_category, fact_subject);


--
-- Name: cd_ga6_verification_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cd_ga6_verification_idx ON public.chart_divisionals USING btree (verification_pass_status) WHERE (verification_pass_status IS NOT NULL);


--
-- Name: chart_divisionals_build_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_divisionals_build_idx ON public.chart_divisionals USING btree (build_id);


--
-- Name: chart_divisionals_chart_ayan_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_divisionals_chart_ayan_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id);


--
-- Name: chart_divisionals_chart_varga_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_divisionals_chart_varga_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id, varga);


--
-- Name: chart_divisionals_unique_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX chart_divisionals_unique_idx ON public.chart_divisionals USING btree (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT;


--
-- Name: chart_fact_identity_chart_entity_kind_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_fact_identity_chart_entity_kind_idx ON public.chart_fact_identity USING btree (chart_id, entity_kind);


--
-- Name: chart_fact_identity_chart_graha_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_fact_identity_chart_graha_idx ON public.chart_fact_identity USING btree (chart_id, graha_code) WHERE (graha_code IS NOT NULL);


--
-- Name: chart_fact_identity_chart_house_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_fact_identity_chart_house_idx ON public.chart_fact_identity USING btree (chart_id, house_num) WHERE (house_num IS NOT NULL);


--
-- Name: chart_fact_identity_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_fact_identity_chart_id_idx ON public.chart_fact_identity USING btree (chart_id);


--
-- Name: chart_fact_identity_chart_sign_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_fact_identity_chart_sign_idx ON public.chart_fact_identity USING btree (chart_id, sign_num) WHERE (sign_num IS NOT NULL);


--
-- Name: chart_fact_identity_chart_varga_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX chart_fact_identity_chart_varga_idx ON public.chart_fact_identity USING btree (chart_id, varga_id) WHERE (varga_id IS NOT NULL);


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
-- Name: idx_charts_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_charts_client_id ON public.charts USING btree (client_id);


--
-- Name: idx_charts_owner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_charts_owner_id ON public.charts USING btree (owner_id);


--
-- Name: idx_charts_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_charts_role ON public.charts USING btree (role);


--
-- Name: idx_ref_planets_planet_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ref_planets_planet_id ON public.reference_planets USING btree (planet_id);


--
-- Name: uq_charts_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_charts_chart_id ON public.charts USING btree (chart_id);


--
-- Name: ux_chart_facts_sade_sati_cycle_end_value; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_chart_facts_sade_sati_cycle_end_value ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_value_text) WHERE ((fact_category = 'sade_sati_cycle'::text) AND (fact_key = 'cycle_end_iso'::text));


--
-- Name: ux_chart_facts_sade_sati_cycle_start_value; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_chart_facts_sade_sati_cycle_start_value ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_value_text) WHERE ((fact_category = 'sade_sati_cycle'::text) AND (fact_key = 'cycle_start_iso'::text));


--
-- Name: chart_divisionals chart_divisionals_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_divisionals
    ADD CONSTRAINT chart_divisionals_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE;

--
-- PostgreSQL database dump complete
--


