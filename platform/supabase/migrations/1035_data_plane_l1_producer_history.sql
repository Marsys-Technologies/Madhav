-- Migration 1035: data_plane_l1_producer_history
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

-- A partition must be declared by open_l1_data_plane_generation before its
-- completion receipt can exist.  Keeping declaration separate from completion
-- preserves legitimate zero-row partitions without allowing an arbitrary key
-- to manufacture an empty completed generation.
CREATE TABLE IF NOT EXISTS public.l1_data_plane_partition_contexts (
    chart_id       UUID NOT NULL,
    asset_id       TEXT NOT NULL,
    generation_id TEXT NOT NULL,
    partition_key TEXT NOT NULL,
    opened_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
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
    FOREIGN KEY (chart_id, asset_id, generation_id)
      REFERENCES public.l1_data_plane_generations(chart_id, asset_id, generation_id)
      ON DELETE RESTRICT
);

-- Earlier drafts constrained one capture per logical row.  A few producers
-- legitimately finalize a row with an UPDATE inside the still-building
-- generation (notably dasha concurrency).  Preserve each revision append-only
-- and select the latest logical row at completion/read time.
DO $$
DECLARE
  v_constraint TEXT;
BEGIN
  FOR v_constraint IN
    SELECT conname
    FROM pg_constraint
    WHERE conrelid = 'public.l1_data_plane_row_snapshots'::regclass
      AND contype = 'u'
      AND pg_get_constraintdef(oid) LIKE
        '%chart_id, asset_id, generation_id, partition_key, source_table, row_identity%'
  LOOP
    EXECUTE format(
      'ALTER TABLE public.l1_data_plane_row_snapshots DROP CONSTRAINT %I',
      v_constraint
    );
  END LOOP;
END;
$$;

CREATE INDEX IF NOT EXISTS l1_data_plane_snapshot_capture_idx
  ON public.l1_data_plane_row_snapshots
  (chart_id, asset_id, generation_id, partition_key, source_table, row_identity,
   captured_at DESC, snapshot_id DESC);

