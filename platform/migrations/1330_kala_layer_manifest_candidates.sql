-- Migration 1330: candidate-scoped Kāla layer manifest.
-- Candidates remain private until a separately-run verifier records acceptance.

CREATE TABLE IF NOT EXISTS public.kala_layer_candidate (
  chart_id uuid NOT NULL,
  generation text NOT NULL,
  build_id uuid NOT NULL,
  expected_head_generation text,
  state text NOT NULL DEFAULT 'building'
    CHECK (state IN ('building', 'complete', 'verified', 'published', 'rejected')),
  model_digest text NOT NULL,
  rule_registry_version text NOT NULL,
  conventions jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, generation),
  UNIQUE (build_id)
);

CREATE TABLE IF NOT EXISTS public.kala_layer_candidate_grain (
  chart_id uuid NOT NULL,
  generation text NOT NULL,
  grain_key text NOT NULL,
  result_state text NOT NULL CHECK (result_state IN ('rows', 'zero_rows', 'failed')),
  input_vector text NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, generation, grain_key),
  FOREIGN KEY (chart_id, generation)
    REFERENCES public.kala_layer_candidate (chart_id, generation) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.kala_layer_verification (
  chart_id uuid NOT NULL,
  generation text NOT NULL,
  verifier_principal text NOT NULL,
  result text NOT NULL CHECK (result IN ('accepted', 'rejected')),
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  verified_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, generation),
  FOREIGN KEY (chart_id, generation)
    REFERENCES public.kala_layer_candidate (chart_id, generation) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.kala_layer_head (
  chart_id uuid PRIMARY KEY,
  generation text NOT NULL,
  published_at timestamptz NOT NULL DEFAULT now()
);

-- A separately dispatched verifier may inspect only recorded grain inputs and
-- append its own receipt. It cannot open, attest, publish, or roll back a
-- candidate generation.
-- (2026-10-08 hotfix) no schema-level grant: the routine migration role may not grant on schema public and every role already has USAGE on it; this line made the production run fail (deploy 37749113939) before 1330 was ever applied.
GRANT SELECT ON TABLE public.kala_layer_candidate_grain TO verifier_principal;
GRANT INSERT ON TABLE public.kala_layer_verification TO verifier_principal;
