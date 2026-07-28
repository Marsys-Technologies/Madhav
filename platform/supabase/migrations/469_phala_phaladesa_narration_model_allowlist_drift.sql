-- Migration 469: close the migration-339 narration_model CHECK constraint drift
-- (P0-N2, parked ŚUDDHA-VĀCA finding, native-authorized fix).
--
-- Migration 339's narration_model CHECK constraint has permitted 'gpt-4o' and
-- 'gpt-4-turbo' (OpenAI models) since it was written, despite the migration's own
-- header comment and column doc committing to a "Gemini/DeepSeek only" policy
-- (services/ph_phaladesa/engine.py's PERMITTED_NARRATION_MODELS_POLICY /
-- 'narration_model_policy': 'gemini_or_deepseek_only (anthropic_banned)'). The
-- Python-side allowlist (PERMITTED_NARRATION_MODELS) already had 'gpt-4o'/
-- 'gpt-4-turbo' removed by an earlier one-liner fix, but the DB CHECK constraint —
-- the documented last line of defense against a policy-violating value ever
-- reaching this column — was never updated to match, leaving OpenAI models
-- DB-permitted even though no in-repo code path is meant to emit them.
--
-- Fix: DROP + re-ADD the CHECK constraint with the exact PERMITTED_NARRATION_MODELS
-- set (gemini-pro, gemini-ultra, gemini-2.0-flash, deepseek-chat, deepseek-r1).
-- No Anthropic model was ever in this list (confirmed, unaffected by this change).
-- Existing rows are unaffected: narration_model is NULL for every row today (the
-- writer never calls an LLM; a separate narration step sets this column, and no
-- narration step has run against a gpt-4o/gpt-4-turbo value in production).

BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM phala_phaladesa WHERE narration_model IN ('gpt-4o', 'gpt-4-turbo')
  ) THEN
    RAISE EXCEPTION
      'Refusing to tighten narration_model CHECK: % existing row(s) already carry a value this migration is about to forbid. Investigate before proceeding.',
      (SELECT count(*) FROM phala_phaladesa WHERE narration_model IN ('gpt-4o', 'gpt-4-turbo'));
  END IF;
END $$;

ALTER TABLE phala_phaladesa DROP CONSTRAINT IF EXISTS phala_phaladesa_narration_model_check;

ALTER TABLE phala_phaladesa ADD CONSTRAINT phala_phaladesa_narration_model_check
  CHECK (narration_model IS NULL OR narration_model IN (
      'gemini-pro', 'gemini-ultra', 'gemini-2.0-flash',
      'deepseek-chat', 'deepseek-r1'
      -- OpenAI models ('gpt-4o', 'gpt-4-turbo') and Anthropic models are NOT
      -- in this list (model policy: Gemini/DeepSeek only).
  ));

COMMIT;

-- DOWN:
-- ALTER TABLE phala_phaladesa DROP CONSTRAINT IF EXISTS phala_phaladesa_narration_model_check;
-- ALTER TABLE phala_phaladesa ADD CONSTRAINT phala_phaladesa_narration_model_check
--   CHECK (narration_model IS NULL OR narration_model IN (
--       'gemini-pro', 'gemini-ultra', 'gemini-2.0-flash',
--       'deepseek-chat', 'deepseek-r1', 'gpt-4o', 'gpt-4-turbo'
--   ));
