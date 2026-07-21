/**
 * tools/register_prashna_ask.ts — the prashna_ask MCP tool (W6 redesign, Task 7).
 *
 * Job-handle-first contract (OT-2 ruling): a caller invokes prashna_ask, gets an
 * immediate `{job_id, status:'pending'}` back WITHOUT waiting for the engine loop
 * (platform's `/api/mcp/prashna_ask` route — see `lib/prashna_ask_bridge.ts`'s
 * header for why the real engine call cannot live in platform-mcp at all), then
 * the full/partial answer is delivered via an MCP `notifications/progress`
 * message keyed by the caller-supplied `progressToken` (`_meta.progressToken` on
 * the tool-call request, per the MCP spec) once the background call resolves.
 * `job_id` exists for correlation/audit only — a caller must never be REQUIRED to
 * separately poll for the finished answer.
 *
 * ── IMPORTANT ARCHITECTURAL CAVEAT (read before relying on this in production) ─
 * Investigation for this task (reading
 * `node_modules/@modelcontextprotocol/sdk/dist/esm/server/webStandardStreamableHttp.js`
 * in full) found: `StreamableHTTPServerTransport.send()` treats a request's SSE
 * stream as done — and calls `stream.cleanup()`, which closes the underlying HTTP
 * response — the instant `allResponsesReady` for that request's stream (see that
 * file's `send()`, ~line 711-747). For a single tools/call request (the case
 * here), that is IMMEDIATELY after this handler's own returned CallToolResult
 * (the job handle) is sent. `server.ts` also runs a brand-new stateless
 * `McpServer` + `StreamableHTTPServerTransport` PER REQUEST (D10) and explicitly
 * disables the standalone GET /mcp SSE channel (`app.get('/mcp', ...)` → 405) that
 * the SDK would otherwise use for server-initiated, out-of-band notifications.
 * Net effect: a `sendNotification()` call made from the background continuation
 * AFTER this handler has already returned its job-handle result has no live
 * stream to write to for that request ID — `send()` throws
 * `No connection established for request ID: ...` in the SDK's own code path.
 * This file still implements the notification call (wrapped in try/catch so a
 * dead channel never crashes the process) because: (a) it is exactly what the
 * task's contract asks for and the SDK's callback shape supports the API in
 * isolation; (b) some MCP clients/transports MAY keep the request's channel
 * alive longer than this codebase's specific stateless-per-request wiring does,
 * so the call is not simply dead code; (c) the `JobRegistry` entry is ALWAYS
 * updated (`complete`/`fail`) regardless of notification delivery, so a caller
 * that falls back to polling `job_id` (audit/logging path) still sees a
 * consistent final state. Closing this gap for real requires either a
 * session-scoped (not per-request) transport with a working standalone SSE
 * stream, or the SDK's experimental MCP "Tasks" feature (`ToolTaskHandler` /
 * `RequestTaskStore`, present in this SDK version's types but not wired into
 * `server.ts` anywhere) — both are bigger architecture changes outside this
 * task's scope and are flagged for a native/architecture ruling rather than
 * silently worked around here.
 */
import { z } from 'zod'
import type { RequestHandlerExtra } from '@modelcontextprotocol/sdk/shared/protocol.js'
import type { ServerRequest, ServerNotification } from '@modelcontextprotocol/sdk/types.js'
import type { Principal } from '../types.js'
import type { McpProfileName } from '../lib/mcp_profile.js'
import { JobRegistry } from '../lib/job_registry.js'
import { callPrashnaAskEngine, type PrashnaAskEngineResponse } from '../lib/prashna_ask_bridge.js'
import { INTENTS, DOMAINS } from './intent_scope_classifier.js'

type ToolExtra = RequestHandlerExtra<ServerRequest, ServerNotification>

// Structural server shape (same narrowing pattern muhurta_finder.ts uses) — this
// tool only needs `.tool(name, description, schema, handler)`; keeping the
// parameter type narrow (rather than importing the full McpServer class) lets
// tests register against a plain mock object instead of a real transport.
export interface PrashnaAskRegisteringServer {
  tool: (
    name: string,
    description: string,
    schema: Record<string, unknown>,
    handler: (args: unknown, extra: ToolExtra) => Promise<unknown>
  ) => void
}

// ── scope_tuple shape (mirrors intent_scope_classifier.ts's ScopeTuple — the
// one shared scope-tuple vocabulary in this codebase; C-1/DR-8's contract) ────

const ScopeTupleSchema = z
  .object({
    intent: z.enum(INTENTS),
    domains: z.array(z.enum(DOMAINS)),
    width: z.enum(['narrow', 'standard', 'broad']),
    depth: z.enum(['shallow', 'standard', 'deep']),
    horizon: z.enum(['past', 'present', 'near', 'far', 'atemporal']),
    intervention: z.enum(['none', 'remedy', 'muhurta', 'mitigation']),
    entitlement: z.enum(['reference', 'native', 'restricted']),
  })
  .strict()

