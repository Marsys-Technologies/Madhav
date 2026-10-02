-- Migration 1300: Persist optional reasoning effort for AI Console role assignments.
-- Created: 2026-10-02
-- Transaction owned by platform/scripts/migrate.ts.

ALTER TABLE ai_custom_configuration_roles
  ADD COLUMN IF NOT EXISTS effort text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'ai_custom_configuration_roles'::regclass
      AND conname = 'ai_custom_configuration_roles_effort_check'
  ) THEN
    ALTER TABLE ai_custom_configuration_roles
      ADD CONSTRAINT ai_custom_configuration_roles_effort_check
      CHECK (effort IS NULL OR effort IN ('low', 'medium', 'high'));
  END IF;
END;
$$;
