---
brief_id: EXEC_BRIEF_PHASE_TRACE
version: 1.0
status: AUTHORED
authored: 2026-04-28
executor: Claude Sonnet 4.6 (Cowork)
feature: Query Trace Panel
---

# EXEC_BRIEF — Query Trace Panel (Phase Trace)

## Mission

Build a real-time query observability panel that opens as a right-side drawer in the
consume chat UI. For every query the native submits, the panel shows every pipeline
step lighting up live (sequenced, typed, latency-timed), parallel tool lanes rendered
accurately, a structured L1 / L2.5 / System context breakdown with token volumes,
and double-click drill-down to the actual chunk text that entered the LLM. Historical
mode lets the native replay any past query's trace from stored data.

## Hard Constraints

- **No new correlation ID needed.** `query_plan_id` (from `QueryPlan.query_plan_id`,
  already the PK of `audit_log`) is the trace key. Surface it to the frontend by
  adding `queryId` to the `messageMetadata` emission on `part.type === 'start'` in
  `consume/route.ts`. The frontend subscribes to SSE immediately on receiving it.
- **Parallelism is real.** Tools fire via `Promise.all()` in `consume/route.ts`
  lines 146-156. The timeline must show overlapping bars for concurrent tools.
- **Full chunk text stored.** Single user; storage cost is acceptable. Each
  `query_trace_steps` row holds the full payload JSONB including raw text.
- **SSE is in-process.** Node.js `EventEmitter` singleton keyed by `query_id`.
  This is correct for the current single-server dev deployment. Document the
  Redis pub/sub upgrade path in a code comment but do not build it.
- **Auth-gated.** The SSE endpoint and history API are `super_admin` only (same
  check pattern as existing audit routes).
- **Non-blocking.** Trace emission must never add latency to the query response path.
  All `emitter.emit()` calls are fire-and-forget. DB writes happen in the background.

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `013_query_trace_steps.sql` migration applies cleanly; table exists with all specified columns |
| AC-2 | `TraceEmitter` singleton compiles; `emitStep` / `subscribe` / `unsubscribe` work in unit test |
| AC-3 | A D1 chart query produces ≥ 7 rows in `query_trace_steps` (classify, compose, each tool, context_assembly, synthesis, audit) |
| AC-4 | `/api/trace/stream/[queryId]` returns `text/event-stream`; events arrive within 50ms of each pipeline step completing |
| AC-5 | TracePanel opens as a drawer when ⚡ TRACE is clicked; steps light up in real time |
| AC-6 | Concurrent tools (vector_search, msr_sql, bundle_load) appear as parallel horizontal bars on the timeline, not stacked sequentially |
| AC-7 | Context breakdown shows L1, L2.5, and System token counts that sum to `synthesis_input_tokens` (±10% tolerance for char/token estimation) |
| AC-8 | Double-clicking an L1 or L2.5 row expands to show the actual chunk / signal text |
| AC-9 | History tab lists past queries; clicking one replays the stored trace |
| AC-10 | Zero increase in p50 synthesis latency (trace emission is fire-and-forget) |

## File Map

```
platform/
  supabase/migrations/
    013_query_trace_steps.sql          ← Stream A
  src/lib/trace/
    types.ts                           ← Stream B
    emitter.ts                         ← Stream B
    writer.ts                          ← Stream B
  src/app/api/
    trace/
      stream/[queryId]/route.ts        ← Stream D
      history/route.ts                 ← Stream F
  src/components/trace/
    TracePanel.tsx                     ← Stream E
    TraceTimeline.tsx                  ← Stream E
    ContextInspector.tsx               ← Stream E
    ChunkDrilldown.tsx                 ← Stream E
    useTraceStream.ts                  ← Stream E
  src/app/clients/[chartId]/consume/
    page.tsx                           ← Stream E (add ⚡ button + TracePanel mount)
```

---

## Stream A — Database Migration

**File:** `platform/supabase/migrations/013_query_trace_steps.sql`

