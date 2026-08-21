-- migration 586: PARIŚEṢA-V4 F-152 — audit trigger on asset_throughput.state changes
-- + admin visibility.
--
-- WHY: asset_throughput.state is the orchestrator's single source of truth for
-- per-asset build completion (CLAUDE.md §N.8). F-150's cascade mutation and an
-- earlier manual 'lit' repair both wrote this column directly with no durable
-- record of who/what changed it, when, or how.
--
-- `orchestrator_event_register` (migration 499, platform/supabase/migrations/)
-- does NOT already cover this gap — checked before building this migration:
--   * it is allowlisted (events.DEFAULT_DURABLE_EVENT_TYPES) to exactly two
--     event types, asset.noop_completion / asset.noop_completion_rejected;
--   * it is written only from pipeline/orchestrator/events.py::persist_event,
--     called from the two no-op-completion sites inside
--     pipeline/orchestrator/asset_runner.py::_run_data_writer — application-level,
--     never DB-level;
--   * it is therefore blind to any OTHER write to asset_throughput.state,
--     including a direct SQL UPDATE issued from psql or a one-off script — which
--     is exactly the class of touch F-150's cascade mutation and the original
--     manual 'lit' repair both were, and exactly the class this finding exists
--     to catch.
-- This migration adds a DB-level AFTER trigger that sees every state change
-- regardless of caller, closing that blind spot. It does not replace or modify
-- orchestrator_event_register — the two are complementary (application-emitted
-- semantic events vs. a DB-level record of every raw state write).
--
-- `admin_audit_log` (platform/migrations/333_admin_audit_log.sql) is NOT used
-- here: its actor_id/target_user_id columns are FKs to public.profiles, and a
-- DB-trigger-sourced row has no profile — writing NULL-actor rows into that
-- user-facing admin surface would pollute it with orchestrator bookkeeping it
-- was never meant to hold. A dedicated table instead. The application-level
-- admin repair path (the manual-'lit'-repair path that motivated this finding)
-- continues to write admin_audit_log itself, where a real actor_id exists.
--
-- SAFETY (the load-bearing constraint): an audit trigger that can raise would
-- break every build, since it fires on every asset_throughput.state write,
-- including inside the orchestrator's own per-asset savepoints. This trigger is
-- therefore AFTER, not BEFORE — it records, it does not block (contrast
-- platform/migrations/331_guard_no_chart_scoped_global_asset_throughput.sql,
-- the style template this migration copies, which is BEFORE because it blocks).
-- The audit table is deliberately unconstrained — no FKs, no CHECKs, every
-- column but id/changed_at nullable — so the INSERT it drives is structurally
-- incapable of failing. current_setting(<name>, true) (missing_ok=true) is used
-- throughout so an unset GUC/session value yields NULL instead of raising. The
-- body is deliberately left UNCAUGHT (no BEGIN/EXCEPTION WHEN OTHERS swallow) —
-- CLAUDE.md §N.8: a try/catch that always succeeds is an unfalsifiable flag, not
-- a clean result. Safety here comes from the table being impossible to violate,
-- not from swallowing an error it should never be able to raise.
--
-- ORCHESTRATOR GUC: `triggered_by` has no automatic source — it is populated by
-- `current_setting('marsys.triggered_by', true)`, which is NULL unless something
-- sets it. Set in the SAME PR, session-scoped (not per-transaction `SET LOCAL`,
-- because pipeline/orchestrator/asset_runner.py::run_asset commits multiple times
-- per asset and a `SET LOCAL` would not survive past the first commit): see
-- pipeline/orchestrator/db.py::connect(), the shared build-session connection
-- factory used by every real chart build (runner.py, global_runner.py, and the
-- standalone writer-driver scripts routed through it) — `SET marsys.triggered_by
-- = 'asset_runner'` now runs there alongside its existing session GUCs
-- (idle_in_transaction_session_timeout / statement_timeout / lock_timeout). A
-- write that did NOT go through that factory (a direct psql UPDATE, an ad hoc
-- script) leaves triggered_by NULL — that NULL is itself diagnostic, not a gap.

CREATE TABLE IF NOT EXISTS asset_throughput_state_audit (
  id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chart_id           UUID        NULL,
  asset_id           TEXT        NULL,
  old_state          TEXT        NULL,
  new_state          TEXT        NULL,
  db_user            TEXT        NULL,
  application_name   TEXT        NULL,
  triggered_by       TEXT        NULL,
  changed_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS asset_throughput_state_audit_changed_at_idx
  ON asset_throughput_state_audit (changed_at DESC);

CREATE INDEX IF NOT EXISTS asset_throughput_state_audit_asset_chart_idx
  ON asset_throughput_state_audit (asset_id, chart_id, changed_at DESC);

COMMENT ON TABLE asset_throughput_state_audit IS
  'F-152: durable AFTER-trigger record of every asset_throughput.state change, '
  'regardless of caller (orchestrator, psql, one-off script). Deliberately '
  'unconstrained (no FKs, no CHECKs, every column but id/changed_at nullable) so '
  'the audit trigger is structurally incapable of aborting the write it records '
  '— see migration 586 header comment. Complements, does not replace, '
  'orchestrator_event_register (migration 499), which is allowlisted to two '
  'application-emitted event types and blind to a direct SQL UPDATE.';

COMMENT ON COLUMN asset_throughput_state_audit.triggered_by IS
  'current_setting(''marsys.triggered_by'', true) at write time. Set to '
  '''asset_runner'' by pipeline/orchestrator/db.py::connect() for every '
  'orchestrator build-session connection; NULL for any write that did not go '
  'through that factory — the NULL is itself diagnostic, not a defect.';

CREATE OR REPLACE FUNCTION _record_asset_throughput_state_change()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO asset_throughput_state_audit
    (chart_id, asset_id, old_state, new_state, db_user, application_name, triggered_by, changed_at)
  VALUES
    (NEW.chart_id, NEW.asset_id, OLD.state, NEW.state,
     current_user,
     current_setting('application_name', true),
     current_setting('marsys.triggered_by', true),
     now());

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- AFTER, not BEFORE: this trigger records, it does not block (see header).
-- WHEN (OLD.state IS DISTINCT FROM NEW.state) so a no-op UPDATE (one that
-- touches other columns, e.g. last_error, without changing state) writes no row.
DROP TRIGGER IF EXISTS trg_asset_throughput_state_audit ON asset_throughput;
CREATE TRIGGER trg_asset_throughput_state_audit
AFTER UPDATE OF state ON asset_throughput
FOR EACH ROW
WHEN (OLD.state IS DISTINCT FROM NEW.state)
EXECUTE FUNCTION _record_asset_throughput_state_change();