CREATE TABLE IF NOT EXISTS public.l1_data_plane_fact_snapshots (
    fact_snapshot_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    row_snapshot_id             UUID NOT NULL REFERENCES public.l1_data_plane_row_snapshots(snapshot_id) ON DELETE RESTRICT,
    chart_id                    UUID NOT NULL,
    asset_id                    TEXT NOT NULL,
    generation_id              TEXT NOT NULL,
    partition_key              TEXT NOT NULL,
    source_table               TEXT NOT NULL,
    row_identity               TEXT NOT NULL,
    context_id                 TEXT NOT NULL,
    fact_identity              TEXT NOT NULL,
    fact_category              TEXT NOT NULL,
    fact_subject               TEXT NOT NULL,
    fact_key                   TEXT NOT NULL,
    grain_jsonb                JSONB NOT NULL,
    source_dependencies_jsonb  JSONB NOT NULL,
    unit                       TEXT,
    epistemic_class            TEXT NOT NULL,
    missingness_state          TEXT NOT NULL,
    missingness_reason         TEXT,
    verification_class         TEXT NOT NULL,
    value_num                  NUMERIC,
    value_text                 TEXT,
    value_bool                 BOOLEAN,
    value_jsonb                JSONB,
    captured_at                TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (missingness_state IN (
      'present','zero','unavailable','floored','inapplicable',
      'unqualified_source','failed','unexplored'
    )),
    CHECK (
      (missingness_state IN ('present','zero') AND
       num_nonnulls(value_num, value_text, value_bool, value_jsonb) = 1)
      OR
      (missingness_state NOT IN ('present','zero') AND
       num_nonnulls(value_num, value_text, value_bool, value_jsonb) = 0 AND
       missingness_reason IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS l1_data_plane_fact_latest_idx
  ON public.l1_data_plane_fact_snapshots
  (chart_id, asset_id, generation_id, source_table, row_identity, fact_key,
   captured_at DESC, fact_snapshot_id DESC);

-- High-volume daśā history stays typed and append-only without serializing each
-- 42-column row through a PL/pgSQL row trigger.  A composite retains the exact
-- active-table schema and supports set-based partition copies and revisions.
CREATE TABLE IF NOT EXISTS public.l1_data_plane_dasha_snapshots (
    dasha_snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id          UUID NOT NULL,
    asset_id          TEXT NOT NULL DEFAULT 'ga_dashas'
                           CHECK (asset_id = 'ga_dashas'),
    generation_id     TEXT NOT NULL,
    partition_key     TEXT NOT NULL,
    source_row        public.chart_dashas NOT NULL,
    captured_at       TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (chart_id, asset_id, generation_id)
      REFERENCES public.l1_data_plane_generations(chart_id, asset_id, generation_id)
      ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS l1_data_plane_dasha_latest_idx
  ON public.l1_data_plane_dasha_snapshots
  (chart_id, asset_id, generation_id, ((source_row).dasha_row_id),
   captured_at DESC, dasha_snapshot_id DESC);

-- Canonical semantic form for replay, generation digests and selection.  Row
-- and parent UUIDs are stable semantic hierarchy identities and remain in the
-- payload.  Build identity and observation time are transport metadata.  The
-- four material TIMESTAMPTZ values are represented as UTC epoch numerics so
-- session TimeZone cannot change equality or hashes.
CREATE OR REPLACE FUNCTION public.l1_data_plane_dasha_semantic_payload(
    p_row public.chart_dashas
) RETURNS JSONB
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
  SELECT jsonb_set(
    jsonb_set(
      jsonb_set(
        jsonb_set(
          to_jsonb(p_row) - 'build_id' - 'computed_at',
          '{start_iso}', to_jsonb(EXTRACT(EPOCH FROM
            NULLIF(to_jsonb(p_row)->>'start_iso', '')::timestamptz)), false
        ),
        '{end_iso}', to_jsonb(EXTRACT(EPOCH FROM
          NULLIF(to_jsonb(p_row)->>'end_iso', '')::timestamptz)), false
      ),
      '{next_dasha_start_iso}',
      COALESCE(to_jsonb(EXTRACT(EPOCH FROM
        NULLIF(to_jsonb(p_row)->>'next_dasha_start_iso', '')::timestamptz)), 'null'::jsonb),
      false
    ),
    '{anchored_solar_return_iso}',
    COALESCE(to_jsonb(EXTRACT(EPOCH FROM
      NULLIF(to_jsonb(p_row)->>'anchored_solar_return_iso', '')::timestamptz)), 'null'::jsonb),
    false
  )
$$;

-- Persist only the canonical hash beside the exact typed composite. This keeps
-- replay and generation completion set-based without restoring the rejected
-- per-row JSON/fact amplification path. The generated column also guarantees
-- that stored comparison material cannot drift from the canonical function.
ALTER TABLE public.l1_data_plane_dasha_snapshots
  ADD COLUMN IF NOT EXISTS semantic_digest TEXT
  GENERATED ALWAYS AS (
    encode(digest(
      public.l1_data_plane_dasha_semantic_payload(source_row)::text,
      'sha256'
    ), 'hex')
  ) STORED;

CREATE TABLE IF NOT EXISTS public.l1_data_plane_configuration_snapshots (
    configuration_snapshot_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    row_snapshot_id             UUID NOT NULL UNIQUE REFERENCES public.l1_data_plane_row_snapshots(snapshot_id) ON DELETE RESTRICT,
    chart_id                    UUID NOT NULL,
    asset_id                    TEXT NOT NULL,
    generation_id              TEXT NOT NULL,
    partition_key              TEXT NOT NULL,
    context_id                 TEXT NOT NULL,
    configuration_id           TEXT NOT NULL,
    configuration_version      TEXT NOT NULL,
    source_rule_id             TEXT NOT NULL,
    source_rule_version        TEXT NOT NULL,
    qualification_state        TEXT NOT NULL,
    observed_state             TEXT NOT NULL,
    admitted_state             TEXT NOT NULL,
    participants_jsonb         JSONB NOT NULL,
    satisfied_clauses_jsonb    JSONB NOT NULL,
    failed_clauses_jsonb       JSONB NOT NULL,
    exceptions_jsonb           JSONB NOT NULL,
    cancellations_jsonb        JSONB NOT NULL,
    constituent_fact_ids_jsonb JSONB NOT NULL,
    qualification_reason       TEXT NOT NULL,
    captured_at                TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
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

DO $l1_partition_fks$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l1_generation_partitions_declared_fk'
      AND conrelid = 'public.l1_data_plane_generation_partitions'::regclass
  ) THEN
    ALTER TABLE public.l1_data_plane_generation_partitions
      ADD CONSTRAINT l1_generation_partitions_declared_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
      REFERENCES public.l1_data_plane_partition_contexts(
        chart_id, asset_id, generation_id, partition_key
      ) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l1_row_snapshots_declared_fk'
      AND conrelid = 'public.l1_data_plane_row_snapshots'::regclass
  ) THEN
    ALTER TABLE public.l1_data_plane_row_snapshots
      ADD CONSTRAINT l1_row_snapshots_declared_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
      REFERENCES public.l1_data_plane_partition_contexts(
        chart_id, asset_id, generation_id, partition_key
      ) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l1_dasha_snapshots_declared_fk'
      AND conrelid = 'public.l1_data_plane_dasha_snapshots'::regclass
  ) THEN
    ALTER TABLE public.l1_data_plane_dasha_snapshots
      ADD CONSTRAINT l1_dasha_snapshots_declared_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
      REFERENCES public.l1_data_plane_partition_contexts(
        chart_id, asset_id, generation_id, partition_key
      ) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l1_configuration_snapshots_declared_fk'
      AND conrelid = 'public.l1_data_plane_configuration_snapshots'::regclass
  ) THEN
    ALTER TABLE public.l1_data_plane_configuration_snapshots
      ADD CONSTRAINT l1_configuration_snapshots_declared_fk
      FOREIGN KEY (chart_id, asset_id, generation_id, partition_key)
      REFERENCES public.l1_data_plane_partition_contexts(
        chart_id, asset_id, generation_id, partition_key
      ) ON DELETE RESTRICT;
  END IF;
END
$l1_partition_fks$;

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

DROP TRIGGER IF EXISTS l1_data_plane_partition_contexts_immutable
  ON public.l1_data_plane_partition_contexts;
CREATE TRIGGER l1_data_plane_partition_contexts_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_partition_contexts
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l1_data_plane_snapshots_immutable
  ON public.l1_data_plane_row_snapshots;
CREATE TRIGGER l1_data_plane_snapshots_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_row_snapshots
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l1_data_plane_facts_immutable
  ON public.l1_data_plane_fact_snapshots;
CREATE TRIGGER l1_data_plane_facts_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_fact_snapshots
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l1_data_plane_dashas_immutable
  ON public.l1_data_plane_dasha_snapshots;
CREATE TRIGGER l1_data_plane_dashas_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_dasha_snapshots
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

DROP TRIGGER IF EXISTS l1_data_plane_configurations_immutable
  ON public.l1_data_plane_configuration_snapshots;
CREATE TRIGGER l1_data_plane_configurations_immutable
BEFORE UPDATE OR DELETE ON public.l1_data_plane_configuration_snapshots
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change();

CREATE OR REPLACE FUNCTION public.l1_data_plane_guard_generation_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  v_recorded_partitions INTEGER;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'building'
       OR NEW.completed_partitions <> 0
       OR NEW.semantic_output_digest IS NOT NULL
       OR NEW.completed_at IS NOT NULL THEN
      RAISE EXCEPTION 'L1 producer generation must be inserted in empty building state';
    END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'L1 producer generations are append-only';
  END IF;
  IF OLD.status = 'complete' THEN
    RAISE EXCEPTION 'completed L1 producer generation is immutable';
  END IF;
  IF ROW(NEW.chart_id, NEW.asset_id, NEW.generation_id,
         NEW.correction_of_generation_id, NEW.contract_version,
         NEW.l0_semantic_release_id, NEW.l0_semantic_release_digest,
         NEW.l0_config_generation_id, NEW.l0_config_digest,
         NEW.base_context_jsonb, NEW.expected_partitions, NEW.opened_at)
     IS DISTINCT FROM
     ROW(OLD.chart_id, OLD.asset_id, OLD.generation_id,
         OLD.correction_of_generation_id, OLD.contract_version,
         OLD.l0_semantic_release_id, OLD.l0_semantic_release_digest,
         OLD.l0_config_generation_id, OLD.l0_config_digest,
         OLD.base_context_jsonb, OLD.expected_partitions, OLD.opened_at) THEN
    RAISE EXCEPTION 'L1 generation identity/context is immutable';
  END IF;

  SELECT count(*) INTO v_recorded_partitions
  FROM public.l1_data_plane_generation_partitions
  WHERE chart_id = OLD.chart_id AND asset_id = OLD.asset_id
    AND generation_id = OLD.generation_id;
  IF NEW.completed_partitions <> v_recorded_partitions THEN
    RAISE EXCEPTION 'L1 generation progress must equal recorded partitions';
  END IF;
  IF NEW.status = 'building' AND (
       NEW.semantic_output_digest IS NOT NULL OR NEW.completed_at IS NOT NULL
     ) THEN
    RAISE EXCEPTION 'invalid building L1 generation progress update';
  END IF;
  IF NEW.status = 'complete' AND (
       NEW.completed_partitions <> NEW.expected_partitions
       OR NEW.semantic_output_digest IS NULL
       OR NEW.completed_at IS NULL
     ) THEN
    RAISE EXCEPTION 'incomplete L1 generation cannot transition to complete';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS l1_data_plane_generation_immutable
  ON public.l1_data_plane_generations;
CREATE TRIGGER l1_data_plane_generation_immutable
BEFORE INSERT OR UPDATE OR DELETE ON public.l1_data_plane_generations
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_guard_generation_change();

CREATE OR REPLACE FUNCTION public.l1_data_plane_jsonb_has_nonfinite(p_value JSONB)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
  v_child JSONB;
  v_scalar TEXT;
BEGIN
  CASE jsonb_typeof(p_value)
    WHEN 'object' THEN
      FOR v_child IN SELECT value FROM jsonb_each(p_value) LOOP
        IF public.l1_data_plane_jsonb_has_nonfinite(v_child) THEN RETURN TRUE; END IF;
      END LOOP;
    WHEN 'array' THEN
      FOR v_child IN SELECT value FROM jsonb_array_elements(p_value) LOOP
        IF public.l1_data_plane_jsonb_has_nonfinite(v_child) THEN RETURN TRUE; END IF;
      END LOOP;
    WHEN 'string' THEN
      v_scalar := lower(p_value #>> '{}');
      RETURN v_scalar IN ('nan', 'infinity', '-infinity', 'inf', '-inf');
    ELSE
      RETURN FALSE;
  END CASE;
  RETURN FALSE;
END;
$$;

CREATE OR REPLACE FUNCTION public.l1_data_plane_fact_unit(
    p_source_table TEXT,
    p_fact_key TEXT,
    p_source_row JSONB
) RETURNS TEXT
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN p_source_table = 'chart_facts' THEN p_source_row->>'unit'
    WHEN p_source_table = 'ga_transit_anchors' AND p_fact_key = 'natal_degree_absolute' THEN 'degree'
    WHEN p_source_table = 'ga_transit_anchors' AND p_fact_key = 'natal_house_from_moon' THEN 'house_number'
    WHEN p_source_table = 'ga_condition_composite' AND p_fact_key IN (
      'dignity_score_d1','varga_dignity_composite','condition_score'
    ) THEN 'score_0_1'
    WHEN p_source_table = 'ga_condition_composite' AND p_fact_key = 'speed_degrees_per_day' THEN 'degree_per_day'
    WHEN p_source_table = 'ga_condition_composite' AND p_fact_key = 'combustion_arc_from_sun' THEN 'degree'
    WHEN p_source_table = 'ga_yoga_firings' AND p_fact_key = 'strength' THEN 'score_0_1'
    WHEN p_source_table = 'ga_yoga_firings' AND p_fact_key = 'partial_formation_pct' THEN 'percent'
    WHEN p_fact_key ~ '(^|_)(start|end)(_iso|_utc)?$' THEN 'instant'
    WHEN p_fact_key ~ '(^|_)(longitude|degree|orb|arc)(_|$)' THEN 'degree'
    WHEN p_fact_key ~ '^is_|_active$|_flag$' THEN 'boolean'
    ELSE NULL
  END
$$;

-- Only fields whose semantics are explicitly specified are projected as atomic
-- facts.  In particular, interval, relation and clock rows remain bounded typed
-- row envelopes instead of being expanded into dozens of synchronous child
-- inserts.  The condition composite is small (45 rows/chart) and is the one
-- denormalized surface whose components must remain independently consumable.
CREATE OR REPLACE FUNCTION public.l1_data_plane_material_fact_specs(
    p_source_table TEXT
) RETURNS TABLE (
    source_table TEXT,
    fact_key TEXT,
    epistemic_class TEXT,
    unit TEXT,
    verification_class TEXT,
    source_fact_keys TEXT[],
    subject_scope TEXT,
    producer_assets TEXT[],
    reference_relations TEXT[]
)
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT * FROM (VALUES
    ('ga_condition_composite','dignity_d1','rule_derived',NULL,'dignity_rule_v1',ARRAY['sign','degree_in_sign']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY['bg_dignity_reference']::TEXT[]),
    ('ga_condition_composite','dignity_score_d1','rule_derived','score_0_1','dignity_rule_v1',ARRAY['sign','degree_in_sign']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY['bg_dignity_reference']::TEXT[]),
    ('ga_condition_composite','varga_dignity_spread','deterministic_derivation',NULL,'varga_source_rows',ARRAY[]::TEXT[],'self',ARRAY['ga_vargas']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','varga_dignity_composite','deterministic_derivation','score_0_1','condition_formula_v1',ARRAY[]::TEXT[],'self',ARRAY['ga_vargas']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','avastha_baladi','rule_derived',NULL,'avastha_rule_v1',ARRAY['degree_in_sign']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','avastha_jagradadi','rule_derived',NULL,'avastha_rule_v1',ARRAY['sign','degree_in_sign']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','avastha_deeptaadi','rule_derived',NULL,'avastha_rule_v1',ARRAY['sign','degree_in_sign','speed_dps','retrograde_flag','longitude_sidereal','longitude']::TEXT[],'self_sun',ARRAY['ga_positions']::TEXT[],ARRAY['bg_combustion_orbs']::TEXT[]),
    ('ga_condition_composite','avastha_lajjitaadi','rule_derived',NULL,'source_state_only',ARRAY[]::TEXT[],'self',ARRAY['ga_condition']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','avastha_sayanadi','rule_derived',NULL,'source_state_only',ARRAY[]::TEXT[],'self',ARRAY['ga_condition']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','motion_state','deterministic_derivation',NULL,'motion_classifier_v1',ARRAY['speed_dps']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','speed_degrees_per_day','astronomical','degree_per_day','source_position_fact',ARRAY['speed_dps']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','is_retrograde','astronomical',NULL,'source_position_fact',ARRAY['retrograde_flag','speed_dps']::TEXT[],'self',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','combustion_arc_from_sun','deterministic_derivation','degree','combustion_formula_v1',ARRAY['longitude_sidereal','longitude']::TEXT[],'self_sun',ARRAY['ga_positions']::TEXT[],ARRAY['bg_combustion_orbs']::TEXT[]),
    ('ga_condition_composite','is_combust','rule_derived',NULL,'combustion_rule_v1',ARRAY['longitude_sidereal','longitude','retrograde_flag']::TEXT[],'self_sun',ARRAY['ga_positions']::TEXT[],ARRAY['bg_combustion_orbs']::TEXT[]),
    ('ga_condition_composite','is_deeply_combust','rule_derived',NULL,'combustion_rule_v1',ARRAY['longitude_sidereal','longitude','retrograde_flag']::TEXT[],'self_sun',ARRAY['ga_positions']::TEXT[],ARRAY['bg_combustion_orbs']::TEXT[]),
    ('ga_condition_composite','naisargika_relation','rule_derived',NULL,'friendship_rule_v1',ARRAY['sign']::TEXT[],'all',ARRAY['ga_positions']::TEXT[],ARRAY['bg_graha_naisargika_friendship']::TEXT[]),
    ('ga_condition_composite','tatkalika_relation','rule_derived',NULL,'friendship_rule_v1',ARRAY['house_d1','house','sign']::TEXT[],'all',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','panchadha_relation','rule_derived',NULL,'friendship_rule_v1',ARRAY['house_d1','house','sign']::TEXT[],'all',ARRAY['ga_positions']::TEXT[],ARRAY['bg_graha_naisargika_friendship']::TEXT[]),
    ('ga_condition_composite','graha_yuddha_with','rule_derived',NULL,'graha_yuddha_rule_v1',ARRAY['sign','longitude_sidereal','longitude']::TEXT[],'all',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','graha_yuddha_result','rule_derived',NULL,'graha_yuddha_rule_v1',ARRAY['sign','longitude_sidereal','longitude']::TEXT[],'all',ARRAY['ga_positions']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','condition_score','rule_derived','score_0_1','condition_formula_v1',ARRAY['sign','degree_in_sign','speed_dps','retrograde_flag','longitude_sidereal','longitude']::TEXT[],'self_sun',ARRAY['ga_positions','ga_vargas']::TEXT[],ARRAY['bg_dignity_reference','bg_combustion_orbs']::TEXT[]),
    ('ga_condition_composite','condition_formula_version','deterministic_derivation',NULL,'source_declared_version',ARRAY[]::TEXT[],'self',ARRAY['ga_condition']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','condition_score_breakdown','rule_derived',NULL,'condition_formula_v1',ARRAY['sign','degree_in_sign','speed_dps','retrograde_flag','longitude_sidereal','longitude']::TEXT[],'self_sun',ARRAY['ga_positions','ga_vargas']::TEXT[],ARRAY['bg_dignity_reference','bg_combustion_orbs']::TEXT[]),
    ('ga_condition_composite','peak_dasha_periods','rule_derived',NULL,'condition_dasha_classifier_v1',ARRAY[]::TEXT[],'self',ARRAY['ga_dashas','ga_condition']::TEXT[],ARRAY[]::TEXT[]),
    ('ga_condition_composite','weak_dasha_periods','rule_derived',NULL,'condition_dasha_classifier_v1',ARRAY[]::TEXT[],'self',ARRAY['ga_dashas','ga_condition']::TEXT[],ARRAY[]::TEXT[])
  ) AS spec(
    source_table, fact_key, epistemic_class, unit, verification_class,
    source_fact_keys, subject_scope, producer_assets, reference_relations
  )
  WHERE spec.source_table = p_source_table
$$;

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
  v_declared INTEGER;
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
    -- A generation spans every declared writer partition.  Its base context
    -- must therefore remain invariant when multi-ayanamsha writers reopen it;
    -- row snapshots below carry the exact row/partition ayanamsha.
    'ayanamsha_id', 'mixed_or_invariant',
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

  INSERT INTO public.l1_data_plane_partition_contexts (
    chart_id, asset_id, generation_id, partition_key
  ) VALUES (
    p_chart_id, p_asset_id, p_generation_id, p_partition_key
  ) ON CONFLICT DO NOTHING;
  SELECT count(*) INTO v_declared
  FROM public.l1_data_plane_partition_contexts
  WHERE chart_id = p_chart_id AND asset_id = p_asset_id
    AND generation_id = p_generation_id;
  IF v_declared > v_existing.expected_partitions THEN
    RAISE EXCEPTION 'generation declared % partitions but expected %',
      v_declared, v_existing.expected_partitions;
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
  v_generation_status TEXT;
  v_context JSONB;
  v_semantic JSONB;
  v_identity_parts TEXT[] := ARRAY[]::TEXT[];
  v_identity TEXT;
  v_context_id TEXT;
  v_digest TEXT;
  v_existing_digest TEXT;
  v_snapshot_id UUID;
  v_key TEXT;
  v_value JSONB;
  v_value_type TEXT;
  v_fact_identity TEXT;
  v_fact_missingness TEXT;
  v_fact_reason TEXT;
  v_value_num NUMERIC;
  v_value_text TEXT;
  v_value_bool BOOLEAN;
  v_value_jsonb JSONB;
  v_deps TEXT[];
  v_dependencies JSONB;
  v_missingness TEXT;
  v_epistemic TEXT;
  v_yoga_rule JSONB;
BEGIN
  -- Compatibility: direct legacy SQL/CLI paths remain usable but do not claim
  -- a governed runtime generation unless the adapter opened one explicitly.
  IF v_asset IS NULL OR v_asset = '' THEN
    RETURN NEW;
  END IF;
  IF v_chart_text IS NULL OR v_generation IS NULL OR v_partition IS NULL THEN
    RAISE EXCEPTION 'incomplete transaction-local L1 producer context';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.l1_data_plane_partition_contexts
    WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
      AND generation_id = v_generation AND partition_key = v_partition
  ) THEN
    RAISE EXCEPTION 'L1 partition was not declared before % insert', TG_TABLE_NAME;
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

  SELECT base_context_jsonb, status INTO v_base, v_generation_status
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
    'ayanamsha_id', COALESCE(
      v_row->>'ayanamsha_id',
      CASE
        WHEN v_partition ~ '^ayanamsha[:_]' THEN
          regexp_replace(v_partition, '^ayanamsha[:_]', '')
        ELSE v_base->>'ayanamsha_id'
      END
    ),
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

  IF public.l1_data_plane_jsonb_has_nonfinite(v_row) THEN
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
  v_dependencies := jsonb_build_object(
    'producer_assets', to_jsonb(COALESCE(v_deps, ARRAY[]::TEXT[])),
    'constituent_fact_ids', COALESCE(
      NULLIF(v_row->'constituent_fact_ids', 'null'::jsonb),
      NULLIF(v_row->'constituent_facts_array', 'null'::jsonb),
      NULLIF(v_row->'constituent_planets', 'null'::jsonb),
      '[]'::jsonb
    )
  );
  SELECT semantic_digest INTO v_existing_digest
  FROM public.l1_data_plane_row_snapshots
  WHERE chart_id = v_chart_text::uuid AND asset_id = v_asset
    AND generation_id = v_generation AND partition_key = v_partition
    AND source_table = TG_TABLE_NAME AND row_identity = v_identity
  ORDER BY captured_at DESC, snapshot_id DESC
  LIMIT 1;
  IF v_generation_status = 'complete' THEN
    IF v_existing_digest IS NULL THEN
      RAISE EXCEPTION 'complete generation % cannot admit new row % %',
        v_generation, TG_TABLE_NAME, v_identity;
    END IF;
    IF v_existing_digest <> v_digest THEN
      RAISE EXCEPTION 'complete generation % replay changed output for % %',
        v_generation, TG_TABLE_NAME, v_identity;
    END IF;
    RETURN NEW;
  END IF;
  IF v_existing_digest IS NOT NULL THEN
    IF v_existing_digest = v_digest THEN
      RETURN NEW;
    END IF;
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
    v_dependencies,
    v_epistemic, v_missingness,
    COALESCE(v_row->>'verification_pass_status', v_row->>'verification_method', 'unverified'),
    v_row->>'unit', v_semantic, v_row, v_digest
  ) RETURNING snapshot_id INTO v_snapshot_id;

  -- Schema-aware typed projection. chart_facts already declares one atomic
  -- fact.  Only an explicit material-field specification may decompose another
  -- table; this prevents high-volume interval rows from multiplying writes and
  -- prevents an asset-level epistemic label from being copied onto every field.
  IF TG_TABLE_NAME = 'chart_facts' THEN
    v_fact_missingness := v_missingness;
    v_fact_reason := CASE WHEN v_fact_missingness IN ('present', 'zero') THEN NULL
      ELSE COALESCE(v_row #>> '{fact_value_jsonb,reason}', v_row->>'citation_human',
                    'source fact carries no typed value') END;
    v_value_num := CASE WHEN v_row->>'fact_value_num' IS NOT NULL
      THEN (v_row->>'fact_value_num')::numeric ELSE NULL END;
    v_value_text := v_row->>'fact_value_text';
    v_value_jsonb := NULLIF(v_row->'fact_value_jsonb', 'null'::jsonb);
    IF v_fact_missingness NOT IN ('present', 'zero') THEN
      v_value_num := NULL; v_value_text := NULL; v_value_jsonb := NULL;
    END IF;
    INSERT INTO public.l1_data_plane_fact_snapshots (
      row_snapshot_id, chart_id, asset_id, generation_id, partition_key,
      source_table, row_identity, context_id, fact_identity, fact_category,
      fact_subject, fact_key, grain_jsonb, source_dependencies_jsonb,
      unit, epistemic_class, missingness_state,
      missingness_reason, verification_class, value_num, value_text, value_jsonb
    ) VALUES (
      v_snapshot_id, v_chart_text::uuid, v_asset, v_generation, v_partition,
      TG_TABLE_NAME, v_identity, v_context_id,
      COALESCE(v_row->>'fact_id', encode(digest(v_context_id || '|' || v_identity, 'sha256'), 'hex')),
      COALESCE(v_row->>'fact_category', v_asset),
      COALESCE(v_row->>'fact_subject', v_identity),
      COALESCE(v_row->>'fact_key', 'value'),
      jsonb_build_object(
        'source_table', TG_TABLE_NAME,
        'row_identity', v_identity,
        'fact_category', COALESCE(v_row->>'fact_category', v_asset),
        'fact_subject', COALESCE(v_row->>'fact_subject', v_identity),
        'fact_key', COALESCE(v_row->>'fact_key', 'value')
      ),
      v_dependencies,
      public.l1_data_plane_fact_unit(TG_TABLE_NAME, COALESCE(v_row->>'fact_key', 'value'), v_row),
      v_epistemic, v_fact_missingness, v_fact_reason,
      COALESCE(v_row->>'verification_pass_status', v_row->>'verification_method', 'unverified'),
      v_value_num, v_value_text, v_value_jsonb
    );
  ELSIF TG_TABLE_NAME = 'ga_condition_composite' THEN
    -- One set-based statement projects the bounded, explicit condition field
    -- registry.  Dependencies name the actual chart_facts rows used by the
    -- writer, the exact producer surfaces and any reference relation.  Varga
    -- and dasha rows use stable natural/row identities because those source
    -- tables do not expose chart_facts-style fact IDs.
    INSERT INTO public.l1_data_plane_fact_snapshots (
      row_snapshot_id, chart_id, asset_id, generation_id, partition_key,
      source_table, row_identity, context_id, fact_identity, fact_category,
      fact_subject, fact_key, grain_jsonb, source_dependencies_jsonb,
      unit, epistemic_class, missingness_state, missingness_reason,
      verification_class, value_num, value_text, value_bool, value_jsonb
    )
    SELECT
      v_snapshot_id, v_chart_text::uuid, v_asset, v_generation, v_partition,
      TG_TABLE_NAME, v_identity, v_context_id,
      encode(digest(
        v_context_id || '|' || TG_TABLE_NAME || '|' || v_identity || '|' || spec.fact_key,
        'sha256'
      ), 'hex'),
      'ga_condition_component', COALESCE(v_row->>'graha', v_identity), spec.fact_key,
      jsonb_build_object(
        'source_table', TG_TABLE_NAME, 'natural_key', v_identity_parts,
        'field', spec.fact_key, 'grain', 'chart-ayanamsha-graha-component'
      ),
      jsonb_build_object(
        'producer_assets', to_jsonb(spec.producer_assets),
        'constituent_fact_ids', COALESCE((
          SELECT jsonb_agg(DISTINCT cf.fact_id ORDER BY cf.fact_id)
          FROM public.chart_facts cf
          WHERE cf.chart_id = v_chart_text::uuid
            AND cf.ayanamsha_id = v_row->>'ayanamsha_id'
            AND cf.fact_key = ANY(spec.source_fact_keys)
            AND (
              spec.subject_scope = 'all'
              OR cf.fact_subject = CASE lower(v_row->>'graha')
                WHEN 'sun' THEN 'SUN' WHEN 'moon' THEN 'MOON'
                WHEN 'mars' THEN 'MAR' WHEN 'mercury' THEN 'MER'
                WHEN 'jupiter' THEN 'JUP' WHEN 'venus' THEN 'VEN'
                WHEN 'saturn' THEN 'SAT' WHEN 'rahu' THEN 'RAH_MEAN'
                WHEN 'ketu' THEN 'KET_MEAN' ELSE upper(v_row->>'graha') END
              OR (spec.subject_scope = 'self_sun' AND cf.fact_subject = 'SUN')
            )
        ), '[]'::jsonb),
        'source_row_identities', CASE
          WHEN 'ga_vargas' = ANY(spec.producer_assets) THEN COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'source_table', 'chart_divisionals',
                'natural_key', jsonb_build_array(
                  'chart_id=' || cd.chart_id::text,
                  'graha=' || cd.graha,
                  'ayanamsha_id=' || cd.ayanamsha_id,
                  'varga=' || cd.varga,
                  'fact_category=' || cd.fact_category,
                  'fact_key=' || cd.fact_key
                )
              ) ORDER BY cd.varga, cd.fact_category, cd.fact_key
            )
            FROM public.chart_divisionals cd
            WHERE cd.chart_id = v_chart_text::uuid
              AND cd.ayanamsha_id = v_row->>'ayanamsha_id'
              AND lower(cd.graha) = lower(v_row->>'graha')
              AND cd.fact_category IN ('varga_position', 'varga_dignity')
              AND cd.fact_key IN ('sign', 'dignity', 'overall_dignity_score')
          ), '[]'::jsonb)
          WHEN spec.fact_key IN ('peak_dasha_periods', 'weak_dasha_periods') THEN
            COALESCE((
              SELECT jsonb_agg(jsonb_build_object(
                'source_table', 'chart_dashas',
                'row_identity', item->>'source_dasha_row_id'
              ) ORDER BY item->>'source_dasha_row_id')
              FROM jsonb_array_elements(CASE
                WHEN jsonb_typeof(v_semantic->spec.fact_key) = 'array'
                THEN v_semantic->spec.fact_key ELSE '[]'::jsonb END) item
              WHERE item ? 'source_dasha_row_id'
            ), '[]'::jsonb)
          ELSE '[]'::jsonb
        END,
        'reference_relations', to_jsonb(spec.reference_relations)
      ),
      spec.unit, spec.epistemic_class,
      CASE
        WHEN jsonb_typeof(v_semantic->spec.fact_key) IS NULL
          OR jsonb_typeof(v_semantic->spec.fact_key) = 'null' THEN 'unavailable'
        WHEN jsonb_typeof(v_semantic->spec.fact_key) = 'number'
          AND (v_semantic->>spec.fact_key)::numeric = 0 THEN 'zero'
        ELSE 'present'
      END,
      CASE
        WHEN jsonb_typeof(v_semantic->spec.fact_key) IS NULL
          OR jsonb_typeof(v_semantic->spec.fact_key) = 'null'
        THEN 'source column is NULL in this generation'
        ELSE NULL
      END,
      spec.verification_class,
      CASE WHEN jsonb_typeof(v_semantic->spec.fact_key) = 'number'
        THEN (v_semantic->>spec.fact_key)::numeric ELSE NULL END,
      CASE WHEN jsonb_typeof(v_semantic->spec.fact_key) = 'string'
        THEN v_semantic->>spec.fact_key ELSE NULL END,
      CASE WHEN jsonb_typeof(v_semantic->spec.fact_key) = 'boolean'
        THEN (v_semantic->>spec.fact_key)::boolean ELSE NULL END,
      CASE WHEN jsonb_typeof(v_semantic->spec.fact_key) IN ('array', 'object')
        THEN v_semantic->spec.fact_key ELSE NULL END
    FROM public.l1_data_plane_material_fact_specs(TG_TABLE_NAME) spec;
  END IF;

  -- Yoga rows are configuration observations, not merely opaque JSON.  The
  -- active schema has no admitted L0 rule-qualification field, so preserve the
  -- observed firing separately while keeping the doctrinal arm unreachable.
  IF TG_TABLE_NAME = 'ga_yoga_firings' THEN
    SELECT formation_rule_jsonb INTO v_yoga_rule
    FROM public.brahma_yoga_catalog
    WHERE canonical_id = v_row->>'yoga_canonical_id';

    INSERT INTO public.l1_data_plane_configuration_snapshots (
      row_snapshot_id, chart_id, asset_id, generation_id, partition_key,
      context_id, configuration_id, configuration_version, source_rule_id,
      source_rule_version, qualification_state, observed_state, admitted_state,
      participants_jsonb, satisfied_clauses_jsonb, failed_clauses_jsonb,
      exceptions_jsonb, cancellations_jsonb, constituent_fact_ids_jsonb,
      qualification_reason
    ) VALUES (
      v_snapshot_id, v_chart_text::uuid, v_asset, v_generation, v_partition,
      v_context_id, v_row->>'yoga_canonical_id',
      'observed-yoga-configuration-v1',
      CASE WHEN v_yoga_rule IS NULL THEN 'UNAVAILABLE'
        ELSE 'catalog:yoga:' || (v_row->>'yoga_canonical_id') END,
      CASE WHEN v_yoga_rule IS NULL THEN 'UNAVAILABLE'
        ELSE 'sha256:' || encode(digest(v_yoga_rule::text, 'sha256'), 'hex') END,
      'UNQUALIFIED_SOURCE',
      CASE WHEN COALESCE((v_row->>'fired')::boolean, false)
        THEN CASE WHEN COALESCE((v_row->>'is_partial')::boolean, false) THEN 'partial' ELSE 'formed' END
        ELSE 'not_formed' END,
      'unqualified_source',
      COALESCE((
        SELECT jsonb_agg(participant ORDER BY role_order, ordinal)
        FROM (
          SELECT 1 AS role_order, p.ordinal,
            jsonb_build_object(
              'role', 'constituent_graha', 'subject', p.value #>> '{}'
            ) AS participant
          FROM jsonb_array_elements(CASE
            WHEN jsonb_typeof(v_row->'constituent_planets') = 'array'
            THEN v_row->'constituent_planets' ELSE '[]'::jsonb END)
            WITH ORDINALITY AS p(value, ordinal)
          UNION ALL
          SELECT 2 AS role_order, h.ordinal,
            jsonb_build_object(
              'role', 'constituent_house',
              'subject', 'HOUSE_' || (h.value #>> '{}')
            ) AS participant
          FROM jsonb_array_elements(CASE
            WHEN jsonb_typeof(v_row->'constituent_houses') = 'array'
            THEN v_row->'constituent_houses' ELSE '[]'::jsonb END)
            WITH ORDINALITY AS h(value, ordinal)
        ) typed_participants
      ), '[]'::jsonb),
      CASE WHEN COALESCE((v_row->>'fired')::boolean, false) THEN
        jsonb_build_array(
          jsonb_build_object(
            'clause_id', 'observed_catalog_formation_rule',
            'rule', v_yoga_rule,
            'result', 'observed_satisfied_not_admitted'
          ),
          jsonb_build_object(
            'clause_id', 'constituent_fact_ancestry',
            'result', CASE
              WHEN jsonb_typeof(v_row->'constituent_fact_ids') = 'array'
               AND jsonb_array_length(v_row->'constituent_fact_ids') > 0
              THEN 'present' ELSE 'absent' END
          )
        )
      ELSE '[]'::jsonb END,
      jsonb_build_array(
        jsonb_build_object(
          'clause_id', 'admitted_l0_rule_qualification',
          'result', 'missing'
        ),
        jsonb_build_object(
          'clause_id', 'exact_catalog_rule',
          'result', CASE WHEN v_yoga_rule IS NULL THEN 'missing' ELSE 'observed_only' END
        )
      ),
      CASE WHEN v_row->>'bhanga_rule_fired' IS NULL THEN '[]'::jsonb
        ELSE jsonb_build_array(jsonb_build_object(
          'role', 'observed_exception_rule',
          'rule_id', v_row->>'bhanga_rule_fired'
        )) END,
      CASE WHEN COALESCE((v_row->>'bhanga_active')::boolean, false)
        THEN jsonb_build_array(jsonb_build_object(
          'role', 'observed_cancellation', 'state', 'bhanga_active'
        )) ELSE '[]'::jsonb END,
      COALESCE(NULLIF(v_row->'constituent_fact_ids', 'null'::jsonb), '[]'::jsonb),
      CASE WHEN v_yoga_rule IS NULL THEN
        'catalog rule and admitted L0 qualification witness are unavailable; doctrinal arm is unreachable'
      ELSE
        'catalog rule is preserved by content digest but has no admitted L0 qualification witness; doctrinal arm is unreachable'
      END
    );
  END IF;
  RETURN NEW;
END;
$$;

-- Daśā is the deliberate high-volume exception to row-trigger capture.  Its
-- writer uses COPY for roughly 536k rows across 35 independently committed
-- system/ayanamsha partitions.  Capture each completed partition in one
-- set-based statement, and capture only changed rows in the final post-pass.
-- This preserves the same immutable generation envelope without defeating COPY
-- with one PL/pgSQL trigger invocation per source row.
CREATE OR REPLACE FUNCTION public.capture_l1_data_plane_dasha_partition(
    p_chart_id UUID,
    p_generation_id TEXT,
    p_partition_key TEXT,
    p_rows_inserted INTEGER
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  v_status TEXT;
  v_system_id TEXT;
  v_ayanamsha_id TEXT;
  v_active_rows INTEGER;
BEGIN
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
    IF v_system_id = '' OR v_ayanamsha_id = '' THEN
      RAISE EXCEPTION 'invalid dasha partition key %', p_partition_key;
    END IF;
    SELECT count(*) INTO v_active_rows
    FROM public.chart_dashas d
    WHERE d.chart_id = p_chart_id
      AND d.build_id::text = p_generation_id
      AND d.system_id = v_system_id
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
            d.system_id = v_system_id AND d.ayanamsha_id = v_ayanamsha_id
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
              (s.source_row).system_id = v_system_id
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
      d.system_id = v_system_id AND d.ayanamsha_id = v_ayanamsha_id
    ))
    AND (previous.source_row IS NULL OR previous.semantic_digest IS DISTINCT FROM
      encode(digest(
        public.l1_data_plane_dasha_semantic_payload(d)::text,
        'sha256'
      ), 'hex'));
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
  v_declared INTEGER;
  v_digest TEXT;
  v_status TEXT;
  v_existing_generation_digest TEXT;
