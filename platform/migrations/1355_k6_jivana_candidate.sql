-- Migration 1355: K6-123 jivana private fixture projection (KYD-140).
-- No live mapping or publication is admitted. Legacy tables remain unchanged.
CREATE TABLE IF NOT EXISTS public.kala_jivana_parva_candidate (
  chart_id uuid NOT NULL,
  generation text NOT NULL CHECK (generation LIKE 'candidate:%'),
  model_key text NOT NULL,
  row_kind text NOT NULL CHECK (row_kind IN ('judge','contact','context','chapter')),
  interval_start timestamptz NOT NULL,
  interval_end timestamptz NOT NULL,
  as_of timestamptz NOT NULL,
  payload jsonb NOT NULL CHECK (jsonb_typeof(payload)='object'),
  upstream_refs jsonb NOT NULL CHECK (jsonb_typeof(upstream_refs)='object'),
  tier text NOT NULL CHECK (tier IN ('fixture_only','testimony','contextual')),
  PRIMARY KEY (chart_id,generation,model_key),
  FOREIGN KEY (chart_id,generation) REFERENCES public.kala_layer_candidate(chart_id,generation),
  CHECK (interval_end > interval_start)
);
COMMENT ON TABLE public.kala_jivana_parva_candidate IS 'K6 fixture-only candidate read model; live mappings and K9-4b cutover unadmitted';
UPDATE public.asset_registry SET count_sql=$count$
SELECT COUNT(*) FROM (
  SELECT chart_id FROM public.kala_jivana_parva
  UNION ALL SELECT chart_id FROM public.kala_jivana_parva_candidate
) model_rows WHERE chart_id = $1
$count$ WHERE asset_id='ka_jivana_parva';
-- Preserve the legacy detector and add candidate ownership/payload validation.
-- No running-state filter: this remains meaningful after the build completes.
UPDATE public.asset_registry SET integrity_check_sql=
  'SELECT (' || COALESCE(NULLIF(regexp_replace(btrim(integrity_check_sql), ';[[:space:]]*$', ''),''),'SELECT true') ||
  ') AND (' || $check$SELECT NOT EXISTS (
    SELECT 1 FROM public.kala_jivana_parva_candidate r
    LEFT JOIN public.kala_layer_candidate c ON c.chart_id=r.chart_id AND c.generation=r.generation
    WHERE c.chart_id IS NULL OR c.conventions->>'fixture' IS DISTINCT FROM 'true'
       OR r.payload->>'acceptance_scope' IS DISTINCT FROM 'fixture_only'
  )$check$ || ')'
WHERE asset_id='ka_jivana_parva' AND COALESCE(integrity_check_sql,'') NOT LIKE '%FROM public.kala_jivana_parva_candidate r%';
