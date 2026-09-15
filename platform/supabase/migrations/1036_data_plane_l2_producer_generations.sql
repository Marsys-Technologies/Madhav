-- Migration 1036: data_plane_l2_producer_generations
-- DP-SD-015: exact-context L2 producer generations, immutable row history,
-- deterministic replay, selection and rollback. No row is backfilled and no
-- L3 activation authority is introduced.

BEGIN;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
    RAISE EXCEPTION 'E1036_PREFLIGHT_EXTENSION: pgcrypto must be installed by the DBA preflight';
  END IF;
END $$;

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
  observed_row_count bigint NOT NULL CHECK (observed_row_count >= 0),
  semantic_output_digest text NOT NULL CHECK (semantic_output_digest ~ '^[0-9a-f]{64}$'),
  replayed_at    timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (chart_id, asset_id, generation_id, partition_key, build_id),
  FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
    REFERENCES public.l2_data_plane_generation_partitions(
      chart_id, asset_id, generation_id, partition_key
    ) ON DELETE RESTRICT
);

ALTER TABLE public.l2_data_plane_generation_runs
  ADD COLUMN IF NOT EXISTS observed_row_count bigint,
  ADD COLUMN IF NOT EXISTS semantic_output_digest text;

-- A prior local application of this still-unreleased migration may already
-- have installed the append-only trigger. Remove it only inside this migration
-- transaction so the compatibility backfill below can run; it is recreated
-- before COMMIT.
DROP TRIGGER IF EXISTS l2_data_plane_runs_immutable
  ON public.l2_data_plane_generation_runs;

UPDATE public.l2_data_plane_generation_runs r
SET observed_row_count = COALESCE(r.observed_row_count, 0),
    semantic_output_digest = COALESCE(
      r.semantic_output_digest,
      p.semantic_output_digest,
      encode(digest('[]', 'sha256'), 'hex')
    )
FROM public.l2_data_plane_generation_partitions p
WHERE p.chart_id = r.chart_id AND p.asset_id = r.asset_id
  AND p.generation_id = r.generation_id AND p.partition_key = r.partition_key
  AND (r.observed_row_count IS NULL OR r.semantic_output_digest IS NULL);

UPDATE public.l2_data_plane_generation_runs
SET observed_row_count = COALESCE(observed_row_count, 0),
    semantic_output_digest = COALESCE(
      semantic_output_digest, encode(digest('[]', 'sha256'), 'hex')
    )
WHERE observed_row_count IS NULL OR semantic_output_digest IS NULL;

ALTER TABLE public.l2_data_plane_generation_runs
  ALTER COLUMN observed_row_count SET NOT NULL,
  ALTER COLUMN semantic_output_digest SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l2_generation_runs_observed_count_check'
      AND conrelid = 'public.l2_data_plane_generation_runs'::regclass
  ) THEN
    ALTER TABLE public.l2_data_plane_generation_runs
      ADD CONSTRAINT l2_generation_runs_observed_count_check
      CHECK (observed_row_count >= 0);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l2_generation_runs_digest_check'
      AND conrelid = 'public.l2_data_plane_generation_runs'::regclass
  ) THEN
    ALTER TABLE public.l2_data_plane_generation_runs
      ADD CONSTRAINT l2_generation_runs_digest_check
      CHECK (semantic_output_digest ~ '^[0-9a-f]{64}$');
  END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS public.l2_data_plane_run_rows (
  chart_id       uuid NOT NULL,
  asset_id       text NOT NULL,
  generation_id text NOT NULL,
  partition_key text NOT NULL,
  build_id       text NOT NULL,
  source_table   text NOT NULL,
  row_identity  text NOT NULL,
  semantic_digest text NOT NULL CHECK (semantic_digest ~ '^[0-9a-f]{64}$'),
  observed_at   timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (
    chart_id, asset_id, generation_id, partition_key, build_id,
    source_table, row_identity
  ),
  FOREIGN KEY (chart_id, asset_id, generation_id)
    REFERENCES public.data_plane_l2_producer_generations(chart_id, asset_id, generation_id)
    ON DELETE RESTRICT
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

-- A calculation partition may be replayed by another build, but every concrete
-- build/partition pair must first be admitted by open_l2_data_plane_generation.
-- This prevents an arbitrary build id from manufacturing an empty replay receipt.
CREATE TABLE IF NOT EXISTS public.l2_data_plane_run_intents (
  chart_id       uuid NOT NULL,
  asset_id       text NOT NULL,
  generation_id text NOT NULL,
  partition_key text NOT NULL,
  build_id       text NOT NULL,
  opened_at      timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (chart_id, asset_id, generation_id, partition_key, build_id),
  FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
    REFERENCES public.l2_data_plane_partition_contexts(
      chart_id, asset_id, generation_id, partition_key
    ) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.l2_data_plane_input_bind_receipts (
  chart_id uuid NOT NULL,
  asset_id text NOT NULL,
  generation_id text NOT NULL,
  partition_key text NOT NULL,
  build_id text NOT NULL,
  dependency_vector_digest text NOT NULL CHECK (dependency_vector_digest ~ '^[0-9a-f]{64}$'),
  bound_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (chart_id, asset_id, generation_id, partition_key, build_id),
  FOREIGN KEY (chart_id, asset_id, generation_id, partition_key, build_id)
    REFERENCES public.l2_data_plane_run_intents(
      chart_id, asset_id, generation_id, partition_key, build_id
    ) ON DELETE RESTRICT
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

DO $l2_partition_fks$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l2_generation_partitions_declared_fk'
      AND conrelid = 'public.l2_data_plane_generation_partitions'::regclass
  ) THEN
    ALTER TABLE public.l2_data_plane_generation_partitions
      ADD CONSTRAINT l2_generation_partitions_declared_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
      REFERENCES public.l2_data_plane_partition_contexts(
        chart_id, asset_id, generation_id, partition_key
      ) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l2_generation_runs_intent_fk'
      AND conrelid = 'public.l2_data_plane_generation_runs'::regclass
  ) THEN
    ALTER TABLE public.l2_data_plane_generation_runs
      ADD CONSTRAINT l2_generation_runs_intent_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key, build_id)
      REFERENCES public.l2_data_plane_run_intents(
        chart_id, asset_id, generation_id, partition_key, build_id
      ) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l2_run_rows_intent_fk'
      AND conrelid = 'public.l2_data_plane_run_rows'::regclass
  ) THEN
    ALTER TABLE public.l2_data_plane_run_rows
      ADD CONSTRAINT l2_run_rows_intent_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key, build_id)
      REFERENCES public.l2_data_plane_run_intents(
        chart_id, asset_id, generation_id, partition_key, build_id
      ) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l2_row_snapshots_declared_fk'
      AND conrelid = 'public.l2_data_plane_row_snapshots'::regclass
  ) THEN
    ALTER TABLE public.l2_data_plane_row_snapshots
      ADD CONSTRAINT l2_row_snapshots_declared_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
      REFERENCES public.l2_data_plane_partition_contexts(
        chart_id, asset_id, generation_id, partition_key
      ) ON DELETE RESTRICT;
  END IF;
