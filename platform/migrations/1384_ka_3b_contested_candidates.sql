-- KA-3b PRE-BUILD, SR-A4-01. NEEDS-PROTECTED-WINDOW. No activation/grants.
-- Guard-numbered after 1382; 1383 belongs to prerequisite KA-3a.
-- Legacy keys/values and publication remain intact. Nullable columns are not
-- backfilled: legacy computations cannot be promoted by a metadata migration.
SET LOCAL lock_timeout = '5s';
ALTER TABLE public.kala_moorti_nirnaya
  ADD COLUMN IF NOT EXISTS method_qualification text,
  ADD COLUMN IF NOT EXISTS coverage jsonb,
  ADD COLUMN IF NOT EXISTS upstream_fingerprint jsonb;
ALTER TABLE public.kala_kota_chakra
  ADD COLUMN IF NOT EXISTS method_qualification text,
  ADD COLUMN IF NOT EXISTS coverage jsonb,
  ADD COLUMN IF NOT EXISTS upstream_fingerprint jsonb;
ALTER TABLE public.kala_tithi_pravesha
  ADD COLUMN IF NOT EXISTS method_qualification text,
  ADD COLUMN IF NOT EXISTS coverage jsonb,
  ADD COLUMN IF NOT EXISTS upstream_fingerprint jsonb;
ALTER TABLE public.kala_sudarshana_varsha
  ADD COLUMN IF NOT EXISTS method_qualification text,
  ADD COLUMN IF NOT EXISTS coverage jsonb,
  ADD COLUMN IF NOT EXISTS upstream_fingerprint jsonb;

-- (I) INTERPRETATION: separate, explicit candidate envelopes instead of a
-- re-key of legacy DATE tables. Entries carry half-open UT Julian days.
DO $tables$
DECLARE family text;
BEGIN
  FOREACH family IN ARRAY ARRAY['moorti_nirnaya','kota_chakra','tithi_pravesha','sudarshana_varsha'] LOOP
    EXECUTE format($ddl$
      CREATE TABLE IF NOT EXISTS public.%I (
        chart_id uuid NOT NULL,
        generation text NOT NULL CHECK (generation ~ '^[A-Za-z0-9_.:-]+$'
          AND generation NOT IN ('legacy','current','published','retained')),
        ayanamsha_id text NOT NULL CHECK (ayanamsha_id<>''),
        family text NOT NULL CHECK (family=%L),
        natal_build_id uuid NOT NULL REFERENCES public.build_runs(id),
        method_qualification text NOT NULL CHECK (method_qualification=%L),
        operator_role text NOT NULL CHECK (operator_role='testimony'),
        coverage jsonb NOT NULL CHECK (COALESCE(jsonb_typeof(coverage)='object'
          AND coverage->>'search_state' IN ('searched','partial','unsearched')
          AND coverage ?& ARRAY['requested','source_interval','covered','complete','backend','convention_id','gaps'],false)),
        upstream_fingerprint jsonb NOT NULL CHECK (COALESCE(upstream_fingerprint->>'schema'='ka_contested_inputs/1'
          AND upstream_fingerprint->>'digest' ~ '^[0-9a-f]{64}$',false)),
        payload jsonb NOT NULL CHECK (COALESCE(payload->>'schema'='ka_contested_payload/1'
          AND jsonb_typeof(payload->'entries')='array' AND jsonb_typeof(payload->'context'->'facts')='array'
          AND jsonb_typeof(payload->'external_computation_required')='array',false)),
        null_reason text CHECK (null_reason IS NULL OR null_reason='information_unavailable'),
        formula_version text NOT NULL CHECK (formula_version='ka_contested_candidate/1'),
        PRIMARY KEY (chart_id,generation,ayanamsha_id),
        FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation)
      )
    $ddl$, 'kala_'||family||'_candidate',family,
      CASE WHEN family='kota_chakra' THEN 'uncited_extension' ELSE 'method_contested' END);
  END LOOP;
END $tables$;

CREATE OR REPLACE FUNCTION public.kala_contested_candidate_guard() RETURNS trigger
LANGUAGE plpgsql AS $guard$
DECLARE r record; c record; f jsonb; e jsonb; spec jsonb;
  subject text; key text; needed text[]; present integer; a double precision; b double precision;
