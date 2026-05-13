-- platform/migrations/046_aiops_stack_config.sql
-- Migration: AIOps CP.1 — global stack configuration table.
-- Stores which LLM stack is globally active. v1.0 supports scope='global' only;
-- the scope column anticipates future per-user overrides.

BEGIN;

CREATE TABLE IF NOT EXISTS llm_stack_config (
  scope        TEXT PRIMARY KEY,           -- 'global' for v1.0
  active_stack TEXT NOT NULL,              -- 'nim' | 'gemini' | 'deepseek' | 'gpt' | 'anthropic' | 'marsys'
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by   TEXT NOT NULL
);

COMMIT;

-- Down:
-- DROP TABLE IF EXISTS llm_stack_config;