// ── Full request schema — manually `.parse()`d inside the handler (the raw
// shape handed to server.tool() below is for the SDK's own JSON-schema
// generation; this strict object is what actually enforces the C-1 "no depth
// param" ban, matching muhurta_finder.ts's split-schema pattern). ─────────────

export const PrashnaAskInputSchema = z
  .object({
    chart_id: z.string().uuid(),
    question: z.string().min(1),
    scope_tuple: ScopeTupleSchema.optional(),
    response_format: z.string(),
  })
  .strict()

export type PrashnaAskInput = z.infer<typeof PrashnaAskInputSchema>

function dualOutput(data: Record<string, unknown>): {
  content: [{ type: 'text'; text: string }]
  structuredContent: Record<string, unknown>
} {
  return {
    content: [{ type: 'text', text: JSON.stringify(data) }],
    structuredContent: data,
  }
}

function errorOutput(
  message: string,
  extra?: Record<string, unknown>
): { content: [{ type: 'text'; text: string }]; structuredContent: Record<string, unknown>; isError: true } {
  return { ...dualOutput({ ok: false, error: message, tool: 'prashna_ask', ...extra }), isError: true }
}

// ── Shared job registry (module-scoped singleton — the store must outlive any
// single request's per-request McpServer instance; exported for tests). ──────

export const prashnaAskJobs = new JobRegistry<PrashnaAskEngineResponse>()

async function sendProgress(
  extra: ToolExtra,
  progressToken: string | number,
  progress: number,
  message: string
): Promise<void> {
  try {
    await extra.sendNotification({
      method: 'notifications/progress',
      params: { progressToken, progress, message },
    })
  } catch (err) {
    // See the file header's architectural caveat — a dead per-request stream
    // is an expected failure mode today, not a bug to crash the process over.
    console.warn(
      '[mcp:prashna_ask] progress notification delivery failed (stream likely closed)',
      err instanceof Error ? err.message : String(err)
    )
  }
}

/**
 * Progress-percentage heuristic (W6 Part 2).
 *
 * Uses whichever ceiling the engine's cost-cap tracker is actually closer to
 * tripping — `elapsed_ms / maxWallClockMs` and `tools_dispatched_count /
 * maxCalls` are both partial signals (a request could finish in 2 fast tool
 * calls out of a 10-call ceiling, or spend most of its wall-clock budget on a
 * single slow call), so this takes the MAX of the two ratios rather than
 * either alone — that is the one that best predicts "how close to done/capped
 * is this job," and erring toward the larger of the two avoids a progress bar
 * that appears to stall when the OTHER dimension is actually the one making
 * progress. Clamped to [0, 99] — 100 is reserved for the terminal update so a
 * caller can distinguish "nearly done" from "actually done."
 */
function estimateProgressPct(progress: import('../lib/prashna_ask_bridge.js').PrashnaAskProgressEvent): number {
  const wallClockRatio = progress.elapsed_ms / Math.max(1, progress.cap_ceiling.maxWallClockMs)
  const callCountRatio = progress.tools_dispatched_count / Math.max(1, progress.cap_ceiling.maxCalls)
  const pct = Math.round(Math.max(wallClockRatio, callCountRatio) * 100)
  return Math.min(99, Math.max(0, pct))
}

/**
 * Run the engine call in the background and deliver the outcome via progress
 * notification + JobRegistry update. Never throws — all failure paths resolve.
 *
 * W6 Part 2/3: `JobRegistry` is the AUTHORITATIVE, always-updated progress
 * source `prashna_status` reads from — the MCP `notifications/progress` send
 * below is best-effort/defensive only (see the file header's architectural
 * caveat on why it is frequently undeliverable in this codebase's current
 * stateless-per-request MCP transport).
 */
