-- Migration 1342: K2-2 / KYD-132: additive candidate-only, weight-free F1 physical targets and role edges.
-- NEEDS-PROTECTED-WINDOW. Legacy resonance rows and serving heads are untouched.
SET LOCAL lock_timeout = '5s';
CREATE TABLE IF NOT EXISTS public.kala_f1_target_object (
    chart_id uuid NOT NULL,
    ayanamsha_id text NOT NULL,
    generation text NOT NULL CHECK (generation LIKE 'candidate:%' AND length(generation) > 10),
    object_id text NOT NULL,
    object_type text NOT NULL CHECK (object_type IN ('graha','sign_interval')),
    longitude_deg double precision,
    sign_num integer,
    fact_ids jsonb NOT NULL CHECK (jsonb_typeof(fact_ids) = 'array' AND jsonb_array_length(fact_ids) > 0),
    PRIMARY KEY (chart_id, ayanamsha_id, generation, object_id),
    CHECK ((object_type = 'graha' AND longitude_deg IS NOT NULL
           AND longitude_deg >= 0 AND longitude_deg < 360 AND sign_num IS NULL)
        OR (object_type = 'sign_interval' AND longitude_deg IS NULL
           AND sign_num IS NOT NULL AND sign_num BETWEEN 1 AND 12))
);
CREATE TABLE IF NOT EXISTS public.kala_f1_relationship (
    chart_id uuid NOT NULL,
    ayanamsha_id text NOT NULL,
    generation text NOT NULL CHECK (generation LIKE 'candidate:%' AND length(generation) > 10),
    edge_id text NOT NULL,
    event_class_id text NOT NULL,
    object_id text,
    role text NOT NULL CHECK (role IN ('bhava','lord','karaka','mechanism_node',
        'sensitive_degree','arudha','bhava_arudha','yoga_constituent','dasha_lord_portfolio',
        'gulika_mandi_distance','yamakantaka_difference','promise_participant')),
    frame text NOT NULL CHECK (frame IN ('lagna','moon','zodiac')),
    mechanism_id text NOT NULL CHECK (length(mechanism_id) > 0),
    rule_id text NOT NULL CHECK (length(rule_id) > 0),
    provenance text NOT NULL,
    target_ref text NOT NULL,
    qualifier text,
    resolution_state text NOT NULL CHECK (resolution_state IN ('resolved','unavailable','unqualified')),
    PRIMARY KEY (chart_id, ayanamsha_id, generation, edge_id),
    FOREIGN KEY (chart_id, ayanamsha_id, generation, object_id)
        REFERENCES public.kala_f1_target_object (chart_id, ayanamsha_id, generation, object_id),
    CHECK ((resolution_state = 'resolved') = (object_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_kala_f1_relationship_class
    ON public.kala_f1_relationship (chart_id, ayanamsha_id, generation, event_class_id);
-- Narrow ACLs on these new objects only; no schema grant, role creation or L0/L1 write.
DO $acl$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        GRANT SELECT, INSERT, DELETE ON public.kala_f1_target_object, public.kala_f1_relationship TO data_plane_builder;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'verifier_principal') THEN
        GRANT SELECT ON public.kala_f1_target_object, public.kala_f1_relationship TO verifier_principal;
    END IF;
END $acl$;