BEGIN
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
  SELECT DISTINCT ON (result.source_table, result.row_identity)
    result.source_table, result.row_identity, result.context_id,
    result.calculation_context_jsonb, result.grain_jsonb,
    result.source_dependencies_jsonb, result.epistemic_class,
    result.missingness_state, result.verification_class, result.unit,
    result.semantic_payload_jsonb, result.semantic_digest
  FROM (
    SELECT s.source_table, s.row_identity, s.context_id,
           s.calculation_context_jsonb, s.grain_jsonb,
           s.source_dependencies_jsonb, s.epistemic_class,
           s.missingness_state, s.verification_class, s.unit,
           s.semantic_payload_jsonb, s.semantic_digest,
           s.captured_at, s.snapshot_id AS ordering_id
    FROM public.l1_data_plane_row_snapshots s
    JOIN public.l1_data_plane_generations g
      USING (chart_id, asset_id, generation_id)
    WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id
      AND s.generation_id = p_generation_id AND g.status = 'complete'

    UNION ALL

    SELECT
      'chart_dashas'::TEXT,
      'dasha_row_id=' || (s.source_row).dasha_row_id::text,
      'l1ctx:' || substr(encode(digest(
        (((g.base_context_jsonb || jsonb_build_object(
          'ayanamsha_id', (s.source_row).ayanamsha_id,
          'method_id', (s.source_row).system_id,
          'varga', 'D1', 'varga_formula', 'not_applicable',
          'varga_domain', 'row_declared_or_not_applicable',
          'karaka_school', 'not_applicable'
        )) - 'build_id') - 'generation_id')::text,
        'sha256'
      ), 'hex'), 1, 24),
      g.base_context_jsonb || jsonb_build_object(
        'ayanamsha_id', (s.source_row).ayanamsha_id,
        'method_id', (s.source_row).system_id,
        'varga', 'D1', 'varga_formula', 'not_applicable',
        'varga_domain', 'row_declared_or_not_applicable',
        'karaka_school', 'not_applicable'
      ),
      jsonb_build_object(
        'source_table', 'chart_dashas',
        'natural_key', jsonb_build_array(
          'dasha_row_id=' || (s.source_row).dasha_row_id::text
        )
      ),
      jsonb_build_object(
        'producer_assets', to_jsonb(COALESCE(r.depends_on, ARRAY[]::TEXT[])),
        'constituent_fact_ids', '[]'::jsonb
      ),
      'deterministic_derivation'::TEXT,
      'present'::TEXT,
      COALESCE(to_jsonb(s.source_row)->>'verification_pass_status',
               to_jsonb(s.source_row)->>'verification_method', 'runtime_snapshot'),
      NULL::TEXT,
      public.l1_data_plane_dasha_semantic_payload(s.source_row),
      s.semantic_digest,
      s.captured_at,
      s.dasha_snapshot_id
    FROM public.l1_data_plane_dasha_snapshots s
    JOIN public.l1_data_plane_generations g
      ON g.chart_id = s.chart_id AND g.asset_id = s.asset_id
     AND g.generation_id = s.generation_id AND g.status = 'complete'
    LEFT JOIN public.asset_registry r ON r.asset_id = 'ga_dashas'
    WHERE p_asset_id = 'ga_dashas'
      AND s.chart_id = p_chart_id AND s.generation_id = p_generation_id
  ) result
  ORDER BY result.source_table, result.row_identity,
           result.captured_at DESC, result.ordering_id DESC
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
SELECT DISTINCT ON (s.chart_id, s.asset_id, s.source_table, s.row_identity) s.*
FROM public.l1_data_plane_generation_heads h
JOIN public.l1_data_plane_row_snapshots s
  ON s.chart_id = h.chart_id
 AND s.asset_id = h.asset_id
 AND s.generation_id = h.current_generation_id
