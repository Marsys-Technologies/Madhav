/**
 * Durable job-handle front door for the Prashna engine.
 *
 * `prashna_ask` performs a durable, idempotent create and returns the
 * caller-generated UUID, then submits the job to a bounded in-process worker
 * queue. The deployment contract explicitly enables instance-based CPU; the
 * queue caps local engine concurrency and database leases recover instance
 * death. `prashna_status` remains a true poll and opportunistically resubmits a
 * pending or lease-expired job without blocking for the engine result.
 */
import { randomUUID } from 'node:crypto'
import { z } from 'zod'
import type { RequestHandlerExtra } from '@modelcontextprotocol/sdk/shared/protocol.js'
import type { ServerRequest, ServerNotification } from '@modelcontextprotocol/sdk/types.js'
import type { Principal } from '../types.js'
import type { McpProfileName } from '../lib/mcp_profile.js'
import { managedPrashnaJobs } from '../lib/managed_prashna_jobs.js'
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
    question: z.string().trim().min(1).max(4000),
    scope_tuple: ScopeTupleSchema.optional(),
    response_format: z.enum(['digest', 'summary', 'standard', 'narrative', 'full']),
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

export { managedPrashnaJobs as prashnaAskJobs }

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
 * Atomically claim or recover a durable job, then run the engine and commit its
 * outcome. Concurrent instances may call this safely; only the lease winner runs.
 * The MCP `notifications/progress` send
 * below is best-effort/defensive only (see the file header's architectural
 * caveat on why it is frequently undeliverable in this codebase's current
 * stateless-per-request MCP transport).
 */
