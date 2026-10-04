CREATE SEQUENCE public.ga_condition_composite_id_seq AS integer;
CREATE SEQUENCE public.ga_yoga_firings_id_seq AS integer;
CREATE SEQUENCE public.chart_vichara_id_seq AS bigint;
CREATE SEQUENCE public.ga_transit_anchors_id_seq AS integer;
CREATE SEQUENCE public.ga_medical_id_seq AS integer;
CREATE SEQUENCE public.ga_vastu_planet_direction_map_id_seq AS integer;
CREATE SEQUENCE public.ga_prashna_lagna_id_seq AS integer;
CREATE SEQUENCE public.ga_prashna_judgment_id_seq AS integer;
CREATE TABLE public."chart_facts" (
  "fact_id" text NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "build_id" uuid NOT NULL,
  "fact_category" text NOT NULL,
  "fact_subject" text NOT NULL,
  "fact_key" text NOT NULL,
  "fact_value_text" text,
  "fact_value_num" numeric,
  "fact_value_jsonb" jsonb,
  "unit" text,
  "citation_ref" text NOT NULL,
  "citation_human" text NOT NULL,
  "source_calculation" text NOT NULL,
  "verification_pass_status" text NOT NULL,
  "engine_version" text NOT NULL,
  "salience_formula_ver" text,
  "computed_at" timestamp with time zone NOT NULL,
  "tolerance_arcsec" double precision,
  "near_sign_boundary_flag" boolean DEFAULT false,
  "near_nakshatra_boundary_flag" boolean DEFAULT false,
  "vargottama_flag_at_point" boolean DEFAULT false,
  "formula_provenance_text" text,
  "cross_ayanamsha_divergence_arcsec" double precision DEFAULT 0.0,
  "formula_id" text,
  CONSTRAINT "chart_facts_pkey" PRIMARY KEY (fact_id),
  CONSTRAINT "chart_facts_verification_pass_status_check" CHECK ((verification_pass_status = ANY (ARRAY['two_pass_verified'::text, 'classical_match'::text, 'divergent_flagged'::text, 'single'::text, 'single_pass'::text, 'documented_approximation'::text, 'computed_extension'::text, 'floored'::text, 'not_defined_for_nodes'::text, 'scope_cap_sentinel'::text, 'skipped_malformed_source'::text, 'external_computation_required'::text, 'pending_w3_verification'::text])))
);
CREATE UNIQUE INDEX ux_chart_facts_sade_sati_cycle_start_value ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_value_text) WHERE ((fact_category = 'sade_sati_cycle'::text) AND (fact_key = 'cycle_start_iso'::text));
CREATE UNIQUE INDEX ux_chart_facts_sade_sati_cycle_end_value ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_value_text) WHERE ((fact_category = 'sade_sati_cycle'::text) AND (fact_key = 'cycle_end_iso'::text));
CREATE INDEX chart_facts_chart_id_idx ON public.chart_facts USING btree (chart_id);
CREATE INDEX chart_facts_category_idx ON public.chart_facts USING btree (chart_id, fact_category);
CREATE INDEX chart_facts_subject_idx ON public.chart_facts USING btree (chart_id, fact_subject);
CREATE INDEX chart_facts_ayanamsha_idx ON public.chart_facts USING btree (chart_id, ayanamsha_id);
CREATE INDEX chart_facts_build_idx ON public.chart_facts USING btree (build_id);
CREATE INDEX chart_facts_chart_aya_cat_idx ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_category);
CREATE INDEX chart_facts_chart_aya_sub_idx ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_subject);
CREATE INDEX chart_facts_chart_cat_sub_key_idx ON public.chart_facts USING btree (chart_id, fact_category, fact_subject, fact_key);
CREATE INDEX chart_facts_verification_idx ON public.chart_facts USING btree (verification_pass_status) WHERE (verification_pass_status <> 'single'::text);
CREATE INDEX chart_facts_jsonb_gin ON public.chart_facts USING gin (fact_value_jsonb);
CREATE UNIQUE INDEX chart_facts_unique_null_formula ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id) WHERE (formula_id IS NULL);
CREATE UNIQUE INDEX chart_facts_unique_with_formula ON public.chart_facts USING btree (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id, formula_id) WHERE (formula_id IS NOT NULL);
CREATE INDEX chart_facts_chart_computed_idx ON public.chart_facts USING btree (chart_id, computed_at DESC);
CREATE TABLE public."chart_dashas" (
  "dasha_row_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "build_id" uuid NOT NULL,
  "system_id" text NOT NULL,
  "level_n" integer NOT NULL,
  "parent_row_id" uuid,
  "lord_graha" text NOT NULL,
  "lord_sign" text,
  "start_date" date NOT NULL,
  "end_date" date NOT NULL,
  "start_iso" timestamp with time zone NOT NULL,
  "end_iso" timestamp with time zone NOT NULL,
  "duration_days" numeric NOT NULL,
  "sandhi_flag" boolean DEFAULT false NOT NULL,
  "karaka_role_at_period" text,
  "verification_pass_status" text NOT NULL,
  "verification_method" text NOT NULL,
  "citation_ref" text NOT NULL,
  "citation_human" text NOT NULL,
  "computed_at" timestamp with time zone DEFAULT now() NOT NULL,
  "engine_version" text NOT NULL,
  "kp_sublevel" text,
  "kp_sub_lord" text,
  "kp_sub_sub_lord" text,
  "lord_natal_house_d1" integer,
  "lord_natal_sign" text,
  "lord_natal_nakshatra" text,
  "lord_natal_dignity_d1" text,
  "lord_natal_shadbala_total" numeric,
  "sandhi_with_next_dasha_lord" text,
  "next_dasha_start_iso" timestamp with time zone,
  "concurrent_system_lords_jsonb" jsonb,
  "convergence_count_at_start" integer,
  "applies_to_this_chart_flag" boolean DEFAULT true NOT NULL,
  "period_deity_or_marker" text,
  "lord_to_parent_relationship" text,
  "varsha_year_lord" text,
  "anchored_solar_return_iso" timestamp with time zone,
  "karakas_active_during_period" text[],
  "is_truncated_at_window_start" boolean DEFAULT false NOT NULL,
  "is_truncated_at_window_end" boolean DEFAULT false NOT NULL,
  CONSTRAINT "chart_dashas_pkey" PRIMARY KEY (dasha_row_id),
  CONSTRAINT "cd_level_n_max4" CHECK (((level_n >= 1) AND (level_n <= 4))),
  CONSTRAINT "chart_dashas_verification_pass_status_check" CHECK ((verification_pass_status = ANY (ARRAY['two_pass_verified'::text, 'classical_match'::text, 'divergent_flagged'::text, 'single'::text, 'scope_cap_sentinel'::text])))
);
CREATE INDEX cd_temporal_lookup_idx ON public.chart_dashas USING btree (chart_id, ayanamsha_id, system_id, level_n, start_date, end_date);
CREATE INDEX cd_lord_lookup_idx ON public.chart_dashas USING btree (chart_id, ayanamsha_id, lord_graha, system_id);
CREATE INDEX cd_parent_idx ON public.chart_dashas USING btree (parent_row_id);
CREATE INDEX cd_kp_sublevel_idx ON public.chart_dashas USING btree (chart_id, ayanamsha_id, system_id, kp_sublevel) WHERE (kp_sublevel IS NOT NULL);
CREATE INDEX cd_convergence_idx ON public.chart_dashas USING btree (chart_id, ayanamsha_id, start_date) WHERE (convergence_count_at_start IS NOT NULL);
CREATE UNIQUE INDEX chart_dashas_natural_key_kp_idx ON public.chart_dashas USING btree (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id, COALESCE(kp_sublevel, ''::text));
CREATE INDEX chart_dashas_condition_lookup_idx ON public.chart_dashas USING btree (chart_id, lord_graha, start_iso) WHERE (level_n = 1);
CREATE INDEX cd_chart_lord_natal_idx ON public.chart_dashas USING btree (chart_id, lord_graha);
CREATE INDEX cd_chart_accretion_key_idx ON public.chart_dashas USING btree (chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_date);
CREATE TABLE public."chart_divisionals" (
  "id" uuid DEFAULT uuid_generate_v4() NOT NULL,
  "chart_id" uuid NOT NULL,
  "graha" text,
  "ayanamsha_id" text NOT NULL,
  "varga" text NOT NULL,
  "sign" text,
  "sign_number" smallint,
  "degree_in_sign" numeric(8,4),
  "house" smallint,
  "vargottama" boolean,
  "source_citation" text DEFAULT 'PyJHora DE441 / MARSYS-engine v1'::text NOT NULL,
  "build_id" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "fact_category" text,
  "fact_key" text,
  "fact_value_text" text,
  "fact_value_num" numeric,
  "fact_subject" text,
  "build_id_uuid" uuid,
  "verification_pass_status" text,
  "engine_version" text,
  "citation_ref" text,
  "citation_human" text,
  "source_calculation" text,
  "computed_at" timestamp with time zone,
  "tolerance_arcsec" numeric,
  "near_sign_boundary_flag" boolean,
  "near_nakshatra_boundary_flag" boolean,
  "vargottama_flag_at_point" boolean,
  "formula_provenance_text" text,
  "cross_ayanamsha_divergence_arcsec" numeric,
  CONSTRAINT "chart_divisionals_pkey" PRIMARY KEY (id),
  CONSTRAINT "chart_divisionals_degree_in_sign_check" CHECK (((degree_in_sign >= (0)::numeric) AND (degree_in_sign < (30)::numeric))),
  CONSTRAINT "chart_divisionals_house_check" CHECK (((house >= 1) AND (house <= 12))),
  CONSTRAINT "chart_divisionals_sign_number_check" CHECK (((sign_number >= 1) AND (sign_number <= 12))),
  CONSTRAINT "chart_divisionals_verification_pass_status_check" CHECK ((verification_pass_status = ANY (ARRAY['two_pass_verified'::text, 'classical_match'::text, 'divergent_flagged'::text, 'single'::text])))
);
CREATE INDEX chart_divisionals_chart_ayan_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id);
CREATE INDEX chart_divisionals_chart_varga_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id, varga);
CREATE INDEX chart_divisionals_build_idx ON public.chart_divisionals USING btree (build_id);
CREATE UNIQUE INDEX chart_divisionals_unique_idx ON public.chart_divisionals USING btree (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT;
CREATE INDEX cd_ga6_cat_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id, varga, fact_category);
CREATE INDEX cd_ga6_subject_idx ON public.chart_divisionals USING btree (chart_id, ayanamsha_id, fact_category, fact_subject);
CREATE INDEX cd_ga6_key_idx ON public.chart_divisionals USING btree (chart_id, varga, fact_category, fact_key);
CREATE INDEX cd_ga6_build_uuid_idx ON public.chart_divisionals USING btree (build_id_uuid);
CREATE INDEX cd_ga6_verification_idx ON public.chart_divisionals USING btree (verification_pass_status) WHERE (verification_pass_status IS NOT NULL);
CREATE TABLE public."ga_condition_composite" (
  "id" integer DEFAULT nextval('ga_condition_composite_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "build_id" uuid,
  "ayanamsha_id" text NOT NULL,
  "graha" text NOT NULL,
  "dignity_d1" text,
  "dignity_score_d1" numeric,
  "varga_dignity_spread" jsonb,
  "varga_dignity_composite" numeric,
  "avastha_baladi" text,
  "avastha_jagradadi" text,
  "avastha_deeptaadi" text,
  "avastha_lajjitaadi" text,
  "avastha_sayanadi" text,
  "motion_state" text,
  "speed_degrees_per_day" numeric,
  "is_retrograde" boolean,
  "combustion_arc_from_sun" numeric,
  "is_combust" boolean,
  "is_deeply_combust" boolean,
  "naisargika_relation" text,
  "tatkalika_relation" text,
  "panchadha_relation" text,
  "graha_yuddha_with" text,
  "graha_yuddha_result" text,
  "condition_score" numeric,
  "condition_formula_version" text DEFAULT 'condition_formula_v1'::text NOT NULL,
  "condition_score_breakdown" jsonb,
  "peak_dasha_periods" jsonb,
  "weak_dasha_periods" jsonb,
  "computed_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ga_condition_composite_unique" UNIQUE (chart_id, ayanamsha_id, graha),
  CONSTRAINT "ga_condition_composite_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_ga_condition_chart_ay ON public.ga_condition_composite USING btree (chart_id, ayanamsha_id);
CREATE INDEX idx_ga_condition_chart_graha ON public.ga_condition_composite USING btree (chart_id, graha);
CREATE TABLE public."ga_yoga_firings" (
  "id" integer DEFAULT nextval('ga_yoga_firings_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "build_id" uuid,
  "ayanamsha_id" text NOT NULL,
  "yoga_canonical_id" text NOT NULL,
  "fired" boolean DEFAULT true NOT NULL,
  "constituent_fact_ids" jsonb,
  "constituent_planets" jsonb,
  "constituent_houses" jsonb,
  "strength" numeric,
  "strength_formula_version" text,
  "partial_formation_pct" numeric,
  "is_partial" boolean DEFAULT false,
  "bhanga_active" boolean DEFAULT false,
  "bhanga_rule_fired" text,
  "family_ids" jsonb,
  "activation_dasha_periods" jsonb,
  "computed_at" timestamp with time zone DEFAULT now(),
  "derivation" text,
  "strength_label" text,
  "citation_ref" text,
  "citation_human" text,
  "bhanga_na_reason" text,
  "grounds_jsonb" jsonb,
  CONSTRAINT "ga_yoga_firings_chart_id_ayanamsha_id_yoga_canonical_id_key" UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id),
  CONSTRAINT "ga_yoga_firings_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_ga_yoga_firings_chart_ayanamsha ON public.ga_yoga_firings USING btree (chart_id, ayanamsha_id);
CREATE INDEX idx_ga_yoga_firings_yoga ON public.ga_yoga_firings USING btree (yoga_canonical_id);
CREATE TABLE public."chart_vichara" (
  "id" bigint DEFAULT nextval('chart_vichara_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "build_id" uuid,
  "vichara_family" text NOT NULL,
  "subject" text NOT NULL,
  "actor" text,
  "target" text,
  "domain" text,
  "varga_id" text,
  "varga" text,
  "value_num" numeric,
  "value_text" text,
  "value_jsonb" jsonb,
  "ratification_factor" numeric,
  "constituent_fact_ids" text[] DEFAULT ARRAY[]::text[],
  "constituent_facts_array" text[] DEFAULT ARRAY[]::text[],
  "formula_version" text,
  "source_citation" text,
  "computed_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "chart_vichara_pkey" PRIMARY KEY (id),
  CONSTRAINT "chart_vichara_ratification_factor_range" CHECK (((ratification_factor IS NULL) OR ((ratification_factor >= 0.6) AND (ratification_factor <= 1.4)))),
  CONSTRAINT "chart_vichara_vichara_family_check" CHECK ((vichara_family = ANY (ARRAY['valence_pass'::text, 'varga_ratification'::text, 'varga_ratification_divergence'::text, 'varga_consistency'::text, 'leverage_index'::text])))
);
CREATE INDEX idx_chart_vichara_chart_ayanamsha ON public.chart_vichara USING btree (chart_id, ayanamsha_id);
CREATE INDEX idx_chart_vichara_family_domain ON public.chart_vichara USING btree (chart_id, vichara_family, domain);
CREATE INDEX idx_chart_vichara_subject ON public.chart_vichara USING btree (chart_id, subject);
CREATE TABLE public."ga_transit_anchors" (
  "id" integer DEFAULT nextval('ga_transit_anchors_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "build_id" text NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "graha" text NOT NULL,
  "natal_sign" text NOT NULL,
  "natal_house_from_moon" integer NOT NULL,
  "natal_degree_absolute" double precision NOT NULL,
  "computed_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ga_transit_anchors_natural_key" UNIQUE (chart_id, ayanamsha_id, graha),
  CONSTRAINT "ga_transit_anchors_pkey" PRIMARY KEY (id),
  CONSTRAINT "ga_transit_anchors_natal_house_from_moon_check" CHECK (((natal_house_from_moon >= 1) AND (natal_house_from_moon <= 12)))
);
CREATE INDEX idx_ga_transit_anchors_chart ON public.ga_transit_anchors USING btree (chart_id, ayanamsha_id);
CREATE INDEX idx_ga_transit_anchors_graha ON public.ga_transit_anchors USING btree (chart_id, graha);
CREATE TABLE public."l1_tajik_varsha_year_lords" (
  "varsha_id" uuid NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "build_id" uuid NOT NULL,
  "varsha_year" integer NOT NULL,
  "varsha_start_iso" timestamp with time zone NOT NULL,
  "varsha_end_iso" timestamp with time zone NOT NULL,
  "year_lord_method" text NOT NULL,
  "year_lord" text NOT NULL,
  "candidate_lord_jsonb" jsonb,
  "muntha_position_jsonb" jsonb,
  "applicable_tajik_yogas_array" text[],
  "classical_source_citation" text NOT NULL,
  "ephemeris_audit_jsonb" jsonb,
  "verification_pass_status" text NOT NULL,
  "citation_ref" text NOT NULL,
  "citation_human" text NOT NULL,
  "computed_at" timestamp with time zone NOT NULL,
  CONSTRAINT "l1_tajik_varsha_year_lords_chart_id_ayanamsha_id_build_id_v_key" UNIQUE (chart_id, ayanamsha_id, build_id, varsha_year),
  CONSTRAINT "l1_tajik_varsha_year_lords_pkey" PRIMARY KEY (varsha_id)
);
CREATE INDEX tajik_varsha_chart_idx ON public.l1_tajik_varsha_year_lords USING btree (chart_id, ayanamsha_id);
CREATE INDEX tajik_varsha_year_idx ON public.l1_tajik_varsha_year_lords USING btree (chart_id, ayanamsha_id, varsha_year);
CREATE TABLE public."ga_medical" (
  "id" integer DEFAULT nextval('ga_medical_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "graha" text NOT NULL,
  "natal_sign" text,
  "natal_nakshatra" text,
  "indication_strength" text,
  "dosha_aggravated" text[],
  "organ_watch" text[],
  "body_part_watch" text[],
  "nakshatra_body_part" text,
  "indication_tier" text DEFAULT 'jyotish_indication'::text NOT NULL,
  "not_diagnosis" boolean DEFAULT true NOT NULL,
  "classical_citation" text NOT NULL,
  "computed_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "ga_medical_chart_id_ayanamsha_id_graha_key" UNIQUE (chart_id, ayanamsha_id, graha),
  CONSTRAINT "ga_medical_pkey" PRIMARY KEY (id)
);
CREATE INDEX ga_medical_chart_aya_idx ON public.ga_medical USING btree (chart_id, ayanamsha_id);
CREATE INDEX ga_medical_graha_idx ON public.ga_medical USING btree (graha);
CREATE TABLE public."ga_vastu_planet_direction_map" (
  "id" integer DEFAULT nextval('ga_vastu_planet_direction_map_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "graha" text NOT NULL,
  "direction" text NOT NULL,
  "condition_score" numeric,
  "dignity_d1" text,
  "direction_impact" text NOT NULL,
  "indication_tier" text DEFAULT 'traditional_vastu'::text NOT NULL,
  "classical_citation" text NOT NULL,
  "computed_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "ga_vastu_planet_direction_map_chart_id_ayanamsha_id_graha_key" UNIQUE (chart_id, ayanamsha_id, graha),
  CONSTRAINT "ga_vastu_planet_direction_map_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_ga_vastu_map_chart ON public.ga_vastu_planet_direction_map USING btree (chart_id, ayanamsha_id);
CREATE TABLE public."ga_prashna_lagna" (
  "id" integer DEFAULT nextval('ga_prashna_lagna_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "lagna_method" text NOT NULL,
  "lagna_rashi" text NOT NULL,
  "lagna_degree" double precision,
  "kp_sub_lord" text,
  "is_primary" boolean DEFAULT false NOT NULL,
  "classical_citation" text NOT NULL,
  CONSTRAINT "ga_prashna_lagna_chart_id_ayanamsha_id_lagna_method_key" UNIQUE (chart_id, ayanamsha_id, lagna_method),
  CONSTRAINT "ga_prashna_lagna_pkey" PRIMARY KEY (id)
);
CREATE TABLE public."ga_prashna_judgment" (
  "id" integer DEFAULT nextval('ga_prashna_judgment_id_seq'::regclass) NOT NULL,
  "chart_id" uuid NOT NULL,
  "ayanamsha_id" text NOT NULL,
  "question_class" text NOT NULL,
  "querent_significator" text NOT NULL,
  "quesited_significator" text NOT NULL,
  "querent_longitude" double precision,
  "quesited_longitude" double precision,
  "longitudinal_gap" double precision,
  "is_applying" boolean,
  "tajik_yoga" text,
  "judgment_text" text NOT NULL,
  "fructification_value" double precision,
  "fructification_unit" text,
  "fructification_rule_id" text,
  "lagna_rashi" text,
  "classical_citation" text NOT NULL,
  CONSTRAINT "ga_prashna_judgment_chart_id_ayanamsha_id_key" UNIQUE (chart_id, ayanamsha_id),
  CONSTRAINT "ga_prashna_judgment_pkey" PRIMARY KEY (id)
);
CREATE TABLE public."fact_category_ownership" (
  "fact_category" text NOT NULL,
  "owning_asset_id" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "fact_category_ownership_pkey" PRIMARY KEY (fact_category, owning_asset_id)
);
CREATE INDEX idx_fact_category_ownership_asset ON public.fact_category_ownership USING btree (owning_asset_id);
CREATE TABLE public."brahma_yoga_catalog" (
  "canonical_id" text NOT NULL,
  "name_sa" text NOT NULL,
  "name_en" text NOT NULL,
  "category" text NOT NULL,
  "formation_rule_jsonb" jsonb NOT NULL,
  "formation_text" text NOT NULL,
  "significations_jsonb" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "significations_text" text NOT NULL,
  "cancellation_conditions" jsonb,
  "classical_citations" jsonb,
  "source_chunk_ids" bigint[] DEFAULT ARRAY[]::bigint[],
  "school" text NOT NULL,
  "rare" boolean DEFAULT false NOT NULL,
  "computed_strength_formula" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "bhanga_rules_jsonb" jsonb,
  "partial_formation_threshold" numeric,
  "strength_formula_ref" text,
  "result_class" text,
  CONSTRAINT "brahma_yoga_catalog_pkey" PRIMARY KEY (canonical_id),
  CONSTRAINT "brahma_yoga_catalog_category_check" CHECK ((category = ANY (ARRAY['raja'::text, 'dhana'::text, 'pancha_mahapurusha'::text, 'aristha'::text, 'sannyasa'::text, 'other'::text]))),
  CONSTRAINT "brahma_yoga_catalog_result_class_check" CHECK ((result_class = ANY (ARRAY['benefic'::text, 'malefic'::text, 'mixed'::text, 'neutral'::text])))
);
CREATE INDEX idx_yoga_category ON public.brahma_yoga_catalog USING btree (category);
CREATE INDEX idx_yoga_school ON public.brahma_yoga_catalog USING btree (school);
CREATE INDEX idx_yoga_formation ON public.brahma_yoga_catalog USING gin (formation_rule_jsonb);
CREATE TABLE public."brahma_dosha_catalog" (
  "canonical_id" text NOT NULL,
  "name_sa" text NOT NULL,
  "name_en" text NOT NULL,
  "category" text NOT NULL,
  "formation_rule_jsonb" jsonb NOT NULL,
  "formation_text" text NOT NULL,
  "effects_text" text NOT NULL,
  "severity_grades" jsonb,
  "cancellation_conditions" jsonb,
  "classical_citations" jsonb,
  "source_chunk_ids" bigint[] DEFAULT ARRAY[]::bigint[],
  "associated_remedies" uuid[] DEFAULT ARRAY[]::uuid[],
  "school" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "brahma_dosha_catalog_pkey" PRIMARY KEY (canonical_id),
  CONSTRAINT "brahma_dosha_catalog_category_check" CHECK ((category = ANY (ARRAY['graha_placement'::text, 'rashi_combination'::text, 'nakshatra_compatibility'::text, 'tithi'::text, 'other'::text])))
);
CREATE INDEX idx_dosha_category ON public.brahma_dosha_catalog USING btree (category);
CREATE INDEX idx_dosha_school ON public.brahma_dosha_catalog USING btree (school);
ALTER SEQUENCE public.ga_condition_composite_id_seq OWNED BY public.ga_condition_composite.id;
ALTER SEQUENCE public.ga_yoga_firings_id_seq OWNED BY public.ga_yoga_firings.id;
ALTER SEQUENCE public.chart_vichara_id_seq OWNED BY public.chart_vichara.id;
ALTER SEQUENCE public.ga_transit_anchors_id_seq OWNED BY public.ga_transit_anchors.id;
ALTER SEQUENCE public.ga_medical_id_seq OWNED BY public.ga_medical.id;
ALTER SEQUENCE public.ga_vastu_planet_direction_map_id_seq OWNED BY public.ga_vastu_planet_direction_map.id;
ALTER SEQUENCE public.ga_prashna_lagna_id_seq OWNED BY public.ga_prashna_lagna.id;
ALTER SEQUENCE public.ga_prashna_judgment_id_seq OWNED BY public.ga_prashna_judgment.id;
