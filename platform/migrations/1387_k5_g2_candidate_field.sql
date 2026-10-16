-- Migration 1387: private G2 replacement-forecaster candidates (K5-3).
-- Created: 2026-10-16. PRE-BUILD ONLY, SR-A4-01; protected Kāla window.
-- Number audit: remote main + all 189 observed kalayantra/* refs; highest 1386.
-- Additive storage only. No registry, writer dispatch, serving head or legacy DML.
SET LOCAL lock_timeout = '5s';

CREATE TABLE IF NOT EXISTS public.kala_kshetra_g2_candidate (
  chart_id uuid NOT NULL,
  generation text NOT NULL CHECK (generation LIKE 'candidate:%'),
  build_id uuid NOT NULL,
  event_class text NOT NULL CHECK (event_class <> ''),
  model_digest text NOT NULL CHECK (model_digest ~ '^[0-9a-f]{64}$'),
  input_digest text NOT NULL CHECK (input_digest ~ '^[0-9a-f]{64}$'),
  payload jsonb NOT NULL CHECK (
    jsonb_typeof(payload) = 'object'
    AND payload->>'schema' IS NOT DISTINCT FROM 'ka_kshetra_g2/1'
    AND payload->'prebuild_only' IS NOT DISTINCT FROM 'true'::jsonb
    AND payload->>'input_digest' IS NOT DISTINCT FROM input_digest
    AND payload->'field'->>'model_digest' IS NOT DISTINCT FROM model_digest
    AND payload->'model'->>'event_class' IS NOT DISTINCT FROM event_class
  ),
  PRIMARY KEY (chart_id, generation, event_class),
  FOREIGN KEY (chart_id, generation)
    REFERENCES public.kala_layer_candidate(chart_id, generation) ON DELETE RESTRICT
);
COMMENT ON TABLE public.kala_kshetra_g2_candidate IS
  'K5-3 pre-build only. Separate model/schema; never served until D-VC, D-G2 and K9-4b activation.';

CREATE OR REPLACE FUNCTION public.guard_kshetra_g2_candidate()
RETURNS trigger LANGUAGE plpgsql AS $guard$
DECLARE
  identity_row public.kala_kshetra_g2_candidate;
  parent_state text;
  parent_build uuid;
  parent_conventions jsonb;
BEGIN
  IF TG_OP IN ('UPDATE', 'TRUNCATE') THEN
    RAISE EXCEPTION 'G2 candidates use owned delete/insert; UPDATE/TRUNCATE forbidden';
  END IF;
  IF TG_OP = 'DELETE' THEN identity_row := OLD; ELSE identity_row := NEW; END IF;
  SELECT state, build_id, conventions INTO parent_state, parent_build, parent_conventions
    FROM public.kala_layer_candidate
    WHERE chart_id=identity_row.chart_id AND generation=identity_row.generation FOR UPDATE;
  IF NOT FOUND OR parent_state <> 'building' OR parent_build <> identity_row.build_id
     OR parent_conventions->'kshetra_g2'->'prebuild_only' IS DISTINCT FROM 'true'::jsonb
     OR parent_conventions->'kshetra_g2'->'model_digests'->>identity_row.event_class
          IS DISTINCT FROM identity_row.model_digest
     OR parent_conventions->'kshetra_g2'->>'source_pin'
          IS DISTINCT FROM identity_row.payload->>'source_pin'
     OR EXISTS (SELECT 1 FROM public.kala_layer_head
                WHERE chart_id=identity_row.chart_id AND generation=identity_row.generation) THEN
    RAISE EXCEPTION 'G2 writes require an owned building prebuild_only candidate, never a published head';
  END IF;
  RETURN identity_row;
END $guard$;

DROP TRIGGER IF EXISTS guard_kshetra_g2_rows ON public.kala_kshetra_g2_candidate;
CREATE TRIGGER guard_kshetra_g2_rows BEFORE INSERT OR UPDATE OR DELETE
  ON public.kala_kshetra_g2_candidate FOR EACH ROW EXECUTE FUNCTION public.guard_kshetra_g2_candidate();
DROP TRIGGER IF EXISTS guard_kshetra_g2_truncate ON public.kala_kshetra_g2_candidate;
CREATE TRIGGER guard_kshetra_g2_truncate BEFORE TRUNCATE
  ON public.kala_kshetra_g2_candidate FOR EACH STATEMENT EXECUTE FUNCTION public.guard_kshetra_g2_candidate();

DO $grants$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_builder') THEN
    GRANT SELECT, INSERT, DELETE ON public.kala_kshetra_g2_candidate TO data_plane_builder;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='verifier_principal') THEN
    GRANT SELECT ON public.kala_kshetra_g2_candidate TO verifier_principal;
  END IF;
END $grants$;
