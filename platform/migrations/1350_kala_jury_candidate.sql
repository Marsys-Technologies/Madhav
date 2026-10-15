-- Migration 1350: K4-2a candidate jury, additive; NEEDS-PROTECTED-WINDOW.
-- Published kala_convergence and kala_layer_head are never modified.
SET LOCAL lock_timeout = '5s';
CREATE TABLE IF NOT EXISTS public.kala_jury_candidate (
    chart_id uuid NOT NULL,
    generation text NOT NULL CHECK (generation LIKE 'candidate:%' AND length(generation)>10),
    event_class text NOT NULL CHECK (length(btrim(event_class))>0),
    assertion_id text NOT NULL CHECK (length(btrim(assertion_id))>0),
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL CHECK (window_start<window_end),
    subject jsonb NOT NULL CHECK (jsonb_typeof(subject)='object' AND subject<>'{}'),
    roots jsonb NOT NULL CHECK (jsonb_typeof(roots)='object' AND (roots<>'{}' OR (null_reason IS NOT NULL AND length(btrim(null_reason))>0))),
    provenance jsonb NOT NULL CHECK (jsonb_typeof(provenance)='object' AND provenance<>'{}'),
    coverage jsonb NOT NULL CHECK (jsonb_typeof(coverage)='object'),
    evidence_graph jsonb NOT NULL CHECK (jsonb_typeof(evidence_graph)='array'),
    witness_groups jsonb NOT NULL CHECK (jsonb_typeof(witness_groups)='array'),
    witness_signature jsonb NOT NULL CHECK (jsonb_typeof(witness_signature)='array'
        AND witness_signature <@ '["G-P","G-J","G-T","G-K"]'::jsonb),
    conditional_effect double precision CHECK (conditional_effect NOT IN ('NaN'::float8,'Infinity'::float8,'-Infinity'::float8)),
    conditional_null jsonb NOT NULL CHECK (jsonb_typeof(conditional_null)='object'
        AND conditional_null->>'estimand' IS NOT DISTINCT FROM 'jury_incremental_agreement'
        AND conditional_null->>'denominator' IS NOT NULL
        AND (conditional_null->>'denominator')::integer>=2
        AND conditional_null->>'verdict' IS NOT NULL
        AND conditional_null->>'verdict' IN ('pass','fail','insufficient_evidence','not_evaluable')),
    pipeline_null jsonb CHECK (pipeline_null IS NULL OR (jsonb_typeof(pipeline_null)='object'
        AND pipeline_null->>'estimand' IS NOT DISTINCT FROM 'whole_pipeline_selection'
        AND pipeline_null->>'denominator' IS NOT NULL
        AND (pipeline_null->>'denominator')::integer>=2
        AND pipeline_null->>'verdict' IS NOT NULL
        AND pipeline_null->>'verdict' IN ('pass','fail','insufficient_evidence','not_evaluable'))),
    pipeline_null_reason text,
    null_reason text,
    PRIMARY KEY (chart_id,generation,event_class,assertion_id),
    FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation) ON DELETE RESTRICT,
    CHECK ((pipeline_null IS NULL AND pipeline_null_reason IS NOT NULL AND length(btrim(pipeline_null_reason))>0)
        OR (pipeline_null IS NOT NULL AND pipeline_null_reason IS NULL)),
    CHECK (conditional_null->>'reason' IS DISTINCT FROM 'zero_null_variance'
        OR (conditional_null->>'verdict'='insufficient_evidence' AND null_reason IS NOT DISTINCT FROM 'zero_null_variance'))
);
CREATE TABLE IF NOT EXISTS public.kala_jury_candidate_segment (
    chart_id uuid NOT NULL,
    generation text NOT NULL,
    event_class text NOT NULL,
    assertion_id text NOT NULL,
    segment_start timestamptz NOT NULL,
    segment_end timestamptz NOT NULL CHECK (segment_start<segment_end),
    support_vector jsonb NOT NULL CHECK (jsonb_typeof(support_vector)='array'
        AND support_vector <@ '["G-P","G-J","G-T","G-K"]'::jsonb),
    support_roots jsonb NOT NULL CHECK (jsonb_typeof(support_roots)='object'),
    PRIMARY KEY (chart_id,generation,event_class,assertion_id,segment_start),
    FOREIGN KEY (chart_id,generation,event_class,assertion_id)
        REFERENCES public.kala_jury_candidate(chart_id,generation,event_class,assertion_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS public.kala_jury_candidate_contest (
    chart_id uuid NOT NULL,
    generation text NOT NULL,
    event_class text NOT NULL,
    assertion_id text NOT NULL,
    contest_id text NOT NULL CHECK (length(btrim(contest_id))>0),
    contest_start timestamptz NOT NULL,
    contest_end timestamptz NOT NULL CHECK (contest_start<contest_end),
    sides jsonb NOT NULL CHECK (jsonb_typeof(sides)='array' AND jsonb_array_length(sides)>=2),
    PRIMARY KEY (chart_id,generation,event_class,assertion_id,contest_id),
    FOREIGN KEY (chart_id,generation,event_class,assertion_id)
        REFERENCES public.kala_jury_candidate(chart_id,generation,event_class,assertion_id) ON DELETE RESTRICT
);