async function runInBackground(
  jobId: string,
  chartId: string,
  question: string,
  principal: Principal,
  extra: ToolExtra,
  progressToken: string | number | undefined
): Promise<void> {
  if (progressToken !== undefined) {
    await sendProgress(extra, progressToken, 0, 'prashna_ask: engine call started')
  }
  prashnaAskJobs.updateProgress(jobId, { message: 'prashna_ask: engine call started', pct: 0 })

  let result: PrashnaAskEngineResponse
  try {
    result = await callPrashnaAskEngine(
      {
        chartId,
        question,
        principal: { userUid: principal.user_uid, keyId: principal.key_id },
      },
      (progress) => {
        const elapsedSec = (progress.elapsed_ms / 1000).toFixed(1)
        prashnaAskJobs.updateProgress(jobId, {
          message:
            `${progress.tools_dispatched_count}/~${progress.cap_ceiling.maxCalls} tool calls made, ` +
            `${elapsedSec}s elapsed`,
          pct: estimateProgressPct(progress),
        })
      }
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    prashnaAskJobs.fail(jobId, message)
    if (progressToken !== undefined) {
      await sendProgress(extra, progressToken, 100, `prashna_ask: failed — ${message}`)
    }
    return
  }

  if (result.ok === false) {
    prashnaAskJobs.fail(jobId, result.error.message)
  } else {
    prashnaAskJobs.complete(jobId, result)
  }

  // Terminal notification carries the FULL/PARTIAL result — not just a
  // "go look it up" pointer (binding requirement: a caller must never be
  // required to separately poll job_id for the finished answer).
  if (progressToken !== undefined) {
    await extra
      .sendNotification({
        method: 'notifications/progress',
        params: {
          progressToken,
          progress: 100,
          message: JSON.stringify({ job_id: jobId, status: prashnaAskJobs.get(jobId)?.status, result }),
        },
      })
      .catch((err: unknown) => {
        console.warn(
          '[mcp:prashna_ask] terminal progress notification delivery failed (stream likely closed)',
          err instanceof Error ? err.message : String(err)
        )
      })
  }
}

export function registerPrashnaAskTool(
  server: PrashnaAskRegisteringServer,
  principal: Principal,
  mcpProfile: McpProfileName
): void {
  server.tool(
    'prashna_ask',
    'Full-loop Vidhi Engine question-answering: plans a tool-dispatch sequence for a natural-' +
    'language chart question, runs it under cost caps + NO-LEAKAGE enforcement, and returns an ' +
    'IMMEDIATE job handle ({job_id, status:"pending"}) — it does NOT block until the answer is ' +
    'ready. Two-step pattern: (1) call prashna_ask, get back {job_id}; (2) call prashna_status ' +
    'with that job_id to check progress (a meaningful message + pct estimate while the job is ' +
    'still running) or retrieve the final result once status is "complete"/"failed" — poll ' +
    'prashna_status again after a short delay if the job is still "pending"/"running". A best-' +
    'effort MCP notifications/progress message MAY also arrive (pass a progressToken in the ' +
    'tool-call request\'s _meta) but is NOT reliably delivered in this deployment — prashna_status ' +
    'is the durable way to get progress or the final answer. NOT for lightweight lookups — no ' +
    '`depth` param (C-1 signature); use a retrieval-tier tool for a pinpointed factual lookup ' +
    'instead. Requires the "full" or "compact" MCP surface profile — rejected for "consult".',
    {
      chart_id: z.string().uuid().describe('Chart UUID to answer the question against.'),
      question: z.string().min(1).describe('Natural-language question about the chart.'),
      scope_tuple: z
        .object({
          intent: z.enum(INTENTS),
          domains: z.array(z.enum(DOMAINS)),
          width: z.enum(['narrow', 'standard', 'broad']),
          depth: z.enum(['shallow', 'standard', 'deep']),
          horizon: z.enum(['past', 'present', 'near', 'far', 'atemporal']),
          intervention: z.enum(['none', 'remedy', 'muhurta', 'mitigation']),
          entitlement: z.enum(['reference', 'native', 'restricted']),
        })
        .optional()
        .describe('Optional pre-classified scope tuple (see intent_scope_classifier.ts). Omit to let the planner classify.'),
      response_format: z.string().describe('Requested response format/verbosity hint for the synthesis layer.'),
    },
    async (args: unknown, extra: ToolExtra) => {
      let parsed: PrashnaAskInput
      try {
        parsed = PrashnaAskInputSchema.parse(args)
      } catch (err) {
        const zodMessage = err instanceof z.ZodError ? err.message : String(err)
        return errorOutput(
          'Invalid prashna_ask input. prashna_ask has no `depth` parameter (C-1 signature) — ' +
          'use scope_tuple.depth if depth classification is needed, or a retrieval-tier tool for ' +
          `a pinpointed lookup. Validation error: ${zodMessage}`
        )
      }

      // Entitlement gate: MCP surface profile, NOT Principal.role (that only sizes
      // cost caps on the platform side — see mcp_profile.ts's header). 'consult' is
      // the safe-default restricted tool-surface profile and may not invoke a
      // full-loop engine call; 'full' and 'compact' may (mcp_profile.ts's own doc
      // comments: 'compact' is a ranked ≤20-tool umbrella surface for a scoped OAuth
      // grant, not a lookup-only tier — only 'consult' is the lookup-only safe default).
      if (mcpProfile === 'consult') {
        return errorOutput(
          'prashna_ask requires the "full" or "compact" MCP surface profile. The "consult" profile ' +
          'is the restricted, lookup-only safe default and cannot invoke a full-loop engine call. ' +
          'Request an OAuth grant carrying mcp:profile:full or mcp:profile:compact.'
        )
      }

      const job = prashnaAskJobs.create({ chartId: parsed.chart_id })
      const progressToken = extra._meta?.progressToken

      // Fire-and-forget: do NOT await — the job-handle-first contract (OT-2)
      // requires this handler to resolve before the engine call does. Report the
      // literal 'pending' status the job was just created with, NOT `job.status`
      // read after the fire-and-forget call — `runInBackground` runs synchronously
      // up to its first await, and (when no progressToken is supplied, skipping
      // the notification await) its first synchronous action is a `JobRegistry
      // .updateProgress()` call that flips status to 'running' before this line
      // would otherwise read it, racing the "immediate job handle" contract.
      void runInBackground(job.id, parsed.chart_id, parsed.question, principal, extra, progressToken)

      return dualOutput({ job_id: job.id, status: 'pending', chart_id: parsed.chart_id })
    }
  )
}