export async function resumeManagedPrashnaJob(
  jobId: string,
  principal: Principal,
  extra?: ToolExtra,
  progressToken?: string | number,
): Promise<void> {
  const workerId = randomUUID()
  const claimed = await managedPrashnaJobs.claim(principal, jobId, workerId)
  if (!claimed || claimed.disposition !== 'acquired') return
  const jobRequest = claimed.job.request
  if (!jobRequest) {
    await managedPrashnaJobs.fail(principal, jobId, workerId, 'MANAGED_JOB_REQUEST_MISSING')
    return
  }

  if (progressToken !== undefined && extra) {
    await sendProgress(extra, progressToken, 0, 'prashna_ask: engine call started')
  }
  await managedPrashnaJobs.updateProgress(
    principal, jobId, workerId, { message: 'prashna_ask: engine call started', pct: 0 },
  ).catch((error) => {
    console.warn('[mcp:prashna_ask] initial durable progress update failed', error instanceof Error ? error.message : String(error))
  })

  let result: PrashnaAskEngineResponse
  try {
    result = await callPrashnaAskEngine(
      {
        chartId: claimed.job.chart_id,
        question: jobRequest.question,
        principal: { userUid: principal.user_uid, keyId: principal.key_id },
        responseFormat: jobRequest.response_format,
        scopeTuple: jobRequest.scope_tuple,
      },
      (progress) => {
        const elapsedSec = (progress.elapsed_ms / 1000).toFixed(1)
        void managedPrashnaJobs.updateProgress(principal, jobId, workerId, {
          message:
            `${progress.tools_dispatched_count}/~${progress.cap_ceiling.maxCalls} tool calls made, ` +
            `${elapsedSec}s elapsed`,
          pct: estimateProgressPct(progress),
        }).catch((error) => {
          console.warn('[mcp:prashna_ask] durable progress update failed', error instanceof Error ? error.message : String(error))
        })
      }
    )
  } catch {
    await retainRetryableFailure(jobId, principal, workerId)
    return
  }

  let terminalCommitted = false
  let deliveredResult: PrashnaAskEngineResponse = result
  if (result.ok === false) {
    if (result.error.retryable === true) {
      await retainRetryableFailure(jobId, principal, workerId)
      return
    }
    await managedPrashnaJobs.fail(principal, jobId, workerId, result.error.message).then(() => {
      terminalCommitted = true
    }).catch((error) => {
      console.warn('[mcp:prashna_ask] durable failure commit failed', error instanceof Error ? error.message : String(error))
    })
  } else {
    deliveredResult = {
      ...result,
      persistence: {
        status: 'managed_job',
        job_id: jobId,
        detail: 'Full managed-MCP terminal result retained in the principal-bound durable job store.',
      },
    }
    await managedPrashnaJobs.complete(principal, jobId, workerId, deliveredResult).then(() => {
      terminalCommitted = true
    }).catch(async (error) => {
      const message = error instanceof Error ? error.message : String(error)
      if (message === 'MANAGED_JOB_RESULT_TOO_LARGE') {
        // A successful engine response that exceeds the durable contract must
        // become an explicit terminal storage failure. Leaving the lease live
        // would rerun an already-successful (and potentially expensive) engine
        // call until retry exhaustion while never making the result retrievable.
        await managedPrashnaJobs.fail(
          principal,
          jobId,
          workerId,
          'MANAGED_JOB_RESULT_TOO_LARGE: engine succeeded but its terminal envelope exceeded the 2 MiB durable-result ceiling',
        ).then(() => {
          terminalCommitted = true
          deliveredResult = {
            ok: false,
            trace_id: result.trace_id,
            error: {
              class: 'storage_contract',
              message: 'MANAGED_JOB_RESULT_TOO_LARGE',
              remediation: 'Narrow the question or use a smaller response format before starting a new job.',
            },
          }
        }).catch((failError) => {
          console.warn('[mcp:prashna_ask] durable oversized-result failure commit failed', failError instanceof Error ? failError.message : String(failError))
        })
        return
      }
      console.warn('[mcp:prashna_ask] durable completion commit failed', message)
    })
  }

  // Terminal notification carries the FULL/PARTIAL result — not just a
  // "go look it up" pointer (binding requirement: a caller must never be
  // required to separately poll job_id for the finished answer).
  if (terminalCommitted && progressToken !== undefined && extra) {
    await extra
      .sendNotification({
        method: 'notifications/progress',
        params: {
          progressToken,
          progress: 100,
          message: JSON.stringify({ job_id: jobId, status: deliveredResult.ok === false ? 'failed' : 'complete', result: deliveredResult }),
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

async function retainRetryableFailure(
  jobId: string,
  principal: Principal,
  workerId: string,
): Promise<void> {
  try {
    await managedPrashnaJobs.updateProgress(principal, jobId, workerId, {
      message: 'prashna_ask: ambiguous transport failure; retry waits for lease expiry',
      pct: 99,
    })
  } catch (error) {
    // Leave the existing lease intact if even the progress update fails. A
    // later status poll may recover only after that lease expires, preventing
    // overlap with a platform request whose execution outcome is ambiguous.
    console.warn('[mcp:prashna_ask] durable transient state update failed', error instanceof Error ? error.message : String(error))
  }
}

const MAX_ACTIVE_MANAGED_PRASHNA_WORKERS = 2
const MAX_QUEUED_MANAGED_PRASHNA_JOBS = 32
type ScheduledJob = {
  jobId: string
  principal: Principal
  extra?: ToolExtra
  progressToken?: string | number
  generation: number
}
const managedJobQueue: ScheduledJob[] = []
const scheduledManagedJobIds = new Set<string>()
let activeManagedPrashnaWorkers = 0
let managedPrashnaSchedulerGeneration = 0

function drainManagedPrashnaJobQueue(): void {
  while (activeManagedPrashnaWorkers < MAX_ACTIVE_MANAGED_PRASHNA_WORKERS && managedJobQueue.length > 0) {
    const job = managedJobQueue.shift()!
    activeManagedPrashnaWorkers += 1
    void resumeManagedPrashnaJob(job.jobId, job.principal, job.extra, job.progressToken)
      .catch((error) => {
        console.warn('[mcp:prashna_ask] scheduled recovery failed', error instanceof Error ? error.message : String(error))
      })
      .finally(() => {
        if (job.generation !== managedPrashnaSchedulerGeneration) return
        activeManagedPrashnaWorkers -= 1
        scheduledManagedJobIds.delete(job.jobId)
        drainManagedPrashnaJobQueue()
      })
  }
}

export function scheduleManagedPrashnaJob(
  jobId: string,
  principal: Principal,
  extra?: ToolExtra,
  progressToken?: string | number,
): 'scheduled' | 'already_scheduled' | 'queue_full' {
  if (scheduledManagedJobIds.has(jobId)) return 'already_scheduled'
  if (managedJobQueue.length >= MAX_QUEUED_MANAGED_PRASHNA_JOBS) return 'queue_full'
  scheduledManagedJobIds.add(jobId)
  managedJobQueue.push({
    jobId, principal, extra, progressToken, generation: managedPrashnaSchedulerGeneration,
  })
  drainManagedPrashnaJobQueue()
  return 'scheduled'
}

export function __resetManagedPrashnaSchedulerForTests(): void {
  managedPrashnaSchedulerGeneration += 1
  managedJobQueue.splice(0)
  scheduledManagedJobIds.clear()
  activeManagedPrashnaWorkers = 0
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
    'IMMEDIATE durable job handle ({job_id, status:"pending"}) before bounded worker execution. ' +
    'Two-step pattern: (1) call prashna_ask, get back {job_id}; (2) poll prashna_status with that ' +
    'job_id for meaningful durable progress or the full terminal result. A status poll also ' +
    'resubmits pending or lease-expired work for cross-instance recovery. ' +
    'NOT for lightweight lookups — no ' +
    '`depth` param (C-1 signature); use a retrieval-tier tool for a pinpointed factual lookup ' +
    'instead. Requires the "full" or "compact" MCP surface profile — rejected for "consult".',
    {
      chart_id: z.string().uuid().describe('Chart UUID to answer the question against.'),
      question: z.string().trim().min(1).max(4000).describe('Natural-language question about the chart (1–4000 characters).'),
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
      response_format: z.enum(['digest', 'summary', 'standard', 'narrative', 'full'])
        .describe('Requested response format for the synthesis layer.'),
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

      const jobId = randomUUID()
      let job
      try {
        job = await managedPrashnaJobs.create(principal, {
          job_id: jobId,
          chart_id: parsed.chart_id,
          request: {
            question: parsed.question,
            response_format: parsed.response_format,
            scope_tuple: parsed.scope_tuple,
          },
        })
      } catch (error) {
        console.error('[mcp:prashna_ask] durable job creation failed', error instanceof Error ? error.message : String(error))
        return errorOutput(
          'MANAGED_JOB_STORE_UNAVAILABLE: creation outcome is unknown; use prashna_status with the returned job_id before retrying',
          { job_id: jobId },
        )
      }
      scheduleManagedPrashnaJob(job.job_id, principal, extra, extra._meta?.progressToken)
      return dualOutput({ job_id: job.job_id, status: 'pending', chart_id: parsed.chart_id })
    }
  )
}