BEGIN
  IF TG_OP='DELETE' THEN r:=OLD; ELSE r:=NEW; END IF;
  IF TG_OP='UPDATE' AND ROW(OLD.chart_id,OLD.generation,OLD.ayanamsha_id,OLD.family)
      IS DISTINCT FROM ROW(NEW.chart_id,NEW.generation,NEW.ayanamsha_id,NEW.family) THEN
    RAISE EXCEPTION 'KA-3b candidate identity is immutable';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(
    replace(json_build_array(r.chart_id::text,r.generation)::text, ', ', ','),0));
  SELECT * INTO c FROM public.kala_layer_candidate
    WHERE chart_id=r.chart_id AND generation=r.generation FOR UPDATE;
  IF NOT FOUND OR c.state<>'building' OR EXISTS (
      SELECT 1 FROM public.kala_layer_head WHERE chart_id=r.chart_id AND generation=r.generation)
      OR NOT EXISTS (SELECT 1 FROM public.build_runs WHERE id=c.build_id AND chart_id=r.chart_id) THEN
    RAISE EXCEPTION 'KA-3b requires a mutable building candidate bound to this chart/build';
  END IF;
  IF TG_OP='DELETE' THEN RETURN r; END IF;
  IF c.conventions->'natal'->>'build_id' IS DISTINCT FROM r.natal_build_id::text
      OR c.conventions->'natal'->>'ayanamsha_id' IS DISTINCT FROM r.ayanamsha_id
      OR NOT EXISTS (SELECT 1 FROM public.build_runs WHERE id=r.natal_build_id AND chart_id=r.chart_id)
      OR r.payload->'context'->>'chart_id' IS DISTINCT FROM r.chart_id::text
      OR r.payload->'context'->>'generation' IS DISTINCT FROM r.generation
      OR r.payload->'context'->>'natal_build_id' IS DISTINCT FROM r.natal_build_id::text
      OR r.payload->'context'->'convention'->>'ayanamsha_id' IS DISTINCT FROM r.ayanamsha_id
      OR r.payload->>'family' IS DISTINCT FROM r.family
      OR r.payload->>'operator_role' IS DISTINCT FROM r.operator_role
      OR r.payload->>'method_qualification' IS DISTINCT FROM r.method_qualification
      OR r.payload->'coverage' IS DISTINCT FROM r.coverage
      OR r.payload->>'null_reason' IS DISTINCT FROM r.null_reason THEN
    RAISE EXCEPTION 'KA-3b payload identity or natal pin mismatch';
  END IF;
  -- Every required natal operand either cites the exact pinned L1 row/value
  -- or carries the exact external-computation spec with no computed entries.
  needed:=CASE WHEN r.family='sudarshana_varsha' THEN ARRAY['LAGNA','MOON','SUN'] ELSE ARRAY['MOON'] END;
  key:=CASE WHEN r.family='sudarshana_varsha' THEN 'sign' ELSE 'longitude_sidereal' END;
  FOREACH subject IN ARRAY needed LOOP
    SELECT count(*) INTO present FROM jsonb_array_elements(r.payload->'context'->'facts') x
      WHERE x->>'fact_subject'=subject AND x->>'fact_key'=key;
    IF present>1 THEN RAISE EXCEPTION 'KA-3b ambiguous L1 facts'; END IF;
    IF present=0 THEN
      spec:=jsonb_build_object('asset','ga_positions','chart_id',r.chart_id::text,'build_id',r.natal_build_id::text,
        'ayanamsha_id',r.ayanamsha_id,'fact_category','graha_position','fact_subject',subject,'fact_key',key);
      IF r.null_reason IS DISTINCT FROM 'information_unavailable'
          OR jsonb_array_length(r.payload->'entries')<>0
          OR NOT r.payload->'external_computation_required' @> jsonb_build_array(spec)
          OR EXISTS (SELECT 1 FROM public.chart_facts cf WHERE cf.chart_id=r.chart_id AND cf.build_id=r.natal_build_id
            AND cf.ayanamsha_id=r.ayanamsha_id AND cf.fact_category='graha_position'
            AND cf.fact_subject=subject AND cf.fact_key=key) THEN
        RAISE EXCEPTION 'KA-3b missing L1 reference requires exact unavailable specification';
      END IF;
    END IF;
  END LOOP;
  FOR f IN SELECT * FROM jsonb_array_elements(r.payload->'context'->'facts') LOOP
    IF (SELECT count(*) FROM public.chart_facts cf WHERE cf.chart_id=r.chart_id AND cf.build_id=r.natal_build_id
        AND cf.ayanamsha_id=r.ayanamsha_id AND cf.fact_category='graha_position'
        AND cf.fact_subject=f->>'fact_subject' AND cf.fact_key=f->>'fact_key')<>1
      OR NOT EXISTS (SELECT 1 FROM public.chart_facts cf WHERE cf.fact_id=f->>'fact_id'
        AND cf.chart_id=r.chart_id AND cf.build_id=r.natal_build_id AND cf.ayanamsha_id=r.ayanamsha_id
        AND cf.fact_category='graha_position' AND cf.fact_subject=f->>'fact_subject' AND cf.fact_key=f->>'fact_key'
        AND CASE WHEN f->>'fact_key'='longitude_sidereal' THEN cf.fact_value_num=(f->>'fact_value_num')::numeric
                 ELSE cf.fact_value_text=f->>'fact_value_text' END) THEN
      RAISE EXCEPTION 'KA-3b L1 fact reference/value differs from pinned authority';
    END IF;
  END LOOP;
  FOR e IN SELECT * FROM jsonb_array_elements(r.payload->'entries') LOOP
    a:=(e->>'t_in')::double precision; b:=(e->>'t_out')::double precision;
    IF a IS NULL OR b IS NULL OR a>=b OR a IN ('Infinity'::float8,'-Infinity'::float8,'NaN'::float8)
        OR b IN ('Infinity'::float8,'-Infinity'::float8,'NaN'::float8)
        OR e ?| ARRAY['score','suppression','tri_lagna_convergence','posture','severity','attack'] THEN
      RAISE EXCEPTION 'KA-3b requires finite half-open testimony, never a scored judgment';
    END IF;
    IF r.family='moorti_nirnaya' AND (e->>'source_status' IS DISTINCT FROM 'uncited_legacy'
        OR e->>'method_id' IS DISTINCT FROM 'moorti_nakshatra_27') THEN
      RAISE EXCEPTION 'KA-3b moorti is the named uncited legacy method';
    ELSIF r.family='kota_chakra' AND (e->>'source_status' IS DISTINCT FROM 'uncited_extension'
        OR e->'direction_of_motion' IS DISTINCT FROM 'null'::jsonb) THEN
      RAISE EXCEPTION 'KA-3b kota direction has no admitted geometry';
    ELSIF r.family='tithi_pravesha' AND (e->>'source_status' IS DISTINCT FROM 'uncited_legacy'
        OR e->>'method_id' IS DISTINCT FROM 'moon_longitude_return' OR e->'phase_return' IS DISTINCT FROM 'null'::jsonb
        OR e->'annual_object_identity_admitted' IS DISTINCT FROM 'false'::jsonb) THEN
      RAISE EXCEPTION 'KA-3b phase return and annual-object admission are unearned';
    ELSIF r.family='sudarshana_varsha' AND (e->'judgment' IS DISTINCT FROM 'null'::jsonb
        OR e->>'year_anchor' IS DISTINCT FROM 'civil_birthday'
        OR e->>'anchor_source_status' IS DISTINCT FROM 'declared_convention') THEN
      RAISE EXCEPTION 'KA-3b Sudarshana adapter has no judge conclusion or sourced year anchor';
    END IF;
  END LOOP;
  RETURN r;
