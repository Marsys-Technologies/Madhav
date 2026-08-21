-- Migration 575: seed llm_pricing_versions (currently empty, root cause of DD-25)
-- Created: 2026-08-21
--
-- PARIPRASHNA-P3-PREFLIGHT Part D. computeCost() (platform/src/lib/llm/observability/
-- cost.ts) has always read pricing from this table, never from registry.ts's
-- costPer1MInput/costPer1MOutput fields directly. The table has had zero rows since
-- its creation (migration 038, archived) — every cost computation for every provider
-- and every pipeline_stage has silently failed (PricingNotFoundError, caught and
-- swallowed to `computed_cost_usd: null` by safeComputeCost() in observe.ts) since the
-- feature shipped. This is why NCD-8's spend ceiling (COALESCE(SUM(computed_cost_usd),
-- 0)) has always evaluated every turn as $0 spent.
--
-- Seeded from platform/src/lib/models/registry.ts's MODELS[] array, current values as
-- of this migration's authorship date. Provider strings translated from registry.ts's
-- StackId vocabulary ('google', 'nvidia') to the llm_usage_events.provider /
-- ProviderName vocabulary ('gemini', 'nim') per
-- platform/src/lib/pariprashna/observability/provider_map.ts's own documented mapping
-- (STACK_ID_TO_PROVIDER_NAME) — every other provider string is identical in both
-- vocabularies.
--
-- DISCLOSED LIMITATIONS (native-ruled 2026-08-21 — ship the flat rate now, file the
-- gaps as dated follow-ups rather than silently absorbing them):
--   1. Google's real pricing is tiered by input size for gemini-2.5-pro and
--      gemini-3.1-pro-preview (see registry.ts's own inline comments — e.g.
--      "$1.25 up to 200K input; $2.50 above 200K"). This table's schema holds one flat
--      price_per_million_usd per (provider, model, token_class); this seed uses the
--      LOWER (<=200K) tier rate. Any call whose input exceeds the tier threshold will
--      be under-priced by computeCost() until the schema is extended to support
--      tiered pricing — a separate, disclosed follow-up, not fixed here.
--   2. This seed uses each model's CURRENT rate as a single flat effective_from
--      covering all history (see below), not a reconstruction of actual historical
--      pricing changes (e.g. deepseek-v4-pro's pre-2026-05-31 promo rate, or any
--      earlier Gemini price point). Re-costing older rows against this seed is
--      therefore an approximation for any row whose real historical price differed
--      from today's rate — acceptable to unblock cost visibility and the NCD-8
--      ceiling now; not a claim of historical pricing accuracy.
--   3. NVIDIA/NIM models are registered in registry.ts at $0.00/$0.00 (registry.ts's
--      own values, not a placeholder introduced here) — seeded as-is; true, since NIM
--      inference is not separately metered/billed in this deployment as of this
--      migration.
--
-- effective_from is set to 2020-01-01, safely before the earliest observed
-- llm_usage_events row (2026-07-22), so every historical row becomes re-costable
-- immediately. effective_to is left NULL (open-ended); a future price change is a new
-- row with a new effective_from, per this table's own versioned-by-effective-window
-- design — never an UPDATE to a row already in force.
--
-- Idempotent: the table already carries a unique index on exactly
-- (provider, model, token_class, effective_from) — uq_llm_pricing_versions_natural_key,
-- from migration 038 / the tracked 001_baseline.sql (confirmed live via pg_indexes,
-- not just pg_constraint, which does not list index-only uniqueness). No new
-- constraint is added here. INSERT targets that existing index directly via
-- ON CONFLICT DO NOTHING, so re-running this migration is a true no-op.

BEGIN;

INSERT INTO llm_pricing_versions
  (provider, model, token_class, price_per_million_usd, effective_from, effective_to, source_url)
