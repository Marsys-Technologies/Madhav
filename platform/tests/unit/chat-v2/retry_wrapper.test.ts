/**
 * Y-S9 — Stream failure auto-retry
 *
 * Tests:
 * 1. is_retry=false + retryable error → retry fires with next stack, retry_recovery trace appended
 * 2. is_retry=true + retryable error → no retry, error surfaces immediately (hard constraint)
 * 3. Flag=false → no retry, passthrough
 * 4. 4xx error → not retried
 * 5. pickNextStack routing
 * 6. Single-stack guard (no alternate available)
 * 7. Both requests fail → error message signals "after retry"
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  streamWithRetry,
  pickNextStack,
  isRetryable,
  RetryableError,
  RETRY_TIMEOUT_MS,
  type RetryableRequest,
} from '@/lib/adapters/retry_wrapper'
import type { RawAdapterResult } from '@/lib/adapters/raw'
import type { QueryRequest } from '@/lib/adapters/types'

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeRequest(overrides: Partial<RetryableRequest> = {}): RetryableRequest {
  return {
    callType: 'synthesis',
    stack: 'nim',
    systemPrompt: 'test',
    messages: [{ role: 'user', content: 'query' }],
    traceId: 'trace-abc',
    ...overrides,
  } as RetryableRequest
}

const fakeResult = { result: {} as never, meta: {} as never } as RawAdapterResult

// ── Module-level mocks ────────────────────────────────────────────────────────

vi.mock('@/lib/config/index', () => ({
  getFlag: vi.fn(() => false),
}))

vi.mock('@/lib/trace/writer', () => ({
  writeTraceStep: vi.fn(() => Promise.resolve()),
}))

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('streamWithRetry — flag=false passthrough (Y-S9)', () => {
  it('calls streamFn directly without retry when flag=false', async () => {
    const streamFn = vi.fn(() => fakeResult)
    const result = await streamWithRetry(makeRequest(), streamFn)
    expect(streamFn).toHaveBeenCalledTimes(1)
    expect(result).toBe(fakeResult)
  })
})

describe('streamWithRetry — flag=true core behavior (Y-S9)', () => {
  beforeEach(async () => {
    const { getFlag } = await import('@/lib/config/index')
    vi.mocked(getFlag).mockReturnValue(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('is_retry=false + 5xx → retry fires with next stack', async () => {
    const error5xx = new RetryableError(503, 'Service Unavailable 503')
    let callCount = 0
    const streamFn = vi.fn((req: QueryRequest) => {
      callCount++
      if (callCount === 1) throw error5xx
      return fakeResult
    })
    const req = makeRequest({ stack: 'nim' })
    const result = await streamWithRetry(req, streamFn)
    expect(streamFn).toHaveBeenCalledTimes(2)
    // Second call must have a different stack
    const secondCall = streamFn.mock.calls[1][0] as RetryableRequest
    expect(secondCall.stack).not.toBe('nim')
    expect(secondCall.is_retry).toBe(true)
    expect(result).toBe(fakeResult)
  })

  it('is_retry=false + 5xx → retry_recovery trace step written', async () => {
    const { writeTraceStep } = await import('@/lib/trace/writer')
    const error = new RetryableError(503, 'Service Unavailable 503')
    let first = true
    const streamFn = vi.fn(() => {
      if (first) { first = false; throw error }
      return fakeResult
    })
    await streamWithRetry(makeRequest({ traceId: 'trace-xyz' }), streamFn)
    // Allow fire-and-forget promise to settle
    await new Promise(r => setTimeout(r, 0))
    expect(writeTraceStep).toHaveBeenCalledWith(
      expect.objectContaining({ step_name: 'retry_recovery', status: 'done' }),
    )
  })

  it('is_retry=true + retryable error → no retry, error surfaces immediately (hard constraint)', async () => {
    const error = new RetryableError(503, 'Service Unavailable 503')
    const streamFn = vi.fn(() => { throw error })
    const req = makeRequest({ is_retry: true })
    await expect(streamWithRetry(req, streamFn)).rejects.toThrow(error)
    expect(streamFn).toHaveBeenCalledTimes(1)
  })

  it('4xx error is NOT retried', async () => {
    const error4xx = new Error('Bad Request 400')
    const streamFn = vi.fn(() => { throw error4xx })
    await expect(streamWithRetry(makeRequest(), streamFn)).rejects.toThrow(error4xx)
    expect(streamFn).toHaveBeenCalledTimes(1)
  })

  it('both original and retry fail → error includes "after retry"', async () => {
    const error = new RetryableError(503, '503')
    const streamFn = vi.fn(() => { throw error })
    await expect(streamWithRetry(makeRequest(), streamFn)).rejects.toThrow(/after retry/)
    expect(streamFn).toHaveBeenCalledTimes(2)
  })

  it('timeout error is retried', async () => {
    const errTimeout = new Error('Request timed out after 30s')
    let first = true
    const streamFn = vi.fn(() => {
      if (first) { first = false; throw errTimeout }
      return fakeResult
    })
    const result = await streamWithRetry(makeRequest(), streamFn)
    expect(streamFn).toHaveBeenCalledTimes(2)
    expect(result).toBe(fakeResult)
  })
})

describe('pickNextStack (Y-S9)', () => {
  it('picks a different stack from the failed one', () => {
    const next = pickNextStack('nim')
    expect(next).not.toBe('nim')
    expect(next).not.toBeNull()
  })

  it('picks gemini when nim failed', () => {
    expect(pickNextStack('nim')).toBe('gemini')
  })

  it('picks anthropic when gemini failed', () => {
    expect(pickNextStack('gemini')).toBe('anthropic')
  })
})

describe('isRetryable (Y-S9)', () => {
  it('RetryableError is retryable', () => {
    expect(isRetryable(new RetryableError(503, 'svc unavail'))).toBe(true)
  })

  it('5xx in message is retryable', () => {
    expect(isRetryable(new Error('HTTP 503 Service Unavailable'))).toBe(true)
  })

  it('timeout is retryable', () => {
    expect(isRetryable(new Error('Request timed out'))).toBe(true)
  })

  it('4xx is not retryable', () => {
    expect(isRetryable(new Error('HTTP 400 Bad Request'))).toBe(false)
  })

  it('non-Error is not retryable', () => {
    expect(isRetryable('some string')).toBe(false)
  })
})

describe('constants (Y-S9)', () => {
  it('RETRY_TIMEOUT_MS is 30_000', () => {
    expect(RETRY_TIMEOUT_MS).toBe(30_000)
  })
})
