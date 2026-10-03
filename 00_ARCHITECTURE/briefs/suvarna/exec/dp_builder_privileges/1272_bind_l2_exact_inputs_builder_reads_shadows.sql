-- 1272_bind_l2_exact_inputs_builder_reads_shadows.sql  (S-L2 precondition B3)
--
-- HELD. NEVER RUN BY migrate.ts: this file lives in an executor-owned folder (00_ARCHITECTURE/briefs/suvarna/exec/dp_builder_privileges/), outside
-- platform/migrations and platform/supabase/migrations, the only directories migrate.ts reads. The number is allocated (SS) for history. The change is applied ONLY
-- by dp_builder_privileges_exec.py (gated owner path: transient membership, SET LOCAL ROLE data_plane_l2_owner, re-attestation of the function row in the SAME
-- transaction, plan hash approved by SS). Applying it any other way leaves l2_data_plane_function_attestations stale and turns the deploy gate RED.
--
-- bind_l2_exact_inputs(uuid, jsonb) after this change differs from the live definition by exactly ONE hunk (bind_patch.py): GRANT SELECT on every pg_temp shadow the
-- function created (owned by the function owner) to data_plane_builder, before the bind receipt is created. The full definition follows.
-- live md5 7bf8987517a7b76bd7ffae1c2bcf32ee -> patched md5 fe428d35f24ba8e54602b89ad76f3472; patched sha256 (= the new attestation digest) 2d161048f05cebeef89548084db00306e517cd309a219a342de284de690a797a
--
-- STATEMENT (run as data_plane_l2_owner), followed by the re-attestation:
CREATE OR REPLACE FUNCTION public.bind_l2_exact_inputs(p_chart_id uuid, p_dependency_vector jsonb)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'pg_temp'
AS $function$
DECLARE
  v_table text;
  v_vector_digest text;
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L2 input binding requires direct data_plane_builder authentication';
  END IF;
  IF jsonb_typeof(p_dependency_vector) <> 'array'
     OR jsonb_array_length(p_dependency_vector) = 0
     OR EXISTS (
       SELECT 1 FROM jsonb_array_elements(p_dependency_vector) d
       GROUP BY d->>'layer', d->>'asset_id'
       HAVING count(*) <> 1
     ) THEN
    RAISE EXCEPTION 'L2 input binding requires a non-empty unique dependency vector';
  END IF;
  IF (SELECT count(*) FROM jsonb_array_elements(p_dependency_vector)) <>
     (SELECT count(*) FROM jsonb_array_elements(p_dependency_vector) d
       WHERE EXISTS (
         SELECT 1 FROM public.l1_data_plane_generation_heads h
         WHERE d->>'layer'='L1' AND h.chart_id=p_chart_id
           AND h.asset_id=d->>'asset_id' AND h.current_generation_id=d->>'generation_id'
       ) OR EXISTS (
         SELECT 1 FROM public.l2_data_plane_generation_heads h
         WHERE d->>'layer'='L2' AND h.chart_id=p_chart_id
           AND h.asset_id=d->>'asset_id' AND h.current_generation_id=d->>'generation_id'
       )) THEN
    RAISE EXCEPTION 'L2 input vector does not match every selected protected head';
  END IF;
  PERFORM 1 FROM public.l1_data_plane_generation_heads h
    JOIN jsonb_array_elements(p_dependency_vector) d
      ON d->>'layer'='L1' AND d->>'asset_id'=h.asset_id
     AND d->>'generation_id'=h.current_generation_id
    WHERE h.chart_id=p_chart_id FOR SHARE OF h;
  PERFORM 1 FROM public.l2_data_plane_generation_heads h
    JOIN jsonb_array_elements(p_dependency_vector) d
      ON d->>'layer'='L2' AND d->>'asset_id'=h.asset_id
     AND d->>'generation_id'=h.current_generation_id
    WHERE h.chart_id=p_chart_id FOR SHARE OF h;
  FOR v_table IN
    SELECT DISTINCT c.relname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT t.tgisinternal AND t.tgname = 'l1_data_plane_capture'
      AND n.nspname = 'public'
    UNION SELECT 'chart_dashas'
  LOOP
    EXECUTE format('DROP TABLE IF EXISTS pg_temp.%I', v_table);
    IF v_table = 'chart_dashas' THEN
      EXECUTE format(
        'CREATE TEMP TABLE %I ON COMMIT DROP AS '
        'SELECT (latest.source_row).* FROM ('
        ' SELECT DISTINCT ON ((s.source_row).dasha_row_id) s.source_row,'
        '        s.captured_at, s.dasha_snapshot_id'
        ' FROM public.l1_data_plane_dasha_snapshots s'
        ' JOIN jsonb_array_elements(%L::jsonb) d'
        '   ON d->>''layer'' = ''L1'' AND d->>''asset_id'' = s.asset_id'
        '  AND d->>''generation_id'' = s.generation_id'
        ' WHERE s.chart_id = %L::uuid'
        ' ORDER BY (s.source_row).dasha_row_id, s.captured_at DESC,'
        '          s.dasha_snapshot_id DESC) latest',
        v_table, p_dependency_vector::text, p_chart_id::text
      );
    ELSE
      EXECUTE format(
        'CREATE TEMP TABLE %I ON COMMIT DROP AS '
        'SELECT (jsonb_populate_record(NULL::public.%I, latest.source_row_jsonb)).* '
        'FROM ('
        ' SELECT DISTINCT ON (s.row_identity) s.row_identity, s.source_row_jsonb,'
        '        s.captured_at, s.snapshot_id'
        ' FROM public.l1_data_plane_row_snapshots s'
        ' JOIN jsonb_array_elements(%L::jsonb) d'
        '   ON d->>''layer'' = ''L1'' AND d->>''asset_id'' = s.asset_id'
        '  AND d->>''generation_id'' = s.generation_id'
        ' WHERE s.chart_id = %L::uuid AND s.source_table = %L'
        ' ORDER BY s.row_identity, s.captured_at DESC, s.snapshot_id DESC) latest',
        v_table, v_table, p_dependency_vector::text, p_chart_id::text, v_table
      );
    END IF;
  END LOOP;

  FOR v_table IN
    SELECT DISTINCT source_table
    FROM public.l2_data_plane_asset_outputs
    ORDER BY source_table
  LOOP
    IF to_regclass('public.' || v_table) IS NULL THEN
      RAISE EXCEPTION 'protected L2 input relation public.% is absent', v_table;
    END IF;
    EXECUTE format('DROP TABLE IF EXISTS pg_temp.%I', v_table);
    EXECUTE format(
      'CREATE TEMP TABLE %I ON COMMIT DROP AS '
      'SELECT (jsonb_populate_record(NULL::public.%I, latest.source_row_jsonb)).* '
      'FROM ('
      ' SELECT DISTINCT ON (s.row_identity) s.row_identity, s.source_row_jsonb,'
      '        s.captured_at, s.snapshot_id'
      ' FROM public.l2_data_plane_row_snapshots s'
      ' JOIN jsonb_array_elements(%L::jsonb) d'
      '   ON d->>''layer'' = ''L2'' AND d->>''asset_id'' = s.asset_id'
      '  AND d->>''generation_id'' = s.generation_id'
      ' JOIN public.l2_data_plane_asset_outputs o'
      '   ON o.asset_id = s.asset_id AND o.source_table = s.source_table'
      ' WHERE s.chart_id = %L::uuid AND s.source_table = %L'
      ' ORDER BY s.row_identity, s.captured_at DESC, s.snapshot_id DESC) latest',
      v_table, v_table, p_dependency_vector::text, p_chart_id::text, v_table
    );
  END LOOP;
  -- 1272: the pipeline login must be able to READ the shadows this function creates (they are owned by the function owner and carry no ACL).
  -- The grant goes to the one login this function already requires (session_user = data_plane_builder); other sessions cannot see these temp
  -- tables and they drop at commit. The bind receipt is NOT granted.
  FOR v_table IN
    SELECT c.relname FROM pg_class c
    WHERE c.relnamespace = pg_my_temp_schema() AND c.relkind = 'r'
      AND pg_get_userbyid(c.relowner) = current_user
      AND c.relname <> 'l2_data_plane_bind_receipt'
    ORDER BY c.relname
  LOOP
    EXECUTE format('GRANT SELECT ON pg_temp.%I TO data_plane_builder', v_table);
  END LOOP;
  v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');
  DROP TABLE IF EXISTS pg_temp.l2_data_plane_bind_receipt;
  CREATE TEMP TABLE l2_data_plane_bind_receipt (
    chart_id uuid PRIMARY KEY,
    dependency_vector_digest text NOT NULL,
    manifest_count integer NOT NULL
  ) ON COMMIT DROP;
  INSERT INTO pg_temp.l2_data_plane_bind_receipt
  SELECT p_chart_id, v_vector_digest,
         (SELECT count(DISTINCT source_table) FROM public.l2_data_plane_asset_outputs);
END;
$function$;

-- re-attestation (same transaction; the immutability trigger is disabled and re-enabled around the UPDATE; rowcount must be 1):
-- ALTER TABLE public.l2_data_plane_function_attestations DISABLE TRIGGER l2_data_plane_function_attestations_immutable;
-- UPDATE public.l2_data_plane_function_attestations a SET definition_digest = encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') FROM pg_proc p WHERE a.function_signature='bind_l2_exact_inputs(uuid,jsonb)' AND p.oid=to_regprocedure('public.'||a.function_signature);
-- ALTER TABLE public.l2_data_plane_function_attestations ENABLE TRIGGER l2_data_plane_function_attestations_immutable;
