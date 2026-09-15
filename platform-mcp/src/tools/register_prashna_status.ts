/**
 * tools/register_prashna_status.ts — the prashna_status MCP tool (W6 Part 3).
 *
 * Companion to prashna_ask's job-handle-first contract (see register_prashna_ask.ts's
 * file header for the full architectural background on why polling job_id via this
 * tool is both the work-driving request and durable delivery mechanism in this
 * codebase's current stateless-per-request MCP transport).
 *
 * Input: { job_id: string }. Reads the platform-backed durable store. A pending
 * job or a running job whose lease expired is safely claimable by this instance;
 * the database permits exactly one worker to resume it.
 *
 *   - Unknown/expired job_id → a clear error, not a silent empty object. Jobs are
 *     inaccessible after a hard 24-hour logical deadline, so a caller polling a
 *     very old id gets an honest "expired or unknown," never `{}`. Physical
 *     cleanup is opportunistic until the external maintenance schedule is bound.
 *   - pending/running → the CURRENT progress snapshot (message, pct, elapsed_ms) —
 *     never a bare `{status:"pending"}` with no other information.
 *   - complete/failed → the FULL final result/error exactly as prashna_ask's
 *     work-driving status request stored it via `job.complete()`/`job.fail()` — the
 *     complete v3-enveloped reading with its completeness receipt, not a summary
 *     or a pointer telling the caller to look elsewhere.
 *
 * SECURITY: a job id is only a correlation handle, never a bearer grant. Every
 * poll is bound to the authenticated user+key that created it and re-runs chart
 * authorization before any progress, result, or error is disclosed.
 */
import { z } from 'zod'
import { scheduleManagedPrashnaJob } from './register_prashna_ask.js'
import { managedPrashnaJobs } from '../lib/managed_prashna_jobs.js'
import type { Principal } from '../types.js'

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
    job_id: z.string().uuid(),
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

export function registerPrashnaStatusTool(server: PrashnaStatusRegisteringServer, principal: Principal): void {
  server.tool(
    'prashna_status',
    'Poll a durable prashna_ask job. Call this with the job_id returned by prashna_ask. A pending ' +
    'or lease-expired job is resubmitted to the bounded local worker queue; the poll itself ' +
    'returns its meaningful durable progress snapshot without waiting for the engine. If the job is ' +
    '"complete", returns the FULL final v3-enveloped reading (with its completeness receipt) — ' +
    'not a summary or a pointer to look elsewhere. If "failed", returns the error. An unknown or ' +
    'expired job_id (outside the 24-hour logical access window) returns a clear error rather than an empty result.',
    {
      job_id: z.string().uuid().describe('The job_id returned by a prior prashna_ask call.'),
    },
    async (args: unknown) => {
      let parsed: { job_id: string }
      try {
        parsed = PrashnaStatusInputSchema.parse(args)
      } catch (err) {
        const zodMessage = err instanceof z.ZodError ? err.message : String(err)
        return errorOutput(`Invalid prashna_status input: ${zodMessage}`)
      }

      let job
      try {
        job = await managedPrashnaJobs.get(principal, parsed.job_id)
      } catch (error) {
        console.error('[mcp:prashna_status] durable store unavailable', error instanceof Error ? error.message : String(error))
        return errorOutput('MANAGED_JOB_STORE_UNAVAILABLE: status is unknown; retry without starting a duplicate job.', { job_id: parsed.job_id })
      }
      if (!job) {
        return errorOutput(
          `Unknown or expired job_id "${parsed.job_id}" (or not owned by this principal). The id ` +
          'was never issued to this authenticated user/API-key pair or its durable retention window expired.',
          { job_id: parsed.job_id }
        )
      }

      const elapsedMs = Math.max(0, Date.now() - Date.parse(job.created_at))

      if (job.status === 'complete') {
        return dualOutput({
          ok: true,
          job_id: job.job_id,
          status: 'complete',
          elapsed_ms: elapsedMs,
          result: job.result,
        })
      }

      if (job.status === 'failed') {
        return dualOutput({
          ok: true,
          job_id: job.job_id,
          status: 'failed',
          elapsed_ms: elapsedMs,
          error: job.error,
        })
      }

      // Instance-based CPU and the bounded scheduler make this post-response
      // work explicit. The DB claim still selects the single cross-instance winner.
      scheduleManagedPrashnaJob(job.job_id, principal)
      return dualOutput({
        ok: true,
        job_id: job.job_id,
        status: job.status,
        elapsed_ms: elapsedMs,
        progress: job.progress ?? { message: 'prashna_ask: job accepted, awaiting durable worker claim', pct: 0 },
      })
    }
  )
}
