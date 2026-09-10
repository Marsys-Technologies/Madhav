-- Migration 604: partition shared L0 class-prior ownership and ratify achieved floors.
--
-- bg_class_priors and bg_class_lifetime_counts intentionally co-write
-- brahma_class_priors at disjoint, immutable prior_version/fact_kind coordinates.
-- Migration 600 gave both assets the same whole-table digest specification,
-- allowing either writer to change the other's acceptance digest. This migration
-- preserves that reviewed specification (and every receipt that may reference it),
-- retires it, and appends one current writer-scoped specification per asset.
-- It also ratifies the production-measured achieved counts: 171 class-prior rows,
-- 6 sourced lifetime-count rows, and 27+12=39 Ghatana ontology rows.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  class_priors_row asset_registry%ROWTYPE;
  lifetime_counts_row asset_registry%ROWTYPE;
  ghatana_row asset_registry%ROWTYPE;
  old_current_rows INTEGER := 0;
  changed_rows INTEGER := 0;
  old_spec CONSTANT JSONB :=
    '{"components":[{"key_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition"],"name":"brahma_class_priors","relation":"brahma_class_priors","value_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition","class_prior","varga_weights","contested","citation","ratified_by","prior_basis","source_ref"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  class_priors_spec CONSTANT JSONB :=
    '{"components":[{"key_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition"],"name":"brahma_class_priors","relation":"brahma_class_priors","value_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition","class_prior","varga_weights","contested","citation","ratified_by","prior_basis","source_ref"],"where_equals":{"prior_version":"1.0"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  lifetime_counts_spec CONSTANT JSONB :=
    '{"components":[{"key_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition"],"name":"brahma_class_priors","relation":"brahma_class_priors","value_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition","class_prior","varga_weights","contested","citation","ratified_by","prior_basis","source_ref"],"where_equals":{"fact_kind":"lifetime_count_per_100y","prior_version":"ne_v01"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  lifetime_counts_description CONSTANT TEXT :=
    'ṢAḌ-DARŚANA W2 (ADJUDICATION-2): N_e — the expected lifetime count of each brahma_event_ontology event class over a 100-year modelled timeline from birth, assuming survival. The chart-INDEPENDENT structural baseline λ⁰_e of the Kāla Kṣetra hazard field. Every value is Tier N-i: a published demographic / actuarial / epidemiological statistic carrying publisher, edition, year, indicator id, geography+cohort and a retrievable URL/DOI, together with the arithmetic converting it to a per-100-year count — or Tier N-ii, a stated arithmetic identity over such a value. Classical-text counts are FORECLOSED (chart-conditional; already carried by P_e) and cohort/LEL-derived counts are FORECLOSED by the circularity guard. A class with no defensible source is NOT seeded and is honestly skipped by ka_kshetra with no_class_prior_row — honest-empty per class, never a fabricated baseline.';
