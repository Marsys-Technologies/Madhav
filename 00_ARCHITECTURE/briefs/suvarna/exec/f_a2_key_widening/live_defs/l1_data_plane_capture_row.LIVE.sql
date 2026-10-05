CREATE OR REPLACE FUNCTION public.l1_data_plane_capture_row()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'pg_temp'
AS $function$
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
  IF session_user <> 'data_plane_builder' THEN
    RAISE EXCEPTION 'L1 governed capture requires direct data_plane_builder authentication';
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
$function$
