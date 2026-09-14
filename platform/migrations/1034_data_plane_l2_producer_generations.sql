-- 1034_data_plane_l2_producer_generations.sql
-- DP-SD-015: exact-context L2 producer generations, immutable row history,
-- deterministic replay, selection and rollback. No row is backfilled and no
-- L3 activation authority is introduced.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.data_plane_l2_producer_generations (
  chart_id                    uuid NOT NULL,
  asset_id                    text NOT NULL,
  generation_id              text NOT NULL,
  correction_of_generation_id text,
  initial_build_id            text NOT NULL,
  contract_version            text NOT NULL,
  accepted_l0_release         text NOT NULL,
  accepted_l1_terminal        text NOT NULL,
  calculation_context_id      text NOT NULL,
  calculation_context_jsonb   jsonb NOT NULL,
  dependency_vector_jsonb     jsonb NOT NULL,
  producer_role               text NOT NULL,
  source_digest               text NOT NULL CHECK (source_digest ~ '^[0-9a-f]{64}$'),
  expected_partitions         integer NOT NULL CHECK (expected_partitions > 0),
  completed_partitions        integer NOT NULL DEFAULT 0 CHECK (completed_partitions >= 0),
  temporal_semantics_status   text NOT NULL DEFAULT 'UNAVAILABLE_AT_L2'
                              CHECK (temporal_semantics_status = 'UNAVAILABLE_AT_L2'),
  state                       text NOT NULL DEFAULT 'building'
                              CHECK (state IN ('building', 'complete')),
  semantic_output_digest      text,
  opened_at                   timestamptz NOT NULL DEFAULT clock_timestamp(),
  completed_at                timestamptz,
  PRIMARY KEY (chart_id, asset_id, generation_id),
  CHECK (jsonb_typeof(calculation_context_jsonb) = 'object'),
  CHECK (jsonb_typeof(dependency_vector_jsonb) = 'array'),
  CHECK (completed_partitions <= expected_partitions),
  CHECK (
    (state = 'building' AND completed_at IS NULL AND semantic_output_digest IS NULL)
    OR
    (state = 'complete' AND completed_at IS NOT NULL
     AND semantic_output_digest ~ '^[0-9a-f]{64}$')
  )
);

