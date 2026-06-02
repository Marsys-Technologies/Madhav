-- platform/migrations/052_aiops_seed.sql
-- Migration: AIOps CP.1 — seed data.
-- Inserts the global stack default (gemini) and the MARSYS routing overrides
-- that give MARSYS sensible starting-point defaults without requiring a
-- super-admin to configure it from scratch on first login.

BEGIN;

-- Global stack: default to Gemini (confirmed active, 2M context, best value).
INSERT INTO llm_stack_config (scope, active_stack, updated_by)
VALUES ('global', 'gemini', 'system')
ON CONFLICT (scope) DO NOTHING;

-- MARSYS stack routing overrides — pre-seed every call type so the resolver
-- never has to fall back to the static registry for MARSYS.
INSERT INTO llm_stack_routing_override (scope, stack, call_type, primary_model, fallback_model, updated_by)
VALUES
  ('global', 'marsys', 'synthesis',        'gemini-2.5-pro',        'deepseek-v4-pro',  'system'),
  ('global', 'marsys', 'planner_deep',     'gemini-2.5-flash',      'deepseek-v4-pro',  'system'),
  ('global', 'marsys', 'planner_fast',     'gemini-2.5-flash-lite', 'gemini-2.5-flash', 'system'),
  ('global', 'marsys', 'context_assembly', 'gemini-2.5-flash',      'gemini-2.5-pro',   'system'),
  ('global', 'marsys', 'worker',           'gemini-2.5-flash-lite', 'gpt-4.1-nano',     'system'),
  ('global', 'marsys', 'eval_judge',       'gemini-2.5-pro',        'deepseek-v4-pro',  'system'),
  ('global', 'marsys', 'eval_generator',   'gemini-2.5-flash',      'deepseek-v4-pro',  'system'),
  ('global', 'marsys', 'smoke_synth',      'gemini-2.5-pro',        'deepseek-v4-pro',  'system'),
  ('global', 'marsys', 'checkpoint_4_5',   'gemini-2.5-flash-lite', 'gpt-4.1-nano',     'system'),
  ('global', 'marsys', 'checkpoint_5_5',   'gemini-2.5-flash-lite', 'gpt-4.1-nano',     'system'),
  ('global', 'marsys', 'checkpoint_8_5',   'gemini-2.5-flash-lite', 'gpt-4.1-nano',     'system')
ON CONFLICT (scope, stack, call_type) DO NOTHING;

COMMIT;

-- Down:
-- DELETE FROM llm_stack_routing_override WHERE stack = 'marsys' AND updated_by = 'system';
-- DELETE FROM llm_stack_config WHERE scope = 'global' AND updated_by = 'system';