BEGIN
  SELECT * INTO class_priors_row
  FROM asset_registry WHERE asset_id = 'bg_class_priors' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 604 requires bg_class_priors registry row';
  END IF;
  IF (
    (
      class_priors_row.target_floor IS NULL
      AND class_priors_row.count_sql = 'SELECT COUNT(*) FROM brahma_class_priors'
      AND COALESCE(class_priors_row.volume_explanation, '') = ''
      AND class_priors_row.english_description =
        'Ranked salience class-prior weights for composite query-time ranking. 4 axes: signal_type_class × source_subsystem × signal_tradition × varga × graha×domain. Seeded from W1 judgment package v1.0; versioned; L5-calibratable.'
    ) OR (
      class_priors_row.target_floor = 164
      AND class_priors_row.count_sql = 'SELECT count(*) FROM brahma_class_priors'
      AND class_priors_row.volume_explanation =
        '17 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha x domain priors (per writer docstring 165; live-measured 164, 2026-07-05).'
      AND class_priors_row.english_description =
        'Global signal-classification priors across 5 axes — signal_type_class, source_subsystem, signal_tradition, varga, graha x domain — from W1 seed package §2-§4.'
    ) OR (
      class_priors_row.target_floor = 171
      AND class_priors_row.count_sql =
        'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''1.0'''
      AND class_priors_row.volume_explanation =
        '24 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha x domain priors = 171 achieved writer-owned rows at prior_version 1.0.'
      AND class_priors_row.english_description =
        'Global signal-classification priors across 5 writer-owned axes — signal_type_class, source_subsystem, signal_tradition, varga, and graha x domain — from W1 seed package §2-§4 plus ratified append-only class extensions.'
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 604 refuses unknown bg_class_priors registry contract';
  END IF;

  SELECT * INTO lifetime_counts_row
  FROM asset_registry WHERE asset_id = 'bg_class_lifetime_counts' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 604 requires bg_class_lifetime_counts registry row';
  END IF;
  IF (
    lifetime_counts_row.english_description = lifetime_counts_description
    AND (
      (
        lifetime_counts_row.target_floor = 0
        AND lifetime_counts_row.count_sql =
          'SELECT COUNT(*) FROM brahma_class_priors WHERE fact_kind=''lifetime_count_per_100y'''
        AND (
          COALESCE(lifetime_counts_row.volume_explanation, '') = ''
          OR lifetime_counts_row.volume_explanation =
            'One row per event class for which a Tier N-i (or Tier N-ii derived-identity) source could actually be obtained and cited. Set to the ACHIEVED count after the first build (§N.4). Unseeded classes are an honest per-class coverage gap registered by name in the ledger, never a reason to invent a row.'
        )
      ) OR (
        lifetime_counts_row.target_floor = 6
        AND lifetime_counts_row.count_sql =
          'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''ne_v01'' AND fact_kind=''lifetime_count_per_100y'''
        AND lifetime_counts_row.volume_explanation =
          '6 achieved Tier N-i/N-ii lifetime-count rows at the writer-owned ne_v01 coordinate. Unseeded event classes remain an explicit coverage gap; this floor must rise only with defensible cited sources, never fabricated rows.'
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 604 refuses unknown bg_class_lifetime_counts registry contract';
  END IF;

  SELECT * INTO ghatana_row
  FROM asset_registry WHERE asset_id = 'bg_ghatana' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 604 requires bg_ghatana registry row';
  END IF;
  IF (
    (
      ghatana_row.target_floor IS NULL
      AND ghatana_row.count_sql =
        'SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count'
      AND COALESCE(ghatana_row.volume_explanation, '') = ''
      AND ghatana_row.english_description =
        'Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended 2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requirements, self_report_non_discriminating flags, kill_switch_criteria) + electional activity ontology (12 muhurta activity classes). Seeded from W1 seed package Sections 5-6; shape/evidence/self-report/kill-switch fields added by D-4a Lane A-2. Governs L4 ph_nimitta, L4 ph_muhurta, the D-4a matcher (A-1), and the D-4a prospective ledger (A-4) claim_shape validation.'
    ) OR (
      ghatana_row.target_floor = 34
      AND ghatana_row.count_sql =
        'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count'
      AND ghatana_row.volume_explanation =
        '22 life-event classes + 12 electional activity classes = 34 total rows, seeded verbatim from W1 seed package §5-§6.'
      AND ghatana_row.english_description =
        'Global life-event + electional-activity ontology — 22 life-event classes (brahma_event_ontology) and 12 electional activity classes (brahma_activity_ontology); source W1 seed package §5-§6.'
    ) OR (
      ghatana_row.target_floor = 39
      AND ghatana_row.count_sql =
        'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count'
      AND ghatana_row.volume_explanation =
        '27 life-event classes + 12 electional activity classes = 39 total rows, including the five DR-13 coverage extensions.'
      AND ghatana_row.english_description =
        'Global life-event + electional-activity ontology — 27 life-event classes (brahma_event_ontology) and 12 electional activity classes (brahma_activity_ontology), including DR-13 temporal-shape and evidence fields.'
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 604 refuses unknown bg_ghatana registry contract';
  END IF;

  -- Lock both current specs and accept only the migration-600 whole-table
  -- contract or this migration's exact scoped contract. Mixed states cannot be
  -- produced by the transactional runner and are treated as drift.
  PERFORM 1
  FROM asset_output_digest_specs
  WHERE asset_id IN ('bg_class_priors', 'bg_class_lifetime_counts')
    AND retired_at IS NULL
  ORDER BY asset_id
  FOR UPDATE;

  IF EXISTS (
    SELECT 1
    FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_priors'
      AND retired_at IS NULL
      AND NOT (
        (spec_sha256 = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1' AND spec = old_spec)
        OR (spec_sha256 = '5b8fd47567c1e2bae76b5b6685a0f5cc347542d140bf80c52eace5ffdf7227ac' AND spec = class_priors_spec)
      )
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_priors' AND retired_at IS NULL
  ) THEN
    RAISE EXCEPTION 'migration 604 refuses unknown current class-prior digest specification';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_lifetime_counts'
      AND retired_at IS NULL
      AND NOT (
        (spec_sha256 = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1' AND spec = old_spec)
        OR (spec_sha256 = '6feacb8dbb3a1889790cab02781d0a5610b98d9ff2fbb176264d02b3556e142e' AND spec = lifetime_counts_spec)
      )
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_lifetime_counts' AND retired_at IS NULL
  ) THEN
    RAISE EXCEPTION 'migration 604 refuses unknown current lifetime-count digest specification';
  END IF;

  SELECT count(*) INTO old_current_rows
  FROM asset_output_digest_specs
  WHERE asset_id IN ('bg_class_priors', 'bg_class_lifetime_counts')
    AND spec_sha256 = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1'
    AND spec = old_spec
    AND retired_at IS NULL;

  IF old_current_rows NOT IN (0, 2) THEN
    RAISE EXCEPTION 'migration 604 refuses mixed digest specification state';
  END IF;

  IF old_current_rows = 2 THEN
    UPDATE asset_output_digest_specs
    SET retired_at = clock_timestamp()
    WHERE asset_id IN ('bg_class_priors', 'bg_class_lifetime_counts')
      AND spec_sha256 = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1'
      AND spec = old_spec
      AND retired_at IS NULL;
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 2 THEN
      RAISE EXCEPTION 'migration 604 expected to retire 2 shared-table digest specs, retired %',
        changed_rows;
    END IF;
  END IF;

  INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
  VALUES
    (
      'bg_class_priors',
      '5b8fd47567c1e2bae76b5b6685a0f5cc347542d140bf80c52eace5ffdf7227ac',
      '{"components":[{"key_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition"],"name":"brahma_class_priors","relation":"brahma_class_priors","value_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition","class_prior","varga_weights","contested","citation","ratified_by","prior_basis","source_ref"],"where_equals":{"prior_version":"1.0"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
    ),
    (
      'bg_class_lifetime_counts',
      '6feacb8dbb3a1889790cab02781d0a5610b98d9ff2fbb176264d02b3556e142e',
      '{"components":[{"key_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition"],"name":"brahma_class_priors","relation":"brahma_class_priors","value_columns":["prior_version","signal_type_class","fact_kind","source_subsystem","signal_tradition","class_prior","varga_weights","contested","citation","ratified_by","prior_basis","source_ref"],"where_equals":{"fact_kind":"lifetime_count_per_100y","prior_version":"ne_v01"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
    )
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

  UPDATE asset_registry
  SET target_floor = 171,
      count_sql = 'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''1.0''',
      volume_explanation =
        '24 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha x domain '
        'priors = 171 achieved writer-owned rows at prior_version 1.0.',
      english_description =
        'Global signal-classification priors across 5 writer-owned axes — '
        'signal_type_class, source_subsystem, signal_tradition, varga, and graha x '
        'domain — from W1 seed package §2-§4 plus ratified append-only class extensions.'
  WHERE asset_id = 'bg_class_priors';

  UPDATE asset_registry
  SET target_floor = 6,
      count_sql =
        'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''ne_v01'' AND fact_kind=''lifetime_count_per_100y''',
      volume_explanation =
        '6 achieved Tier N-i/N-ii lifetime-count rows at the writer-owned ne_v01 '
        'coordinate. Unseeded event classes remain an explicit coverage gap; this '
        'floor must rise only with defensible cited sources, never fabricated rows.',
      english_description = lifetime_counts_description
  WHERE asset_id = 'bg_class_lifetime_counts';

  UPDATE asset_registry
  SET target_floor = 39,
      count_sql =
        'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count',
      volume_explanation =
        '27 life-event classes + 12 electional activity classes = 39 total rows, '
        'including the five DR-13 coverage extensions.',
      english_description =
        'Global life-event + electional-activity ontology — 27 life-event classes '
        '(brahma_event_ontology) and 12 electional activity classes '
        '(brahma_activity_ontology), including DR-13 temporal-shape and evidence fields.'
  WHERE asset_id = 'bg_ghatana';

  IF NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_priors'
      AND spec_sha256 = '5b8fd47567c1e2bae76b5b6685a0f5cc347542d140bf80c52eace5ffdf7227ac'
      AND spec = class_priors_spec AND retired_at IS NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_lifetime_counts'
      AND spec_sha256 = '6feacb8dbb3a1889790cab02781d0a5610b98d9ff2fbb176264d02b3556e142e'
      AND spec = lifetime_counts_spec AND retired_at IS NULL
  ) THEN
    RAISE EXCEPTION 'migration 604 failed scoped digest specification postflight';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_priors'
      AND spec_sha256 = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1'
      AND spec = old_spec AND retired_at IS NOT NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_class_lifetime_counts'
      AND spec_sha256 = 'ddab67f339af980fd4092270d6ed598189524d73b7d295a79e9f449fc64bd6c1'
      AND spec = old_spec AND retired_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 604 failed historical digest preservation postflight';
  END IF;

  IF EXISTS (
    SELECT 1 FROM asset_registry
    WHERE (asset_id = 'bg_class_priors' AND (
      target_floor IS DISTINCT FROM 171
      OR count_sql IS DISTINCT FROM
        'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''1.0'''
      OR volume_explanation IS DISTINCT FROM
        '24 classes + 12 subsystems + 6 traditions + 30 vargas + 99 graha x domain priors = 171 achieved writer-owned rows at prior_version 1.0.'
      OR english_description IS DISTINCT FROM
        'Global signal-classification priors across 5 writer-owned axes — signal_type_class, source_subsystem, signal_tradition, varga, and graha x domain — from W1 seed package §2-§4 plus ratified append-only class extensions.'
    )) OR (asset_id = 'bg_class_lifetime_counts' AND (
      target_floor IS DISTINCT FROM 6
      OR count_sql IS DISTINCT FROM
        'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''ne_v01'' AND fact_kind=''lifetime_count_per_100y'''
      OR volume_explanation IS DISTINCT FROM
        '6 achieved Tier N-i/N-ii lifetime-count rows at the writer-owned ne_v01 coordinate. Unseeded event classes remain an explicit coverage gap; this floor must rise only with defensible cited sources, never fabricated rows.'
      OR english_description IS DISTINCT FROM lifetime_counts_description
    )) OR (asset_id = 'bg_ghatana' AND (
      target_floor IS DISTINCT FROM 39
      OR count_sql IS DISTINCT FROM
        'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count'
      OR volume_explanation IS DISTINCT FROM
        '27 life-event classes + 12 electional activity classes = 39 total rows, including the five DR-13 coverage extensions.'
      OR english_description IS DISTINCT FROM
        'Global life-event + electional-activity ontology — 27 life-event classes (brahma_event_ontology) and 12 electional activity classes (brahma_activity_ontology), including DR-13 temporal-shape and evidence fields.'
    ))
  ) THEN
    RAISE EXCEPTION 'migration 604 failed registry ownership-scope postflight';
  END IF;
END
$$;
