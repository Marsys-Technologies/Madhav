-- K5-G1a PRE-BUILD, SR-A4-01. NEEDS-PROTECTED-WINDOW; no activation/grants.
-- 1384 is the highest migration observed on all local main/open refs (2026-10-16).
-- (I) INTERPRETATION: additive sibling tables isolate every stage, not just
-- the four final tables. Never ALTER, re-key, copy or delete legacy rows.
SET LOCAL lock_timeout = '5s';

CREATE OR REPLACE FUNCTION public.kala_kshetra_candidate_guard() RETURNS trigger
LANGUAGE plpgsql AS $guard$
DECLARE r record; c record;
BEGIN
  IF TG_OP='DELETE' THEN r:=OLD; ELSE r:=NEW; END IF;
  IF TG_OP='UPDATE' AND ROW(OLD.chart_id,OLD.generation) IS DISTINCT FROM ROW(NEW.chart_id,NEW.generation) THEN
    RAISE EXCEPTION 'K5-G1a candidate identity is immutable';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(
    replace(json_build_array(r.chart_id::text,r.generation)::text, ', ', ','),0));
  SELECT * INTO c FROM public.kala_layer_candidate
    WHERE chart_id=r.chart_id AND generation=r.generation FOR UPDATE;
  IF NOT FOUND OR c.state<>'building' OR EXISTS (
    SELECT 1 FROM public.kala_layer_head WHERE chart_id=r.chart_id AND generation=r.generation)
    OR NOT EXISTS (SELECT 1 FROM public.build_runs WHERE id=c.build_id AND chart_id=r.chart_id) THEN
    RAISE EXCEPTION 'K5-G1a requires a building candidate bound to this chart/build';
  END IF;
  RETURN r;
END $guard$;

DO $tables$
DECLARE source text; target text; idx record; cols text; seq_name text; constraint_row record;
BEGIN
  FOREACH source IN ARRAY ARRAY[
    'kala_field_provenance','kala_field_salience','kala_insights','kala_timeline_spec',
    'kala_field_windows','kala_field_null','kala_field','kala_field_snapshots',
    'kala_field_primitives','kala_field_boundaries','kala_field_clocks',
    'kala_field_routes','kala_field_promise_edges','kala_field_promise_nodes',
    'kala_field_kinematics','build_substep_progress'
  ] LOOP
    target:=source||'_candidate';
    EXECUTE format('CREATE TABLE IF NOT EXISTS public.%I (LIKE public.%I INCLUDING DEFAULTS INCLUDING CONSTRAINTS)',target,source);
    EXECUTE format('ALTER TABLE public.%I ADD COLUMN IF NOT EXISTS generation text NOT NULL CHECK (generation ~ ''^[A-Za-z0-9_.:-]{1,128}$'' AND generation NOT IN (''legacy'',''published'',''current'',''retained''))',target);
    -- LIKE must not reuse a legacy BIGSERIAL sequence: allocate candidate IDs independently.
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=source AND column_name='id' AND column_default LIKE 'nextval(%') THEN
      seq_name:=target||'_id_seq';
      EXECUTE format('CREATE SEQUENCE IF NOT EXISTS public.%I',seq_name);
      EXECUTE format('ALTER SEQUENCE public.%I OWNED BY public.%I.id',seq_name,target);
      EXECUTE format('ALTER TABLE public.%I ALTER COLUMN id SET DEFAULT nextval(%L::regclass)',target,'public.'||seq_name);
    END IF;
    FOR idx IN SELECT indexrelid,relname FROM pg_index JOIN pg_class ON oid=indexrelid
               WHERE indrelid=format('public.%I',source)::regclass AND indisunique LOOP
      SELECT string_agg(pg_get_indexdef(idx.indexrelid,n,true),', ' ORDER BY n) INTO cols
        FROM generate_series(1,(SELECT indnkeyatts FROM pg_index WHERE indexrelid=idx.indexrelid)) n;
      EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS %I ON public.%I (generation, %s)',
        'kyg1_'||source||'_'||substr(md5(idx.relname),1,8),target,cols);
    END LOOP;
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON public.%I (chart_id,generation)', 'kyg1_'||source||'_partition',target);
    EXECUTE format('DROP TRIGGER IF EXISTS kshetra_candidate_mutability ON public.%I',target);
    EXECUTE format('CREATE TRIGGER kshetra_candidate_mutability BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.kala_kshetra_candidate_guard()',target);
    EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC',target);
  END LOOP;
  -- Extend candidate symbolization only; the legacy CHECK remains untouched.
  FOR constraint_row IN SELECT conname FROM pg_constraint
    WHERE conrelid='public.kala_field_primitives_candidate'::regclass AND contype='c'
      AND pg_get_constraintdef(oid) LIKE '%primitive_kind%' LOOP
    EXECUTE format('ALTER TABLE public.kala_field_primitives_candidate DROP CONSTRAINT %I',constraint_row.conname);
  END LOOP;
END $tables$;
ALTER TABLE public.kala_field_primitives_candidate ADD CONSTRAINT kyg1_primitive_kind CHECK (
  primitive_kind IN ('contact_moon_ref','contact_lagna_ref','station_band','syzygy_band',
    'moorti_at_ingress','vedha','panchanga_limb','sandhi_band','av_kaksha_gate','latta',
    'moorti_testimony','negative_space','input_mask'));
COMMENT ON TABLE public.kala_field_snapshots_candidate IS
  'K5-G1a code-only candidate output. config_pin declares as_of, UTC birth axis, canonical rarity, constants and unavailable terms. No serving-head change.';
