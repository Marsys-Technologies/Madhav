CREATE OR REPLACE FUNCTION public.assert_l2_msr_delete_safe(p_chart_id uuid, p_ayanamsha_ids text[] DEFAULT NULL::text[], p_signal_type_ids text[] DEFAULT NULL::text[], p_signal_type_classes text[] DEFAULT NULL::text[])
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'pg_temp'
AS $function$
DECLARE
  v_fk record;
  v_exists boolean;
  v_asset text := current_setting('madhav.l2_asset_id',true);
  v_generation text := current_setting('madhav.l2_generation_id',true);
  v_partition text := current_setting('madhav.l2_partition_key',true);
  v_build text := current_setting('madhav.l2_build_id',true);
BEGIN
  IF session_user <> 'data_plane_builder' OR v_asset IS NULL
     OR current_setting('madhav.l2_chart_id',true) IS DISTINCT FROM p_chart_id::text
     OR NOT EXISTS (
       SELECT 1 FROM public.l2_data_plane_run_intents i
       JOIN public.data_plane_l2_producer_generations g USING(chart_id,asset_id,generation_id)
       WHERE i.chart_id=p_chart_id AND i.asset_id=v_asset
         AND i.generation_id=v_generation AND i.partition_key=v_partition
         AND i.build_id=v_build AND g.state='building'
     ) THEN
    RAISE EXCEPTION 'L2 MSR delete authorization is outside admitted asset context';
  END IF;
  -- Parent FOR UPDATE conflicts with the KEY SHARE lock acquired by a foreign-
  -- key insert. Holding the exact replacement scope through the later DELETE
  -- closes the check/delete race for CASCADE, SET NULL and future FK actions.
  PERFORM 1
  FROM public.bodha_msr_signals s
  WHERE s.chart_id = p_chart_id
    AND s.producer_asset_id = v_asset
    AND (p_ayanamsha_ids IS NULL OR s.ayanamsha_id = ANY(p_ayanamsha_ids))
    AND (p_signal_type_ids IS NULL OR s.signal_type_id = ANY(p_signal_type_ids))
    AND (p_signal_type_classes IS NULL OR s.signal_type_class = ANY(p_signal_type_classes))
  ORDER BY s.signal_id
  FOR UPDATE;

  FOR v_fk IN
    SELECT n.nspname AS schema_name, c.relname AS table_name,
           a.attname AS column_name, cardinality(k.conkey) AS key_count,
           ra.attname AS referenced_column
    FROM pg_constraint k
    JOIN pg_class c ON c.oid = k.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    LEFT JOIN pg_attribute a
      ON a.attrelid = k.conrelid AND a.attnum = k.conkey[1]
    LEFT JOIN pg_attribute ra
      ON ra.attrelid = k.confrelid AND ra.attnum = k.confkey[1]
    WHERE k.contype = 'f'
      AND k.confrelid = 'public.bodha_msr_signals'::regclass
  LOOP
    IF v_fk.schema_name = 'public'
       AND v_fk.table_name IN ('bodha_signal_embeddings', 'bodha_contradictions') THEN
      CONTINUE;
    END IF;
    IF v_fk.key_count <> 1 OR v_fk.referenced_column <> 'signal_id'
       OR v_fk.column_name IS NULL THEN
      RAISE EXCEPTION 'unsupported cross-layer MSR foreign key %.%',
        v_fk.schema_name, v_fk.table_name;
    END IF;
    EXECUTE format(
      'SELECT EXISTS ('
      ' SELECT 1 FROM %I.%I d'
      ' JOIN public.bodha_msr_signals s ON d.%I = s.signal_id'
      ' WHERE s.chart_id = $1'
      '   AND ($2 IS NULL OR s.ayanamsha_id = ANY($2))'
      '   AND ($3 IS NULL OR s.signal_type_id = ANY($3))'
      '   AND ($4 IS NULL OR s.signal_type_class = ANY($4))'
      '   AND s.producer_asset_id = $5'
      ')',
      v_fk.schema_name, v_fk.table_name, v_fk.column_name
    ) INTO v_exists
      USING p_chart_id, p_ayanamsha_ids, p_signal_type_ids, p_signal_type_classes, v_asset;
    IF v_exists THEN
      RAISE EXCEPTION
        'L2 MSR replacement blocked by cross-layer dependent rows in %.%',
        v_fk.schema_name, v_fk.table_name;
    END IF;
  END LOOP;
  DROP TABLE IF EXISTS pg_temp.l2_data_plane_msr_delete_receipt;
  CREATE TEMP TABLE l2_data_plane_msr_delete_receipt (
    chart_id uuid NOT NULL,
    asset_id text NOT NULL,
    signal_id uuid PRIMARY KEY
  ) ON COMMIT DROP;
  INSERT INTO pg_temp.l2_data_plane_msr_delete_receipt(chart_id, asset_id, signal_id)
  SELECT s.chart_id, v_asset, s.signal_id
  FROM public.bodha_msr_signals s
  WHERE s.chart_id = p_chart_id
    AND s.producer_asset_id = v_asset
    AND (p_ayanamsha_ids IS NULL OR s.ayanamsha_id = ANY(p_ayanamsha_ids))
    AND (p_signal_type_ids IS NULL OR s.signal_type_id = ANY(p_signal_type_ids))
    AND (p_signal_type_classes IS NULL OR s.signal_type_class = ANY(p_signal_type_classes));
END;
$function$

