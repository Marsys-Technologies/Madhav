/**
 * Y-S9 — Single-retry wrapper for stream failures.
 *
 * On first 5xx or timeout, routes the retry to the next available stack in
 * RETRY_STACK_ORDER, records a `retry_recovery` trace step, and only surfaces
 * the error if the retry also fails.
 *
 * Hard constraint: fires at most ONCE per query.
 * `is_retry: true` on the request context prevents any further retry.
 *
 * Gated by MARSYS_FLAG_R10_AUTO_RETRY (default false — cost risk, opt-in only).
 * Server-side only. No NEXT_PUBLIC prefix. No deploy.yml entry.
 */
import 'server-only'

import type { ModelStack } from '@/lib/models/registry'
import type { QueryRequest } from './types'
import type { RawAdapterResult } from './raw'
import { streamAdapterRaw } from './raw'
import { getFlag } from '@/lib/config/index'
import { writeTraceStep } from '@/lib/trace/writer'

export const RETRY_TIMEOUT_MS = 30_000

/** Ordered list of fallback stacks for retry routing (marsys excluded — cross-provider). */
const RETRY_STACK_ORDER: ModelStack[] = ['gemini', 'anthropic', 'nim', 'gpt', 'deepseek']

export interface RetryableRequest extends QueryRequest {
  /** Hard constraint: when true, the retry wrapper MUST NOT fire again. */
  is_retry?: boolean
}

/** Picks the next stack in RETRY_STACK_ORDER that differs from the failed stack. */
export function pickNextStack(failedStack: ModelStack): ModelStack | null {
  const candidate = RETRY_STACK_ORDER.find(s => s !== failedStack)
  return candidate ?? null
}

/**
 * Classify an error as retry-eligible.
 * Retries on: 5xx HTTP codes, connection timeout, upstream stream abort.
 * Does NOT retry on: 4xx (client errors), user-initiated stops.
 */
export function isRetryable(err: unknown): boolean {
  if (err instanceof RetryableError) return true
  if (err instanceof Error) {
    const msg = err.message.toLowerCase()
    // 5xx HTTP codes surfaced as error messages
    if (/\b5\d\d\b/.test(err.message)) return true
    // Timeout signals
    if (msg.includes('timeout') || msg.includes('timed out')) return true
    // Upstream abort (not user-initiated — user aborts come via AbortSignal on the request)
    if (msg.includes('upstream') || msg.includes('stream abort') || msg.includes('econnreset')) return true
  }
  return false
}

/** Wrap a known retryable error for explicit signalling from callers. */
export class RetryableError extends Error {
  constructor(
    public readonly statusCode: number,
    message: string,
  ) {
    super(message)
    this.name = 'RetryableError'
  }
}

/**
 * Main entry point. Wraps `streamAdapterRaw` with a single-retry policy.
 *
 * @param req - Request context. When `is_retry: true`, wrapper is bypassed.
 * @param streamFn - Injectable for testing; defaults to `streamAdapterRaw`.
 */
export async function streamWithRetry(
  req: RetryableRequest,
  streamFn: (r: QueryRequest) => RawAdapterResult = streamAdapterRaw,
): Promise<RawAdapterResult> {
  if (true) { // R10_AUTO_RETRY permanently false (WS-0 2026-06-04)
    return streamFn(req)
  }

  // Hard constraint: is_retry guard prevents retry-of-retry
  if (req.is_retry === true) {
    return streamFn(req)
  }

  const originalStack = req.stack ?? 'nim'
  let originalError: unknown

  try {
    return streamFn(req)
  } catch (err) {
    if (!isRetryable(err)) throw err
    originalError = err
  }

  // Find next stack
  const retryStack = pickNextStack(originalStack as ModelStack)
  if (!retryStack) {
    throw new Error(
      `Query failed after retry attempt: no alternate stack available. ` +
        `Original error: ${(originalError as Error).message}`,
    )
  }

  const retryReq: RetryableRequest = { ...req, stack: retryStack ?? undefined, is_retry: true }
  const startedAt = new Date().toISOString()

  try {
    const result = streamFn(retryReq)

    // Record recovery trace step (fire-and-forget)
    if (req.traceId) {
      const recoveredAt = new Date().toISOString()
      writeTraceStep({
        query_id: req.traceId!,
        conversation_id: undefined,
        user_id: req.userId,
        step_seq: 9900,
        step_name: 'retry_recovery',
        step_type: 'retry_recovery' as import('@/lib/trace/types').StepType,
        status: 'done',
        started_at: startedAt,
        completed_at: recoveredAt,
        latency_ms: new Date(recoveredAt).getTime() - new Date(startedAt).getTime(),
        data_summary: {
          tool_count: 0,
          token_estimate: 0,
        },
        payload: {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          original_stack: originalStack as any,
          retry_stack: retryStack,
          original_error_code: (originalError as Error).message,
          recovered_at: recoveredAt,
        } as import('@/lib/trace/types').TracePayload,
      }).catch(() => { /* trace write failure is non-fatal */ })
    }

    return result
  } catch (retryErr) {
    throw new Error(
      `Query failed after retry. Original stack: ${originalStack}, ` +
        `retry stack: ${retryStack}. ` +
        `Retry error: ${(retryErr as Error).message}`,
    )
  }
}
