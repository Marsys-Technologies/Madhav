-- Migration 1158: distinguish provider and CLI presets from custom configurations
-- Created: 2026-09-30
-- Additive and idempotent. The migration runner owns the transaction.
-- Existing mixed configurations remain readable as legacy_mixed; no saved choice is rewritten.

ALTER TABLE ai_custom_configurations
  ADD COLUMN IF NOT EXISTS configuration_kind text NOT NULL DEFAULT 'legacy_mixed',
  ADD COLUMN IF NOT EXISTS owner_connection_id uuid,
  ADD COLUMN IF NOT EXISTS owner_cli_id text;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ai_configuration_kind_shape'
    AND conrelid = 'ai_custom_configurations'::regclass) THEN
    ALTER TABLE ai_custom_configurations ADD CONSTRAINT ai_configuration_kind_shape CHECK (
      (configuration_kind = 'provider_preset' AND owner_connection_id IS NOT NULL AND owner_cli_id IS NULL)
      OR (configuration_kind = 'cli_preset' AND owner_cli_id IS NOT NULL AND owner_connection_id IS NULL)
      OR (configuration_kind IN ('custom_api', 'custom_cli', 'legacy_mixed')
        AND owner_connection_id IS NULL AND owner_cli_id IS NULL)
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ai_configuration_owner_connection_fk'
    AND conrelid = 'ai_custom_configurations'::regclass) THEN
    ALTER TABLE ai_custom_configurations ADD CONSTRAINT ai_configuration_owner_connection_fk
      FOREIGN KEY (user_id, owner_connection_id) REFERENCES ai_provider_connections(user_id, id)
      ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ai_configuration_owner_cli_fk'
    AND conrelid = 'ai_custom_configurations'::regclass) THEN
    ALTER TABLE ai_custom_configurations ADD CONSTRAINT ai_configuration_owner_cli_fk
      FOREIGN KEY (owner_cli_id) REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ai_provider_preset_owner_idx
  ON ai_custom_configurations(user_id, owner_connection_id)
  WHERE configuration_kind = 'provider_preset' AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ai_cli_preset_owner_idx
  ON ai_custom_configurations(user_id, owner_cli_id)
  WHERE configuration_kind = 'cli_preset' AND deleted_at IS NULL;

CREATE OR REPLACE FUNCTION ai_configuration_role_scope_valid(
  configuration_kind text, owner_connection_id uuid, owner_cli_id text,
  role_kind text, role_connection_id uuid, role_cli_id text
) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE configuration_kind
    WHEN 'provider_preset' THEN role_kind = 'provider_model' AND role_connection_id = owner_connection_id
    WHEN 'cli_preset' THEN role_kind = 'local_cli' AND role_cli_id = owner_cli_id
    WHEN 'custom_api' THEN role_kind = 'provider_model'
    WHEN 'custom_cli' THEN role_kind = 'local_cli'
    ELSE configuration_kind = 'legacy_mixed'
  END
$$;

CREATE OR REPLACE FUNCTION ai_check_configuration_role_scope() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE c record;
BEGIN
  SELECT configuration_kind, owner_connection_id, owner_cli_id INTO c
    FROM ai_custom_configurations WHERE id = NEW.configuration_id AND user_id = NEW.user_id
    FOR NO KEY UPDATE;
  IF NOT FOUND OR ai_configuration_role_scope_valid(c.configuration_kind, c.owner_connection_id,
    c.owner_cli_id, NEW.kind, NEW.connection_id, NEW.cli_id) IS NOT TRUE THEN
    RAISE EXCEPTION 'AI configuration role scope mismatch' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS ai_configuration_role_scope ON ai_custom_configuration_roles;
CREATE TRIGGER ai_configuration_role_scope BEFORE INSERT OR UPDATE ON ai_custom_configuration_roles
  FOR EACH ROW EXECUTE FUNCTION ai_check_configuration_role_scope();

CREATE OR REPLACE FUNCTION ai_check_configuration_scope_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM ai_custom_configuration_roles r WHERE r.configuration_id = NEW.id
    AND ai_configuration_role_scope_valid(NEW.configuration_kind, NEW.owner_connection_id,
      NEW.owner_cli_id, r.kind, r.connection_id, r.cli_id) IS NOT TRUE) THEN
    RAISE EXCEPTION 'AI configuration scope update mismatch' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS ai_configuration_scope_update ON ai_custom_configurations;
CREATE TRIGGER ai_configuration_scope_update BEFORE UPDATE ON ai_custom_configurations
  FOR EACH ROW EXECUTE FUNCTION ai_check_configuration_scope_update();

-- Classify existing configurations only after all ALTER TABLE statements and
-- trigger installation. Updating rows earlier leaves pending FK trigger events
-- in the migration runner's transaction; PostgreSQL then refuses the later
-- ALTER TABLE with "cannot ALTER TABLE ... because it has pending trigger events".
-- The existing ai_configuration_version_guard requires every metadata update to
-- advance the version. Historical turn snapshots retain their original versions.
UPDATE ai_custom_configurations c SET configuration_kind = 'custom_api', version = version + 1
WHERE c.configuration_kind = 'legacy_mixed'
  AND EXISTS (SELECT 1 FROM ai_custom_configuration_roles r WHERE r.configuration_id = c.id)
  AND NOT EXISTS (SELECT 1 FROM ai_custom_configuration_roles r
    WHERE r.configuration_id = c.id AND r.kind <> 'provider_model');

UPDATE ai_custom_configurations c SET configuration_kind = 'custom_cli', version = version + 1
WHERE c.configuration_kind = 'legacy_mixed'
  AND EXISTS (SELECT 1 FROM ai_custom_configuration_roles r WHERE r.configuration_id = c.id)
  AND NOT EXISTS (SELECT 1 FROM ai_custom_configuration_roles r
    WHERE r.configuration_id = c.id AND r.kind <> 'local_cli');
