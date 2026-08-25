-- 598_nirmana_output_digest_specs.sql
-- Content-sensitive, migration-reviewed output digest specifications.
-- 597 is deliberately reserved for the Sky replay repair.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

CREATE TABLE IF NOT EXISTS asset_output_digest_specs (
    asset_id       TEXT        NOT NULL REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
    spec_sha256    TEXT        NOT NULL CHECK (spec_sha256 ~ '^[a-f0-9]{64}$'),
    spec           JSONB       NOT NULL,
    reviewed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retired_at     TIMESTAMPTZ,
    PRIMARY KEY (asset_id, spec_sha256),
    CHECK (jsonb_typeof(spec) = 'object'),
    CHECK (retired_at IS NULL OR retired_at >= reviewed_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS asset_output_digest_specs_one_current
    ON asset_output_digest_specs (asset_id)
    WHERE retired_at IS NULL;

COMMENT ON TABLE asset_output_digest_specs IS
    'Reviewed, append-only content-digest specifications. The sidecar composes only fixed SQL from validated identifiers and streams rows; missing specifications intentionally produce unknown provenance receipts.';

ALTER TABLE asset_provenance_receipts
    ADD COLUMN IF NOT EXISTS output_digest_spec_sha256 TEXT
    CHECK (output_digest_spec_sha256 IS NULL OR output_digest_spec_sha256 ~ '^[a-f0-9]{64}$');

ALTER TABLE asset_provenance_receipts
    ADD CONSTRAINT asset_provenance_receipts_output_digest_spec_fk
    FOREIGN KEY (asset_id, output_digest_spec_sha256)
    REFERENCES asset_output_digest_specs (asset_id, spec_sha256)
    ON DELETE RESTRICT;

-- These component lists are audited against the owning writer and its DDL. They
-- exclude execution metadata (build_id/created_at/computed_at) so identical
-- content has the same digest across runs. Other assets remain intentionally
-- unspecced until their complete multi-table/co-writer contract is reviewed.
INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES
(
  'bg_formula_constants',
  '126465c083e5a3ca77c545a8ef6954a5d79b9df3104d79efe371960a2c55738b',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"formula_constants","relation":"brahma_formula_constants","key_columns":["constant_id"],"value_columns":["constant_id","value_jsonb","class","consumer_assets","citation_or_ratification","calibratable","bounds","version"]}]}'::jsonb
),
(
  'bg_ghatana',
  'd6289d7e793e8cbefb3af3e2866a6b9863312cd1fd381d9127cf4967b15fc615',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"event_ontology","relation":"brahma_event_ontology","key_columns":["event_class_id"],"value_columns":["event_class_id","name_en","domain","lel_category","signature_model","magnitude_floor","adjacency","base_rate_by_age","matching_rules","citations","version","temporal_shape","duration_prior","milestone_template","irreversibility_milestone","evidence_requirements","self_report_non_discriminating","kill_switch_criteria"]},{"name":"activity_ontology","relation":"brahma_activity_ontology","key_columns":["activity_class_id"],"value_columns":["activity_class_id","name_en","significators","fructification_rules","related_event_class","citations","version"]}]}'::jsonb
),
(
  'bg_parihara_rules',
  '80bd33a7269dfb1c48d5433e51dcbfc1017764ccc102e019fde9253b51ba33cc',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"parihara_rules","relation":"bg_parihara_rules","key_columns":["dosha_canonical_id","cancellation_index"],"value_columns":["dosha_canonical_id","dosha_name_en","dosha_category","cancellation_index","cancellation_condition_text","net_standing","scope","source_text_id","source_chapter","source_citation"]},{"name":"muhurta_activity_rules","relation":"bg_muhurta_activity_rules","key_columns":["activity_class","factor_type","factor_id"],"value_columns":["activity_class","factor_type","factor_id","quality_score","source_citation"]},{"name":"muhurta_factor_census","relation":"bg_muhurta_factor_census","key_columns":["factor_family","factor_name"],"value_columns":["factor_family","factor_name","disposition","citation_or_gap_note","evidence_pointer","school_tag"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

-- Forward reversal (only before any receipt references a reviewed spec): drop
-- `asset_provenance_receipts_output_digest_spec_fk`, then the receipt column,
-- index, and spec table. After receipt use, preserve receipt evidence instead.