```sql
-- 013_query_trace_steps.sql
-- Query Trace Panel: per-step execution record for every pipeline invocation.
-- One row per step per query. query_id FK → audit_log.query_id.
-- payload JSONB stores full chunk/signal text for drill-down (single user; acceptable storage).

CREATE TABLE IF NOT EXISTS public.query_trace_steps (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        UUID        NOT NULL,          -- FK to audit_log.query_id (loose; no hard FK to avoid audit-log timing dependency)
  conversation_id UUID,                          -- informational; from conversations.id
  step_seq        SMALLINT    NOT NULL,          -- 1-based sequence within the query
  step_name       TEXT        NOT NULL,          -- e.g. 'classify', 'vector_search', 'context_assembly'
  step_type       TEXT        NOT NULL           -- 'deterministic' | 'llm' | 'sql' | 'vector' | 'gcs'
                  CHECK (step_type IN ('deterministic','llm','sql','vector','gcs')),
  status          TEXT        NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','running','done','error')),
  started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at    TIMESTAMPTZ,
  latency_ms      INTEGER,                       -- null until step completes
  parallel_group  TEXT,                          -- non-null for concurrent steps (e.g. 'tool_fetch')
  data_summary    JSONB       NOT NULL DEFAULT '{}',
  -- data_summary shape (varies by step_type):
  -- deterministic: { result?: string, confidence?: number }
  -- llm:           { model: string, input_tokens?: number, output_tokens?: number }
  -- sql:           { rows_returned: number, token_estimate: number, tool_name: string }
  -- vector:        { chunks_returned: number, top_score: number, token_estimate: number }
  -- gcs:           { bytes: number, token_estimate: number, source_path: string }
  payload         JSONB       NOT NULL DEFAULT '{}',
  -- payload shape:
  -- sql/gcs/vector steps: { items: [{ id, source, layer, token_estimate, text }] }
  -- context_assembly:     { l1_tokens, l2_tokens, system_tokens, total_tokens,
  --                          l1_items: [...], l2_items: [...] }
  -- llm steps:            { prompt_preview: string (first 500 chars) }
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_query_trace_steps_query_id
  ON public.query_trace_steps (query_id, step_seq);

CREATE INDEX idx_query_trace_steps_created_at
  ON public.query_trace_steps (created_at DESC);

COMMENT ON TABLE public.query_trace_steps IS
  'Per-step execution trace for every query pipeline run. Powers the real-time Query Trace Panel.';
```

**Apply via:**
```bash
cd platform
npx supabase db push --local
# OR directly against Cloud SQL Auth Proxy (port 5433):
psql postgresql://amjis_app:...@127.0.0.1:5433/amjis -f supabase/migrations/013_query_trace_steps.sql
```

---

## Stream B — TraceEmitter + Types

### `src/lib/trace/types.ts`

```typescript
/**
 * MARSYS-JIS Query Trace Panel — shared types
 * schema_version: 1.0
 */

export type StepType = 'deterministic' | 'llm' | 'sql' | 'vector' | 'gcs'
export type StepStatus = 'pending' | 'running' | 'done' | 'error'

export interface TraceChunkItem {
  id: string               // chunk_id / signal_id
  source: string           // canonical_id or tool_name
  layer: 'L1' | 'L2.5' | 'system'
  token_estimate: number
  text: string             // full raw text
}

export interface TraceDataSummary {
  // deterministic
  result?: string
  confidence?: number
  // llm
  model?: string
  input_tokens?: number
  output_tokens?: number
  // sql
  rows_returned?: number
  tool_name?: string
  // vector
  chunks_returned?: number
  top_score?: number
  // shared
  token_estimate?: number
  // gcs
  source_path?: string
  bytes?: number
}

export interface TracePayload {
  // sql / vector / gcs steps
  items?: TraceChunkItem[]
  // context_assembly
  l1_tokens?: number
  l2_tokens?: number
  system_tokens?: number
  total_tokens?: number
  l1_items?: TraceChunkItem[]
  l2_items?: TraceChunkItem[]
  // llm steps
  prompt_preview?: string
}

export interface TraceStep {
  query_id: string
  conversation_id?: string
  step_seq: number
  step_name: string
  step_type: StepType
  status: StepStatus
  started_at: string       // ISO
  completed_at?: string    // ISO, set on done/error
  latency_ms?: number
  parallel_group?: string  // e.g. 'tool_fetch'
  data_summary: TraceDataSummary
  payload: TracePayload
}

/** Sent over SSE */
export interface TraceEvent {
  event: 'step_start' | 'step_done' | 'step_error' | 'done'
  step?: TraceStep
  query_id: string
}
```

