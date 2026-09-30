-- Migration 1151: User-curated AI model shortlist and model-level probe evidence
-- Created: 2026-09-30

ALTER TABLE ai_connection_models
  ADD COLUMN IF NOT EXISTS user_selected boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS plain_tested_at timestamptz,
  ADD COLUMN IF NOT EXISTS tested_credential_version bigint,
  ADD COLUMN IF NOT EXISTS last_probe_at timestamptz,
  ADD COLUMN IF NOT EXISTS last_probe_error_code text,
  ADD COLUMN IF NOT EXISTS last_probe_input_tokens bigint,
  ADD COLUMN IF NOT EXISTS last_probe_output_tokens bigint;

ALTER TABLE ai_cli_models
  ADD COLUMN IF NOT EXISTS is_manual boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tested_entrypoint_sha256 text,
  ADD COLUMN IF NOT EXISTS tested_version text;

ALTER TABLE ai_cli_models DROP CONSTRAINT IF EXISTS ai_cli_manual_evidence_check;
ALTER TABLE ai_cli_models ADD CONSTRAINT ai_cli_manual_evidence_check CHECK (
  NOT is_manual OR (NOT is_builtin_default AND tested_entrypoint_sha256 IS NOT NULL
    AND tested_entrypoint_sha256 ~ '^[a-f0-9]{64}$'
    AND tested_version IS NOT NULL AND btrim(tested_version) <> '')
);

ALTER TABLE ai_configuration_audit_log DROP CONSTRAINT IF EXISTS ai_configuration_audit_log_event_check;
ALTER TABLE ai_configuration_audit_log ADD CONSTRAINT ai_configuration_audit_log_event_check
CHECK (event IN ('connection_created','connection_updated','connection_renamed',
  'connection_credential_replaced','connection_validated','connection_validation_succeeded',
  'connection_validation_rejected','connection_deleted','configuration_created','configuration_updated',
  'configuration_duplicated','configuration_deleted','default_selected','cli_granted','cli_revoked',
  'conversation_selected','cli_model_added'));

ALTER TABLE ai_connection_models
  DROP CONSTRAINT IF EXISTS ai_connection_models_tested_version_check;
ALTER TABLE ai_connection_models
  ADD CONSTRAINT ai_connection_models_tested_version_check
  CHECK (tested_credential_version IS NULL OR tested_credential_version > 0);

ALTER TABLE ai_connection_models DROP CONSTRAINT IF EXISTS ai_connection_models_probe_usage_check;
ALTER TABLE ai_connection_models ADD CONSTRAINT ai_connection_models_probe_usage_check
  CHECK ((last_probe_input_tokens IS NULL OR last_probe_input_tokens >= 0)
    AND (last_probe_output_tokens IS NULL OR last_probe_output_tokens >= 0));

-- Existing defaults and saved configurations remain discoverable in the new
-- shortlist. This backfill does not claim that any model was individually tested.
UPDATE ai_connection_models m SET user_selected = true
WHERE EXISTS (
  SELECT 1 FROM ai_user_defaults d
  WHERE d.kind = 'provider_model' AND d.connection_id = m.connection_id AND d.model_id = m.model_id
) OR EXISTS (
  SELECT 1 FROM ai_custom_configuration_roles r
  JOIN ai_custom_configurations c ON c.id = r.configuration_id
  WHERE c.deleted_at IS NULL AND r.kind = 'provider_model'
    AND r.connection_id = m.connection_id AND r.model_id = m.model_id
) OR EXISTS (
  SELECT 1 FROM ai_conversation_selections s
  WHERE s.kind = 'provider_model' AND s.connection_id = m.connection_id AND s.model_id = m.model_id
);

-- Kimi ACP cannot satisfy the pipeline's structured planner/worker contract.
-- Keep its plain-text synthesis capability visible without advertising unsafe roles.
UPDATE ai_cli_models SET compatible_roles = ARRAY['synthesizer']::text[]
WHERE cli_id = 'kimi_code' AND compatible_roles <> ARRAY['synthesizer']::text[];
