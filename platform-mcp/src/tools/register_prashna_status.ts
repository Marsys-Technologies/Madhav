/**
 * tools/register_prashna_status.ts — the prashna_status MCP tool (W6 Part 3).
 *
 * Companion to prashna_ask's job-handle-first contract (see register_prashna_ask.ts's
 * file header for the full architectural background on why polling job_id via this
 * tool — not MCP `notifications/progress` — is the durable delivery mechanism in
 * this codebase's current stateless-per-request MCP transport).
 *
 * Input: { job_id: string }. Looks up the job in the SAME `JobRegistry` instance
 * prashna_ask writes to (`prashnaAskJobs`, exported from register_prashna_ask.ts —
 * a module-scoped singleton, not a new registry).
 *
 *   - Unknown/expired job_id → a clear error, not a silent empty object. Jobs are
 *     TTL-swept (`JobRegistry.sweepExpired()`), so a caller polling a very old id
 *     gets an honest "expired or unknown," never `{}`.
 *   - pending/running → the CURRENT progress snapshot (message, pct, elapsed_ms) —
 *     never a bare `{status:"pending"}` with no other information.
 *   - complete/failed → the FULL final result/error exactly as prashna_ask's
 *     background execution stored it via `job.complete()`/`job.fail()` — the
 *     complete v3-enveloped reading with its completeness receipt, not a summary
 *     or a pointer telling the caller to look elsewhere.
 *
 * SECURITY NOTE (inherited from JobRegistry.get()'s own doc comment): the registry
 * does not itself check chart entitlement on lookup — any caller holding a job_id
 * can read that job's result regardless of which chart it belongs to. This mirrors
 * prashna_ask's own model: the per-chart entitlement check already happened once,
 * server-side, when the engine call that produced this job ran (authorizeChartAccess
 * in platform/.../prashna_ask/route.ts) — job_id is a correlation handle for that
 * already-authorized call's outcome, not a fresh capability grant. A caller who
 * never had chart access could not have produced a job_id for that chart's
 * question in the first place (job_id is not guessable/enumerable — crypto.randomUUID()).
 */
import { z } from 'zod'
import { prashnaAskJobs } from './register_prashna_ask.js'

export interface PrashnaStatusRegisteringServer {
  tool: (
    name: string,
    description: string,
    schema: Record<string, unknown>,
    handler: (args: unknown) => Promise<unknown>
  ) => void
}

const PrashnaStatusInputSchema = z
  .object({
    job_id: z.string().min(1),
  })
  .strict()

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
  return { ...dualOutput({ ok: false, error: message, tool: 'prashna_status', ...extra }), isError: true }
}

export function registerPrashnaStatusTool(server: PrashnaStatusRegisteringServer): void {
  server.tool(
    'prashna_status',
    'Poll the status/result of a prashna_ask background job. Call this with the job_id ' +
    'returned by prashna_ask. If the job is still "pending"/"running", returns a MEANINGFUL ' +
    'progress snapshot (a human-readable message, a 0-99 pct estimate, elapsed_ms) — never a ' +
    'bare "pending" with no other information; poll again after a short delay. If the job is ' +
    '"complete", returns the FULL final v3-enveloped reading (with its completeness receipt) — ' +
    'not a summary or a pointer to look elsewhere. If "failed", returns the error. An unknown or ' +
    'expired job_id (jobs are TTL-swept) returns a clear error rather than an empty result.',
    {
      job_id: z.string().min(1).describe('The job_id returned by a prior prashna_ask call.'),
    },
    async (args: unknown) => {
      let parsed: { job_id: string }
      try {
        parsed = PrashnaStatusInputSchema.parse(args)
      } catch (err) {
        const zodMessage = err instanceof z.ZodError ? err.message : String(err)
        return errorOutput(`Invalid prashna_status input: ${zodMessage}`)
      }

      const job = prashnaAskJobs.get(parsed.job_id)
      if (!job) {
        return errorOutput(
          `Unknown or expired job_id "${parsed.job_id}". Jobs are held in memory only and are ` +
          'evicted after a TTL — this id was either never issued by prashna_ask, belongs to a ' +
          'different server instance, or has expired. Call prashna_ask again to start a new job.',
          { job_id: parsed.job_id }
        )
      }

      const elapsedMs = Date.now() - job.createdAt

      if (job.status === 'complete') {
        return dualOutput({
          ok: true,
          job_id: job.id,
          status: 'complete',
          elapsed_ms: elapsedMs,
          result: job.result,
        })
      }

      if (job.status === 'failed') {
        return dualOutput({
          ok: true,
          job_id: job.id,
          status: 'failed',
          elapsed_ms: elapsedMs,
          error: job.error,
        })
      }

      // pending/running — return the current progress snapshot, never a bare
      // status with no other information.
      return dualOutput({
        ok: true,
        job_id: job.id,
        status: job.status,
        elapsed_ms: elapsedMs,
        progress: job.progress ?? { message: 'prashna_ask: job accepted, engine call not yet started', pct: 0 },
      })
    }
  )
}