### `src/lib/trace/emitter.ts`

```typescript
/**
 * MARSYS-JIS Query Trace Panel — in-process event emitter
 *
 * Singleton EventEmitter keyed by query_id. Each pipeline step calls
 * emitStep(); the SSE endpoint subscribes. DB writes happen in the
 * background (fire-and-forget) and never block the response path.
 *
 * NOTE: This is correct for a single-server deployment. If the platform
 * ever runs multiple instances, swap this for Redis pub/sub:
 *   publisher.publish(`trace:${queryId}`, JSON.stringify(event))
 *   subscriber.subscribe(`trace:${queryId}`, handler)
 */

import { EventEmitter } from 'events'
import type { TraceEvent, TraceStep } from './types'
import { writeTraceStep } from './writer'

class TraceEmitter extends EventEmitter {
  constructor() {
    super()
    this.setMaxListeners(50) // one per open SSE connection
  }

  emitStep(event: TraceEvent): void {
    // Fire-and-forget: emit to live SSE subscribers
    this.emit(event.query_id, event)

    // Fire-and-forget: persist to DB
    if (event.step) {
      void writeTraceStep(event.step).catch(err =>
        console.error('[trace] DB write failed:', err)
      )
    }
  }

  subscribe(queryId: string, handler: (event: TraceEvent) => void): void {
    this.on(queryId, handler)
  }

  unsubscribe(queryId: string, handler: (event: TraceEvent) => void): void {
    this.off(queryId, handler)
  }
}

// Module-level singleton (survives hot-reload in Next.js dev via globalThis)
const globalForTrace = globalThis as unknown as { __traceEmitter?: TraceEmitter }
if (!globalForTrace.__traceEmitter) {
  globalForTrace.__traceEmitter = new TraceEmitter()
}
export const traceEmitter = globalForTrace.__traceEmitter
```

### `src/lib/trace/writer.ts`

```typescript
/**
 * MARSYS-JIS Query Trace Panel — DB persistence
 */

import { query } from '@/lib/db/client'
import type { TraceStep } from './types'

export async function writeTraceStep(step: TraceStep): Promise<void> {
  await query(
    `INSERT INTO public.query_trace_steps
       (query_id, conversation_id, step_seq, step_name, step_type, status,
        started_at, completed_at, latency_ms, parallel_group, data_summary, payload)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12::jsonb)
     ON CONFLICT DO NOTHING`,
    [
      step.query_id,
      step.conversation_id ?? null,
      step.step_seq,
      step.step_name,
      step.step_type,
      step.status,
      step.started_at,
      step.completed_at ?? null,
      step.latency_ms ?? null,
      step.parallel_group ?? null,
      JSON.stringify(step.data_summary),
      JSON.stringify(step.payload),
    ]
  )
}

/** For historical mode: fetch all steps for a query, ordered by seq */
export async function fetchTraceSteps(queryId: string): Promise<TraceStep[]> {
  const result = await query<TraceStep>(
    `SELECT query_id, conversation_id, step_seq, step_name, step_type,
            status, started_at, completed_at, latency_ms, parallel_group,
            data_summary, payload
     FROM public.query_trace_steps
     WHERE query_id = $1
     ORDER BY step_seq ASC`,
    [queryId]
  )
  return result.rows
}

/** For history list: recent queries with summary stats */
export async function fetchTraceHistory(limit = 30): Promise<{
  query_id: string
  query_text: string | null
  created_at: string
  step_count: number
  total_latency_ms: number | null
}[]> {
  const result = await query(
    `SELECT
       t.query_id,
       a.query_text,
       MIN(t.started_at) AS created_at,
       COUNT(*)::int AS step_count,
       EXTRACT(EPOCH FROM (MAX(t.completed_at) - MIN(t.started_at))) * 1000 AS total_latency_ms
     FROM public.query_trace_steps t
     LEFT JOIN public.audit_log a ON a.query_id = t.query_id
     GROUP BY t.query_id, a.query_text
     ORDER BY MIN(t.started_at) DESC
     LIMIT $1`,
    [limit]
  )
  return result.rows
}
```