END
$l2_partition_fks$;

-- bo_samvada is retained as a passive registry identity. Its legacy view is a
-- shared serving projection, not output produced by this per-chart run. Make
-- zero rows the explicit valid receipt, prevent the runner's no-op probe from
-- promoting legacy view rows, and retire the serving-view digest specification.
-- The direct legacy owner performs this exact row transition in the one-shot
-- DBA preflight; this protected-owner migration only attests it.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.asset_registry WHERE asset_id='bo_samvada'
    AND (target_floor IS DISTINCT FROM 0 OR count_sql IS DISTINCT FROM 'SELECT 0 AS count')) THEN
    RAISE EXCEPTION 'E1036_PREFLIGHT_BO_SAMVADA: registry transition was not performed by DBA preflight';
  END IF;
  IF EXISTS (SELECT 1 FROM public.asset_output_digest_specs WHERE asset_id='bo_samvada' AND retired_at IS NULL) THEN
    RAISE EXCEPTION 'E1036_PREFLIGHT_BO_SAMVADA: digest specification was not retired by DBA preflight';
  END IF;
END;
$$;

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

CREATE OR REPLACE FUNCTION public.l2_data_plane_guard_completed_run_rows()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_chart uuid := COALESCE(NEW.chart_id, OLD.chart_id);
  v_asset text := COALESCE(NEW.asset_id, OLD.asset_id);
  v_generation text := COALESCE(NEW.generation_id, OLD.generation_id);
  v_partition text := COALESCE(NEW.partition_key, OLD.partition_key);
  v_build text := COALESCE(NEW.build_id, OLD.build_id);
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.l2_data_plane_generation_runs
    WHERE chart_id = v_chart AND asset_id = v_asset
      AND generation_id = v_generation AND partition_key = v_partition
      AND build_id = v_build
  ) THEN
    RAISE EXCEPTION 'completed L2 replay run rows are immutable';
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS l2_data_plane_run_rows_immutable
  ON public.l2_data_plane_run_rows;
CREATE TRIGGER l2_data_plane_run_rows_immutable
BEFORE INSERT OR UPDATE OR DELETE ON public.l2_data_plane_run_rows
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_guard_completed_run_rows();

DROP TRIGGER IF EXISTS l2_data_plane_partition_contexts_immutable
  ON public.l2_data_plane_partition_contexts;
CREATE TRIGGER l2_data_plane_partition_contexts_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_partition_contexts
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l2_data_plane_run_intents_immutable
  ON public.l2_data_plane_run_intents;
CREATE TRIGGER l2_data_plane_run_intents_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_run_intents
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l2_data_plane_bind_receipts_immutable
  ON public.l2_data_plane_input_bind_receipts;
