-- Migration 1387: K5-2b compact candidate field. PRE-BUILD, SR-A4-01. NEEDS-PROTECTED-WINDOW; no activation or source DML.
-- Allocated after origin/main + all 188 kalayantra/* remote heads (highest 1386).
-- (I) INTERPRETATION: a lossless coefficient projection beside G1 candidate rows.
-- No knot coalescing; risk-set eligibility is unknown until ALGO 3.20 G2 specifies it.
SET LOCAL lock_timeout = '5s';

CREATE TABLE IF NOT EXISTS public.kala_field_compact (
  chart_id uuid NOT NULL,
  generation text NOT NULL CHECK (generation ~ '^[A-Za-z0-9_.:-]{1,128}$'
    AND generation NOT IN ('legacy','current','retained','published')),
  build_id uuid NOT NULL,
  event_class text NOT NULL,
  segment_index integer NOT NULL CHECK (segment_index >= 0),
  t_start double precision NOT NULL CHECK (t_start > '-Infinity'::float8 AND t_start < 'Infinity'::float8),
  t_end double precision NOT NULL CHECK (t_end > t_start AND t_end < 'Infinity'::float8),
  alpha double precision NOT NULL CHECK (alpha > '-Infinity'::float8 AND alpha < 'Infinity'::float8),
  gamma double precision NOT NULL CHECK (gamma > '-Infinity'::float8 AND gamma < 'Infinity'::float8),
  integral_days double precision NOT NULL CHECK (integral_days >= 0 AND integral_days < 'Infinity'::float8),
  refinement_depth smallint NOT NULL CHECK (refinement_depth BETWEEN 0 AND 6),
  refinement_exhausted boolean NOT NULL,
  refinement_residual double precision CHECK (refinement_residual >= 0 AND refinement_residual < 'Infinity'::float8),
  field_snapshot_id text NOT NULL CHECK (length(field_snapshot_id)>0),
  weights_version text NOT NULL CHECK (length(weights_version)>0),
  x_schema_version text NOT NULL CHECK (length(x_schema_version)>0),
  risk_mask boolean,
  risk_mask_reason text NOT NULL CHECK (risk_mask IS NULL AND risk_mask_reason='risk_set_not_specified'),
  PRIMARY KEY (chart_id,generation,event_class,segment_index),
  FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation)
);
CREATE INDEX IF NOT EXISTS kala_field_compact_span
  ON public.kala_field_compact(chart_id,generation,event_class,t_start,t_end);

CREATE OR REPLACE FUNCTION public.kala_field_compact_guard() RETURNS trigger
LANGUAGE plpgsql AS $guard$
DECLARE r record; c record;
BEGIN
  IF TG_OP='TRUNCATE' THEN RAISE EXCEPTION 'compact generations cannot be truncated'; END IF;
  IF TG_OP='DELETE' THEN r:=OLD; ELSE r:=NEW; END IF;
  IF TG_OP='UPDATE' AND ROW(OLD.chart_id,OLD.generation,OLD.build_id,OLD.event_class,OLD.segment_index)
    IS DISTINCT FROM ROW(NEW.chart_id,NEW.generation,NEW.build_id,NEW.event_class,NEW.segment_index) THEN
    RAISE EXCEPTION 'compact field identity is immutable';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(
    replace(json_build_array(r.chart_id::text,r.generation)::text, ', ', ','),0));
  SELECT * INTO c FROM public.kala_layer_candidate
    WHERE chart_id=r.chart_id AND generation=r.generation FOR UPDATE;
  IF NOT FOUND OR c.state<>'building' OR c.build_id<>r.build_id OR EXISTS (
      SELECT 1 FROM public.kala_layer_head WHERE chart_id=r.chart_id AND generation=r.generation)
    OR NOT EXISTS (SELECT 1 FROM public.build_runs WHERE id=r.build_id AND chart_id=r.chart_id) THEN
    RAISE EXCEPTION 'compact field requires a building candidate bound to this chart/build';
  END IF;
  RETURN r;
END $guard$;
DROP TRIGGER IF EXISTS compact_field_mutability ON public.kala_field_compact;
CREATE TRIGGER compact_field_mutability BEFORE INSERT OR UPDATE OR DELETE ON public.kala_field_compact
  FOR EACH ROW EXECUTE FUNCTION public.kala_field_compact_guard();
DROP TRIGGER IF EXISTS compact_field_no_truncate ON public.kala_field_compact;
CREATE TRIGGER compact_field_no_truncate BEFORE TRUNCATE ON public.kala_field_compact
  FOR EACH STATEMENT EXECUTE FUNCTION public.kala_field_compact_guard();
REVOKE ALL ON public.kala_field_compact FROM PUBLIC;
COMMENT ON TABLE public.kala_field_compact IS
  'K5-2b lossless G1 coefficient projection, units hazard/day and integral expected event count. '
  'Unknown risk mask, candidate only. Dense rows retained until K9-4b publication and N-29 impact statement.';
