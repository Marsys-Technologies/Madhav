CREATE OR REPLACE FUNCTION public.capture_l1_data_plane_dasha_partition(p_chart_id uuid, p_generation_id text, p_partition_key text, p_rows_inserted integer)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'pg_temp'
AS $function$
DECLARE
  v_status TEXT;
  v_system_id TEXT;
  v_ayanamsha_id TEXT;
  v_active_rows INTEGER;
  v_systems TEXT[];
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L1 partition completion requires direct data_plane_builder authentication';
  END IF;
  IF current_setting('madhav.l1_asset_id', true) IS DISTINCT FROM 'ga_dashas'
     OR current_setting('madhav.l1_chart_id', true) IS DISTINCT FROM p_chart_id::text
     OR current_setting('madhav.l1_generation_id', true) IS DISTINCT FROM p_generation_id
     OR current_setting('madhav.l1_partition_key', true) IS DISTINCT FROM p_partition_key THEN
    RAISE EXCEPTION 'L1 completion context does not match the requested generation';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.l1_data_plane_partition_contexts
    WHERE chart_id = p_chart_id AND asset_id = 'ga_dashas'
      AND generation_id = p_generation_id AND partition_key = p_partition_key
  ) THEN
    RAISE EXCEPTION 'L1 dasha partition % was not declared before capture', p_partition_key;
  END IF;
  SELECT status INTO v_status
  FROM public.l1_data_plane_generations
  WHERE chart_id = p_chart_id AND asset_id = 'ga_dashas'
    AND generation_id = p_generation_id;
  IF v_status IS NULL THEN
    RAISE EXCEPTION 'L1 dasha generation was not opened before partition capture';
  END IF;

  IF p_partition_key <> '__concurrency_post_pass__' THEN
    v_system_id := split_part(p_partition_key, ':', 1);
    v_ayanamsha_id := split_part(p_partition_key, ':', 2);
    v_systems := CASE WHEN v_system_id = 'vimshottari' THEN ARRAY['vimshottari','vimshottari_kp']::TEXT[] ELSE ARRAY[v_system_id]::TEXT[] END;
    IF v_system_id = '' OR v_ayanamsha_id = '' THEN
      RAISE EXCEPTION 'invalid dasha partition key %', p_partition_key;
    END IF;
    SELECT count(*) INTO v_active_rows
    FROM public.chart_dashas d
    WHERE d.chart_id = p_chart_id
      AND d.build_id::text = p_generation_id
      AND d.system_id = ANY(v_systems)
      AND d.ayanamsha_id = v_ayanamsha_id;
    IF v_active_rows <> p_rows_inserted THEN
      RAISE EXCEPTION 'dasha partition % reported % rows but active build scope has %',
        p_partition_key, p_rows_inserted, v_active_rows;
    END IF;
  END IF;

  -- A completed generation may be replayed only when the current semantic
  -- identity set equals the already-captured latest semantic identity set.
  -- Stable row/parent UUIDs remain material; build/time transport fields do not.
  IF v_status = 'complete' THEN
    IF EXISTS (
      WITH current_semantics AS (
        SELECT d.dasha_row_id,
               encode(digest(
                 public.l1_data_plane_dasha_semantic_payload(d)::text,
                 'sha256'
               ), 'hex') AS semantic_digest
        FROM public.chart_dashas d
        WHERE d.chart_id = p_chart_id AND d.build_id::text = p_generation_id
          AND (p_partition_key = '__concurrency_post_pass__' OR (
            d.system_id = ANY(v_systems) AND d.ayanamsha_id = v_ayanamsha_id
          ))
      ), previous_semantics AS (
        SELECT (latest.source_row).dasha_row_id AS dasha_row_id,
               latest.semantic_digest
        FROM (
          SELECT DISTINCT ON ((s.source_row).dasha_row_id)
            s.source_row, s.semantic_digest
          FROM public.l1_data_plane_dasha_snapshots s
          WHERE s.chart_id = p_chart_id AND s.asset_id = 'ga_dashas'
            AND s.generation_id = p_generation_id
            AND (p_partition_key = '__concurrency_post_pass__' OR (
              (s.source_row).system_id = ANY(v_systems)
              AND (s.source_row).ayanamsha_id = v_ayanamsha_id
            ))
          ORDER BY (s.source_row).dasha_row_id,
                   s.captured_at DESC, s.dasha_snapshot_id DESC
        ) latest
      )
      SELECT 1
      FROM current_semantics current_row
      FULL OUTER JOIN previous_semantics previous_row USING (dasha_row_id)
      WHERE current_row.dasha_row_id IS NULL
         OR previous_row.dasha_row_id IS NULL
         OR current_row.semantic_digest IS DISTINCT FROM previous_row.semantic_digest
    ) THEN
      RAISE EXCEPTION 'complete generation % replay changed or added dasha output',
        p_generation_id;
    END IF;
    RETURN;
  END IF;

  INSERT INTO public.l1_data_plane_dasha_snapshots (
    chart_id, asset_id, generation_id, partition_key, source_row
  )
  SELECT
    p_chart_id, 'ga_dashas', p_generation_id, p_partition_key, d
  FROM public.chart_dashas d
  LEFT JOIN LATERAL (
    SELECT s.source_row, s.semantic_digest
    FROM public.l1_data_plane_dasha_snapshots s
    WHERE s.chart_id = p_chart_id AND s.asset_id = 'ga_dashas'
      AND s.generation_id = p_generation_id
      AND (s.source_row).dasha_row_id = d.dasha_row_id
    ORDER BY s.captured_at DESC, s.dasha_snapshot_id DESC
    LIMIT 1
  ) previous ON true
  WHERE d.chart_id = p_chart_id AND d.build_id::text = p_generation_id
    AND (p_partition_key = '__concurrency_post_pass__' OR (
      d.system_id = ANY(v_systems) AND d.ayanamsha_id = v_ayanamsha_id
    ))
    AND (previous.source_row IS NULL OR previous.semantic_digest IS DISTINCT FROM
      encode(digest(
        public.l1_data_plane_dasha_semantic_payload(d)::text,
        'sha256'
      ), 'hex'));
END;
$function$;