VALUES
  -- Anthropic
  ('anthropic', 'claude-haiku-4-5',  'input',  1.00,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('anthropic', 'claude-haiku-4-5',  'output', 5.00,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('anthropic', 'claude-sonnet-4-6', 'input',  3.00,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('anthropic', 'claude-sonnet-4-6', 'output', 15.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('anthropic', 'claude-opus-4-7',   'input',  15.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('anthropic', 'claude-opus-4-7',   'output', 75.00, '2020-01-01T00:00:00Z', NULL, NULL),

  -- Gemini (registry.ts provider='google' -> ProviderName 'gemini')
  ('gemini', 'gemini-2.5-flash-lite', 'input',  0.015, '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-2.5-flash-lite', 'output', 0.06,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-2.5-flash',      'input',  0.075, '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-2.5-flash',      'output', 0.30,  '2020-01-01T00:00:00Z', NULL, NULL),
  -- gemini-2.5-pro: <=200K-input tier rate (see DISCLOSED LIMITATIONS #1 above)
  ('gemini', 'gemini-2.5-pro',        'input',  1.25,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-2.5-pro',        'output', 10.00, '2020-01-01T00:00:00Z', NULL, NULL),
  -- gemini-3.1-pro-preview: catalog-only as of this migration (not wired to any
  -- CallType) — <=200K-input tier rate; seeded now so it is ready the moment Part B
  -- wires it, rather than reproducing this same null-cost gap for a brand-new model.
  ('gemini', 'gemini-3.1-pro-preview', 'input',  2.00,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-3.1-pro-preview', 'output', 12.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-3.7-flash',       'input',  0.75,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('gemini', 'gemini-3.7-flash',       'output', 3.75,  '2020-01-01T00:00:00Z', NULL, NULL),

  -- DeepSeek
  ('deepseek', 'deepseek-v4-pro',   'input',  1.74, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-v4-pro',   'output', 3.48, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-v4-flash', 'input',  0.14, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-v4-flash', 'output', 0.28, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-chat',     'input',  0.14, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-chat',     'output', 0.28, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-reasoner', 'input',  1.74, '2020-01-01T00:00:00Z', NULL, NULL),
  ('deepseek', 'deepseek-reasoner', 'output', 3.48, '2020-01-01T00:00:00Z', NULL, NULL),

  -- OpenAI
  ('openai', 'gpt-4.1',      'input',  2.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4.1',      'output', 8.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4.1-mini', 'input',  0.40, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4.1-mini', 'output', 1.60, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4.1-nano', 'input',  0.05, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4.1-nano', 'output', 0.20, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4o-mini',  'input',  0.15, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4o-mini',  'output', 0.60, '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4o',       'input',  2.50,  '2020-01-01T00:00:00Z', NULL, NULL),
  ('openai', 'gpt-4o',       'output', 10.00, '2020-01-01T00:00:00Z', NULL, NULL),

  -- NIM (registry.ts provider='nvidia' -> ProviderName 'nim'); registry.ts's own
  -- values are $0.00/$0.00 for every entry (see DISCLOSED LIMITATIONS #3 above)
  ('nim', 'deepseek-ai/deepseek-v4-pro',                       'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'deepseek-ai/deepseek-v4-pro',                       'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/llama-3.1-nemotron-ultra-253b-v1',           'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/llama-3.1-nemotron-ultra-253b-v1',           'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'moonshotai/kimi-k2-instruct',                       'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'moonshotai/kimi-k2-instruct',                       'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning',     'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning',     'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'mistralai/mistral-large-3-675b-instruct-2512',      'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'mistralai/mistral-large-3-675b-instruct-2512',      'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/llama-3.3-nemotron-super-49b-v1',            'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/llama-3.3-nemotron-super-49b-v1',            'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/nemotron-3-super-120b-a12b',                 'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'nvidia/nemotron-3-super-120b-a12b',                 'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'qwen/qwen3-235b-a22b',                              'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'qwen/qwen3-235b-a22b',                              'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'meta/llama-3.1-8b-instruct',                        'input',  0.00, '2020-01-01T00:00:00Z', NULL, NULL),
  ('nim', 'meta/llama-3.1-8b-instruct',                        'output', 0.00, '2020-01-01T00:00:00Z', NULL, NULL)
ON CONFLICT (provider, model, token_class, effective_from) DO NOTHING;

COMMIT;