---

## Stream C — Pipeline Instrumentation

All emit calls are **fire-and-forget** (no `await`). Import `traceEmitter` at the top of each file.

### Instrumentation helper (inline in each callsite)

```typescript
// Pattern used throughout:
import { traceEmitter } from '@/lib/trace/emitter'
import type { TraceStep } from '@/lib/trace/types'

function makeStep(partial: Partial<TraceStep> & { query_id: string; step_seq: number; step_name: string; step_type: TraceStep['step_type'] }): TraceStep {
  return {
    status: 'running',
    started_at: new Date().toISOString(),
    data_summary: {},
    payload: {},
    ...partial,
  }
}
```

### C.1 — `consume/route.ts` — Step 1: Classify

Wrap the `classify()` call:

```typescript
// BEFORE:
const queryPlan = await classify(queryText, { ... })

// AFTER:
const classifyStart = Date.now()
traceEmitter.emitStep({
  event: 'step_start',
  query_id: 'PENDING', // query_id not yet known — use placeholder, fill after classify
  step: makeStep({ query_id: 'PENDING', step_seq: 1, step_name: 'classify', step_type: 'deterministic' }),
})
const queryPlan = await classify(queryText, { ... })
const queryId = queryPlan.query_plan_id
// Re-emit with real query_id:
traceEmitter.emitStep({
  event: 'step_done',
  query_id: queryId,
  step: {
    ...makeStep({ query_id: queryId, step_seq: 1, step_name: 'classify', step_type: 'deterministic' }),
    status: 'done',
    completed_at: new Date().toISOString(),
    latency_ms: Date.now() - classifyStart,
    data_summary: { result: queryPlan.query_class, confidence: queryPlan.router_confidence },
    payload: {},
  },
})
```

**Note:** Since `query_id` comes from `queryPlan`, Step 1 must emit a `step_done` event (not `step_start`) with the real `query_id` immediately after `classify()` resolves. The `PENDING` step_start is omitted from DB (writer checks for `PENDING` and skips).

### C.2 — `consume/route.ts` — Step 2: Compose Bundle

```typescript
const composeStart = Date.now()
const bundle = await compose(queryPlan)
traceEmitter.emitStep({
  event: 'step_done',
  query_id: queryId,
  step: {
    query_id: queryId,
    step_seq: 2,
    step_name: 'compose_bundle',
    step_type: 'deterministic',
    status: 'done',
    started_at: new Date(composeStart).toISOString(),
    completed_at: new Date().toISOString(),
    latency_ms: Date.now() - composeStart,
    data_summary: {
      result: `${bundle.mandatory_context.length} bundles, ${queryPlan.tools_authorized.length} tools authorized`,
    },
    payload: {},
  },
})
```

### C.3 — `consume/route.ts` — Steps 3-N: Parallel Tool Fetch

Replace the existing `Promise.all` block:

```typescript
const toolFetchStart = Date.now()
// Emit 'running' for all tools simultaneously
queryPlan.tools_authorized.forEach((toolName, idx) => {
  traceEmitter.emitStep({
    event: 'step_start',
    query_id: queryId,
    step: {
      query_id: queryId,
      conversation_id: finalConversationId,
      step_seq: 3 + idx,
      step_name: toolName,
      step_type: toolStepType(toolName), // see helper below
      status: 'running',
      started_at: new Date().toISOString(),
      parallel_group: 'tool_fetch',
      data_summary: {},
      payload: {},
    },
  })
})

const toolResults = await Promise.all(
  queryPlan.tools_authorized.map(async (toolName, idx) => {
    const t = getTool(toolName)
    if (!t) return null
    const toolStart = Date.now()
    try {
      const result = await executeWithCache(t, queryPlan, cache)
      traceEmitter.emitStep({
        event: 'step_done',
        query_id: queryId,
        step: {
          query_id: queryId,
          conversation_id: finalConversationId,
          step_seq: 3 + idx,
          step_name: toolName,
          step_type: toolStepType(toolName),
          status: 'done',
          started_at: new Date(toolStart).toISOString(),
          completed_at: new Date().toISOString(),
          latency_ms: Date.now() - toolStart,
          parallel_group: 'tool_fetch',
          data_summary: buildToolSummary(toolName, result),
          payload: buildToolPayload(toolName, result),
        },
      })
      return result
    } catch (err) {
      traceEmitter.emitStep({
        event: 'step_error',
        query_id: queryId,
        step: {
          query_id: queryId,
          step_seq: 3 + idx,
          step_name: toolName,
          step_type: toolStepType(toolName),
          status: 'error',
          started_at: new Date(toolStart).toISOString(),
          completed_at: new Date().toISOString(),
          latency_ms: Date.now() - toolStart,
          parallel_group: 'tool_fetch',
          data_summary: { result: String(err) },
          payload: {},
        },
      })
      return null
    }
  })
)
```

**Helpers to add in `consume/route.ts`:**

```typescript
function toolStepType(toolName: string): TraceStep['step_type'] {
  if (toolName === 'vector_search') return 'vector'
  if (toolName === 'msr_sql' || toolName === 'query_msr_aggregate') return 'sql'
  return 'gcs' // bundle loads, manifest_query, etc.
}

function buildToolSummary(toolName: string, result: ToolBundle): TraceDataSummary {
  const totalChars = result.results.reduce((s, r) => s + r.content.length, 0)
  const tokenEstimate = Math.ceil(totalChars / 4)
  if (toolName === 'vector_search') {
    const topScore = result.results[0]?.significance ?? result.results[0]?.confidence ?? 0
    return { chunks_returned: result.results.length, top_score: topScore, token_estimate: tokenEstimate }
  }
  return { rows_returned: result.results.length, tool_name: toolName, token_estimate: tokenEstimate }
}

function buildToolPayload(toolName: string, result: ToolBundle): TracePayload {
  const items: TraceChunkItem[] = result.results.map(r => ({
    id: r.signal_id ?? r.source_canonical_id ?? toolName,
    source: r.source_canonical_id ?? toolName,
    layer: inferLayer(toolName, r),
    token_estimate: Math.ceil(r.content.length / 4),
    text: r.content,
  }))
  return { items }
}

function inferLayer(toolName: string, _r: ToolBundleResult): 'L1' | 'L2.5' | 'system' {
  if (toolName === 'vector_search') {
    // vector_search returns mixed l1_fact + synthesis chunks; approximated as L1
    return 'L1'
  }
  if (['msr_sql', 'query_msr_aggregate', 'pattern_register', 'resonance_register',
       'cluster_atlas', 'contradiction_register', 'temporal', 'cgm_graph_walk'].includes(toolName)) {
    return 'L2.5'
  }
  return 'L1'
}
```

### C.4 — `single_model_strategy.ts` — Context Assembly Step

Add immediately after the `nonVsResults` block is built and before `renderedPrompt` is finalized. The step_seq for context_assembly = `3 + queryPlan.tools_authorized.length`.

```typescript
// Emit context_assembly trace step (fire-and-forget)
if (request.query_plan?.query_plan_id) {
  const qid = request.query_plan.query_plan_id
  const nToolSteps = (request.query_plan.tools_authorized?.length ?? 0)
  const ctxSeq = 3 + nToolSteps

  // Build L1/L2 item lists from vsResults + nonVsResults
  const l1Items: TraceChunkItem[] = vsResults.map(r => ({
    id: r.signal_id ?? 'unknown',
    source: 'vector_search',
    layer: 'L1' as const,
    token_estimate: Math.ceil(r.content.length / 4),
    text: r.content,
  }))

  const l2Items: TraceChunkItem[] = nonVsResults.flatMap(tb =>
    tb.results.map(r => ({
      id: r.signal_id ?? tb.tool_name,
      source: tb.tool_name,
      layer: 'L2.5' as const,
      token_estimate: Math.ceil(r.content.length / 4),
      text: r.content,
    }))
  )

  const systemTokens = Math.ceil(renderedPrompt.length / 4) // approximation before injection
  const l1Tokens = l1Items.reduce((s, i) => s + i.token_estimate, 0)
  const l2Tokens = l2Items.reduce((s, i) => s + i.token_estimate, 0)

  traceEmitter.emitStep({
    event: 'step_done',
    query_id: qid,
    step: {
      query_id: qid,
      step_seq: ctxSeq,
      step_name: 'context_assembly',
      step_type: 'deterministic',
      status: 'done',
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      latency_ms: 0,
      data_summary: {
        token_estimate: l1Tokens + l2Tokens + systemTokens,
      },
      payload: {
        l1_tokens: l1Tokens,
        l2_tokens: l2Tokens,
        system_tokens: systemTokens,
        total_tokens: l1Tokens + l2Tokens + systemTokens,
        l1_items: l1Items,
        l2_items: l2Items,
      },
    },
  })
}
```

