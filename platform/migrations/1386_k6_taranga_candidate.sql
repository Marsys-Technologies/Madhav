-- K6-4 PRE-BUILD under SR-A4-01; NEEDS-PROTECTED-WINDOW. No activation/grants.
-- Allocated above 1385 after inspecting origin/main + all 178 open kalayantra/*
-- refs in BOTH migration directories on 2026-10-16. Never alter legacy tables.
-- (I) INTERPRETATION: sibling tables preserve the legacy unique key and serving
-- path. K5-G1a 1385's candidate field/snapshot contract is an activation gate.
SET LOCAL lock_timeout = '5s';

CREATE TABLE IF NOT EXISTS public.kala_taranga_candidate (
  chart_id uuid NOT NULL,
  generation text NOT NULL CHECK (generation ~ '^[A-Za-z0-9_.:-]{1,128}$'
    AND generation NOT IN ('legacy','published','current','retained')),
  month date NOT NULL CHECK (extract(day FROM month)=1),
  scope_kind text NOT NULL CHECK (scope_kind IN ('event_class','domain')),
  scope_id text NOT NULL CHECK (length(btrim(scope_id))>0),
  integral double precision NOT NULL CHECK (integral>=0 AND integral<'Infinity'::float8),
  units text NOT NULL CHECK (units='expected_events'),
  risk_set jsonb,
  risk_set_null_reason text,
  judge_window_count integer CHECK (judge_window_count>=0),
  judge_count_null_reason text,
  overlap_flag boolean NOT NULL,
  source_refs jsonb NOT NULL CHECK (jsonb_typeof(source_refs)='object'),
  formula_version text NOT NULL,
  PRIMARY KEY (chart_id,generation,month,scope_kind,scope_id),
  FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation),
  CHECK ((risk_set IS NULL AND length(btrim(risk_set_null_reason))>0 AND risk_set_null_reason IS NOT NULL)
      OR (risk_set IS NOT NULL AND risk_set_null_reason IS NULL)),
  CHECK ((judge_window_count IS NULL AND length(btrim(judge_count_null_reason))>0 AND judge_count_null_reason IS NOT NULL)
      OR (judge_window_count IS NOT NULL AND judge_count_null_reason IS NULL))
);
CREATE TABLE IF NOT EXISTS public.kala_taranga_class_domain (
  chart_id uuid NOT NULL,
  generation text NOT NULL,
  event_class text NOT NULL CHECK (length(btrim(event_class))>0),
  domain text NOT NULL CHECK (length(btrim(domain))>0),
  source text NOT NULL CHECK (length(btrim(source))>0),
  PRIMARY KEY (chart_id,generation,event_class,domain,source),
  FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation)
);
COMMENT ON TABLE public.kala_taranga_class_domain IS
  'Declared sourced mapping only; no seed guesses. Overlap rule: once per class per domain; multi-domain membership flagged; expected_events units preserved, never an event probability.';
COMMENT ON COLUMN public.kala_taranga_candidate.risk_set IS
  'Honest null until the upstream forecaster provides a risk-set/mask contract; never infer eligibility from field presence.';
COMMENT ON COLUMN public.kala_taranga_candidate.units IS
  'Integral of per-day intensity, expected number of events (492 kala_field_windows.expected_count); no probability/calibration claim.';

CREATE OR REPLACE FUNCTION public.kala_taranga_candidate_guard() RETURNS trigger
LANGUAGE plpgsql AS $guard$
DECLARE r record; c record;
BEGIN
  IF TG_OP='TRUNCATE' THEN RAISE EXCEPTION 'taranga TRUNCATE refused: use candidate-scoped replacement'; END IF;
  IF TG_OP='DELETE' THEN r:=OLD; ELSE r:=NEW; END IF;
  IF TG_OP='UPDATE' AND ROW(OLD.chart_id,OLD.generation) IS DISTINCT FROM ROW(NEW.chart_id,NEW.generation) THEN
    RAISE EXCEPTION 'taranga candidate identity is immutable';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(
    replace(json_build_array(r.chart_id::text,r.generation)::text, ', ', ','),0));
  SELECT * INTO c FROM public.kala_layer_candidate
    WHERE chart_id=r.chart_id AND generation=r.generation FOR UPDATE;
  IF NOT FOUND OR c.state<>'building' OR r.generation IN ('legacy','published','current','retained')
    OR EXISTS (SELECT 1 FROM public.kala_layer_head WHERE chart_id=r.chart_id AND generation=r.generation)
    OR NOT EXISTS (SELECT 1 FROM public.build_runs WHERE id=c.build_id AND chart_id=r.chart_id) THEN
    RAISE EXCEPTION 'taranga requires a building candidate bound to chart/build; published output is immutable';
  END IF;
  RETURN r;
END $guard$;
DROP TRIGGER IF EXISTS taranga_candidate_mutability ON public.kala_taranga_candidate;
CREATE TRIGGER taranga_candidate_mutability BEFORE INSERT OR UPDATE OR DELETE ON public.kala_taranga_candidate
  FOR EACH ROW EXECUTE FUNCTION public.kala_taranga_candidate_guard();
DROP TRIGGER IF EXISTS taranga_mapping_mutability ON public.kala_taranga_class_domain;
CREATE TRIGGER taranga_mapping_mutability BEFORE INSERT OR UPDATE OR DELETE ON public.kala_taranga_class_domain
  FOR EACH ROW EXECUTE FUNCTION public.kala_taranga_candidate_guard();
DROP TRIGGER IF EXISTS taranga_no_truncate ON public.kala_taranga_candidate;
CREATE TRIGGER taranga_no_truncate BEFORE TRUNCATE ON public.kala_taranga_candidate
  FOR EACH STATEMENT EXECUTE FUNCTION public.kala_taranga_candidate_guard();
DROP TRIGGER IF EXISTS taranga_mapping_no_truncate ON public.kala_taranga_class_domain;
CREATE TRIGGER taranga_mapping_no_truncate BEFORE TRUNCATE ON public.kala_taranga_class_domain
  FOR EACH STATEMENT EXECUTE FUNCTION public.kala_taranga_candidate_guard();
REVOKE ALL ON public.kala_taranga_candidate,public.kala_taranga_class_domain FROM PUBLIC;

UPDATE public.asset_registry SET count_sql=$count$
SELECT count(*) FROM (
  SELECT chart_id FROM public.kala_taranga_candidate WHERE generation = (
    SELECT c.generation FROM public.kala_layer_candidate c JOIN public.build_runs b
      ON b.id=c.build_id AND b.chart_id=c.chart_id WHERE c.chart_id=$1
      ORDER BY b.created_at DESC,b.id DESC LIMIT 1)
  UNION ALL SELECT chart_id FROM public.kala_taranga WHERE NOT EXISTS (
    SELECT 1 FROM public.kala_layer_candidate c WHERE c.chart_id=$1)
) rows WHERE chart_id = $1
$count$,
-- Structural source-integrity detector, not a claim of numerical verification.
-- Transaction pins also work for a completed build; no global latest-build guess.
integrity_check_sql=$check$
WITH target AS (
  SELECT b.chart_id,c.generation FROM public.build_runs b
  LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id
  WHERE b.chart_id=NULLIF(current_setting('kala.integrity_chart_id',true),'')::uuid
    AND b.id=NULLIF(current_setting('kala.integrity_build_id',true),'')::uuid
)
SELECT EXISTS (SELECT 1 FROM target) AND NOT EXISTS (
  SELECT 1 FROM public.kala_taranga_candidate r JOIN target t USING(chart_id,generation)
  WHERE jsonb_typeof(r.source_refs->'field_snapshot_ids') IS DISTINCT FROM 'array'
     OR r.source_refs->'field_snapshot_ids' = '[]'::jsonb
     OR jsonb_typeof(r.source_refs->'field_segment_ids') IS DISTINCT FROM 'array'
     OR r.source_refs->'field_segment_ids' = '[]'::jsonb
     OR (r.scope_kind='domain' AND (jsonb_typeof(r.source_refs->'class_domain_sources') IS DISTINCT FROM 'array'
       OR r.source_refs->'class_domain_sources'='[]'::jsonb))
)
$check$ WHERE asset_id='ka_taranga';
