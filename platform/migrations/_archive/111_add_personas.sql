-- R9-S3: Persona library — named system prompt variants for ModelStylePicker.
-- A persona bundles a custom system_prompt with optional default style + stack.
-- Only one persona may be the default per user (enforced by unique partial index).
-- Gated behind MARSYS_FLAG_R9_PERSONAS (default true — additive, no risk).
--
-- Rollback / down-migration notes:
--   DROP INDEX IF EXISTS idx_personas_user_default;
--   DROP TABLE personas;

CREATE TABLE personas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL CHECK (char_length(name) <= 50),
  system_prompt TEXT NOT NULL CHECK (char_length(system_prompt) <= 4000),
  default_style TEXT,
  default_stack TEXT,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_personas_user_id ON personas(user_id);

-- Enforce at most one default persona per user.
CREATE UNIQUE INDEX idx_personas_user_default
  ON personas(user_id) WHERE is_default = TRUE;
