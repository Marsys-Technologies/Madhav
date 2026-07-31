-- Migration 499:
-- orchestrator_event_register — a durable, queryable register for no-op-completion events
-- (SAMĀPTI lane B-EVENTREG · brief v2.0 §9.6 · register item SD-EVENTREG-1)
-- =============================================================================
--
-- !! MIGRATION NUMBER IS A PLACEHOLDER !!
--   Per SAMAPTI_CONDUCTOR_PROMPT_v1_0.md §5, migration numbers are allocated by the
--   Conductor at MERGE time, not at authoring time:
--       max(highest in platform/migrations/, highest in platform/supabase/migrations/) + 1
--   read from `origin/main` at the moment MERGE-LOCK is taken. At authoring time the
--   observed max across both directories was 474
--   (platform/migrations/474_asset_throughput_incomplete_state.sql), so this will most
--   likely become 475 — but DO NOT rely on that; re-read at merge.
--   The Conductor must rewrite BOTH:
--     (a) this file's name  (XXX_PLACEHOLDER_orchestrator_event_register.sql -> <N>_orchestrator_event_register.sql)
--     (b) the "Migration XXX" token in this header comment.
--   (Migration 474 shipped with a stale internal number in its own header — that is
--   exactly the residual lane B-MIG474-COMMENT exists to clean up. Do not repeat it.)
--
-- -----------------------------------------------------------------------------
-- WHY THIS TABLE EXISTS
-- -----------------------------------------------------------------------------
-- SATYA_DIPA_REPORT_v1_0.md §1 ("Forensic-lead correction", load-bearing finding):
--
--     "The brief's forensic lead instructed querying the `asset.noop_completion` event
--      history first, as 'a near-complete register of every time this fired.' **That
--      register does not exist as a queryable, durable artifact.** ... There is no
--      `build_events`-style durable table for orchestrator events ... A Cloud Logging
--      query (`gcloud logging read 'textPayload:"noop_completion"' --freshness=9999d`)
--      returned zero results ... Recommend, as a non-blocking follow-up: persist
--      `asset.noop_completion` / `asset.noop_completion_rejected` to a durable table
--      (or a Cloud Logging sink with export) so a future audit of this class of defect
--      has a real register to query."
--
-- Today `emit_event()` (pipeline/orchestrator/events.py) has exactly two sinks, and
-- neither is a register:
--   * stdout  -> Cloud Logging, only when running on Cloud Run, ~30d default retention.
--   * Pub/Sub -> fire-and-forget to `cockpit-events`, whose only consumer
--                (src/app/api/cockpit/sse/route.ts) opens an ephemeral per-connection
--                subscription with a 600-second message-retention window.
-- Both are transports, not stores. SATYA-DĪPA's Phase A had to abandon its primary
-- forensic method for lack of this table and fall back to reconciling
-- `build_substep_progress`. This migration closes that gap.
--
-- CHOICE OF MECHANISM — table, not a Cloud Logging export sink. The brief allowed
-- either. A table wins on four counts: (1) it is queryable with the same psql/SQL
-- surface every other forensic artifact in this project uses, with no gcloud/BigQuery
-- dependency in the audit path; (2) it works identically for local, CLI, Cloud Run Job
-- and Cloud Run service builds — a logging sink only ever captures the Cloud Run
-- subset, which is precisely the subset that returned ZERO in the SATYA-DĪPA probe;
-- (3) it can be written atomically with the state decision it records (see below),
-- which a log sink structurally cannot; (4) it needs no new IAM, no new GCP resource,
-- and no new failure domain.
--
-- -----------------------------------------------------------------------------
-- WRITE PATH + TRANSACTION SEMANTICS (the important part)
-- -----------------------------------------------------------------------------
-- The register is written by `persist_event()` in pipeline/orchestrator/events.py,
-- called from `emit_event(evt, cur=cur)` at the two no-op-completion sites in
-- pipeline/orchestrator/asset_runner.py::_run_data_writer.
--
-- It writes on the ORCHESTRATOR'S OWN cursor, inside the same transaction as the
-- `UPDATE asset_throughput SET state = ...` that the event describes. That is
-- deliberate and is the whole forensic contract of this table:
--
--     a register row exists  <=>  that state decision actually committed.
--
-- The register can therefore never claim a promotion-to-'lit' that was rolled back,
-- and can never miss one that was not. An autonomous side connection would have been
-- more "durable" in the naive sense and strictly LESS truthful — it would log
-- decisions that never happened. Truth over completion (§1.1).
--
-- The INSERT is wrapped in a SAVEPOINT by `persist_event()`, so a register failure
-- (table absent because this migration has not been applied yet, permission problem,
-- anything) can never abort the enclosing build transaction. A build must never fail
-- because its audit trail failed. The failure is logged loudly instead.
--
-- -----------------------------------------------------------------------------
-- COLUMN TYPE NOTES
-- -----------------------------------------------------------------------------
-- chart_id / run_id are TEXT, not UUID, on purpose. Every real value is a UUID and
-- callers may cast on read (`chart_id::uuid`), but this is an audit sink whose single
-- job is to never lose an event: a malformed or non-UUID identifier (a CLI/local run,
-- a synthetic id, a future scope key) must land in the register as a row to be read,
-- not be discarded by a type error. Global/singleton assets legitimately carry
-- chart_id IS NULL.
--
-- rows_present / substeps_remaining are promoted to first-class columns (not left in
-- `payload`) because they are the two numbers the brief names explicitly and the two
-- an audit filters and aggregates on. `payload` retains the complete verbatim event
-- so nothing is lost to the projection.
--
-- VOLUME. Persistence is allowlisted (events.DEFAULT_DURABLE_EVENT_TYPES) to the two no-op
-- classes only, not to the full ~12-type orchestrator event vocabulary. Those two fire
-- only from writers with cross-attempt substep resumption — empirically ka_sangam and
-- ka_gochara_sweep alone (SATYA_DIPA_REPORT §"Plain-language answer") — i.e. a handful
-- of rows per full build, not a firehose. No retention/partitioning machinery is
-- warranted at this volume and none is created here.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS orchestrator_event_register (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type          TEXT        NOT NULL,
    chart_id            TEXT        NULL,
    asset_id            TEXT        NULL,
    run_id              TEXT        NULL,
    rows_present        BIGINT      NULL,
    substeps_remaining  INTEGER     NULL,
    emitted_by          TEXT        NULL,
    payload             JSONB       NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT orchestrator_event_register_type_nonempty CHECK (event_type <> '')
);

