-- Migration 1356: K6-123 detector generation correction.
-- The three creation files were applied in the lane rehearsal; preserve those bytes.
-- Current chart build selects its candidate; a legacy/default build still counts legacy rows.
-- No state filter: a completed run retains its candidate's count and integrity.
UPDATE public.asset_registry SET count_sql=$count$
SELECT COUNT(*) FROM (
  SELECT chart_id,'legacy'::text generation FROM public.kala_activation
  UNION ALL SELECT chart_id,generation FROM public.kala_activation_candidate
) model_rows WHERE chart_id = $1 AND generation=COALESCE((
  SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END
  FROM public.build_runs b LEFT JOIN public.kala_layer_candidate c
    ON c.chart_id=b.chart_id AND c.build_id=b.id
  WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1
),'legacy')
$count$ WHERE asset_id='ka_kalasutra';
-- Keep the entire legacy detector in the ELSE branch, byte for byte.
UPDATE public.asset_registry SET integrity_check_sql=
  $target$WITH k6_target AS (
    SELECT b.chart_id,c.generation,c.conventions FROM public.build_runs b
    LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id
    ORDER BY b.created_at DESC,b.id DESC LIMIT 1
  ) SELECT CASE WHEN EXISTS (SELECT 1 FROM k6_target WHERE conventions->>'fixture'='true') THEN (
    SELECT NOT EXISTS (
      SELECT 1 FROM public.kala_activation_candidate r JOIN k6_target t
        ON r.chart_id=t.chart_id AND r.generation=t.generation
      WHERE r.payload->>'acceptance_scope' IS DISTINCT FROM 'fixture_only'
        OR NOT (r.upstream_refs ?& ARRAY['judge','F1','F2','jury','negative_space','LEL'])
    )
  ) ELSE ($target$ ||
  COALESCE(NULLIF(regexp_replace(btrim(integrity_check_sql), ';[[:space:]]*$', ''),''),'SELECT true') || ') END'
WHERE asset_id='ka_kalasutra' AND COALESCE(integrity_check_sql,'') NOT LIKE 'WITH k6_target AS%';
-- Current chart build selects its candidate; a legacy/default build still counts legacy rows.
-- No state filter: a completed run retains its candidate's count and integrity.
UPDATE public.asset_registry SET count_sql=$count$
SELECT COUNT(*) FROM (
  SELECT chart_id,'legacy'::text generation FROM public.kala_darshana
  UNION ALL SELECT chart_id,generation FROM public.kala_darshana_candidate
) model_rows WHERE chart_id = $1 AND generation=COALESCE((
  SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END
  FROM public.build_runs b LEFT JOIN public.kala_layer_candidate c
    ON c.chart_id=b.chart_id AND c.build_id=b.id
  WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1
),'legacy')
$count$ WHERE asset_id='ka_kala_darshana';
-- Keep the entire legacy detector in the ELSE branch, byte for byte.
UPDATE public.asset_registry SET integrity_check_sql=
  $target$WITH k6_target AS (
    SELECT b.chart_id,c.generation,c.conventions FROM public.build_runs b
    LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id
    ORDER BY b.created_at DESC,b.id DESC LIMIT 1
  ) SELECT CASE WHEN EXISTS (SELECT 1 FROM k6_target WHERE conventions->>'fixture'='true') THEN (
    SELECT NOT EXISTS (
      SELECT 1 FROM public.kala_darshana_candidate r JOIN k6_target t
        ON r.chart_id=t.chart_id AND r.generation=t.generation
      WHERE r.payload->>'acceptance_scope' IS DISTINCT FROM 'fixture_only'
        OR NOT (r.upstream_refs ?& ARRAY['judge','F1','F2','jury','negative_space','LEL'])
    )
  ) ELSE ($target$ ||
  COALESCE(NULLIF(regexp_replace(btrim(integrity_check_sql), ';[[:space:]]*$', ''),''),'SELECT true') || ') END'
WHERE asset_id='ka_kala_darshana' AND COALESCE(integrity_check_sql,'') NOT LIKE 'WITH k6_target AS%';
-- Current chart build selects its candidate; a legacy/default build still counts legacy rows.
-- No state filter: a completed run retains its candidate's count and integrity.
UPDATE public.asset_registry SET count_sql=$count$
SELECT COUNT(*) FROM (
  SELECT chart_id,'legacy'::text generation FROM public.kala_jivana_parva
  UNION ALL SELECT chart_id,generation FROM public.kala_jivana_parva_candidate
) model_rows WHERE chart_id = $1 AND generation=COALESCE((
  SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END
  FROM public.build_runs b LEFT JOIN public.kala_layer_candidate c
    ON c.chart_id=b.chart_id AND c.build_id=b.id
  WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1
),'legacy')
$count$ WHERE asset_id='ka_jivana_parva';
-- Keep the entire legacy detector in the ELSE branch, byte for byte.
UPDATE public.asset_registry SET integrity_check_sql=
  $target$WITH k6_target AS (
    SELECT b.chart_id,c.generation,c.conventions FROM public.build_runs b
    LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id
    ORDER BY b.created_at DESC,b.id DESC LIMIT 1
  ) SELECT CASE WHEN EXISTS (SELECT 1 FROM k6_target WHERE conventions->>'fixture'='true') THEN (
    SELECT NOT EXISTS (
      SELECT 1 FROM public.kala_jivana_parva_candidate r JOIN k6_target t
        ON r.chart_id=t.chart_id AND r.generation=t.generation
      WHERE r.payload->>'acceptance_scope' IS DISTINCT FROM 'fixture_only'
        OR NOT (r.upstream_refs ?& ARRAY['judge','F1','F2','jury','negative_space','LEL'])
    )
  ) ELSE ($target$ ||
  COALESCE(NULLIF(regexp_replace(btrim(integrity_check_sql), ';[[:space:]]*$', ''),''),'SELECT true') || ') END'
WHERE asset_id='ka_jivana_parva' AND COALESCE(integrity_check_sql,'') NOT LIKE 'WITH k6_target AS%';