CREATE TRIGGER l2_data_plane_bind_receipts_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_input_bind_receipts
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
DECLARE
  v_recorded_partitions integer;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.state <> 'building'
       OR NEW.completed_partitions <> 0
       OR NEW.semantic_output_digest IS NOT NULL
       OR NEW.completed_at IS NOT NULL THEN
      RAISE EXCEPTION 'L2 producer generation must be inserted in empty building state';
    END IF;
    RETURN NEW;
  END IF;
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

  SELECT count(*) INTO v_recorded_partitions
  FROM public.l2_data_plane_generation_partitions
  WHERE chart_id = OLD.chart_id AND asset_id = OLD.asset_id
    AND generation_id = OLD.generation_id;
  IF NEW.completed_partitions <> v_recorded_partitions THEN
    RAISE EXCEPTION 'L2 generation progress must equal recorded partitions';
  END IF;
  IF NEW.state = 'building' AND (
       NEW.semantic_output_digest IS NOT NULL
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
BEFORE INSERT OR UPDATE OR DELETE ON public.data_plane_l2_producer_generations
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

CREATE OR REPLACE FUNCTION public.l2_data_plane_jsonb_has_nonfinite(p_value jsonb)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
  v_child jsonb;
  v_scalar text;
BEGIN
  CASE jsonb_typeof(p_value)
    WHEN 'object' THEN
      FOR v_child IN SELECT value FROM jsonb_each(p_value) LOOP
        IF public.l2_data_plane_jsonb_has_nonfinite(v_child) THEN RETURN true; END IF;
      END LOOP;
    WHEN 'array' THEN
      FOR v_child IN SELECT value FROM jsonb_array_elements(p_value) LOOP
        IF public.l2_data_plane_jsonb_has_nonfinite(v_child) THEN RETURN true; END IF;
      END LOOP;
    WHEN 'string' THEN
      v_scalar := lower(p_value #>> '{}');
      RETURN v_scalar IN ('nan', 'infinity', '-infinity', 'inf', '-inf');
    ELSE
      RETURN false;
  END CASE;
  RETURN false;
END;
$$;

CREATE OR REPLACE FUNCTION public.l2_data_plane_dependency_topology_matches(
  p_asset_id text,
  p_dependency_vector jsonb
) RETURNS boolean LANGUAGE sql STABLE AS $$
  WITH RECURSIVE expected(asset_id) AS (
    SELECT unnest(COALESCE(r.depends_on, ARRAY[]::text[]))
    FROM public.asset_registry r WHERE r.asset_id = p_asset_id
    UNION
    SELECT unnest(COALESCE(r.depends_on, ARRAY[]::text[]))
    FROM public.asset_registry r
    JOIN expected e ON e.asset_id = r.asset_id
  ), expected_keys AS (
    SELECT CASE WHEN asset_id LIKE 'ga\_%%' ESCAPE '\' THEN 'L1' ELSE 'L2' END AS layer,
           asset_id
    FROM expected
    WHERE asset_id <> p_asset_id
      AND (asset_id LIKE 'ga\_%%' ESCAPE '\' OR asset_id LIKE 'bo\_%%' ESCAPE '\')
  ), provided_keys AS (
    SELECT value->>'layer' AS layer, value->>'asset_id' AS asset_id
    FROM jsonb_array_elements(p_dependency_vector)
  )
  SELECT jsonb_typeof(p_dependency_vector) = 'array'
     AND jsonb_array_length(p_dependency_vector) = (SELECT count(*) FROM expected_keys)
     AND NOT EXISTS (
       (SELECT layer, asset_id FROM expected_keys
        EXCEPT SELECT layer, asset_id FROM provided_keys)
       UNION ALL
       (SELECT layer, asset_id FROM provided_keys
        EXCEPT SELECT layer, asset_id FROM expected_keys)
     )
$$;

CREATE OR REPLACE FUNCTION public.l2_data_plane_generation_is_compatible(
  p_chart_id uuid,
  p_asset_id text,
  p_generation_id text
) RETURNS boolean LANGUAGE plpgsql STABLE AS $$
DECLARE
  v_vector jsonb;
  v_dep jsonb;
  v_digest text;
BEGIN
  SELECT dependency_vector_jsonb INTO v_vector
  FROM public.data_plane_l2_producer_generations
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id AND state = 'complete';
  IF NOT FOUND THEN RETURN false; END IF;
  IF NOT public.l2_data_plane_dependency_topology_matches(p_asset_id, v_vector) THEN
    RETURN false;
  END IF;

  FOR v_dep IN SELECT value FROM jsonb_array_elements(v_vector) LOOP
    v_digest := NULL;
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
      RETURN false;
    END IF;
    IF v_digest IS DISTINCT FROM v_dep->>'semantic_output_digest' THEN
      RETURN false;
    END IF;
  END LOOP;
  RETURN true;
END;
$$;

-- Delete-then-insert is permitted only while it remains inside L2. Discover
-- every current FK from the catalogue so a future L3/L4 reference also fails
-- closed without relying on a stale hand-maintained table list.
CREATE OR REPLACE FUNCTION public.assert_l2_msr_delete_safe(
  p_chart_id uuid,
  p_ayanamsha_ids text[] DEFAULT NULL,
  p_signal_type_ids text[] DEFAULT NULL,
  p_signal_type_classes text[] DEFAULT NULL
) RETURNS void LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  v_fk record;
  v_exists boolean;
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L2 MSR delete authorization requires direct data_plane_builder authentication';
  END IF;
  -- Parent FOR UPDATE conflicts with the KEY SHARE lock acquired by a foreign-
  -- key insert. Holding the exact replacement scope through the later DELETE
  -- closes the check/delete race for CASCADE, SET NULL and future FK actions.
  PERFORM 1
  FROM public.bodha_msr_signals s
  WHERE s.chart_id = p_chart_id
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
      ')',
      v_fk.schema_name, v_fk.table_name, v_fk.column_name
    ) INTO v_exists
      USING p_chart_id, p_ayanamsha_ids, p_signal_type_ids, p_signal_type_classes;
    IF v_exists THEN
      RAISE EXCEPTION
        'L2 MSR replacement blocked by cross-layer dependent rows in %.%',
        v_fk.schema_name, v_fk.table_name;
    END IF;
  END LOOP;
  DROP TABLE IF EXISTS pg_temp.l2_data_plane_msr_delete_receipt;
  CREATE TEMP TABLE l2_data_plane_msr_delete_receipt (
    chart_id uuid NOT NULL,
    signal_id uuid PRIMARY KEY
  ) ON COMMIT DROP;
  INSERT INTO pg_temp.l2_data_plane_msr_delete_receipt(chart_id, signal_id)
  SELECT s.chart_id, s.signal_id
  FROM public.bodha_msr_signals s
  WHERE s.chart_id = p_chart_id
    AND (p_ayanamsha_ids IS NULL OR s.ayanamsha_id = ANY(p_ayanamsha_ids))
    AND (p_signal_type_ids IS NULL OR s.signal_type_id = ANY(p_signal_type_ids))
    AND (p_signal_type_classes IS NULL OR s.signal_type_class = ANY(p_signal_type_classes));
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
) RETURNS void LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
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
) RETURNS void LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  v_existing public.data_plane_l2_producer_generations%ROWTYPE;
  v_existing_partition public.l2_data_plane_partition_contexts%ROWTYPE;
  v_dep jsonb;
  v_digest text;
  v_generation_context jsonb;
  v_declared integer;
  v_vector_digest text;
  v_receipt_owner text;
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L2 generation open requires direct data_plane_builder authentication';
  END IF;
  IF current_setting('madhav.l2_asset_id', true) IS DISTINCT FROM p_asset_id
     OR current_setting('madhav.l2_chart_id', true) IS DISTINCT FROM p_chart_id::text
     OR current_setting('madhav.l2_generation_id', true) IS DISTINCT FROM p_generation_id
     OR current_setting('madhav.l2_partition_key', true) IS DISTINCT FROM p_partition_key
     OR current_setting('madhav.l2_build_id', true) IS DISTINCT FROM p_build_id
     OR current_setting('madhav.l2_contract_version', true) IS DISTINCT FROM p_contract_version THEN
    RAISE EXCEPTION 'L2 transaction context does not match the requested generation';
  END IF;
  IF p_build_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
     OR NOT EXISTS (
       SELECT 1
       FROM public.build_runs br
       JOIN public.build_run_assets bra ON bra.run_id = br.id
       WHERE br.id = p_build_id::uuid
         AND br.chart_id = p_chart_id
         AND br.state = 'running'
         AND bra.asset_id = p_asset_id
         AND bra.state = 'building'
     ) THEN
    RAISE EXCEPTION 'L2 generation is not bound to the active build run/asset';
  END IF;
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
  v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');
  IF to_regclass('pg_temp.l2_data_plane_bind_receipt') IS NULL THEN
    RAISE EXCEPTION 'L2 generation open requires an exact-input bind receipt';
  END IF;
  SELECT pg_get_userbyid(relowner) INTO v_receipt_owner
  FROM pg_class WHERE oid = to_regclass('pg_temp.l2_data_plane_bind_receipt');
  IF v_receipt_owner <> current_user OR NOT EXISTS (
    SELECT 1 FROM pg_temp.l2_data_plane_bind_receipt
    WHERE chart_id = p_chart_id
      AND dependency_vector_digest = v_vector_digest
      AND manifest_count = (SELECT count(DISTINCT source_table) FROM public.l2_data_plane_asset_outputs)
  ) THEN
    RAISE EXCEPTION 'L2 exact-input bind receipt is missing, forged, or mismatched';
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
  IF NOT public.l2_data_plane_dependency_topology_matches(
    p_asset_id, p_dependency_vector
  ) THEN
    RAISE EXCEPTION 'L2 generation dependency topology is stale or incomplete';
  END IF;

  FOR v_dep IN
    SELECT value FROM jsonb_array_elements(p_dependency_vector)
    ORDER BY value->>'layer', value->>'asset_id'
  LOOP
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
    IF v_dep->>'layer' = 'L2' AND NOT public.l2_data_plane_generation_is_compatible(
      p_chart_id, v_dep->>'asset_id', v_dep->>'generation_id'
    ) THEN
      RAISE EXCEPTION 'L2 dependency %/% has a stale transitive closure',
        v_dep->>'asset_id', v_dep->>'generation_id';
    END IF;

    -- Serialize this producer transaction with dependency head changes. The
    -- caller supplies its vector in canonical layer/asset order, so all L2
    -- producers acquire these locks in the same order.
    IF v_dep->>'layer' = 'L1' THEN
      PERFORM 1 FROM public.l1_data_plane_generation_heads
      WHERE chart_id = p_chart_id AND asset_id = v_dep->>'asset_id'
      FOR SHARE;
    ELSE
      PERFORM 1 FROM public.l2_data_plane_generation_heads
      WHERE chart_id = p_chart_id AND asset_id = v_dep->>'asset_id'
      FOR SHARE;
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
  SELECT count(*) INTO v_declared
  FROM public.l2_data_plane_partition_contexts
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id;
  IF v_declared > v_existing.expected_partitions THEN
    RAISE EXCEPTION 'L2 generation declared % partitions but expected %',
      v_declared, v_existing.expected_partitions;
  END IF;
  INSERT INTO public.l2_data_plane_run_intents (
    chart_id, asset_id, generation_id, partition_key, build_id
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key, p_build_id
  ) ON CONFLICT DO NOTHING;
  INSERT INTO public.l2_data_plane_input_bind_receipts (
    chart_id, asset_id, generation_id, partition_key, build_id,
    dependency_vector_digest
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key, p_build_id,
    v_vector_digest
  ) ON CONFLICT DO NOTHING;
  IF NOT EXISTS (
    SELECT 1 FROM public.l2_data_plane_input_bind_receipts
    WHERE chart_id=p_chart_id AND asset_id=p_asset_id
      AND generation_id=p_generation_id AND partition_key=p_partition_key
      AND build_id=p_build_id AND dependency_vector_digest=v_vector_digest
  ) THEN
    RAISE EXCEPTION 'L2 generation was reopened with a different bind receipt';
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.l2_data_plane_capture_row()
RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
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
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L2 governed capture requires direct data_plane_builder authentication';
  END IF;
  IF v_chart_text IS NULL OR v_generation IS NULL OR v_partition IS NULL
     OR v_build IS NULL THEN
    RAISE EXCEPTION 'incomplete transaction-local L2 producer context';
  END IF;
  IF COALESCE(v_row->>'chart_id', '') <> v_chart_text THEN
    RAISE EXCEPTION 'writer row chart % mismatches L2 producer chart %',
      v_row->>'chart_id', v_chart_text;
  END IF;
  -- Row-level build_id is legacy active-table provenance and update-only
  -- producers (notably bo_laksana_rerank) intentionally preserve the root
  -- producer's value. Invocation build identity lives in this immutable
  -- generation/run envelope, so it must not be inferred from the active row.

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
  IF NOT EXISTS (
    SELECT 1 FROM public.l2_data_plane_run_intents
    WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
      AND generation_id = v_generation AND partition_key = v_partition
      AND build_id = v_build
  ) THEN
    RAISE EXCEPTION 'L2 build/partition run intent was not opened before % write', TG_TABLE_NAME;
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

  IF public.l2_data_plane_jsonb_has_nonfinite(v_row) THEN
    RAISE EXCEPTION 'non-finite L2 numeric output from %', v_asset;
  END IF;

  INSERT INTO public.l2_data_plane_run_rows (
    chart_id, asset_id, generation_id, partition_key, build_id,
    source_table, row_identity, semantic_digest
  ) VALUES (
    v_chart_text::uuid, v_asset, v_generation, v_partition, v_build,
    TG_TABLE_NAME, v_identity, v_digest
  ) ON CONFLICT (
    chart_id, asset_id, generation_id, partition_key, build_id,
    source_table, row_identity
  ) DO UPDATE SET semantic_digest = EXCLUDED.semantic_digest,
                  observed_at = clock_timestamp();

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
) RETURNS void LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  v_partition_digest text;
  v_observed_row_count bigint;
  v_existing public.l2_data_plane_generation_partitions%ROWTYPE;
  v_completed integer;
  v_expected integer;
  v_generation_digest text;
  v_state text;
  v_existing_generation_digest text;
  v_declared integer;
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L2 partition completion requires direct data_plane_builder authentication';
  END IF;
  IF current_setting('madhav.l2_asset_id', true) IS DISTINCT FROM p_asset_id
     OR current_setting('madhav.l2_chart_id', true) IS DISTINCT FROM p_chart_id::text
     OR current_setting('madhav.l2_generation_id', true) IS DISTINCT FROM p_generation_id
     OR current_setting('madhav.l2_partition_key', true) IS DISTINCT FROM p_partition_key
     OR current_setting('madhav.l2_build_id', true) IS DISTINCT FROM p_build_id THEN
    RAISE EXCEPTION 'L2 completion context does not match the requested generation';
  END IF;
  IF p_rows_inserted < 0 OR p_rows_updated < 0 OR p_rows_skipped < 0 THEN
    RAISE EXCEPTION 'L2 producer row counts cannot be negative';
  END IF;
  SELECT state, expected_partitions INTO v_state, v_expected
  FROM public.data_plane_l2_producer_generations
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'L2 generation % is not open', p_generation_id;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.l2_data_plane_partition_contexts
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
  ) THEN
    RAISE EXCEPTION 'L2 partition % was not declared by generation open', p_partition_key;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.l2_data_plane_run_intents
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
      AND build_id = p_build_id
  ) THEN
    RAISE EXCEPTION 'L2 build % has no declared run intent for partition %',
      p_build_id, p_partition_key;
  END IF;
  SELECT encode(digest(COALESCE(jsonb_agg(
           jsonb_build_array(source_table, row_identity, semantic_digest)
           ORDER BY source_table, row_identity
         ), '[]'::jsonb)::text, 'sha256'), 'hex')
  INTO v_partition_digest
  FROM (
    SELECT source_table, row_identity, semantic_digest
    FROM public.l2_data_plane_run_rows
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
      AND build_id = p_build_id
    ORDER BY source_table, row_identity
  ) latest;

  SELECT count(*) INTO v_observed_row_count
  FROM public.l2_data_plane_run_rows
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id AND partition_key = p_partition_key
    AND build_id = p_build_id;
  IF v_observed_row_count <> p_rows_inserted + p_rows_updated THEN
    RAISE EXCEPTION 'L2 partition % reported % inserts + % updates but protected capture contains % rows',
      p_partition_key, p_rows_inserted, p_rows_updated, v_observed_row_count;
  END IF;
  IF v_observed_row_count = 0 AND NOT EXISTS (
    SELECT 1 FROM public.asset_registry
    WHERE asset_id = p_asset_id AND target_floor = 0
  ) THEN
    RAISE EXCEPTION 'L2 partition % has undeclared empty output', p_partition_key;
  END IF;

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
    rows_inserted, rows_updated, rows_skipped,
    observed_row_count, semantic_output_digest
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key, p_build_id,
    p_rows_inserted, p_rows_updated, p_rows_skipped,
    v_observed_row_count, v_partition_digest
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

  SELECT count(*) INTO v_declared
  FROM public.l2_data_plane_partition_contexts
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id;
  IF v_declared <> v_expected THEN
    RAISE EXCEPTION 'L2 generation completed % partitions but declared % of expected %',
      v_completed, v_declared, v_expected;
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

  IF NOT public.l2_data_plane_generation_is_compatible(
    p_chart_id, p_asset_id, p_generation_id
  ) THEN
    RAISE EXCEPTION 'L2 generation % became stale before head selection',
      p_generation_id;
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
) LANGUAGE sql STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
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
) RETURNS void LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  v_current text;
BEGIN
  IF session_user <> 'data_plane_migrator' THEN
    RAISE EXCEPTION 'L2 rollback requires direct data_plane_migrator authentication';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.data_plane_l2_producer_generations
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND state = 'complete'
  ) THEN
    RAISE EXCEPTION 'rollback target % is absent or incomplete', p_generation_id;
  END IF;
  IF NOT public.l2_data_plane_generation_is_compatible(
    p_chart_id, p_asset_id, p_generation_id
  ) THEN
    RAISE EXCEPTION 'rollback target % has a stale dependency closure',
      p_generation_id;
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
WHERE public.l2_data_plane_generation_is_compatible(
  h.chart_id, h.asset_id, h.current_generation_id
)
ORDER BY s.chart_id, s.asset_id, s.source_table, s.row_identity,
         s.captured_at DESC, s.snapshot_id DESC;