CREATE TABLE IF NOT EXISTS public.l2_data_plane_generation_partitions (
  chart_id              uuid NOT NULL,
  asset_id              text NOT NULL,
  generation_id         text NOT NULL,
  partition_key         text NOT NULL,
  rows_inserted         bigint NOT NULL CHECK (rows_inserted >= 0),
  rows_updated          bigint NOT NULL CHECK (rows_updated >= 0),
  rows_skipped          bigint NOT NULL CHECK (rows_skipped >= 0),
  semantic_output_digest text NOT NULL CHECK (semantic_output_digest ~ '^[0-9a-f]{64}$'),
  completed_at          timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (chart_id, asset_id, generation_id, partition_key),
  FOREIGN KEY (chart_id, asset_id, generation_id)
    REFERENCES public.data_plane_l2_producer_generations(chart_id, asset_id, generation_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.l2_data_plane_generation_runs (
  chart_id       uuid NOT NULL,
  asset_id       text NOT NULL,
  generation_id text NOT NULL,
  partition_key text NOT NULL,
  build_id       text NOT NULL,
  rows_inserted  bigint NOT NULL CHECK (rows_inserted >= 0),
  rows_updated   bigint NOT NULL CHECK (rows_updated >= 0),
  rows_skipped   bigint NOT NULL CHECK (rows_skipped >= 0),
  replayed_at    timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (chart_id, asset_id, generation_id, partition_key, build_id),
  FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
    REFERENCES public.l2_data_plane_generation_partitions(
      chart_id, asset_id, generation_id, partition_key
    ) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.l2_data_plane_partition_contexts (
  chart_id                   uuid NOT NULL,
  asset_id                   text NOT NULL,
  generation_id             text NOT NULL,
  partition_key              text NOT NULL,
  calculation_context_id     text NOT NULL,
  calculation_context_jsonb  jsonb NOT NULL,
  PRIMARY KEY (chart_id, asset_id, generation_id, partition_key),
  FOREIGN KEY (chart_id, asset_id, generation_id)
    REFERENCES public.data_plane_l2_producer_generations(chart_id, asset_id, generation_id)
    ON DELETE RESTRICT,
  CHECK (jsonb_typeof(calculation_context_jsonb) = 'object')
);

CREATE TABLE IF NOT EXISTS public.l2_data_plane_row_snapshots (
  snapshot_id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                    uuid NOT NULL,
  asset_id                    text NOT NULL,
  generation_id              text NOT NULL,
  partition_key               text NOT NULL,
  source_table                text NOT NULL,
  row_identity               text NOT NULL,
  calculation_context_id      text NOT NULL,
  calculation_context_jsonb   jsonb NOT NULL,
  source_dependencies_jsonb   jsonb NOT NULL,
  producer_role               text NOT NULL,
  semantic_payload_jsonb      jsonb NOT NULL,
  source_row_jsonb            jsonb NOT NULL,
  semantic_digest             text NOT NULL CHECK (semantic_digest ~ '^[0-9a-f]{64}$'),
  captured_at                 timestamptz NOT NULL DEFAULT clock_timestamp(),
  FOREIGN KEY (chart_id, asset_id, generation_id)
    REFERENCES public.data_plane_l2_producer_generations(chart_id, asset_id, generation_id)
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS l2_data_plane_snapshot_latest_idx
  ON public.l2_data_plane_row_snapshots
  (chart_id, asset_id, generation_id, partition_key, source_table, row_identity,
   captured_at DESC, snapshot_id DESC);

CREATE TABLE IF NOT EXISTS public.l2_data_plane_generation_heads (
  chart_id               uuid NOT NULL,
  asset_id               text NOT NULL,
  current_generation_id  text NOT NULL,
  previous_generation_id text,
  selected_at            timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (chart_id, asset_id),
  FOREIGN KEY (chart_id, asset_id, current_generation_id)
    REFERENCES public.data_plane_l2_producer_generations(chart_id, asset_id, generation_id)
    ON DELETE RESTRICT
);

-- Static ownership manifest used to build exact, transaction-local L2 input
-- relations. It deliberately records even output tables whose selected
-- generation has zero rows, so an empty exact generation cannot fall through
-- to legacy active rows. Writers direct every mutation to public.<table>;
-- unqualified reads therefore resolve to these immutable snapshots.
CREATE TABLE IF NOT EXISTS public.l2_data_plane_asset_outputs (
  asset_id     text NOT NULL,
  source_table text NOT NULL,
  PRIMARY KEY (asset_id, source_table)
);

INSERT INTO public.l2_data_plane_asset_outputs (asset_id, source_table) VALUES
  ('bo_laksana', 'bodha_msr_signals'),
  ('bo_laksana_rerank', 'bodha_msr_signals'),
  ('bo_arudha', 'bodha_msr_signals'),
  ('bo_special_lagna', 'bodha_msr_signals'),
  ('bo_sudarshana', 'bodha_msr_signals'),
  ('bo_vargottama_dhana', 'bodha_msr_signals'),
  ('bo_nakshatra_semantic', 'bodha_msr_signals'),
  ('bo_bimba', 'bodha_cgm_nodes'),
  ('bo_karanajala', 'bodha_cgm_nodes'),
  ('bo_karanajala', 'bodha_cgm_edges'),
  ('bo_karanajala', 'bodha_contradictions'),
  ('bo_cgm_paths', 'bodha_cgm_paths'),
  ('bo_cgm_motifs', 'bodha_cgm_motifs'),
  ('bo_cgm_motifs', 'bodha_cgm_sub_graphs'),
  ('bo_cgm_motifs', 'bodha_cgm_chart_topology_summary'),
  ('bo_yantra_mechanism', 'bodha_mechanisms'),
  ('bo_sangati', 'bodha_cdlm_cells'),
  ('bo_sangati', 'bodha_convergence'),
  ('bo_sangati', 'bodha_triangulation'),
  ('bo_cdlm_summary', 'bodha_cdlm_chart_summary'),
  ('bo_cdlm_summary', 'bodha_cdlm_domain_rollups'),
  ('bo_cdlm_summary', 'bodha_cdlm_pattern_clusters'),
  ('bo_pratijna', 'bodha_pratijna'),
  ('bo_upaya', 'bodha_rm_resonances'),
  ('bo_upaya', 'bodha_rm_remedy_prescriptions'),
  ('bo_upaya', 'bodha_rm_dasha_windowed_prescriptions'),
  ('bo_upaya', 'bodha_rm_chart_summary'),
  ('bo_upaya', 'bodha_rm_dosha_remedy_bundles'),
  ('bo_upaya', 'bodha_rm_pattern_remedies'),
  ('bo_samskara', 'bodha_signal_embeddings'),
  ('bo_anveshana', 'bodha_discoveries'),
  ('bo_anveshana', 'bodha_anomalies'),
  ('bo_drishti', 'bodha_question_lenses'),
  ('bo_chart_gestalt', 'bodha_chart_gestalt'),
  ('bo_pramana_mapa', 'synthesis_quality_scorecard'),
  ('bo_grounding', 'bodha_grounding_matches')
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION public.l2_data_plane_reject_immutable_change()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is append-only; % is forbidden', TG_TABLE_NAME, TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS l2_data_plane_partitions_immutable
  ON public.l2_data_plane_generation_partitions;
CREATE TRIGGER l2_data_plane_partitions_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_generation_partitions
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l2_data_plane_runs_immutable
  ON public.l2_data_plane_generation_runs;
CREATE TRIGGER l2_data_plane_runs_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_generation_runs
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l2_data_plane_partition_contexts_immutable
  ON public.l2_data_plane_partition_contexts;
CREATE TRIGGER l2_data_plane_partition_contexts_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_partition_contexts
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l2_data_plane_snapshots_immutable
  ON public.l2_data_plane_row_snapshots;
CREATE TRIGGER l2_data_plane_snapshots_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_row_snapshots
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l2_data_plane_outputs_immutable
  ON public.l2_data_plane_asset_outputs;
CREATE TRIGGER l2_data_plane_outputs_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_asset_outputs
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

CREATE OR REPLACE FUNCTION public.l2_data_plane_guard_generation_change()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'L2 producer generations are append-only';
  END IF;
  IF OLD.state = 'complete' THEN
    RAISE EXCEPTION 'completed L2 producer generation is immutable';
  END IF;
  IF ROW(NEW.chart_id, NEW.asset_id, NEW.generation_id,
            NEW.correction_of_generation_id, NEW.initial_build_id,
            NEW.contract_version, NEW.accepted_l0_release,
            NEW.accepted_l1_terminal, NEW.calculation_context_id,
            NEW.calculation_context_jsonb, NEW.dependency_vector_jsonb,
            NEW.producer_role, NEW.source_digest, NEW.expected_partitions,
            NEW.temporal_semantics_status, NEW.opened_at)
        IS DISTINCT FROM
        ROW(OLD.chart_id, OLD.asset_id, OLD.generation_id,
            OLD.correction_of_generation_id, OLD.initial_build_id,
            OLD.contract_version, OLD.accepted_l0_release,
            OLD.accepted_l1_terminal, OLD.calculation_context_id,
            OLD.calculation_context_jsonb, OLD.dependency_vector_jsonb,
            OLD.producer_role, OLD.source_digest, OLD.expected_partitions,
            OLD.temporal_semantics_status, OLD.opened_at) THEN
    RAISE EXCEPTION 'L2 generation identity/context is immutable';
  END IF;
  IF NEW.state = 'building' AND (
       NEW.completed_partitions < OLD.completed_partitions
       OR NEW.semantic_output_digest IS NOT NULL
       OR NEW.completed_at IS NOT NULL
     ) THEN
    RAISE EXCEPTION 'invalid building L2 generation progress update';
  END IF;
  IF NEW.state = 'complete' AND (
       NEW.completed_partitions <> NEW.expected_partitions
       OR NEW.semantic_output_digest IS NULL
       OR NEW.completed_at IS NULL
     ) THEN
    RAISE EXCEPTION 'incomplete L2 generation cannot transition to complete';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS l2_data_plane_generation_immutable
  ON public.data_plane_l2_producer_generations;
CREATE TRIGGER l2_data_plane_generation_immutable
BEFORE UPDATE OR DELETE ON public.data_plane_l2_producer_generations
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_guard_generation_change();

CREATE OR REPLACE FUNCTION public.l2_data_plane_strip_volatile(p_value jsonb)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE STRICT AS $$
DECLARE
  v_result jsonb;
BEGIN
  CASE jsonb_typeof(p_value)
    WHEN 'object' THEN
      SELECT COALESCE(jsonb_object_agg(key, public.l2_data_plane_strip_volatile(value)), '{}'::jsonb)
      INTO v_result
      FROM jsonb_each(p_value)
      WHERE key NOT IN (
        'build_id','generation_id','computed_at','created_at','updated_at',
        'recorded_at','scored_at','query_time','captured_at','opened_at','completed_at'
      );
      RETURN v_result;
    WHEN 'array' THEN
      SELECT COALESCE(jsonb_agg(public.l2_data_plane_strip_volatile(value)), '[]'::jsonb)
      INTO v_result FROM jsonb_array_elements(p_value);
      RETURN v_result;
    ELSE
      RETURN p_value;
  END CASE;
END;
$$;

-- Bind unqualified L1 and L2 relation reads to immutable snapshots from the
-- exact dependency vector. Every governed source relation gets a transaction-
-- local shadow table, including an empty one when that exact generation has no
-- rows. A missing snapshot therefore cannot silently fall through to a mixed
-- legacy active table. The tables disappear at transaction end. All L2 writer
-- mutations are schema-qualified to public and continue to hit active tables.
CREATE OR REPLACE FUNCTION public.bind_l2_exact_inputs(
  p_chart_id uuid,
  p_dependency_vector jsonb
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_table text;
BEGIN
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
      CONTINUE;
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
END;
$$;

CREATE OR REPLACE FUNCTION public.open_l2_data_plane_generation(
  p_chart_id uuid,
  p_asset_id text,
  p_generation_id text,
  p_partition_key text,
  p_expected_partitions integer,
  p_build_id text,
  p_correction_of_generation_id text,
  p_contract_version text,
  p_source_digest text,
  p_calculation_context jsonb,
  p_dependency_vector jsonb,
  p_producer_role text
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_existing public.data_plane_l2_producer_generations%ROWTYPE;
  v_existing_partition public.l2_data_plane_partition_contexts%ROWTYPE;
  v_dep jsonb;
  v_digest text;
  v_generation_context jsonb;
BEGIN
  IF p_asset_id NOT LIKE 'bo\_%%' ESCAPE '\'
     OR p_generation_id IS NULL OR p_generation_id = ''
     OR p_partition_key IS NULL OR p_partition_key = ''
     OR p_build_id IS NULL OR p_build_id = ''
     OR p_expected_partitions < 1 THEN
    RAISE EXCEPTION 'incomplete L2 producer generation identity';
  END IF;
  IF p_contract_version <> 'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0'
     OR p_source_digest !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'invalid L2 producer contract or source digest';
  END IF;
  IF p_calculation_context->>'chart_id' IS DISTINCT FROM p_chart_id::text
     OR p_calculation_context->>'generation_context_id' IS NULL
     OR p_calculation_context->>'calculation_context_id' IS NULL
     OR p_calculation_context->>'subject_id' IS NULL
     OR p_calculation_context->>'ayanamsha_id' IS NULL
     OR p_calculation_context->>'reference_frame' IS NULL
     OR p_calculation_context->>'varga_id' IS NULL
     OR p_calculation_context->>'partition_key' IS DISTINCT FROM p_partition_key THEN
    RAISE EXCEPTION 'incomplete or mismatched L2 calculation context';
  END IF;
  v_generation_context := p_calculation_context
    - 'calculation_context_id' - 'ayanamsha_id' - 'varga_id' - 'partition_key';
  IF jsonb_typeof(p_dependency_vector) <> 'array'
     OR jsonb_array_length(p_dependency_vector) = 0
     OR NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements(p_dependency_vector) d
       WHERE d->>'layer' = 'L1'
     ) THEN
    RAISE EXCEPTION 'L2 generation requires a non-empty L1 dependency vector';
  END IF;

  FOR v_dep IN SELECT value FROM jsonb_array_elements(p_dependency_vector) LOOP
    IF v_dep->>'layer' = 'L1' THEN
      SELECT g.semantic_output_digest INTO v_digest
      FROM public.l1_data_plane_generation_heads h
      JOIN public.l1_data_plane_generations g
        ON g.chart_id = h.chart_id AND g.asset_id = h.asset_id
       AND g.generation_id = h.current_generation_id
      WHERE h.chart_id = p_chart_id AND h.asset_id = v_dep->>'asset_id'
        AND h.current_generation_id = v_dep->>'generation_id'
        AND g.status = 'complete';
    ELSIF v_dep->>'layer' = 'L2' THEN
      SELECT g.semantic_output_digest INTO v_digest
      FROM public.l2_data_plane_generation_heads h
      JOIN public.data_plane_l2_producer_generations g
        ON g.chart_id = h.chart_id AND g.asset_id = h.asset_id
       AND g.generation_id = h.current_generation_id
      WHERE h.chart_id = p_chart_id AND h.asset_id = v_dep->>'asset_id'
        AND h.current_generation_id = v_dep->>'generation_id'
        AND g.state = 'complete';
    ELSE
      RAISE EXCEPTION 'unknown dependency layer %', v_dep->>'layer';
    END IF;
    IF v_digest IS DISTINCT FROM v_dep->>'semantic_output_digest' THEN
      RAISE EXCEPTION 'dependency %/% is absent, stale or digest-mismatched',
        v_dep->>'layer', v_dep->>'asset_id';
    END IF;
  END LOOP;

  IF p_correction_of_generation_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM public.data_plane_l2_producer_generations
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_correction_of_generation_id AND state = 'complete'
  ) THEN
    RAISE EXCEPTION 'correction predecessor % is absent or incomplete',
      p_correction_of_generation_id;
  END IF;

  INSERT INTO public.data_plane_l2_producer_generations (
    chart_id, asset_id, generation_id, correction_of_generation_id,
    initial_build_id, contract_version, accepted_l0_release,
    accepted_l1_terminal, calculation_context_id,
    calculation_context_jsonb, dependency_vector_jsonb, producer_role,
    source_digest, expected_partitions
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_correction_of_generation_id,
    p_build_id, p_contract_version,
    'f6fed12c794224329f6b3b436f8b1b814499d06d',
    '18503e9c2dbb140f5d17b4bc34a5f6d087f97c38',
    p_calculation_context->>'generation_context_id',
    v_generation_context, p_dependency_vector, p_producer_role,
    p_source_digest, p_expected_partitions
  ) ON CONFLICT (chart_id, asset_id, generation_id) DO NOTHING;

  SELECT * INTO v_existing
  FROM public.data_plane_l2_producer_generations
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id
  FOR UPDATE;
  IF v_existing.contract_version <> p_contract_version
     OR v_existing.source_digest <> p_source_digest
     OR v_existing.expected_partitions <> p_expected_partitions
     OR v_existing.calculation_context_jsonb <> v_generation_context
     OR v_existing.dependency_vector_jsonb <> p_dependency_vector
     OR v_existing.producer_role <> p_producer_role
     OR v_existing.correction_of_generation_id IS DISTINCT FROM p_correction_of_generation_id THEN
    RAISE EXCEPTION 'generation % was reopened with incompatible context', p_generation_id;
  END IF;
  IF v_existing.state = 'complete' AND NOT EXISTS (
    SELECT 1 FROM public.l2_data_plane_generation_partitions
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
  ) THEN
    RAISE EXCEPTION 'complete generation % cannot admit a new partition', p_generation_id;
  END IF;

  INSERT INTO public.l2_data_plane_partition_contexts (
    chart_id, asset_id, generation_id, partition_key,
    calculation_context_id, calculation_context_jsonb
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key,
    p_calculation_context->>'calculation_context_id', p_calculation_context
  ) ON CONFLICT DO NOTHING;
  SELECT * INTO v_existing_partition
  FROM public.l2_data_plane_partition_contexts
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id AND partition_key = p_partition_key;
  IF v_existing_partition.calculation_context_id
       <> p_calculation_context->>'calculation_context_id'
     OR v_existing_partition.calculation_context_jsonb <> p_calculation_context THEN
    RAISE EXCEPTION 'partition % was reopened with incompatible calculation context',
      p_partition_key;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.l2_data_plane_capture_row()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_asset text := current_setting('madhav.l2_asset_id', true);
  v_chart_text text := current_setting('madhav.l2_chart_id', true);
  v_generation text := current_setting('madhav.l2_generation_id', true);
  v_partition text := current_setting('madhav.l2_partition_key', true);
  v_build text := current_setting('madhav.l2_build_id', true);
  v_row jsonb := to_jsonb(NEW);
  v_semantic jsonb;
  v_identity_parts text[] := ARRAY[]::text[];
  v_identity text;
  v_key text;
  v_generation_row public.data_plane_l2_producer_generations%ROWTYPE;
  v_partition_context public.l2_data_plane_partition_contexts%ROWTYPE;
  v_digest text;
  v_existing_digest text;
BEGIN
  IF v_asset IS NULL OR v_asset = '' THEN
    RETURN NEW;
  END IF;
  IF v_chart_text IS NULL OR v_generation IS NULL OR v_partition IS NULL
     OR v_build IS NULL THEN
    RAISE EXCEPTION 'incomplete transaction-local L2 producer context';
  END IF;
  IF COALESCE(v_row->>'chart_id', '') <> v_chart_text THEN
    RAISE EXCEPTION 'writer row chart % mismatches L2 producer chart %',
      v_row->>'chart_id', v_chart_text;
  END IF;
  IF v_row ? 'build_id' AND v_row->>'build_id' IS NOT NULL
     AND v_row->>'build_id' <> v_build THEN
    RAISE EXCEPTION 'writer row build % mismatches L2 invocation build %',
      v_row->>'build_id', v_build;
  END IF;

  SELECT * INTO v_generation_row
  FROM public.data_plane_l2_producer_generations
  WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
    AND generation_id = v_generation;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'L2 generation was not opened before % write', TG_TABLE_NAME;
  END IF;
  SELECT * INTO v_partition_context
  FROM public.l2_data_plane_partition_contexts
  WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
    AND generation_id = v_generation AND partition_key = v_partition;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'L2 partition context was not opened before % write', TG_TABLE_NAME;
  END IF;
  FOREACH v_key IN ARRAY TG_ARGV LOOP
    IF NOT (v_row ? v_key) THEN
      RAISE EXCEPTION '% has no declared identity column %', TG_TABLE_NAME, v_key;
    END IF;
    v_identity_parts := array_append(
      v_identity_parts, v_key || '=' || COALESCE(v_row->>v_key, '<null>')
    );
  END LOOP;
  v_identity := array_to_string(v_identity_parts, '|');
  v_semantic := public.l2_data_plane_strip_volatile(v_row);
  v_digest := encode(digest(v_semantic::text, 'sha256'), 'hex');

  SELECT semantic_digest INTO v_existing_digest
  FROM public.l2_data_plane_row_snapshots
  WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
    AND generation_id = v_generation AND partition_key = v_partition
    AND source_table = TG_TABLE_NAME AND row_identity = v_identity
  ORDER BY captured_at DESC, snapshot_id DESC LIMIT 1;

  IF v_generation_row.state = 'complete' THEN
    IF v_existing_digest IS NULL THEN
      RAISE EXCEPTION 'complete L2 generation % cannot admit new row % %',
        v_generation, TG_TABLE_NAME, v_identity;
    END IF;
    IF v_existing_digest <> v_digest THEN
      RAISE EXCEPTION 'complete L2 generation % replay changed output for % %',
        v_generation, TG_TABLE_NAME, v_identity;
    END IF;
    RETURN NEW;
  END IF;
  IF v_existing_digest = v_digest THEN
    RETURN NEW;
  END IF;

  INSERT INTO public.l2_data_plane_row_snapshots (
    chart_id, asset_id, generation_id, partition_key, source_table,
    row_identity, calculation_context_id, calculation_context_jsonb,
    source_dependencies_jsonb, producer_role, semantic_payload_jsonb,
    source_row_jsonb, semantic_digest
  ) VALUES (
    v_chart_text::uuid, v_asset, v_generation, v_partition, TG_TABLE_NAME,
    v_identity, v_partition_context.calculation_context_id,
    v_partition_context.calculation_context_jsonb,
    v_generation_row.dependency_vector_jsonb, v_generation_row.producer_role,
    v_semantic, v_row, v_digest
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.complete_l2_data_plane_partition(
  p_chart_id uuid,
  p_asset_id text,
  p_generation_id text,
  p_partition_key text,
  p_build_id text,
  p_rows_inserted bigint,
  p_rows_updated bigint,
  p_rows_skipped bigint
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_partition_digest text;
  v_existing public.l2_data_plane_generation_partitions%ROWTYPE;
  v_completed integer;
  v_expected integer;
  v_generation_digest text;
  v_state text;
  v_existing_generation_digest text;
BEGIN
  IF p_rows_inserted < 0 OR p_rows_updated < 0 OR p_rows_skipped < 0 THEN
    RAISE EXCEPTION 'L2 producer row counts cannot be negative';
  END IF;
  SELECT encode(digest(COALESCE(jsonb_agg(
           jsonb_build_array(source_table, row_identity, semantic_digest)
           ORDER BY source_table, row_identity
         ), '[]'::jsonb)::text, 'sha256'), 'hex')
  INTO v_partition_digest
  FROM (
    SELECT DISTINCT ON (source_table, row_identity)
      source_table, row_identity, semantic_digest
    FROM public.l2_data_plane_row_snapshots
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
    ORDER BY source_table, row_identity, captured_at DESC, snapshot_id DESC
  ) latest;

  INSERT INTO public.l2_data_plane_generation_partitions (
    chart_id, asset_id, generation_id, partition_key,
    rows_inserted, rows_updated, rows_skipped, semantic_output_digest
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key,
    p_rows_inserted, p_rows_updated, p_rows_skipped, v_partition_digest
  ) ON CONFLICT DO NOTHING;

  SELECT * INTO v_existing
  FROM public.l2_data_plane_generation_partitions
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id AND partition_key = p_partition_key;
  IF ROW(v_existing.rows_inserted, v_existing.rows_updated, v_existing.rows_skipped,
         v_existing.semantic_output_digest)
     IS DISTINCT FROM
     ROW(p_rows_inserted, p_rows_updated, p_rows_skipped, v_partition_digest) THEN
    RAISE EXCEPTION 'partition % replay changed counts or semantic output', p_partition_key;
  END IF;

  INSERT INTO public.l2_data_plane_generation_runs (
    chart_id, asset_id, generation_id, partition_key, build_id,
    rows_inserted, rows_updated, rows_skipped
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key, p_build_id,
    p_rows_inserted, p_rows_updated, p_rows_skipped
  ) ON CONFLICT DO NOTHING;

  SELECT count(*), max(g.expected_partitions), max(g.state),
         max(g.semantic_output_digest)
  INTO v_completed, v_expected, v_state, v_existing_generation_digest
  FROM public.l2_data_plane_generation_partitions p
  JOIN public.data_plane_l2_producer_generations g
    USING (chart_id, asset_id, generation_id)
  WHERE p.chart_id = p_chart_id AND p.asset_id = p_asset_id
    AND p.generation_id = p_generation_id;
  IF v_completed > v_expected THEN
    RAISE EXCEPTION 'L2 generation has % partitions but expected %', v_completed, v_expected;
  END IF;
  IF v_completed < v_expected THEN
    UPDATE public.data_plane_l2_producer_generations
    SET completed_partitions = v_completed
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND state = 'building';
    RETURN;
  END IF;

  SELECT encode(digest(COALESCE(jsonb_agg(
           jsonb_build_array(partition_key, semantic_output_digest)
           ORDER BY partition_key
         ), '[]'::jsonb)::text, 'sha256'), 'hex')
  INTO v_generation_digest
  FROM public.l2_data_plane_generation_partitions
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id;
  IF v_state = 'complete' THEN
    IF v_existing_generation_digest <> v_generation_digest THEN
      RAISE EXCEPTION 'complete L2 generation replay changed generation digest';
    END IF;
  ELSE
    UPDATE public.data_plane_l2_producer_generations
    SET completed_partitions = v_completed, state = 'complete',
        semantic_output_digest = v_generation_digest,
        completed_at = clock_timestamp()
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id;
  END IF;

  INSERT INTO public.l2_data_plane_generation_heads (
    chart_id, asset_id, current_generation_id
  ) VALUES (p_chart_id, p_asset_id, p_generation_id)
  ON CONFLICT (chart_id, asset_id) DO UPDATE
  SET previous_generation_id = CASE
        WHEN public.l2_data_plane_generation_heads.current_generation_id
             <> EXCLUDED.current_generation_id
        THEN public.l2_data_plane_generation_heads.current_generation_id
        ELSE public.l2_data_plane_generation_heads.previous_generation_id
      END,
      current_generation_id = EXCLUDED.current_generation_id,
      selected_at = clock_timestamp();
END;
$$;

CREATE OR REPLACE FUNCTION public.select_l2_data_plane_generation(
  p_chart_id uuid,
  p_asset_id text,
  p_generation_id text
) RETURNS TABLE (
  source_table text,
  row_identity text,
  calculation_context_id text,
  calculation_context_jsonb jsonb,
  source_dependencies_jsonb jsonb,
  producer_role text,
  semantic_payload_jsonb jsonb,
  semantic_digest text
) LANGUAGE sql STABLE AS $$
  SELECT DISTINCT ON (s.source_table, s.row_identity)
    s.source_table, s.row_identity, s.calculation_context_id,
    s.calculation_context_jsonb, s.source_dependencies_jsonb,
    s.producer_role, s.semantic_payload_jsonb, s.semantic_digest
  FROM public.l2_data_plane_row_snapshots s
  JOIN public.data_plane_l2_producer_generations g
    USING (chart_id, asset_id, generation_id)
  WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
    AND s.generation_id = p_generation_id AND g.state = 'complete'
  ORDER BY s.source_table, s.row_identity, s.captured_at DESC, s.snapshot_id DESC
$$;

CREATE OR REPLACE FUNCTION public.rollback_l2_data_plane_generation(
  p_chart_id uuid,
  p_asset_id text,
  p_generation_id text
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_current text;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.data_plane_l2_producer_generations
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND state = 'complete'
  ) THEN
    RAISE EXCEPTION 'rollback target % is absent or incomplete', p_generation_id;
  END IF;
  SELECT current_generation_id INTO v_current
  FROM public.l2_data_plane_generation_heads
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id FOR UPDATE;
  IF v_current IS NULL THEN
    RAISE EXCEPTION 'L2 asset % has no selected generation', p_asset_id;
  END IF;
  UPDATE public.l2_data_plane_generation_heads
  SET current_generation_id = p_generation_id,
      previous_generation_id = v_current,
      selected_at = clock_timestamp()
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id;
END;
$$;

CREATE OR REPLACE VIEW public.l2_data_plane_current_rows AS
SELECT DISTINCT ON (s.chart_id, s.asset_id, s.source_table, s.row_identity) s.*
FROM public.l2_data_plane_generation_heads h
JOIN public.l2_data_plane_row_snapshots s
  ON s.chart_id = h.chart_id AND s.asset_id = h.asset_id
 AND s.generation_id = h.current_generation_id
ORDER BY s.chart_id, s.asset_id, s.source_table, s.row_identity,
         s.captured_at DESC, s.snapshot_id DESC;

CREATE OR REPLACE FUNCTION public.l2_data_plane_install_capture_trigger(
  p_table text,
  p_identity_columns text[]
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_args text;
BEGIN
  IF to_regclass('public.' || p_table) IS NULL THEN
    RETURN;
  END IF;
  SELECT string_agg(quote_literal(value), ',') INTO v_args
  FROM unnest(p_identity_columns) value;
  EXECUTE format('DROP TRIGGER IF EXISTS l2_data_plane_capture ON public.%I', p_table);
  EXECUTE format(
    'CREATE TRIGGER l2_data_plane_capture AFTER INSERT OR UPDATE ON public.%I '
    'FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_capture_row(%s)',
    p_table, v_args
  );
END;
$$;

SELECT public.l2_data_plane_install_capture_trigger('bodha_msr_signals', ARRAY['signal_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cgm_nodes', ARRAY['node_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cgm_edges', ARRAY['edge_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_contradictions', ARRAY['contradiction_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cgm_paths', ARRAY['path_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cgm_motifs', ARRAY['motif_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cgm_sub_graphs', ARRAY['subgraph_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cgm_chart_topology_summary', ARRAY['summary_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_mechanisms', ARRAY['mechanism_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cdlm_cells', ARRAY['cell_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_convergence', ARRAY['convergence_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_triangulation', ARRAY['triangulation_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cdlm_chart_summary', ARRAY['summary_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cdlm_domain_rollups', ARRAY['rollup_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_cdlm_pattern_clusters', ARRAY['pattern_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_pratijna', ARRAY['pratijna_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_rm_resonances', ARRAY['resonance_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_rm_remedy_prescriptions', ARRAY['prescription_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_rm_dasha_windowed_prescriptions', ARRAY['window_prescription_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_rm_chart_summary', ARRAY['summary_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_rm_dosha_remedy_bundles', ARRAY['bundle_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_rm_pattern_remedies', ARRAY['pattern_remedy_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_signal_embeddings', ARRAY['signal_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_discoveries', ARRAY['discovery_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_anomalies', ARRAY['anomaly_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_question_lenses', ARRAY['lens_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_chart_gestalt', ARRAY['gestalt_id']);
SELECT public.l2_data_plane_install_capture_trigger('synthesis_quality_scorecard', ARRAY['scorecard_id']);
SELECT public.l2_data_plane_install_capture_trigger('bodha_grounding_matches', ARRAY['match_id']);

COMMENT ON TABLE public.data_plane_l2_producer_generations IS
  'DP-SD-015 exact upstream context and immutable L2 producer generations; no L3 activation authority.';

COMMIT;
