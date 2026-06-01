-- 118_build_events.sql
-- Platform Modernization Wave 4 — unit 4.build_trigger.
--
-- Persisted progress rail for `marsys-build-pipeline-job`. Powers the
-- /api/build/events/[buildId] SSE stream the cockpit subscribes to, and
-- is durable so a refresh re-hydrates progress without losing rows.
--
-- One row per (build_id, stage_seq). build_id is opaque to the cockpit;
-- the trigger route returns it on enqueue.

CREATE TABLE IF NOT EXISTS build_events (
  build_id        text        NOT NULL,
  stage_seq       integer     NOT NULL,
  chart_id        text        NOT NULL,
  ayanamsha_role  text        NOT NULL,
  asset           text        NOT NULL,      -- e.g. 'chart_facts', 'msr', 'cdlm', 'cgm', 'ucn', 'rm', 'panchanga'
  stage           text        NOT NULL,      -- 'fetch' | 'parse' | 'validate' | 'stage_write' | 'swap' | 'verify' | 'freeze_old'
  status          text        NOT NULL,      -- 'started' | 'progress' | 'complete' | 'failed' | 'rolled_back'
  percent         numeric(5,2),              -- 0..100 for within-asset progress (NULL ⇒ binary stage)
  message         text,
  metadata        jsonb       NOT NULL DEFAULT '{}'::jsonb,
  emitted_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (build_id, stage_seq)
);

CREATE INDEX IF NOT EXISTS build_events_chart_id_emitted_at_idx
  ON build_events (chart_id, emitted_at DESC);

CREATE INDEX IF NOT EXISTS build_events_build_id_emitted_at_idx
  ON build_events (build_id, emitted_at DESC);

COMMENT ON TABLE build_events IS
  'Progress rail for marsys-build-pipeline-job. Written by the Python pipeline '
  'and the task handler; read by /api/build/events/[buildId] SSE.';