CREATE OR REPLACE FUNCTION public.l2_data_plane_guard_active_mutation()
RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  v_asset text := current_setting('madhav.l2_asset_id', true);
  v_chart text := current_setting('madhav.l2_chart_id', true);
  v_generation text := current_setting('madhav.l2_generation_id', true);
  v_partition text := current_setting('madhav.l2_partition_key', true);
  v_build text := current_setting('madhav.l2_build_id', true);
  v_row jsonb := CASE WHEN TG_OP='DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
  v_delete_authorized boolean := false;
BEGIN
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'protected L2 % requires direct data_plane_builder authentication', TG_OP;
  END IF;
  IF v_asset IS NULL OR v_asset='' OR v_chart IS NULL OR v_generation IS NULL
     OR v_partition IS NULL OR v_build IS NULL THEN
    RAISE EXCEPTION 'protected L2 % has no admitted transaction context', TG_OP;
  END IF;
  IF COALESCE(v_row->>'chart_id','') <> v_chart THEN
    RAISE EXCEPTION 'protected L2 % row chart does not match admitted chart', TG_OP;
  END IF;
  IF TG_OP='DELETE' AND TG_TABLE_NAME IN (
    'bodha_msr_signals','bodha_signal_embeddings','bodha_contradictions'
  ) THEN
    IF EXISTS (
      SELECT 1 FROM pg_class c
      WHERE c.oid=to_regclass('pg_temp.l2_data_plane_msr_delete_receipt')
        AND pg_get_userbyid(c.relowner)=current_user
    ) THEN
      IF TG_TABLE_NAME IN ('bodha_msr_signals','bodha_signal_embeddings') THEN
        EXECUTE 'SELECT EXISTS (
          SELECT 1 FROM pg_temp.l2_data_plane_msr_delete_receipt
          WHERE chart_id=$1 AND signal_id=$2
        )' INTO v_delete_authorized USING v_chart::uuid, (v_row->>'signal_id')::uuid;
      ELSE
        EXECUTE 'SELECT EXISTS (
          SELECT 1 FROM pg_temp.l2_data_plane_msr_delete_receipt
          WHERE chart_id=$1 AND signal_id IN ($2,$3)
        )' INTO v_delete_authorized USING v_chart::uuid,
          (v_row->>'signal_a_id')::uuid, (v_row->>'signal_b_id')::uuid;
      END IF;
    END IF;
  END IF;
  IF TG_OP='DELETE' AND TG_TABLE_NAME='bodha_msr_signals' AND NOT v_delete_authorized THEN
    RAISE EXCEPTION 'L2 MSR deletion lacks an exact protected-owner scope receipt';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.l2_data_plane_asset_outputs
    WHERE asset_id=v_asset AND source_table=TG_TABLE_NAME
  ) AND NOT (
    TG_OP='DELETE'
    AND TG_TABLE_NAME IN ('bodha_signal_embeddings','bodha_contradictions')
    AND v_delete_authorized
  ) THEN
    RAISE EXCEPTION 'L2 asset % cannot mutate protected table %', v_asset, TG_TABLE_NAME;
  END IF;
  IF NOT EXISTS (
    SELECT 1
    FROM public.l2_data_plane_run_intents i
    JOIN public.data_plane_l2_producer_generations g USING(chart_id,asset_id,generation_id)
    JOIN public.build_runs br ON br.id=v_build::uuid AND br.chart_id=i.chart_id
    JOIN public.build_run_assets bra ON bra.run_id=br.id AND bra.asset_id=i.asset_id
    JOIN public.l2_data_plane_input_bind_receipts r
      ON r.chart_id=i.chart_id AND r.asset_id=i.asset_id
     AND r.generation_id=i.generation_id AND r.partition_key=i.partition_key
     AND r.build_id=i.build_id
    WHERE i.chart_id=v_chart::uuid AND i.asset_id=v_asset
      AND i.generation_id=v_generation AND i.partition_key=v_partition
      AND i.build_id=v_build AND g.state='building'
      AND br.state='running' AND bra.state='building'
  ) THEN
    RAISE EXCEPTION 'protected L2 % is outside an active admitted generation', TG_OP;
  END IF;
  RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;

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
  EXECUTE format('DROP TRIGGER IF EXISTS l2_data_plane_mutation_guard ON public.%I', p_table);
  EXECUTE format(
    'CREATE TRIGGER l2_data_plane_mutation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.%I '
    'FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_guard_active_mutation()',
    p_table
  );
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

