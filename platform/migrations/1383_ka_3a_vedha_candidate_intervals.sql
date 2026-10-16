-- KA-3a pre-build, SR-A4-01. NEEDS-PROTECTED-WINDOW; migrate.ts owns transaction.
-- Additive only: legacy dates, IDs, natural key, registry and readers unchanged.
-- Allocated above origin/open-branch maximum 1381; no activation or role grants.
SET LOCAL lock_timeout = '5s';
ALTER TABLE public.kala_vedha_gochara
  ADD COLUMN IF NOT EXISTS method_qualification text,
  ADD COLUMN IF NOT EXISTS coverage jsonb,
  ADD COLUMN IF NOT EXISTS upstream_fingerprint jsonb;

CREATE TABLE IF NOT EXISTS public.kala_vedha_gochara_candidate (
  chart_id uuid NOT NULL,
  generation text NOT NULL CHECK (generation ~ '^[A-Za-z0-9_.:-]+$'
    AND generation NOT IN ('legacy','current','published','retained')),
  ayanamsha_id text NOT NULL CHECK (ayanamsha_id <> ''),
  vedha_kind text NOT NULL CHECK (vedha_kind IN ('house_vedha','sarvatobhadra','latta')),
  janma_reference_fact_id text NOT NULL CHECK (janma_reference_fact_id<>''),
  formula_version text NOT NULL CHECK (formula_version <> ''),
  natal_build_id uuid NOT NULL,
  coverage jsonb NOT NULL CHECK (COALESCE(jsonb_typeof(coverage)='object'
    AND coverage->>'search_state' IN ('searched','partial','unsearched')
    AND coverage ?& ARRAY['requested','source_interval','covered','complete','backend','convention_id','gaps'],false)),
  upstream_fingerprint jsonb NOT NULL CHECK (COALESCE(upstream_fingerprint->>'schema'='ka_vedha_inputs/1'
    AND upstream_fingerprint->>'digest' ~ '^[0-9a-f]{64}$',false)),
  payload jsonb NOT NULL CHECK (COALESCE(payload->>'schema'='ka_vedha_payload/1',false)),
  method_qualification text,
  null_reason text,
  PRIMARY KEY (chart_id,generation,ayanamsha_id,vedha_kind),
  FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation),
  CHECK (COALESCE((method_qualification IN ('qualified','method_contested','uncited_extension') AND null_reason IS NULL)
    OR (method_qualification IS NULL AND null_reason IS NOT NULL AND null_reason <> ''),false))
);

