import { describe, expect, it } from 'vitest'
import { requestWithValidationThrottle } from '../../../../scripts/ai-console/validation_scheduler'

function response(status: number, retryAfter?: string) {
  const headers: Record<string, string> = {}
  if (retryAfter !== undefined) headers['retry-after'] = retryAfter
  return {
    status: () => status,
    headers: () => headers,
    dispose: async () => undefined,
  }
}

describe('owner acceptance validation throttle scheduler', () => {
  it('honors Retry-After and retries without a real wait', async () => {
    const values = [response(429, '2'), response(200)]
    const waits: number[] = []
    const result = await requestWithValidationThrottle(async () => values.shift()!, {
      now: () => Date.parse('2026-09-28T00:00:00.000Z'),
      sleep: async ms => { waits.push(ms) },
    })
    expect(result.status()).toBe(200)
    expect(waits).toEqual([2_000])
  })

  it('honors an HTTP-date Retry-After using the injected clock', async () => {
    const values = [response(429, 'Sun, 28 Sep 2026 00:00:03 GMT'), response(200)]
    const waits: number[] = []
    await requestWithValidationThrottle(async () => values.shift()!, {
      now: () => Date.parse('2026-09-28T00:00:00.000Z'), sleep: async ms => { waits.push(ms) },
    })
    expect(waits).toEqual([3_000])
  })

  it('fails closed on missing or excessive retry guidance', async () => {
    await expect(requestWithValidationThrottle(async () => response(429), {
      now: () => 0, sleep: async () => undefined,
    })).rejects.toThrow('AIC_E2E_VALIDATION_RETRY_INVALID')
    await expect(requestWithValidationThrottle(async () => response(429, '131'), {
      now: () => 0, sleep: async () => undefined,
    })).rejects.toThrow('AIC_E2E_VALIDATION_RETRY_EXCEEDED')
  })
})