CREATE TABLE IF NOT EXISTS public.l2_data_plane_function_attestations (
  function_signature text PRIMARY KEY,
  definition_digest text NOT NULL CHECK (definition_digest ~ '^[0-9a-f]{64}$'),
  owner_name text NOT NULL,
  security_definer boolean NOT NULL,
  config text[]
);
INSERT INTO public.l2_data_plane_function_attestations(function_signature, definition_digest, owner_name, security_definer, config)
SELECT p.oid::regprocedure::text,
       encode(digest(pg_get_functiondef(p.oid), 'sha256'), 'hex'),
       pg_get_userbyid(p.proowner),p.prosecdef,p.proconfig
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND (
  p.proname LIKE 'l2_data_plane_%' OR p.proname IN (
    'assert_l2_msr_delete_safe','bind_l2_exact_inputs',
    'open_l2_data_plane_generation','complete_l2_data_plane_partition',
    'select_l2_data_plane_generation','rollback_l2_data_plane_generation'
  )
)
ON CONFLICT (function_signature) DO UPDATE
SET definition_digest=EXCLUDED.definition_digest,owner_name=EXCLUDED.owner_name,
    security_definer=EXCLUDED.security_definer,config=EXCLUDED.config;
DROP TRIGGER IF EXISTS l2_data_plane_function_attestations_immutable
  ON public.l2_data_plane_function_attestations;