ORDER BY s.chart_id, s.asset_id, s.source_table, s.row_identity,
         s.captured_at DESC, s.snapshot_id DESC;

CREATE OR REPLACE VIEW public.l1_data_plane_current_dashas AS
SELECT DISTINCT ON (
  s.chart_id, s.asset_id, (s.source_row).dasha_row_id
) s.*
FROM public.l1_data_plane_generation_heads h
JOIN public.l1_data_plane_dasha_snapshots s
  ON s.chart_id = h.chart_id
 AND s.asset_id = h.asset_id
 AND s.generation_id = h.current_generation_id
ORDER BY s.chart_id, s.asset_id, (s.source_row).dasha_row_id,
         s.captured_at DESC, s.dasha_snapshot_id DESC;

CREATE OR REPLACE VIEW public.l1_data_plane_current_facts AS
SELECT DISTINCT ON (
  f.chart_id, f.asset_id, f.source_table, f.row_identity, f.fact_key
) f.*
FROM public.l1_data_plane_generation_heads h
JOIN public.l1_data_plane_fact_snapshots f
  ON f.chart_id = h.chart_id
 AND f.asset_id = h.asset_id
 AND f.generation_id = h.current_generation_id
ORDER BY f.chart_id, f.asset_id, f.source_table, f.row_identity, f.fact_key,
         f.captured_at DESC, f.fact_snapshot_id DESC;