CREATE TABLE IF NOT EXISTS public.kala_vedha_gochara_interval (
  chart_id uuid NOT NULL,
  generation text NOT NULL,
  ayanamsha_id text NOT NULL,
  vedha_kind text NOT NULL CHECK (vedha_kind IN ('house_vedha','latta')),
  graha text NOT NULL CHECK (graha IN ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')),
  state text NOT NULL CHECK (state IN ('active','inactive','unqualified')),
  classical_citation text NOT NULL CHECK (classical_citation <> ''),
  source_qualification text NOT NULL CHECK (source_qualification IN ('verse_cited','algorithmic_approximation','unsourced')),
  t_in timestamptz NOT NULL,
  t_out timestamptz NOT NULL,
  reasons text[] NOT NULL,
  obstructors text[] NOT NULL,
  unknown_obstructors text[] NOT NULL,
  detail jsonb NOT NULL,
  unqualified_reason text,
  moon_scope text,
  PRIMARY KEY (chart_id,generation,ayanamsha_id,vedha_kind,graha,t_in),
  FOREIGN KEY (chart_id,generation,ayanamsha_id,vedha_kind)
    REFERENCES public.kala_vedha_gochara_candidate(chart_id,generation,ayanamsha_id,vedha_kind),
  CHECK (isfinite(t_in) AND isfinite(t_out) AND t_in<t_out),
  CHECK (source_qualification='verse_cited'),
  CHECK (COALESCE(
    (state='unqualified' AND cardinality(reasons)>0 AND unqualified_reason=reasons[1]
      AND reasons <@ ARRAY['obstructor_residence_unknown','node_obstruction_undecided','node_residence_unknown']::text[]
      AND cardinality(obstructors)=0 AND moon_scope IS NULL)
    OR (state='active' AND unqualified_reason IS NULL AND cardinality(reasons)=0 AND moon_scope IS NULL
      AND cardinality(unknown_obstructors)=0 AND (vedha_kind='latta' OR cardinality(obstructors)>0))
    OR (state='inactive' AND unqualified_reason IS NULL AND cardinality(reasons)=0
      AND cardinality(obstructors)=0 AND cardinality(unknown_obstructors)=0
      AND ((graha='Mercury' AND moon_scope IS NULL)
        OR (graha<>'Mercury' AND moon_scope='excluding_on_demand_moon_obstruction'))), false)),
  CHECK (COALESCE((vedha_kind='house_vedha' AND graha NOT IN ('Moon','Rahu','Ketu')
      AND jsonb_typeof(detail->'primary_house')='number' AND jsonb_typeof(detail->'vedha_house')='number'
      AND (detail->>'primary_house')::integer BETWEEN 1 AND 12
      AND (detail->>'vedha_house')::integer BETWEEN 1 AND 12
      AND detail->>'primary_house'<>detail->>'vedha_house')
    OR (vedha_kind='latta' AND graha<>'Ketu' AND state='active'
      AND (detail->>'source_nakshatra')::integer BETWEEN 1 AND 27
      AND (detail->>'target_nakshatra')::integer BETWEEN 1 AND 27
      AND detail->>'janma_reference_fact_id' IS NOT NULL AND detail->>'verse_ref' IS NOT NULL), false)),
  CHECK (NOT detail ?| ARRAY['score','segments','concurrent_latta_count']),
  CHECK (NOT ('Moon'=ANY(obstructors)) AND NOT ('Rahu'=ANY(obstructors)) AND NOT ('Ketu'=ANY(obstructors))),
  CHECK (NOT (graha='Sun' AND 'Saturn'=ANY(obstructors))
    AND NOT (graha='Saturn' AND 'Sun'=ANY(obstructors))
    AND NOT (graha='Mercury' AND 'Moon'=ANY(obstructors)))
);

-- The same candidate advisory/row locks as manifest publication. No cascades:
-- children must be deleted first, and publication/retention makes both immutable.
CREATE OR REPLACE FUNCTION public.kala_vedha_candidate_guard() RETURNS trigger
LANGUAGE plpgsql AS $guard$
DECLARE r record; c record;
BEGIN
  IF TG_OP='DELETE' THEN r:=OLD; ELSE r:=NEW; END IF;
  IF TG_OP='UPDATE' AND ROW(OLD.chart_id,OLD.generation,OLD.ayanamsha_id,OLD.vedha_kind)
      IS DISTINCT FROM ROW(NEW.chart_id,NEW.generation,NEW.ayanamsha_id,NEW.vedha_kind) THEN
    RAISE EXCEPTION 'KA-3a identity is immutable';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(
    replace(json_build_array(r.chart_id::text,r.generation)::text, ', ', ','),0));
  SELECT * INTO c FROM public.kala_layer_candidate
    WHERE chart_id=r.chart_id AND generation=r.generation FOR UPDATE;
  IF NOT FOUND OR c.state<>'building' OR EXISTS (
      SELECT 1 FROM public.kala_layer_head WHERE chart_id=r.chart_id AND generation=r.generation)
      OR NOT EXISTS (SELECT 1 FROM public.build_runs b WHERE b.id=c.build_id AND b.chart_id=r.chart_id) THEN
    RAISE EXCEPTION 'KA-3a requires a mutable building candidate bound to this chart/build';
  END IF;
  IF TG_OP<>'DELETE' AND TG_TABLE_NAME='kala_vedha_gochara_candidate' THEN
    IF c.conventions->'natal'->>'build_id' IS DISTINCT FROM r.natal_build_id::text
        OR c.conventions->'natal'->>'ayanamsha_id' IS DISTINCT FROM r.ayanamsha_id
        OR NOT EXISTS (SELECT 1 FROM public.build_runs b WHERE b.id=r.natal_build_id AND b.chart_id=r.chart_id) THEN
      RAISE EXCEPTION 'KA-3a natal pin does not match candidate';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.chart_facts f WHERE f.fact_id=r.janma_reference_fact_id
        AND f.chart_id=r.chart_id AND f.build_id=r.natal_build_id AND f.ayanamsha_id=r.ayanamsha_id
        AND f.fact_category='graha_position' AND f.fact_subject='MOON' AND f.fact_key='longitude_sidereal') THEN
      IF r.janma_reference_fact_id<>'[EXTERNAL_COMPUTATION_REQUIRED]'
          OR r.null_reason IS DISTINCT FROM 'information_unavailable'
          OR NOT r.payload ? 'external_computation_required'
          OR r.payload->'external_computation_required' IS DISTINCT FROM jsonb_build_object(
            'asset','ga_positions','fact_category','graha_position','fact_subject','MOON',
            'fact_key','longitude_sidereal','chart_id',r.chart_id::text,'build_id',r.natal_build_id::text,
            'ayanamsha_id',r.ayanamsha_id)
          OR EXISTS (SELECT 1 FROM public.chart_facts f WHERE f.chart_id=r.chart_id AND f.build_id=r.natal_build_id
            AND f.ayanamsha_id=r.ayanamsha_id AND f.fact_category='graha_position'
            AND f.fact_subject='MOON' AND f.fact_key='longitude_sidereal') THEN
        RAISE EXCEPTION 'KA-3a natal fact reference does not match pinned chart/build/ayanamsha';
      END IF;
    END IF;
  END IF;
  IF TG_OP<>'DELETE' AND TG_TABLE_NAME='kala_vedha_gochara_interval' THEN
    IF EXISTS (SELECT 1 FROM public.kala_vedha_gochara_candidate h
        WHERE h.chart_id=r.chart_id AND h.generation=r.generation AND h.ayanamsha_id=r.ayanamsha_id
          AND h.vedha_kind=r.vedha_kind AND h.janma_reference_fact_id='[EXTERNAL_COMPUTATION_REQUIRED]') THEN
      RAISE EXCEPTION 'KA-3a cannot compute an interval without its natal reference';
    END IF;
    IF EXISTS (SELECT 1 FROM public.kala_vedha_gochara_interval i
        WHERE i.chart_id=r.chart_id AND i.generation=r.generation AND i.ayanamsha_id=r.ayanamsha_id
          AND i.vedha_kind=r.vedha_kind AND i.graha=r.graha
          AND tstzrange(i.t_in,i.t_out,'[)') && tstzrange(r.t_in,r.t_out,'[)')
          AND (TG_OP='INSERT' OR i.t_in<>OLD.t_in)) THEN
      RAISE EXCEPTION 'KA-3a overlapping intervals';
    END IF;
  END IF;
  RETURN r;