### C.5 — `consume/route.ts` — Add queryId to stream metadata

```typescript
// In messageMetadata callback, add queryId:
if (part.type === 'start' && isFirstTurn) {
  return { conversationId: finalConversationId, model: modelId, pipeline: 'v2', queryId }
}
if (part.type === 'start') {
  return { model: modelId, pipeline: 'v2', queryId }
}
```

### C.6 — Synthesis + Audit steps

Emit `synthesis` step_start before `orchestrator.synthesize()` and `step_done` in `onFinish`.
Emit `audit_validation` step_done inside the existing `createAuditConsumer` callback.
(Exact wiring TBD by executor based on final step_seq count.)

---

## Stream D — SSE Endpoint

**File:** `src/app/api/trace/stream/[queryId]/route.ts`

```typescript
import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { traceEmitter } from '@/lib/trace/emitter'
import { fetchTraceSteps } from '@/lib/trace/writer'
import type { TraceEvent } from '@/lib/trace/types'

export const dynamic = 'force-dynamic'
export const maxDuration = 120

async function isSuperAdmin(uid: string): Promise<boolean> {
  const r = await query<{ is_super_admin: boolean }>(
    'SELECT is_super_admin FROM public.user_profiles WHERE firebase_uid = $1',
    [uid]
  )
  return r.rows[0]?.is_super_admin === true
}

export async function GET(
  _request: Request,
  { params }: { params: { queryId: string } }
) {
  const user = await getServerUser()
  if (!user) return new Response('Unauthorized', { status: 401 })
  if (!(await isSuperAdmin(user.uid))) return new Response('Forbidden', { status: 403 })

  const { queryId } = params
  const isHistorical = _request.headers.get('x-trace-mode') === 'historical'

  const encoder = new TextEncoder()
  const send = (event: TraceEvent) =>
    encoder.encode(`data: ${JSON.stringify(event)}\n\n`)

  if (isHistorical) {
    // Replay stored steps as a stream
    const steps = await fetchTraceSteps(queryId)
    const stream = new ReadableStream({
      start(controller) {
        for (const step of steps) {
          controller.enqueue(send({ event: 'step_done', query_id: queryId, step }))
        }
        controller.enqueue(send({ event: 'done', query_id: queryId }))
        controller.close()
      },
    })
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    })
  }

  // Live mode: subscribe to in-process emitter
  let cleanupHandler: ((e: TraceEvent) => void) | null = null
  const stream = new ReadableStream({
    start(controller) {
      const handler = (event: TraceEvent) => {
        try {
          controller.enqueue(send(event))
          if (event.event === 'done') {
            controller.close()
          }
        } catch {
          // Client disconnected
        }
      }
      cleanupHandler = handler
      traceEmitter.subscribe(queryId, handler)
    },
    cancel() {
      if (cleanupHandler) traceEmitter.unsubscribe(queryId, cleanupHandler)
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
```

---

## Stream E — TracePanel UI

### `src/components/trace/useTraceStream.ts`