CREATE OR REPLACE VIEW public.l1_data_plane_current_configurations AS
SELECT DISTINCT ON (
  c.chart_id, c.asset_id, c.configuration_id, c.source_rule_id
) c.*
FROM public.l1_data_plane_generation_heads h
JOIN public.l1_data_plane_configuration_snapshots c
  ON c.chart_id = h.chart_id
 AND c.asset_id = h.asset_id
 AND c.generation_id = h.current_generation_id
ORDER BY c.chart_id, c.asset_id, c.configuration_id, c.source_rule_id,
         c.captured_at DESC, c.configuration_snapshot_id DESC;

-- One trigger per active output table. The transaction-local asset id keeps
-- shared chart_facts rows owned by the writer that emitted them.
DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.chart_facts;
CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.chart_facts
FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row('fact_id');

DROP TRIGGER IF EXISTS l1_data_plane_capture ON public.chart_dashas;
-- Intentionally no row trigger: complete_l1_data_plane_partition performs one
-- set-based capture per dasha partition so COPY retains its bulk behavior.

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

-- Close PostgreSQL's default PUBLIC EXECUTE surface and declare the intended
-- future build-role privileges explicitly. Production currently runs both the
-- migration executor and build path as amjis_app, which owns objects it creates;
-- these grants therefore do not claim owner isolation. RI-01 remains held until
-- the separately governed role/credential cutover removes that owner bypass.
DO $l1_role_preflight$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_orchestrator') THEN
    RAISE EXCEPTION
      'E1035_PREFLIGHT_MISSING_ROLE: role_orchestrator must exist before L1 history installation';
  END IF;