END $guard$;
DROP TRIGGER IF EXISTS kala_vedha_candidate_guard ON public.kala_vedha_gochara_candidate;
CREATE TRIGGER kala_vedha_candidate_guard BEFORE INSERT OR UPDATE OR DELETE ON public.kala_vedha_gochara_candidate
  FOR EACH ROW EXECUTE FUNCTION public.kala_vedha_candidate_guard();
DROP TRIGGER IF EXISTS kala_vedha_interval_guard ON public.kala_vedha_gochara_interval;
CREATE TRIGGER kala_vedha_interval_guard BEFORE INSERT OR UPDATE OR DELETE ON public.kala_vedha_gochara_interval
  FOR EACH ROW EXECUTE FUNCTION public.kala_vedha_candidate_guard();

-- TRUNCATE bypasses row triggers and must not erase retained generations.
CREATE OR REPLACE FUNCTION public.kala_vedha_refuse_truncate() RETURNS trigger
LANGUAGE plpgsql AS $truncate_guard$
BEGIN
  RAISE EXCEPTION 'KA-3a candidate history cannot be truncated; use guarded candidate replacement';
END $truncate_guard$;
DROP TRIGGER IF EXISTS kala_vedha_no_truncate ON public.kala_vedha_gochara_candidate;
CREATE TRIGGER kala_vedha_no_truncate BEFORE TRUNCATE ON public.kala_vedha_gochara_candidate
  FOR EACH STATEMENT EXECUTE FUNCTION public.kala_vedha_refuse_truncate();
DROP TRIGGER IF EXISTS kala_vedha_no_truncate ON public.kala_vedha_gochara_interval;
CREATE TRIGGER kala_vedha_no_truncate BEFORE TRUNCATE ON public.kala_vedha_gochara_interval
  FOR EACH STATEMENT EXECUTE FUNCTION public.kala_vedha_refuse_truncate();