CREATE TRIGGER l2_data_plane_function_attestations_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_function_attestations
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

CREATE TABLE IF NOT EXISTS public.l2_data_plane_policy_attestations (
  table_name text NOT NULL,
  policy_name text NOT NULL,
  command text NOT NULL,
  permissive boolean NOT NULL,
  role_oids oid[] NOT NULL,
  using_expression text,
  check_expression text,
  PRIMARY KEY(table_name, policy_name)
);
INSERT INTO public.l2_data_plane_policy_attestations
SELECT c.relname,p.polname,p.polcmd,p.polpermissive,p.polroles,
       pg_get_expr(p.polqual,p.polrelid),pg_get_expr(p.polwithcheck,p.polrelid)
FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relname IN (
  'bodha_msr_signals','bodha_cgm_nodes','bodha_cgm_edges','bodha_contradictions',
  'bodha_cgm_paths','bodha_cgm_motifs','bodha_cgm_sub_graphs','bodha_cgm_chart_topology_summary',
  'bodha_mechanisms','bodha_cdlm_cells','bodha_convergence','bodha_triangulation',
  'bodha_cdlm_chart_summary','bodha_cdlm_domain_rollups','bodha_cdlm_pattern_clusters',
  'bodha_pratijna','bodha_rm_resonances','bodha_rm_remedy_prescriptions',
  'bodha_rm_dasha_windowed_prescriptions','bodha_rm_chart_summary','bodha_rm_dosha_remedy_bundles',
  'bodha_rm_pattern_remedies','bodha_signal_embeddings','bodha_discoveries','bodha_anomalies',
  'bodha_question_lenses','bodha_chart_gestalt','synthesis_quality_scorecard','bodha_grounding_matches'
) ON CONFLICT (table_name,policy_name) DO UPDATE SET
  command=EXCLUDED.command,permissive=EXCLUDED.permissive,role_oids=EXCLUDED.role_oids,
  using_expression=EXCLUDED.using_expression,check_expression=EXCLUDED.check_expression;