END
$l1_role_preflight$;

REVOKE ALL ON TABLE
  public.l1_data_plane_generations,
  public.l1_data_plane_generation_partitions,
  public.l1_data_plane_partition_contexts,
  public.l1_data_plane_row_snapshots,
  public.l1_data_plane_fact_snapshots,
  public.l1_data_plane_dasha_snapshots,
  public.l1_data_plane_configuration_snapshots,
  public.l1_data_plane_generation_heads,
  public.l1_data_plane_current_rows,
  public.l1_data_plane_current_dashas,
  public.l1_data_plane_current_facts,
  public.l1_data_plane_current_configurations
FROM PUBLIC, role_orchestrator;

GRANT SELECT ON TABLE
  public.l1_data_plane_generations,
  public.l1_data_plane_generation_heads,
  public.l1_data_plane_generation_partitions,
  public.l1_data_plane_partition_contexts,
  public.l1_data_plane_row_snapshots,
  public.l1_data_plane_fact_snapshots,
  public.l1_data_plane_dasha_snapshots,
  public.l1_data_plane_configuration_snapshots,
  public.l1_data_plane_current_rows,
  public.l1_data_plane_current_dashas,
  public.l1_data_plane_current_facts,
  public.l1_data_plane_current_configurations
TO role_orchestrator;

