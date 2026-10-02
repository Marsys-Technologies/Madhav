CREATE OR REPLACE FUNCTION public.complete_l1_data_plane_partition(p_chart_id uuid, p_asset_id text, p_generation_id text, p_partition_key text, p_rows_inserted integer)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'pg_temp'
AS $function$
DECLARE
  v_existing_rows INTEGER;
  v_observed_rows INTEGER;
  v_completed INTEGER;
  v_expected INTEGER;
  v_declared INTEGER;
  v_digest TEXT;
  v_status TEXT;
  v_existing_generation_digest TEXT;
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L1 partition completion requires direct data_plane_builder authentication';
  END IF;
  IF current_setting('madhav.l1_asset_id', true) IS DISTINCT FROM p_asset_id
     OR current_setting('madhav.l1_chart_id', true) IS DISTINCT FROM p_chart_id::text
     OR current_setting('madhav.l1_generation_id', true) IS DISTINCT FROM p_generation_id
     OR current_setting('madhav.l1_partition_key', true) IS DISTINCT FROM p_partition_key THEN
    RAISE EXCEPTION 'L1 completion context does not match the requested generation';
  END IF;
  IF p_rows_inserted < 0 THEN
    RAISE EXCEPTION 'rows_inserted cannot be negative';
  END IF;
  SELECT expected_partitions, status, semantic_output_digest
  INTO v_expected, v_status, v_existing_generation_digest
  FROM public.l1_data_plane_generations
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'L1 generation % is not open', p_generation_id;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.l1_data_plane_partition_contexts
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
  ) THEN
    RAISE EXCEPTION 'L1 partition % was not declared by generation open', p_partition_key;
  END IF;
  IF p_asset_id = 'ga_dashas' THEN
    PERFORM public.capture_l1_data_plane_dasha_partition(
      p_chart_id, p_generation_id, p_partition_key, p_rows_inserted
    );
  END IF;
  IF p_asset_id = 'ga_dashas' AND p_partition_key <> '__concurrency_post_pass__' THEN
    SELECT count(*) INTO v_observed_rows
    FROM (
      SELECT DISTINCT ON ((s.source_row).dasha_row_id) (s.source_row).dasha_row_id
      FROM public.l1_data_plane_dasha_snapshots s
      WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
        AND s.generation_id = p_generation_id
        AND s.partition_key = p_partition_key
      ORDER BY (s.source_row).dasha_row_id, s.captured_at DESC, s.dasha_snapshot_id DESC
    ) captured;
  ELSE
    SELECT count(*) INTO v_observed_rows
    FROM (
      SELECT DISTINCT ON (s.source_table, s.row_identity)
        s.source_table, s.row_identity
      FROM public.l1_data_plane_row_snapshots s
      WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
        AND s.generation_id = p_generation_id
        AND s.partition_key = p_partition_key
      ORDER BY s.source_table, s.row_identity, s.captured_at DESC, s.snapshot_id DESC
    ) captured;
  END IF;
  IF v_observed_rows <> p_rows_inserted THEN
    RAISE EXCEPTION 'L1 partition % reported % rows but protected capture contains %',
      p_partition_key, p_rows_inserted, v_observed_rows;
  END IF;
  IF v_observed_rows = 0 AND NOT EXISTS (
    SELECT 1 FROM public.asset_registry
    WHERE asset_id = p_asset_id AND target_floor = 0
  ) THEN
    RAISE EXCEPTION 'L1 partition % has undeclared empty output', p_partition_key;
  END IF;
  INSERT INTO public.l1_data_plane_generation_partitions (
    chart_id, asset_id, generation_id, partition_key, rows_inserted
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key, p_rows_inserted
  ) ON CONFLICT DO NOTHING;

  SELECT rows_inserted INTO v_existing_rows
  FROM public.l1_data_plane_generation_partitions
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id AND partition_key = p_partition_key;
  IF v_existing_rows IS DISTINCT FROM p_rows_inserted THEN
    RAISE EXCEPTION 'partition % replay changed row count from % to %',
      p_partition_key, v_existing_rows, p_rows_inserted;
  END IF;

  SELECT count(*), max(g.expected_partitions)
  INTO v_completed, v_expected
  FROM public.l1_data_plane_generation_partitions p
  JOIN public.l1_data_plane_generations g
    USING (chart_id, asset_id, generation_id)
  WHERE p.chart_id = p_chart_id AND p.asset_id = p_asset_id
    AND p.generation_id = p_generation_id;

  IF v_completed > v_expected THEN
    RAISE EXCEPTION 'generation has % partitions but expected %', v_completed, v_expected;
  END IF;
  IF v_completed < v_expected THEN
    UPDATE public.l1_data_plane_generations
    SET completed_partitions = v_completed
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id;
    RETURN;
  END IF;

  SELECT count(*) INTO v_declared
  FROM public.l1_data_plane_partition_contexts
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id;
  IF v_declared <> v_expected THEN
    RAISE EXCEPTION 'L1 generation completed % partitions but declared % of expected %',
      v_completed, v_declared, v_expected;
  END IF;

  IF p_asset_id = 'ga_dashas' THEN
    -- Hash fixed-size per-row canonical SHA-256 components into the generation SHA-256. This
    -- avoids building a 536k-element JSON aggregate while retaining a stable,
    -- stable-ID-ordered digest over every canonical typed dasha payload plus
    -- the two ordinary chart_facts scope sentinels. Build identity and
    -- wall-clock observation time are transport metadata, not output.
    SELECT encode(digest(
      COALESCE((
        SELECT string_agg(
          latest.semantic_digest, ''
          ORDER BY (latest.source_row).dasha_row_id
        )
        FROM (
          SELECT DISTINCT ON ((s.source_row).dasha_row_id)
            s.source_row, s.semantic_digest
          FROM public.l1_data_plane_dasha_snapshots s
          WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
            AND s.generation_id = p_generation_id
          ORDER BY (s.source_row).dasha_row_id,
                   s.captured_at DESC, s.dasha_snapshot_id DESC
        ) latest
      ), '') || '|' || COALESCE((
        SELECT string_agg(latest.semantic_digest, ''
                          ORDER BY latest.source_table, latest.row_identity)
        FROM (
          SELECT DISTINCT ON (s.source_table, s.row_identity)
            s.source_table, s.row_identity, s.semantic_digest
          FROM public.l1_data_plane_row_snapshots s
          WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
            AND s.generation_id = p_generation_id
          ORDER BY s.source_table, s.row_identity,
                   s.captured_at DESC, s.snapshot_id DESC
        ) latest
      ), ''),
      'sha256'
    ), 'hex') INTO v_digest;
  ELSE
    SELECT encode(digest(COALESCE(
      jsonb_agg(
        jsonb_build_array(source_table, row_identity, semantic_digest)
        ORDER BY source_table, row_identity
      ), '[]'::jsonb
    )::text, 'sha256'), 'hex')
    INTO v_digest
    FROM (
      SELECT DISTINCT ON (source_table, row_identity)
        source_table, row_identity, semantic_digest
      FROM public.l1_data_plane_row_snapshots
      WHERE chart_id = p_chart_id AND asset_id = p_asset_id
        AND generation_id = p_generation_id
      ORDER BY source_table, row_identity, captured_at DESC, snapshot_id DESC
    ) latest;
  END IF;

  IF v_status = 'complete' THEN
    IF v_existing_generation_digest IS DISTINCT FROM v_digest THEN
      RAISE EXCEPTION 'complete L1 generation replay changed generation digest';
    END IF;
  ELSE
    UPDATE public.l1_data_plane_generations
    SET completed_partitions = v_completed,
        status = 'complete', semantic_output_digest = v_digest,
        completed_at = clock_timestamp()
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id;
  END IF;

  INSERT INTO public.l1_data_plane_generation_heads (
    chart_id, asset_id, current_generation_id
  ) VALUES (p_chart_id, p_asset_id, p_generation_id)
  ON CONFLICT (chart_id, asset_id) DO UPDATE
  SET previous_generation_id = CASE
        WHEN public.l1_data_plane_generation_heads.current_generation_id
             <> EXCLUDED.current_generation_id
        THEN public.l1_data_plane_generation_heads.current_generation_id
        ELSE public.l1_data_plane_generation_heads.previous_generation_id
      END,
      current_generation_id = EXCLUDED.current_generation_id,
      selected_at = clock_timestamp();
END;
$function$