```typescript
'use client'
import { useState, useEffect, useRef } from 'react'
import type { TraceEvent, TraceStep } from '@/lib/trace/types'

export interface TraceState {
  steps: TraceStep[]
  done: boolean
}

export function useTraceStream(queryId: string | null, historical = false): TraceState {
  const [steps, setSteps] = useState<TraceStep[]>([])
  const [done, setDone] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!queryId) return
    setSteps([])
    setDone(false)

    const url = `/api/trace/stream/${queryId}`
    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e) => {
      const event: TraceEvent = JSON.parse(e.data)
      if (event.event === 'done') {
        setDone(true)
        es.close()
        return
      }
      if (event.step) {
        setSteps(prev => {
          const idx = prev.findIndex(s => s.step_seq === event.step!.step_seq)
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = event.step!
            return next
          }
          return [...prev, event.step!].sort((a, b) => a.step_seq - b.step_seq)
        })
      }
    }

    es.onerror = () => es.close()

    return () => { es.close(); esRef.current = null }
  }, [queryId, historical])

  return { steps, done }
}
```

### `src/components/trace/TracePanel.tsx`

Full component with:
- Right-side drawer (65vw), slides in over chat
- Header: "Query Trace" title + LIVE/DONE badge + query pill + History toggle
- Body: two-column — TraceTimeline (left, 320px) + ContextInspector (right, flex)
- Footer: wall-clock timeline bar with parallel lanes
- Uses `useTraceStream(queryId)`

Key layout structure (implement with Tailwind):

```tsx
<div className="fixed inset-y-0 right-0 w-[65vw] bg-[#0d1117] border-l border-[#1e2a3a] flex flex-col z-50 shadow-2xl">
  {/* Header */}
  {/* Body: flex-row */}
  <div className="flex flex-1 overflow-hidden">
    <TraceTimeline steps={steps} onSelect={setSelectedStep} selectedSeq={selectedStep?.step_seq} />
    <ContextInspector steps={steps} selectedStep={selectedStep} />
  </div>
  {/* Footer timeline */}
  <TimelineBar steps={steps} queryStartMs={queryStartMs} />
</div>
```

### `src/components/trace/TraceTimeline.tsx`

Render each step as a row. Parallel group steps render in a nested sub-group with a "⇉ Parallel" label:

```
Step 1  Classify               [DET]  ✓  4ms
Step 2  Compose Bundle         [DET]  ✓  12ms
⇉ Parallel — tool_fetch
  Step 3  vector_search        [VEC]  ✓  49ms
  Step 4  msr_sql              [SQL]  ✓  61ms
  Step 5  manifest_query       [GCS]  ● running
Step 6  Context Assembly       [DET]  …
Step 7  LLM Synthesis          [LLM]  …
Step 8  Audit Validation       [DET]  …
```

Color coding for type badges matches the mockup:
- `DET` → slate
- `LLM` → violet
- `SQL` → sky blue
- `VEC` → green
- `GCS` → red

### `src/components/trace/ContextInspector.tsx`

Reads the `context_assembly` step from `steps`. Shows:
- Total token count (large)
- Colored progress bar (L1 red, L2.5 violet, System slate)
- Three expandable rows: L1 / L2.5 / System

On double-click of L1 or L2.5 row → renders `ChunkDrilldown`.

### `src/components/trace/ChunkDrilldown.tsx`

Scrollable list of chunk items:
```
┌─────────────────────────────────────────┐
│ ▼ L1 — Raw Facts (4 chunks, 4,100 tok) │
│                                         │
│ [fcf469e1] vector_search  · 0.87        │
│ Sun: Aquarius 21°57'35" nakshatra…      │
│                                         │
│ [a3b2c1d0] vector_search  · 0.81        │
│ Moon: Scorpio 18°42'11"…               │
└─────────────────────────────────────────┘
```

### Timeline bar (footer)

Uses `started_at` / `completed_at` timestamps to compute pixel offsets relative to
the earliest `started_at` across all steps. Parallel group steps render as overlapping
bars in adjacent vertical lanes within the same horizontal span.

```
0ms    200ms   400ms   600ms   800ms   1200ms   2400ms
[1][2][──── 3,4,5 parallel ────][6][7: LLM synthesis ──────→]
       vec  msr  gcs
```

Steps within a parallel group are shown as stacked thin bars in the same time window.