COMMENT ON TABLE orchestrator_event_register IS
    'Durable, queryable register of allowlisted orchestrator events (SAMĀPTI §9.6 / '
    'SD-EVENTREG-1). Closes the gap SATYA_DIPA_REPORT §1 documented: asset.noop_completion '
    'and asset.noop_completion_rejected previously went only to stdout (~30d Cloud Logging '
    'retention, and a --freshness=9999d query returned zero) or fire-and-forget Pub/Sub '
    '(600s per-connection window), so no queryable history existed. Written by '
    'pipeline/orchestrator/events.py::persist_event on the orchestrator''s own cursor, in '
    'the same transaction as the asset_throughput state write it records — a row here means '
    'that state decision actually committed.';

COMMENT ON COLUMN orchestrator_event_register.event_type IS
    'The emit_event() "type" field, e.g. asset.noop_completion / asset.noop_completion_rejected. '
    'Which types reach this table is governed by events.DEFAULT_DURABLE_EVENT_TYPES (overridable '
    'at runtime by the ORCHESTRATOR_DURABLE_EVENT_TYPES env var), not by the schema.';
COMMENT ON COLUMN orchestrator_event_register.chart_id IS
    'TEXT, not UUID: audit sink must never drop an event to a type error. NULL for global/singleton assets.';
COMMENT ON COLUMN orchestrator_event_register.rows_present IS
    'Data rows the count_sql probe found present at decision time. Present on both no-op classes.';
COMMENT ON COLUMN orchestrator_event_register.substeps_remaining IS
    'Substeps the writer''s own plan_substeps() still reported outstanding. Non-NULL on '
    'asset.noop_completion_rejected; NULL on asset.noop_completion (by definition zero remained).';
COMMENT ON COLUMN orchestrator_event_register.emitted_by IS
    'Best-effort emitter identity — K_SERVICE / CLOUD_RUN_JOB / hostname — so a future audit can '
    'tell a Cloud Run build from a local CLI run, the exact distinction that made the SATYA-DĪPA '
    'Cloud Logging probe ambiguous ("never fired on Cloud Run" vs "aged out of retention").';
COMMENT ON COLUMN orchestrator_event_register.payload IS
    'The complete verbatim event dict, so the first-class column projection loses nothing.';

-- "All no-op completions, newest first" — the primary audit query.
CREATE INDEX IF NOT EXISTS orchestrator_event_register_type_time_idx
    ON orchestrator_event_register (event_type, occurred_at DESC);

-- "Did THIS asset ever no-op-complete on THIS chart?" — the per-asset forensic query.
CREATE INDEX IF NOT EXISTS orchestrator_event_register_asset_chart_time_idx
    ON orchestrator_event_register (asset_id, chart_id, occurred_at DESC);

-- "What happened during run X?" — the per-run reconstruction query.
CREATE INDEX IF NOT EXISTS orchestrator_event_register_run_idx
    ON orchestrator_event_register (run_id)
    WHERE run_id IS NOT NULL;

-- Convenience read surface. The two no-op classes side by side with a decoded verdict,
-- so an auditor does not have to remember which event type means which outcome.
CREATE OR REPLACE VIEW orchestrator_noop_events AS
SELECT
    id,
    occurred_at,
    event_type,
    CASE event_type
        WHEN 'asset.noop_completion'          THEN 'promoted_to_lit'
        WHEN 'asset.noop_completion_rejected' THEN 'held_incomplete'
        ELSE 'unknown'
    END                                        AS verdict,
    chart_id,
    asset_id,
    run_id,
    rows_present,
    COALESCE(substeps_remaining, 0)            AS substeps_remaining,
    emitted_by,
    payload
FROM orchestrator_event_register
WHERE event_type IN ('asset.noop_completion', 'asset.noop_completion_rejected');

COMMENT ON VIEW orchestrator_noop_events IS
    'SD-EVENTREG-1 audit surface: every recorded no-op-completion decision with its verdict '
    'decoded (promoted_to_lit / held_incomplete). This is the register SATYA_DIPA_REPORT §1 '
    'looked for and did not find.';

COMMIT;
