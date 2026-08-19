/**
 * both_doors_refusal.test.ts — NCD-8 "both doors, designed failure state, not a 500".
 *
 * The two doors PPR-25 names are the WEB door (`/api/pariprashna`, gated by
 * `safety_gate.admitWithinLimits`) and the MCP door (`/api/mcp/prashna_ask`).
 * This file exercises the WEB door's real gate function end-to-end — it builds a
 * genuine `Response` — and asserts the wire contract a client actually branches
 * on: HTTP 429, a stable `LIMIT_*` code, and a message naming the real ceiling.
 * The MCP door's own refusal is asserted in that route's suite
 * (`src/app/api/mcp/prashna_ask/__tests__/route.test.ts`), against the real POST.
 *
 * The point of the status assertion is negative as much as positive: a ceiling
 * refusal must NEVER be a 5xx. A 500 tells a caller "we are broken, retry blindly";
 * 429 + LIMIT_SPEND_CEILING_EXCEEDED tells it the truth.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn() }))
vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(),
  insertConversationWithId: vi.fn(),
}))

import { configService } from '@/lib/config/index'
import { getModelMeta } from '@/lib/models/registry'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'
import { admitWithinLimits } from '@/lib/pariprashna/pipeline/safety_gate'
import type { TurnParams } from '@/lib/pariprashna/pipeline/stage_context'

function params(modelId: string): TurnParams {
  const modelMeta = getModelMeta(modelId)!
  return {
    selectedStack: 'gemini',
    modelId,
    modelMeta,
    readingDepth: 'auto',
    deepDive: false,
    lengthTier: 'standard',
    lelContextEnabled: true,
    style: 'acharya',
  }
}

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [{ total: '0' }] })
  __resetRpmCountersForTest()
})

afterEach(() => {
  configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', false)
})

describe('web door — flag OFF (the shipped default)', () => {
  it('admits a turn that would otherwise breach the per-turn ceiling', async () => {
    const result = await admitWithinLimits({
      user: { uid: 'u1' },
      params: params('claude-opus-4-7'),
    })
    expect(result.admitted).toBe(true)
  })
})

describe('web door — $2/turn ceiling exceeded', () => {
  beforeEach(() => configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true))

  it('answers 429 with LIMIT_SPEND_CEILING_EXCEEDED — never a 500', async () => {
    const result = await admitWithinLimits({
      user: { uid: 'u1' },
      params: params('claude-opus-4-7'), // projects to $6.72
    })
    expect(result.admitted).toBe(false)
    if (result.admitted) throw new Error('unreachable')

    const response = result.response
    expect(response.status).toBe(429)
    expect(response.status).not.toBe(500)

    const body = await response.json()
    expect(body.error.code).toBe('LIMIT_SPEND_CEILING_EXCEEDED')
    expect(body.error.retry).toBe(true)
    expect(body.error.detail).toContain('$2.00')
    expect(body.error.detail).toContain('claude-opus-4-7')
  })
})

describe('web door — $40/day ceiling exceeded', () => {
  beforeEach(() => configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true))

  it('answers 429 with LIMIT_SPEND_CEILING_EXCEEDED and names the reset', async () => {
    queryMock.mockResolvedValue({ rows: [{ total: '40.00' }] })
    const result = await admitWithinLimits({
      user: { uid: 'u1' },
      params: params('gemini-2.5-flash'),
    })
    expect(result.admitted).toBe(false)
    if (result.admitted) throw new Error('unreachable')

    expect(result.response.status).toBe(429)
    const body = await result.response.json()
    expect(body.error.code).toBe('LIMIT_SPEND_CEILING_EXCEEDED')
    expect(body.error.detail).toContain('$40.00')
    expect(body.error.detail).toContain('00:00 UTC')
  })

  it('admits the same turn when the day still has room', async () => {
    queryMock.mockResolvedValue({ rows: [{ total: '1.00' }] })
    const result = await admitWithinLimits({
      user: { uid: 'u1' },
      params: params('gemini-2.5-flash'),
    })
    expect(result.admitted).toBe(true)
  })
})

describe('web door — rate limit exceeded', () => {
  beforeEach(() => configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true))

  it('answers 429 with LIMIT_RATE_LIMIT_EXCEEDED and a Retry-After header', async () => {
    let result = await admitWithinLimits({ user: { uid: 'rl' }, params: params('gemini-2.5-flash') })
    for (let i = 1; i < 61; i++) {
      result = await admitWithinLimits({ user: { uid: 'rl' }, params: params('gemini-2.5-flash') })
    }

    expect(result.admitted).toBe(false)
    if (result.admitted) throw new Error('unreachable')

    expect(result.response.status).toBe(429)
    expect(result.response.headers.get('retry-after')).toBeTruthy()
    const body = await result.response.json()
    expect(body.error.code).toBe('LIMIT_RATE_LIMIT_EXCEEDED')
    expect(body.error.retry).toBe(true)
  })
})
