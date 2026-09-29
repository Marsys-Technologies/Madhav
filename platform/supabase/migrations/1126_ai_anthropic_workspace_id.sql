-- Migration 1126: optional Anthropic workspace selection for BYOK connections
-- Created: 2026-09-30
-- Additive. The migration runner owns the transaction and tracking insert.

ALTER TABLE ai_provider_connections
  ADD COLUMN IF NOT EXISTS anthropic_workspace_id text;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'ai_provider_connections'::regclass
    AND conname = 'ai_provider_connections_anthropic_workspace_id_check') THEN
    ALTER TABLE ai_provider_connections
      ADD CONSTRAINT ai_provider_connections_anthropic_workspace_id_check
      CHECK (anthropic_workspace_id IS NULL OR (
        provider_id = 'anthropic'
        AND anthropic_workspace_id ~ '^wrkspc_[A-Za-z0-9]{20,64}$'
      ));
  END IF;
END $$;
