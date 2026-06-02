-- 013_query_trace_steps.sql
-- Query Trace Panel: per-step execution record for every pipeline invocation.
-- One row per step per query. query_id is a loose FK to audit_log.query_id
-- (no hard FK constraint to avoid timing dependency — audit row may not yet
-- exist when first trace steps are written).
-- payload JSONB stores full chunk/signal text for drill-down.

CREATE TABLE IF NOT EXISTS public.query_trace_steps (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        UUID        NOT NULL,
  conversation_id UUID,
  step_seq        SMALLINT    NOT NULL,
  step_name       TEXT        NOT NULL,
  step_type       TEXT        NOT NULL
                  CHECK (step_type IN ('deterministic','llm','sql','vector','gcs')),
  status          TEXT        NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','running','done','error')),
  started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at    TIMESTAMPTZ,
  latency_ms      INTEGER,
  parallel_group  TEXT,
  data_summary    JSONB       NOT NULL DEFAULT '{}',
  payload         JSONB       NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Primary lookup: all steps for a given query, in order
CREATE INDEX idx_query_trace_steps_query_id
  ON public.query_trace_steps (query_id, step_seq);

-- History list: recent queries sorted by time
CREATE INDEX idx_query_trace_steps_created_at
  ON public.query_trace_steps (created_at DESC);

COMMENT ON TABLE public.query_trace_steps IS
  'Per-step execution trace for every pipeline invocation. Powers the real-time Query Trace Panel.';

COMMENT ON COLUMN public.query_trace_steps.step_type IS
  'deterministic | llm | sql | vector | gcs';

COMMENT ON COLUMN public.query_trace_steps.parallel_group IS
  'Non-null for steps that execute concurrently (e.g. tool_fetch). Used by the UI to render parallel timeline lanes.';

COMMENT ON COLUMN public.query_trace_steps.data_summary IS
  'Lightweight stats per step type: {result, confidence} | {model, input_tokens, output_tokens} | {rows_returned, token_estimate, tool_name} | {chunks_returned, top_score, token_estimate} | {bytes, token_estimate, source_path}';

COMMENT ON COLUMN public.query_trace_steps.payload IS
  'Full data payload for drill-down. sql/vector/gcs: {items:[{id,source,layer,token_estimate,text}]}. context_assembly: {l1_tokens,l2_tokens,system_tokens,total_tokens,l1_items,l2_items}. llm: {prompt_preview}.';
