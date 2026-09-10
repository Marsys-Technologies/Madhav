-- 574 — NCD-8 spend ceilings: per-(user, channel, model) cost attribution.
--
-- Paripraśna P1 / lane G1-D "Limits" (PARIPRASHNA_IMPLEMENTATION_ROADMAP §G1-D;
-- ruling NCD-8 in PARIPRASHNA_DECISION_REGISTER_v1_0.md line 66, RULED 2026-08-18:
-- "Spend caps $2/turn · $40/day, pre-dispatch, both doors"; requirement PPR-25 in
-- PARIPRASHNA_ARCHITECTURE_v1_0.md line 129).
--
-- NO NEW COST TABLE. `llm_usage_events` is already the per-user cost ledger
-- (user_id, provider, model, computed_cost_usd, started_at) and stays the single
-- source of truth for spend. It carries (user, model) attribution today but has no
-- notion of WHICH SERVING DOOR a call came through, so a per-(user, channel, model)
-- rollup is not derivable from it. This migration adds that one missing dimension
-- and the composite index the pre-dispatch daily-ceiling query needs.
--
-- `channel` is NULLABLE with NO default on purpose. A row written by a call site
-- that does not declare its door records an honest NULL — never a plausible-looking
-- invented channel (CLAUDE.md §N.7 item 6). Every historical row is therefore NULL,
-- which is the truth: the door was not recorded when they were written.

BEGIN;

ALTER TABLE public.llm_usage_events
  ADD COLUMN IF NOT EXISTS channel TEXT;

COMMENT ON COLUMN public.llm_usage_events.channel IS
  'Serving door this LLM call was dispatched through: ''web'' (the /api/pariprashna '
  'browser door) | ''mcp'' (the prashna_ask service-to-service door) | ''other''. '
  'NULL means the call site did not declare a door — an honest absence, not a default. '
  'Added by NCD-8 (spend ceilings $2/turn, $40/day, pre-dispatch, both doors) so cost '
  'attribution can be rolled up per (user_id, channel, model).';

-- Deliberately NOT a CHECK constraint: a call site that grows a new door must be
-- able to record it honestly rather than have its telemetry INSERT rejected.
-- persistObservation() never throws, so a CHECK violation here would silently drop
-- the whole cost row — losing the very spend data the ceiling reads. The permitted
-- vocabulary is enforced in TypeScript (SpendChannel in @/lib/limits/spend_ceiling).

-- The pre-dispatch daily-ceiling query is
--   SELECT SUM(computed_cost_usd) FROM llm_usage_events
--    WHERE user_id = $1 AND started_at >= <UTC day start>
-- and it runs on the request-latency critical path before every turn on both doors.
-- idx_llm_usage_events_user_id alone forces a heap scan of the user's whole history;
-- this composite serves the range predicate from the index.
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_user_started
  ON public.llm_usage_events (user_id, started_at DESC);

-- Serves the per-(user, channel, model) attribution rollup.
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_user_channel_model
  ON public.llm_usage_events (user_id, channel, model);

COMMIT;
