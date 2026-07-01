-- 384_mcp_api_keys_model_family.sql
-- M6: Per-model declared profile — add model_family column to mcp_api_keys.
--
-- Adds a nullable model_family column to mcp_api_keys that binds a model family
-- (anthropic, gemini, openai, deepseek) to the key at issuance.
--
-- Semantics:
--   - NULL (default): undeclared → the MCP server serves the universal-best surface.
--   - 'anthropic': Claude-profiled surface (fine-grained tools, detailed verbosity).
--   - 'gemini': Gemini-profiled surface (fat bundles, standard verbosity).
--   - 'openai': OpenAI-profiled surface (strict schema, minimal verbosity).
--   - 'deepseek': DeepSeek-profiled surface (compact, minimal verbosity).
--
-- Client-hint override: x-mcp-model-family header takes precedence over the key binding.
-- Precedence: header override > key binding > 'universal' fallback.
--
-- Additive-only migration — existing rows keep NULL (= undeclared = universal-best).
--
-- Rollback:
--   ALTER TABLE mcp_api_keys DROP COLUMN IF EXISTS model_family;

ALTER TABLE mcp_api_keys
  ADD COLUMN IF NOT EXISTS model_family TEXT
    CHECK (model_family IN ('anthropic', 'gemini', 'openai', 'deepseek'))
    DEFAULT NULL;

COMMENT ON COLUMN mcp_api_keys.model_family IS
  'Bound model family for this API key. NULL = undeclared (universal-best surface). '
  'Values: anthropic | gemini | openai | deepseek. '
  'Client-hint override: x-mcp-model-family header takes precedence at request time.';