DROP TRIGGER IF EXISTS l2_data_plane_policy_attestations_immutable ON public.l2_data_plane_policy_attestations;
CREATE TRIGGER l2_data_plane_policy_attestations_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_policy_attestations
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

CREATE TABLE IF NOT EXISTS public.l2_data_plane_view_attestations (
  view_name text PRIMARY KEY,
  relation_kind "char" NOT NULL,
  definition_digest text NOT NULL CHECK (definition_digest ~ '^[0-9a-f]{64}$'),
  owner_name text NOT NULL,
  options text[]
);
INSERT INTO public.l2_data_plane_view_attestations(view_name, relation_kind, definition_digest, owner_name, options)
SELECT c.relname,c.relkind,
       encode(digest(pg_get_viewdef(c.oid, true), 'sha256'), 'hex'),
       pg_get_userbyid(c.relowner),c.reloptions
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind='v'
  AND starts_with(c.relname, 'l2_data_plane_current_')
ON CONFLICT (view_name) DO NOTHING;
DROP TRIGGER IF EXISTS l2_data_plane_view_attestations_immutable ON public.l2_data_plane_view_attestations;
CREATE TRIGGER l2_data_plane_view_attestations_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_view_attestations
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

CREATE TABLE IF NOT EXISTS public.l2_data_plane_trigger_attestations (
  table_name text NOT NULL,
  trigger_name text NOT NULL,
  trigger_type smallint NOT NULL,
  enabled "char" NOT NULL,
  function_oid oid NOT NULL,
  function_signature text NOT NULL,
  definition_digest text NOT NULL CHECK (definition_digest ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY(table_name, trigger_name)
);
INSERT INTO public.l2_data_plane_trigger_attestations(
  table_name,trigger_name,trigger_type,enabled,function_oid,function_signature,definition_digest
)
SELECT c.relname,t.tgname,t.tgtype,t.tgenabled,t.tgfoid,
       t.tgfoid::regprocedure::text,
       encode(digest(pg_get_triggerdef(t.oid, true), 'sha256'), 'hex')
FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname IN (
  'bodha_msr_signals','bodha_cgm_nodes','bodha_cgm_edges','bodha_contradictions',
  'bodha_cgm_paths','bodha_cgm_motifs','bodha_cgm_sub_graphs','bodha_cgm_chart_topology_summary',
  'bodha_mechanisms','bodha_cdlm_cells','bodha_convergence','bodha_triangulation',
  'bodha_cdlm_chart_summary','bodha_cdlm_domain_rollups','bodha_cdlm_pattern_clusters',
  'bodha_pratijna','bodha_rm_resonances','bodha_rm_remedy_prescriptions',
  'bodha_rm_dasha_windowed_prescriptions','bodha_rm_chart_summary','bodha_rm_dosha_remedy_bundles',
  'bodha_rm_pattern_remedies','bodha_signal_embeddings','bodha_discoveries','bodha_anomalies',
  'bodha_question_lenses','bodha_chart_gestalt','synthesis_quality_scorecard','bodha_grounding_matches'
) ON CONFLICT (table_name,trigger_name) DO NOTHING;
DROP TRIGGER IF EXISTS l2_data_plane_trigger_attestations_immutable ON public.l2_data_plane_trigger_attestations;
CREATE TRIGGER l2_data_plane_trigger_attestations_immutable
BEFORE UPDATE OR DELETE ON public.l2_data_plane_trigger_attestations
FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_reject_immutable_change();

-- DP-SD-018 protected-owner boundary. This file is applied only by the
-- deployment-only attestation runner after SET LOCAL ROLE data_plane_l2_owner.
DO $l2_role_preflight$
BEGIN
  IF session_user <> 'data_plane_migrator' OR current_user <> 'data_plane_l2_owner' THEN
    RAISE EXCEPTION 'E1036_WRONG_ACTOR: expected data_plane_migrator SET ROLE data_plane_l2_owner';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
    WHERE rolname = 'data_plane_builder' AND rolcanlogin AND NOT rolinherit
      AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolbypassrls
  ) OR NOT EXISTS (
    SELECT 1 FROM pg_roles
    WHERE rolname = 'data_plane_verifier' AND rolcanlogin AND NOT rolinherit
      AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'E1036_PREFLIGHT_ROLES: normalized builder and verifier must exist';
  END IF;
END
$l2_role_preflight$;

REVOKE ALL ON TABLE
  public.data_plane_l2_producer_generations,
  public.l2_data_plane_generation_partitions,
  public.l2_data_plane_generation_runs,
  public.l2_data_plane_run_rows,
  public.l2_data_plane_partition_contexts,
  public.l2_data_plane_run_intents,
  public.l2_data_plane_input_bind_receipts,
  public.l2_data_plane_row_snapshots,
  public.l2_data_plane_generation_heads,
  public.l2_data_plane_asset_outputs,
  public.l2_data_plane_function_attestations,
  public.l2_data_plane_policy_attestations,
  public.l2_data_plane_view_attestations,
  public.l2_data_plane_trigger_attestations,
  public.l2_data_plane_current_rows
FROM PUBLIC, role_orchestrator, data_plane_builder, data_plane_verifier,
     data_plane_migrator, amjis_app;

GRANT SELECT ON TABLE
  public.data_plane_l2_producer_generations,
  public.l2_data_plane_run_rows,
  public.l2_data_plane_generation_heads,
  public.l2_data_plane_generation_partitions,
  public.l2_data_plane_generation_runs,
  public.l2_data_plane_partition_contexts,
  public.l2_data_plane_run_intents,
  public.l2_data_plane_input_bind_receipts,
  public.l2_data_plane_row_snapshots,
  public.l2_data_plane_asset_outputs,
  public.l2_data_plane_function_attestations,
  public.l2_data_plane_policy_attestations,
  public.l2_data_plane_view_attestations,
  public.l2_data_plane_trigger_attestations,
  public.l2_data_plane_current_rows
TO data_plane_builder, data_plane_verifier, data_plane_migrator, amjis_app;

DO $l2_function_acl$
DECLARE
  v_function regprocedure;
BEGIN
  FOR v_function IN
    SELECT p.oid::regprocedure
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND (
        p.proname LIKE 'l2_data_plane_%'
        OR p.proname IN (
          'assert_l2_msr_delete_safe',
          'bind_l2_exact_inputs',
          'open_l2_data_plane_generation',
          'complete_l2_data_plane_partition',
          'select_l2_data_plane_generation',
          'rollback_l2_data_plane_generation'
        )
      )
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC', v_function);
    EXECUTE format(
      'REVOKE EXECUTE ON FUNCTION %s FROM role_orchestrator, data_plane_builder, data_plane_verifier, data_plane_migrator, amjis_app',
      v_function
    );
  END LOOP;
END
$l2_function_acl$;

GRANT EXECUTE ON FUNCTION public.assert_l2_msr_delete_safe(
  UUID, TEXT[], TEXT[], TEXT[]
) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bind_l2_exact_inputs(
  UUID, JSONB
) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.open_l2_data_plane_generation(
  UUID, TEXT, TEXT, TEXT, INTEGER, TEXT, TEXT, TEXT, TEXT, JSONB, JSONB, TEXT
) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.complete_l2_data_plane_partition(
  UUID, TEXT, TEXT, TEXT, TEXT, BIGINT, BIGINT, BIGINT
) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.select_l2_data_plane_generation(
  UUID, TEXT, TEXT
) TO data_plane_builder, data_plane_verifier, data_plane_migrator, amjis_app;
GRANT EXECUTE ON FUNCTION public.rollback_l2_data_plane_generation(
  UUID, TEXT, TEXT
) TO data_plane_migrator;

-- Publish builder DML only after every L2 admission/capture trigger exists.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
  public.bodha_msr_signals,public.bodha_cgm_nodes,public.bodha_cgm_edges,
  public.bodha_contradictions,public.bodha_cgm_paths,public.bodha_cgm_motifs,
  public.bodha_cgm_sub_graphs,public.bodha_cgm_chart_topology_summary,
  public.bodha_mechanisms,public.bodha_cdlm_cells,public.bodha_convergence,
  public.bodha_triangulation,public.bodha_cdlm_chart_summary,
  public.bodha_cdlm_domain_rollups,public.bodha_cdlm_pattern_clusters,
  public.bodha_pratijna,public.bodha_rm_resonances,public.bodha_rm_remedy_prescriptions,
  public.bodha_rm_dasha_windowed_prescriptions,public.bodha_rm_chart_summary,
  public.bodha_rm_dosha_remedy_bundles,public.bodha_rm_pattern_remedies,
  public.bodha_signal_embeddings,public.bodha_discoveries,public.bodha_anomalies,
  public.bodha_question_lenses,public.bodha_chart_gestalt,
  public.synthesis_quality_scorecard,public.bodha_grounding_matches
TO data_plane_builder;

DO $l2_builder_sequence_acl$
DECLARE v_sequence regclass;
BEGIN
  FOR v_sequence IN
    SELECT DISTINCT seq.oid::regclass
    FROM pg_class tab JOIN pg_namespace ns ON ns.oid=tab.relnamespace
    JOIN pg_depend dep ON dep.refobjid=tab.oid AND dep.refclassid='pg_class'::regclass
      AND dep.classid='pg_class'::regclass AND dep.deptype IN ('a','i')
    JOIN pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
    WHERE ns.nspname='public' AND tab.relname IN (
      'bodha_msr_signals','bodha_cgm_nodes','bodha_cgm_edges','bodha_contradictions',
      'bodha_cgm_paths','bodha_cgm_motifs','bodha_cgm_sub_graphs','bodha_cgm_chart_topology_summary',
      'bodha_mechanisms','bodha_cdlm_cells','bodha_convergence','bodha_triangulation',
      'bodha_cdlm_chart_summary','bodha_cdlm_domain_rollups','bodha_cdlm_pattern_clusters',
      'bodha_pratijna','bodha_rm_resonances','bodha_rm_remedy_prescriptions',
      'bodha_rm_dasha_windowed_prescriptions','bodha_rm_chart_summary','bodha_rm_dosha_remedy_bundles',
      'bodha_rm_pattern_remedies','bodha_signal_embeddings','bodha_discoveries','bodha_anomalies',
      'bodha_question_lenses','bodha_chart_gestalt','synthesis_quality_scorecard','bodha_grounding_matches'
    )
  LOOP
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO data_plane_builder', v_sequence);
  END LOOP;
END
$l2_builder_sequence_acl$;

COMMENT ON TABLE public.data_plane_l2_producer_generations IS
  'DP-SD-015 exact upstream context and immutable L2 producer generations; no L3 activation authority.';

COMMIT;