END $guard$;

CREATE OR REPLACE FUNCTION public.kala_contested_refuse_truncate() RETURNS trigger
LANGUAGE plpgsql AS $truncate_guard$
BEGIN
  RAISE EXCEPTION 'KA-3b candidate history cannot be truncated; use guarded candidate replacement';
END $truncate_guard$;
DO $triggers$
DECLARE family text;
BEGIN
  FOREACH family IN ARRAY ARRAY['moorti_nirnaya','kota_chakra','tithi_pravesha','sudarshana_varsha'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS kala_contested_guard ON public.%I','kala_'||family||'_candidate');
    EXECUTE format('CREATE TRIGGER kala_contested_guard BEFORE INSERT OR UPDATE OR DELETE ON public.%I '
      'FOR EACH ROW EXECUTE FUNCTION public.kala_contested_candidate_guard()','kala_'||family||'_candidate');
    EXECUTE format('DROP TRIGGER IF EXISTS kala_contested_no_truncate ON public.%I','kala_'||family||'_candidate');
    EXECUTE format('CREATE TRIGGER kala_contested_no_truncate BEFORE TRUNCATE ON public.%I '
      'FOR EACH STATEMENT EXECUTE FUNCTION public.kala_contested_refuse_truncate()','kala_'||family||'_candidate');
  END LOOP;
END $triggers$;