### Trigger button in consume page

In `src/app/clients/[chartId]/consume/page.tsx` (or the chat input component),
add an ⚡ button next to the submit button:

```tsx
<button onClick={() => setTracePanelOpen(true)} className="...">
  ⚡ Trace
</button>
{tracePanelOpen && (
  <TracePanel
    queryId={currentQueryId}
    onClose={() => setTracePanelOpen(false)}
  />
)}
```

`currentQueryId` is extracted from the AI SDK stream metadata:
```typescript
// In useChatSession.ts or the consume page, read from onFinish / metadata:
onResponse: (response) => {
  // AI SDK provides metadata via stream annotations
  // queryId arrives in the 'start' part metadata
}
```

Use the `experimental_onChunkReceived` or `onToolCall` hook (check AI SDK version)
to capture `queryId` from the `start` stream part metadata and store in component state.

---

## Stream F — Historical Mode

**File:** `src/app/api/trace/history/route.ts`

```typescript
import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { fetchTraceHistory } from '@/lib/trace/writer'
import { query } from '@/lib/db/client'
import { NextResponse } from 'next/server'

export async function GET() {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  const r = await query<{ is_super_admin: boolean }>(
    'SELECT is_super_admin FROM public.user_profiles WHERE firebase_uid = $1', [user.uid]
  )
  if (!r.rows[0]?.is_super_admin) return NextResponse.json({ error: 'forbidden' }, { status: 403 })

  const history = await fetchTraceHistory(50)
  return NextResponse.json(history)
}
```

**UI:** In TracePanel header, a "History" tab. When active:
- Calls `GET /api/trace/history`
- Renders a list: query text (truncated), relative time, step count, total latency
- Click any row → sets `queryId` + `historical=true` → `useTraceStream` opens
  SSE with `x-trace-mode: historical` header → replays stored steps

---

## Execution Order

```
Stream A (migration)  ─┐
Stream B (types + emitter) ─┤─→ Stream C (instrumentation) ─→ Stream D (SSE) ─→ Stream E (UI) ─→ Stream F (history)
```

Streams A and B can be done in parallel. Stream C requires B. Stream D requires C.
Stream E requires D. Stream F requires E.

## Smoke Test (AC verification)

After all streams complete:

```bash
# 1. Verify migration applied
psql postgresql://amjis_app:...@127.0.0.1:5433/amjis \
  -c "SELECT column_name FROM information_schema.columns WHERE table_name='query_trace_steps'"

# 2. Start dev server
cd platform && npm run dev

# 3. Open browser → /clients/362f9f17.../consume/<new-uuid>
# 4. Click ⚡ TRACE — panel opens
# 5. Submit query: "What is my D1 chart? List Sun, Moon, Ascendant with sign, degree, house."
# 6. Observe: steps light up in real time; parallel group shows 3 overlapping bars
# 7. After done: context inspector shows L1/L2.5/System breakdown summing to ~13k tokens
# 8. Double-click L1 row → chunk text visible
# 9. Click History → past query appears

# 10. Verify DB rows
psql postgresql://amjis_app:...@127.0.0.1:5433/amjis \
  -c "SELECT step_seq, step_name, step_type, status, latency_ms, parallel_group FROM query_trace_steps ORDER BY step_seq"

# 11. Latency check — run 3 queries with TracePanel closed, 3 with open; compare p50
```

## Known Risks

| Risk | Mitigation |
|------|------------|
| AI SDK version may not expose `queryId` cleanly in metadata callbacks | Inspect actual stream part structure; alternative: return `queryId` as a custom HTTP response header on the SSE stream start |
| `renderedPrompt.length / 4` token estimate for System is rough | Add a comment; sufficient for proportional display; exact count requires tiktoken which is not installed |
| Node.js EventEmitter drops events if SSE subscriber not yet connected | Frontend connects to SSE immediately on `queryId` arrival in metadata; Steps 1-2 complete in <20ms, giving subscriber time to connect before tool events arrive |
| `context_assembly` step receives tool results after parallel completion | `Promise.all()` ensures all tools are done before `single_model_strategy.ts` runs; ordering is guaranteed |
