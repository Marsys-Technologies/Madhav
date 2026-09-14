-- 1033_data_plane_l1_producer_history.sql
-- L1 Gaṇita data-plane producer context, append-only generations, replay and rollback.
--
-- Forward order: apply this migration before deploying the adapters that invoke
-- open_l1_data_plane_generation()/complete_l1_data_plane_partition().  Existing
-- active tables remain source-compatible and replace-in-place; inserted versions
-- are copied transactionally into the immutable store before a build can complete.
-- No historical row is synthesized or backfilled by this migration.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.l1_data_plane_generations (
    chart_id                       UUID NOT NULL,
    asset_id                       TEXT NOT NULL,
    generation_id                 TEXT NOT NULL,
    correction_of_generation_id   TEXT,
    contract_version               TEXT NOT NULL,
    l0_semantic_release_id         TEXT NOT NULL,
    l0_semantic_release_digest     TEXT NOT NULL,
    l0_config_generation_id        TEXT NOT NULL,
    l0_config_digest               TEXT NOT NULL,
    base_context_jsonb             JSONB NOT NULL,
    expected_partitions            INTEGER NOT NULL CHECK (expected_partitions > 0),
    completed_partitions           INTEGER NOT NULL DEFAULT 0
                                  CHECK (completed_partitions >= 0),
    status                         TEXT NOT NULL DEFAULT 'building'
                                  CHECK (status IN ('building', 'complete')),
    semantic_output_digest         TEXT,
    opened_at                      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at                   TIMESTAMPTZ,
    PRIMARY KEY (chart_id, asset_id, generation_id),
    CHECK (completed_partitions <= expected_partitions),
    CHECK (
      (status = 'building' AND completed_at IS NULL AND semantic_output_digest IS NULL)
      OR
      (status = 'complete' AND completed_at IS NOT NULL AND semantic_output_digest IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS public.l1_data_plane_generation_partitions (
    chart_id            UUID NOT NULL,
    asset_id            TEXT NOT NULL,
    generation_id       TEXT NOT NULL,
    partition_key       TEXT NOT NULL,
    rows_inserted       INTEGER NOT NULL CHECK (rows_inserted >= 0),
    completed_at        TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (chart_id, asset_id, generation_id, partition_key),
    FOREIGN KEY (chart_id, asset_id, generation_id)
      REFERENCES public.l1_data_plane_generations(chart_id, asset_id, generation_id)
      ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.l1_data_plane_row_snapshots (
    snapshot_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                    UUID NOT NULL,
    asset_id                    TEXT NOT NULL,
    generation_id              TEXT NOT NULL,
    partition_key              TEXT NOT NULL,
    source_table               TEXT NOT NULL,
    row_identity               TEXT NOT NULL,
    context_id                 TEXT NOT NULL,
    calculation_context_jsonb  JSONB NOT NULL,
    grain_jsonb                JSONB NOT NULL,
    source_dependencies_jsonb  JSONB NOT NULL,
    epistemic_class            TEXT NOT NULL,
    missingness_state          TEXT NOT NULL,
    verification_class         TEXT NOT NULL,
    unit                       TEXT,
    semantic_payload_jsonb     JSONB NOT NULL,
    source_row_jsonb           JSONB NOT NULL,
    semantic_digest            TEXT NOT NULL,
    captured_at                TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (chart_id, asset_id, generation_id, partition_key, source_table, row_identity),
    FOREIGN KEY (chart_id, asset_id, generation_id)
      REFERENCES public.l1_data_plane_generations(chart_id, asset_id, generation_id)
      ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.l1_data_plane_generation_heads (
    chart_id                       UUID NOT NULL,
    asset_id                       TEXT NOT NULL,
    current_generation_id          TEXT NOT NULL,
    previous_generation_id         TEXT,
    selected_at                    TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (chart_id, asset_id),
    FOREIGN KEY (chart_id, asset_id, current_generation_id)
      REFERENCES public.l1_data_plane_generations(chart_id, asset_id, generation_id)
      ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS l1_data_plane_snapshots_generation_idx
  ON public.l1_data_plane_row_snapshots
  (chart_id, asset_id, generation_id, source_table, row_identity);

CREATE OR REPLACE FUNCTION public.l1_data_plane_reject_immutable_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION '% is append-only; % is forbidden', TG_TABLE_NAME, TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS l1_data_plane_partitions_immutable
  ON public.l1_data_plane_generation_partitions;
CREATE TRIGGER l1_data_plane_partitions_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_generation_partitions
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l1_data_plane_snapshots_immutable
  ON public.l1_data_plane_row_snapshots;
CREATE TRIGGER l1_data_plane_snapshots_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_row_snapshots
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

CREATE OR REPLACE FUNCTION public.open_l1_data_plane_generation(
    p_chart_id UUID,
    p_asset_id TEXT,
    p_generation_id TEXT,
    p_partition_key TEXT,
    p_expected_partitions INTEGER,
    p_correction_of_generation_id TEXT,
    p_contract_version TEXT,
    p_l0_semantic_release_id TEXT,
    p_l0_semantic_release_digest TEXT,
    p_l0_config_generation_id TEXT,
    p_l0_config_digest TEXT
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  v_chart public.charts%ROWTYPE;
  v_context JSONB;
  v_existing public.l1_data_plane_generations%ROWTYPE;
BEGIN
  IF p_asset_id NOT IN (
    'ga_positions','ga_vargas','ga_dashas','ga_nakshatra','ga_panchanga',
    'ga_sensitive','ga_sensitive_degree','ga_strength','ga_structural',
    'ga_condition','ga_yoga','ga_vichara','ga_sade_sati','ga_transit_anchors',
    'ga_tajaka','ga_ayurdaya','ga_medical','ga_vastu','ga_prashna'
  ) THEN
    RAISE EXCEPTION 'unknown L1 producer asset %', p_asset_id;
  END IF;
  IF p_generation_id IS NULL OR p_generation_id = ''
     OR p_partition_key IS NULL OR p_partition_key = ''
     OR p_expected_partitions < 1 THEN
    RAISE EXCEPTION 'incomplete L1 generation identity';
  END IF;
  IF p_contract_version <> 'l1.data-plane.contract.1.0'
     OR p_l0_semantic_release_id <> 'l0.semantic.2026-09-13.1'
     OR p_l0_semantic_release_digest <> '665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1'
     OR p_l0_config_generation_id <> 'l0-resource-config-g1'
     OR p_l0_config_digest <> 'd516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a' THEN
    RAISE EXCEPTION 'L1 producer pins do not match the accepted L0 release';
  END IF;

  SELECT * INTO v_chart
  FROM public.charts
  WHERE id = p_chart_id OR chart_id = p_chart_id
  LIMIT 1;
  IF NOT FOUND OR v_chart.birth_date IS NULL OR v_chart.birth_time IS NULL
     OR v_chart.birth_lat IS NULL OR v_chart.birth_lng IS NULL
     OR v_chart.timezone_id IS NULL OR v_chart.timezone_id = ''
     OR v_chart.house_system IS NULL OR v_chart.house_system = '' THEN
    RAISE EXCEPTION 'chart % lacks exact calculation-context inputs', p_chart_id;
  END IF;

  IF p_correction_of_generation_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM public.l1_data_plane_generations
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_correction_of_generation_id AND status = 'complete'
  ) THEN
    RAISE EXCEPTION 'correction predecessor % is absent or incomplete',
      p_correction_of_generation_id;
  END IF;

  v_context := jsonb_build_object(
    'subject_id', COALESCE(v_chart.client_id, v_chart.owner_id, v_chart.id::text),
    'chart_id', p_chart_id::text,
    'build_id', p_generation_id,
    'generation_id', p_generation_id,
    'instant_iso', to_char(
      timezone('UTC', timezone(v_chart.timezone_id, v_chart.birth_date + v_chart.birth_time)),
      'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
    ),
    'latitude_deg', v_chart.birth_lat,
    'longitude_deg', v_chart.birth_lng,
    'timezone_name', v_chart.timezone_id,
    'input_precision', 'postgres_date_plus_time_microsecond',
    'frame', 'sidereal',
    'ayanamsha_id', CASE
      WHEN p_partition_key ~ '^ayanamsha[:_]' THEN
        regexp_replace(p_partition_key, '^ayanamsha[:_]', '')
      ELSE 'mixed_or_invariant'
    END,
    'node_type', 'mean',
    'house_convention', v_chart.house_system,
    'varga', 'D1',
    'varga_formula', 'writer_row_declared',
    'varga_domain', 'writer_row_declared',
    'karaka_school', 'writer_row_declared',
    'engine_version', p_asset_id,
    'contract_version', p_contract_version,
    'l0_semantic_release_id', p_l0_semantic_release_id,
    'l0_semantic_release_digest', p_l0_semantic_release_digest,
    'l0_resource_config_generation_id', p_l0_config_generation_id,
    'l0_resource_config_digest', p_l0_config_digest
  );

  INSERT INTO public.l1_data_plane_generations (
    chart_id, asset_id, generation_id, correction_of_generation_id,
    contract_version, l0_semantic_release_id, l0_semantic_release_digest,
    l0_config_generation_id, l0_config_digest, base_context_jsonb,
    expected_partitions
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_correction_of_generation_id,
    p_contract_version, p_l0_semantic_release_id, p_l0_semantic_release_digest,
    p_l0_config_generation_id, p_l0_config_digest, v_context,
    p_expected_partitions
  ) ON CONFLICT (chart_id, asset_id, generation_id) DO NOTHING;

  SELECT * INTO v_existing
  FROM public.l1_data_plane_generations
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id
  FOR UPDATE;
  IF v_existing.expected_partitions <> p_expected_partitions
     OR v_existing.contract_version <> p_contract_version
     OR v_existing.base_context_jsonb <> v_context
     OR v_existing.correction_of_generation_id IS DISTINCT FROM p_correction_of_generation_id THEN
    RAISE EXCEPTION 'generation % was reopened with incompatible context', p_generation_id;
  END IF;
  IF v_existing.status = 'complete' AND NOT EXISTS (
    SELECT 1 FROM public.l1_data_plane_generation_partitions
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND partition_key = p_partition_key
  ) THEN
    RAISE EXCEPTION 'complete generation % cannot admit a new partition', p_generation_id;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.l1_data_plane_capture_row()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  v_asset TEXT := current_setting('madhav.l1_asset_id', true);
  v_chart_text TEXT := current_setting('madhav.l1_chart_id', true);
  v_generation TEXT := current_setting('madhav.l1_generation_id', true);
  v_partition TEXT := current_setting('madhav.l1_partition_key', true);
  v_row JSONB := to_jsonb(NEW);
  v_base JSONB;
  v_context JSONB;
  v_semantic JSONB;
  v_identity_parts TEXT[] := ARRAY[]::TEXT[];
  v_identity TEXT;
  v_context_id TEXT;
  v_digest TEXT;
  v_existing_digest TEXT;
  v_key TEXT;
  v_deps TEXT[];
  v_missingness TEXT;
  v_epistemic TEXT;
BEGIN
  -- Compatibility: direct legacy SQL/CLI paths remain usable but do not claim
  -- a governed runtime generation unless the adapter opened one explicitly.
  IF v_asset IS NULL OR v_asset = '' THEN
    RETURN NEW;
  END IF;
  IF v_chart_text IS NULL OR v_generation IS NULL OR v_partition IS NULL THEN
    RAISE EXCEPTION 'incomplete transaction-local L1 producer context';
  END IF;
  IF COALESCE(v_row->>'chart_id', '') <> v_chart_text THEN
    RAISE EXCEPTION 'writer row chart % mismatches producer chart %',
      v_row->>'chart_id', v_chart_text;
  END IF;
  IF v_row ? 'build_id' AND v_row->>'build_id' IS NOT NULL
     AND v_row->>'build_id' <> v_generation THEN
    RAISE EXCEPTION 'writer row build % mismatches generation %',
      v_row->>'build_id', v_generation;
  END IF;

  SELECT base_context_jsonb INTO v_base
  FROM public.l1_data_plane_generations
  WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
    AND generation_id = v_generation;
  IF v_base IS NULL THEN
    RAISE EXCEPTION 'L1 generation was not opened before % insert', TG_TABLE_NAME;
  END IF;

  FOREACH v_key IN ARRAY TG_ARGV LOOP
    IF NOT (v_row ? v_key) THEN
      RAISE EXCEPTION '% has no declared natural-key column %', TG_TABLE_NAME, v_key;
    END IF;
    v_identity_parts := array_append(
      v_identity_parts, v_key || '=' || COALESCE(v_row->>v_key, '<null>')
    );
  END LOOP;
  v_identity := array_to_string(v_identity_parts, '|');

  v_context := v_base || jsonb_build_object(
    'ayanamsha_id', COALESCE(v_row->>'ayanamsha_id', v_base->>'ayanamsha_id'),
    'frame', CASE
      WHEN lower(COALESCE(v_row->>'ayanamsha_id', '')) = 'tropical' THEN 'tropical'
      ELSE 'sidereal'
    END,
    'node_type', CASE
      WHEN upper(v_row::text) ~ '(RAH_TRUE|KET_TRUE|TRUE_NODE)' THEN 'true'
      ELSE 'mean'
    END,
    'varga', COALESCE(v_row->>'varga', v_row->>'varga_id', 'D1'),
    'varga_formula', COALESCE(
      v_row->>'varga_formula', v_row->>'formula_version',
      v_row->>'formula_provenance_text',
      v_row->>'condition_formula_version', 'not_applicable'
    ),
    'varga_domain', COALESCE(v_row->>'domain', 'row_declared_or_not_applicable'),
    'karaka_school', COALESCE(v_row->>'karaka_school', 'not_applicable'),
    'method_id', COALESCE(
      v_row->>'system_id', v_row->>'year_lord_method',
      v_row->>'lagna_method', v_row->>'source_calculation', 'not_applicable'
    ),
    'output_precision', COALESCE(
      v_row->>'tolerance_arcsec', v_row->>'unit', 'schema_declared'
    ),
    'engine_version', COALESCE(
      v_row->>'engine_version', v_row->>'source_calculation', v_asset
    )
  );
  v_context_id := 'l1ctx:' || substr(encode(digest(
    ((v_context - 'build_id') - 'generation_id')::text, 'sha256'
  ), 'hex'), 1, 24);

  IF lower(COALESCE(v_row->>'fact_value_num', '')) IN ('nan','infinity','-infinity')
     OR lower(COALESCE(v_row->>'value_num', '')) IN ('nan','infinity','-infinity')
     OR lower(COALESCE(v_row->>'strength', '')) IN ('nan','infinity','-infinity') THEN
    RAISE EXCEPTION 'non-finite L1 numeric output from %', v_asset;
  END IF;

  v_semantic := v_row
    - 'id' - 'snapshot_id' - 'build_id' - 'computed_at' - 'created_at'
    - 'recorded_at' - 'updated_at';
  v_digest := encode(digest(v_semantic::text, 'sha256'), 'hex');

  v_missingness := CASE lower(COALESCE(v_row #>> '{fact_value_jsonb,state}', ''))
    WHEN 'method_inapplicable' THEN 'inapplicable'
    WHEN 'unqualified_source' THEN 'unqualified_source'
    WHEN 'failed' THEN 'failed'
    WHEN 'unavailable' THEN 'unavailable'
    WHEN 'unexplored' THEN 'unexplored'
    WHEN 'floored' THEN 'floored'
    ELSE CASE
      WHEN v_row ? 'fact_value_num' AND v_row->>'fact_value_num' = '0' THEN 'zero'
      ELSE 'present'
    END
  END;
  v_epistemic := CASE
    WHEN v_asset = 'ga_ayurdaya' THEN 'restricted_scholarly'
    WHEN v_asset IN ('ga_positions','ga_nakshatra','ga_panchanga','ga_transit_anchors')
      THEN 'astronomical'
    WHEN v_asset IN ('ga_condition','ga_yoga') THEN 'rule_derived'
    WHEN v_asset IN ('ga_vichara','ga_medical','ga_vastu','ga_prashna') THEN 'judged'
    ELSE 'deterministic_derivation'
  END;

  SELECT depends_on INTO v_deps FROM public.asset_registry WHERE asset_id = v_asset;
  SELECT semantic_digest INTO v_existing_digest
  FROM public.l1_data_plane_row_snapshots
  WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
    AND generation_id = v_generation AND partition_key = v_partition
    AND source_table = TG_TABLE_NAME AND row_identity = v_identity;
  IF v_existing_digest IS NOT NULL THEN
    IF v_existing_digest <> v_digest THEN
      RAISE EXCEPTION 'same generation/identity replay changed output for % %',
        v_asset, v_identity;
    END IF;
    RETURN NEW;
  END IF;

  INSERT INTO public.l1_data_plane_row_snapshots (
    chart_id, asset_id, generation_id, partition_key, source_table,
    row_identity, context_id, calculation_context_jsonb, grain_jsonb,
    source_dependencies_jsonb, epistemic_class, missingness_state,
    verification_class, unit, semantic_payload_jsonb, source_row_jsonb,
    semantic_digest
  ) VALUES (
    v_chart_text::uuid, v_asset, v_generation, v_partition, TG_TABLE_NAME,
    v_identity, v_context_id, v_context,
    jsonb_build_object('source_table', TG_TABLE_NAME, 'natural_key', v_identity_parts),
    jsonb_build_object(
      'producer_assets', to_jsonb(COALESCE(v_deps, ARRAY[]::TEXT[])),
      'constituent_fact_ids', COALESCE(
        v_row->'constituent_fact_ids', v_row->'constituent_facts_array',
        v_row->'constituent_planets', '[]'::jsonb
      )
    ),
    v_epistemic, v_missingness,
    COALESCE(v_row->>'verification_pass_status', v_row->>'verification_method', 'unverified'),
    v_row->>'unit', v_semantic, v_row, v_digest
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.complete_l1_data_plane_partition(
    p_chart_id UUID,
    p_asset_id TEXT,
    p_generation_id TEXT,
    p_partition_key TEXT,
    p_rows_inserted INTEGER
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  v_existing_rows INTEGER;
  v_completed INTEGER;
  v_expected INTEGER;
  v_digest TEXT;
BEGIN
  IF p_rows_inserted < 0 THEN
    RAISE EXCEPTION 'rows_inserted cannot be negative';
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

  UPDATE public.l1_data_plane_generations
  SET completed_partitions = v_completed,
      status = 'complete', semantic_output_digest = v_digest,
      completed_at = COALESCE(completed_at, clock_timestamp())
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id;

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
$$;

CREATE OR REPLACE FUNCTION public.select_l1_data_plane_generation(
    p_chart_id UUID,
    p_asset_id TEXT,
    p_generation_id TEXT
) RETURNS TABLE (
    source_table TEXT,
    row_identity TEXT,
    context_id TEXT,
    calculation_context_jsonb JSONB,
    grain_jsonb JSONB,
    source_dependencies_jsonb JSONB,
    epistemic_class TEXT,
    missingness_state TEXT,
    verification_class TEXT,
    unit TEXT,
    semantic_payload_jsonb JSONB,
    semantic_digest TEXT
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT ON (s.source_table, s.row_identity)
         s.source_table, s.row_identity, s.context_id,
         s.calculation_context_jsonb, s.grain_jsonb,
         s.source_dependencies_jsonb, s.epistemic_class,
         s.missingness_state, s.verification_class, s.unit,
         s.semantic_payload_jsonb, s.semantic_digest
  FROM public.l1_data_plane_row_snapshots s
  JOIN public.l1_data_plane_generations g
    USING (chart_id, asset_id, generation_id)
  WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
    AND s.generation_id = p_generation_id AND g.status = 'complete'
  ORDER BY s.source_table, s.row_identity, s.captured_at DESC, s.snapshot_id DESC
$$;

CREATE OR REPLACE FUNCTION public.rollback_l1_data_plane_generation(
    p_chart_id UUID,
    p_asset_id TEXT,
    p_generation_id TEXT
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  v_current TEXT;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.l1_data_plane_generations
    WHERE chart_id = p_chart_id AND asset_id = p_asset_id
      AND generation_id = p_generation_id AND status = 'complete'
  ) THEN
    RAISE EXCEPTION 'rollback target % is absent or incomplete', p_generation_id;
  END IF;
  SELECT current_generation_id INTO v_current
  FROM public.l1_data_plane_generation_heads
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
  FOR UPDATE;
  IF v_current IS NULL THEN
    RAISE EXCEPTION 'asset % has no selected generation', p_asset_id;
  END IF;
  UPDATE public.l1_data_plane_generation_heads
  SET current_generation_id = p_generation_id,
      previous_generation_id = v_current,
      selected_at = clock_timestamp()
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id;
END;
$$;

CREATE OR REPLACE VIEW public.l1_data_plane_current_rows AS
SELECT s.*
FROM public.l1_data_plane_generation_heads h
JOIN public.l1_data_plane_row_snapshots s
  ON s.chart_id = h.chart_id
 AND s.asset_id = h.asset_id
 AND s.generation_id = h.current_generation_id;

-- One trigger per active output table. The transaction-local asset id keeps
-- shared chart_facts rows owned by the writer that emitted them.
DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.chart_facts;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.chart_facts
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row('fact_id');

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.chart_dashas;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON public.chart_dashas
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row('dasha_row_id');

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.chart_divisionals;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.chart_divisionals
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','graha','ayanamsha_id','varga','fact_category','fact_key'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_condition_composite;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_condition_composite
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','graha'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_yoga_firings;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_yoga_firings
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','yoga_canonical_id'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.chart_vichara;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.chart_vichara
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','vichara_family','subject','target','domain','varga_id','formula_version'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_transit_anchors;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_transit_anchors
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','graha'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.l1_tajik_varsha_year_lords;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.l1_tajik_varsha_year_lords
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row('varsha_id');

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_medical;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_medical
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','graha'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_vastu_planet_direction_map;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_vastu_planet_direction_map
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','graha'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_prashna_lagna;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_prashna_lagna
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id','lagna_method'
);

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.ga_prashna_judgment;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.ga_prashna_judgment
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row(
  'chart_id','ayanamsha_id'
);

COMMENT ON TABLE public.l1_data_plane_row_snapshots IS
  'Append-only exact L1 producer rows. Active-table replacement never deletes a prior compatible generation.';
COMMENT ON FUNCTION public.rollback_l1_data_plane_generation(UUID, TEXT, TEXT) IS
  'Selects an already-complete historical generation; it does not rewrite active producer tables.';

COMMIT;

-- Manual code rollback/read compatibility:
-- 1. Revert the 19 adapter decorators first; active tables remain unchanged.
-- 2. Retain these history tables for replay/audit. They are append-only evidence.
-- 3. Only after archival and explicit destructive authorization may the triggers,
--    functions, view and tables be dropped in reverse dependency order.
