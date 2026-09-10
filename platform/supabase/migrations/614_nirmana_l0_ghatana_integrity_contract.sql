-- Migration 614: install the exact integrity contract for bg_ghatana.
--
-- Accepted disposition: PRESERVE + GOVERNED REBUILD. The Python writer
-- converges the base event/activity ontology fields. DR-13 matching, evidence,
-- self-report, and kill-switch columns remain migration-owned retained capital.
-- The detector covers both ownership partitions as one semantic asset: all 27
-- event rows and all 12 activity rows. Read-only production hashes were matched
-- to a deterministic local replay on 2026-08-26.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_count_sql constant text :=
    'SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count';
  canonical_count_sql constant text :=
    'SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count';
  legacy_description constant text :=
    'Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended 2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requirements, self_report_non_discriminating flags, kill_switch_criteria) + electional activity ontology (12 muhurta activity classes). Seeded from W1 seed package Sections 5-6; shape/evidence/self-report/kill-switch fields added by D-4a Lane A-2. Governs L4 ph_nimitta, L4 ph_muhurta, the D-4a matcher (A-1), and the D-4a prospective ledger (A-4) claim_shape validation.';
  canonical_description constant text :=
    'Global life-event + electional-activity ontology — 27 life-event classes (brahma_event_ontology) and 12 electional activity classes (brahma_activity_ontology), including DR-13 temporal-shape and evidence fields.';
  canonical_explanation constant text :=
    '27 life-event classes + 12 electional activity classes = 39 total rows, including the five DR-13 coverage extensions.';
  canonical_partition constant text :=
    'brahma_event_ontology.event_class_id; brahma_activity_ontology.activity_class_id';
  ghatana_check constant text := $check$
SELECT
  (SELECT count(*) = 27 FROM brahma_event_ontology)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(event_class_id,name_en,domain,lel_category,
      signature_model,magnitude_floor,adjacency,base_rate_by_age,
      matching_rules,citations,version,temporal_shape,duration_prior,
      milestone_template,irreversibility_milestone,evidence_requirements,
      self_report_non_discriminating,kill_switch_criteria)::text,
    E'\n' ORDER BY event_class_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    'ec13daa39559ddbed5556bde597f16514cc815287c094d92b011957d246398c3'
  FROM brahma_event_ontology)
  AND (SELECT count(*) = 12 FROM brahma_activity_ontology)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(activity_class_id,name_en,significators,
      fructification_rules,related_event_class,citations,version)::text,
    E'\n' ORDER BY activity_class_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '261576cc17c10d69d856d74b82f2987094a981a0d58c564294a5bbebd4d70210'
  FROM brahma_activity_ontology)
$check$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_ghatana'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'brahma_event_ontology'
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (
      (
        registry_row.sort_order = 17
        AND registry_row.target_floor IS NULL
        AND registry_row.count_sql = legacy_count_sql
        AND registry_row.english_description = legacy_description
        AND registry_row.volume_explanation IS NULL
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      )
      OR (
        registry_row.sort_order IN (16, 17)
        AND registry_row.target_floor = 39
        AND registry_row.count_sql = canonical_count_sql
        AND registry_row.english_description = canonical_description
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      )
      OR (
        registry_row.sort_order = 16
        AND registry_row.target_floor = 39
        AND registry_row.count_sql = canonical_count_sql
        AND registry_row.english_description = canonical_description
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.data_disposition = 'RETAINED_AS_CAPITAL'
        AND registry_row.integrity_check_sql = ghatana_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 614 refuses unknown registry contract for bg_ghatana';
  END IF;

  UPDATE asset_registry
  SET sort_order = 16,
      target_floor = 39,
      count_sql = canonical_count_sql,
      english_description = canonical_description,
      volume_explanation = canonical_explanation,
      natural_key_partition = canonical_partition,
      data_disposition = 'RETAINED_AS_CAPITAL',
      integrity_check_sql = ghatana_check
  WHERE asset_id = 'bg_ghatana';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 614 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_ghatana'
      AND sort_order = 16
      AND target_floor = 39
      AND count_sql = canonical_count_sql
      AND english_description = canonical_description
      AND volume_explanation = canonical_explanation
      AND natural_key_partition = canonical_partition
      AND data_disposition = 'RETAINED_AS_CAPITAL'
      AND integrity_check_sql = ghatana_check
  ) THEN
    RAISE EXCEPTION 'migration 614 postflight registry mismatch';
  END IF;
END $$;