DO $l1_function_acl$
DECLARE
  v_function regprocedure;
BEGIN
  FOR v_function IN
    SELECT p.oid::regprocedure
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND (
        p.proname LIKE 'l1_data_plane_%'
        OR p.proname IN (
          'open_l1_data_plane_generation',
          'capture_l1_data_plane_dasha_partition',
          'complete_l1_data_plane_partition',
          'select_l1_data_plane_generation',
          'rollback_l1_data_plane_generation'
        )
      )
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC', v_function);
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM role_orchestrator', v_function);
  END LOOP;
END
$l1_function_acl$;

GRANT EXECUTE ON FUNCTION public.open_l1_data_plane_generation(
  UUID, TEXT, TEXT, TEXT, INTEGER, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT
) TO role_orchestrator;
GRANT EXECUTE ON FUNCTION public.capture_l1_data_plane_dasha_partition(
  UUID, TEXT, TEXT, INTEGER
) TO role_orchestrator;
GRANT EXECUTE ON FUNCTION public.complete_l1_data_plane_partition(
  UUID, TEXT, TEXT, TEXT, INTEGER
) TO role_orchestrator;
GRANT EXECUTE ON FUNCTION public.select_l1_data_plane_generation(
  UUID, TEXT, TEXT
) TO role_orchestrator;
GRANT EXECUTE ON FUNCTION public.rollback_l1_data_plane_generation(
  UUID, TEXT, TEXT
) TO role_orchestrator;

COMMENT ON TABLE public.l1_data_plane_row_snapshots IS
  'Append-only exact L1 producer rows. Active-table replacement never deletes a prior compatible generation.';
COMMENT ON TABLE public.l1_data_plane_fact_snapshots IS
  'Append-only typed field facts decomposed from each runtime producer row, preserving unit, zero, null and reason.';
COMMENT ON TABLE public.l1_data_plane_configuration_snapshots IS
  'Append-only runtime configuration observations with observed state separated from admitted rule qualification.';
COMMENT ON FUNCTION public.rollback_l1_data_plane_generation(UUID, TEXT, TEXT) IS
  'Selects an already-complete historical generation; it does not rewrite active producer tables.';

COMMIT;

-- Manual code rollback/read compatibility:
-- 1. Revert the 19 adapter decorators first; active tables remain unchanged.
-- 2. Retain these history tables for replay/audit. They are append-only evidence.
-- 3. Only after archival and explicit destructive authorization may the triggers,
--    functions, view and tables be dropped in reverse dependency order.
