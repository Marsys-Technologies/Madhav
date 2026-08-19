/**
 * enforce_turn_limits.test.ts — the shared pre-dispatch gate (NCD-8, lane G1-D).
 *
 * Proves the three properties the lane is accountable for:
 *   1. FLAG-OFF BY DEFAULT — nothing is enforced, and nothing is even computed,
 *      until PARIPRASHNA_LIMITS_ENABLED is flipped.
 *   2. ONE RATE-LIMIT IMPLEMENTATION — the gate drives the same rolling window
 *      `lib/mcp/rate_limiter.ts` uses (`rate_limiter_core.checkRpm`).
 *   3. DESIGNED FAILURE STATE — a refusal carries a stable code and HTTP 429.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { configService } from '@/lib/config/index'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'
import {
  RATE_LIMIT_ERROR_CODE,
  SPEND_CEILING_ERROR_CODE,
  enforceTurnLimits,
  limitsEnabled,
  rateLimitKey,
} from '../index'

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [{ total: '0' }] })
  __resetRpmCountersForTest()
})

afterEach(() => {
  configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', false)
})

describe('flag-OFF by default', () => {
  it('PARIPRASHNA_LIMITS_ENABLED defaults to false', () => {
    expect(limitsEnabled()).toBe(false)
  })

  it('does no DB or ceiling work while the flag is off, even for a turn that would be refused', async () => {
    // claude-opus-4-7 projects to $6.72 — it WOULD be refused if the gate were armed.
    const decision = await enforceTurnLimits({
      userId: 'u1',
      channel: 'web',
      modelId: 'claude-opus-4-7',
    })
    expect(decision.allowed).toBe(true)
    expect(decision.allowed && decision.enforced).toBe(false)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('refuses the same turn once the flag is flipped on — proving the flag is the only difference', async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)
    const decision = await enforceTurnLimits({
      userId: 'u1',
      channel: 'web',
      modelId: 'claude-opus-4-7',
    })
    expect(decision.allowed).toBe(false)
  })
})

describe('an allowed turn is distinguishable from an unchecked turn', () => {
  it('reports enforced:true when the gates actually ran', async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)
    const decision = await enforceTurnLimits({
      userId: 'u1',
      channel: 'web',
      modelId: 'gemini-2.5-flash',
    })
    expect(decision.allowed).toBe(true)
    expect(decision.allowed && decision.enforced).toBe(true)
  })
})

describe('rate limiting reuses the one shared rolling window', () => {
  it('namespaces the window per channel and principal', () => {
    expect(rateLimitKey('web', 'uid-1')).toBe('web:user:uid-1')
    expect(rateLimitKey('mcp', 'key-1')).toBe('mcp:user:key-1')
  })

  it('refuses with LIMIT_RATE_LIMIT_EXCEEDED and 429 once the window is full', async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)

    // MCP_RPM_LIMIT defaults to 60. Drive the window to its limit, then one more.
    let last = await enforceTurnLimits({ userId: 'flood', channel: 'web', modelId: 'gemini-2.5-flash' })
    for (let i = 1; i < 61; i++) {
      last = await enforceTurnLimits({ userId: 'flood', channel: 'web', modelId: 'gemini-2.5-flash' })
    }

    expect(last.allowed).toBe(false)
    if (last.allowed) throw new Error('unreachable')
    expect(last.code).toBe(RATE_LIMIT_ERROR_CODE)
    expect(last.status).toBe(429)
    expect(last.retry_after_seconds).toBeGreaterThan(0)
    expect(last.message).toMatch(/Too many requests/)
  })

  it("a flooded web caller does not consume the MCP door's window", async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)
    for (let i = 0; i < 61; i++) {
      await enforceTurnLimits({ userId: 'shared-uid', channel: 'web', modelId: 'gemini-2.5-flash' })
    }
    const mcp = await enforceTurnLimits({
      userId: 'shared-uid',
      channel: 'mcp',
      modelId: 'gemini-2.5-flash',
    })
    expect(mcp.allowed).toBe(true)
  })

  it('keys the MCP door on the credential id when one is supplied', async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)
    for (let i = 0; i < 61; i++) {
      await enforceTurnLimits({
        userId: 'same-user',
        channel: 'mcp',
        modelId: 'gemini-2.5-flash',
        rateLimitPrincipalId: 'key-A',
      })
    }
    // Same user, different credential → its own window, still open.
    const other = await enforceTurnLimits({
      userId: 'same-user',
      channel: 'mcp',
      modelId: 'gemini-2.5-flash',
      rateLimitPrincipalId: 'key-B',
    })
    expect(other.allowed).toBe(true)
  })
})

describe('designed failure state — 429 with a branchable code, never a 500', () => {
  it('per-turn ceiling breach', async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)
    const decision = await enforceTurnLimits({
      userId: 'u1',
      channel: 'web',
      modelId: 'claude-opus-4-7',
    })
    expect(decision.allowed).toBe(false)
    if (decision.allowed) throw new Error('unreachable')
    expect(decision.code).toBe(SPEND_CEILING_ERROR_CODE)
    expect(decision.code).toBe('LIMIT_SPEND_CEILING_EXCEEDED')
    expect(decision.status).toBe(429)
    expect(decision.spend?.reason).toBe('turn_ceiling_exceeded')
  })

  it('daily ceiling breach, on the MCP door', async () => {
    configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true)
    queryMock.mockResolvedValue({ rows: [{ total: '39.99' }] })
    const decision = await enforceTurnLimits({
      userId: 'u1',
      channel: 'mcp',
      modelId: 'gemini-2.5-pro',
    })
    expect(decision.allowed).toBe(false)
    if (decision.allowed) throw new Error('unreachable')
    expect(decision.code).toBe(SPEND_CEILING_ERROR_CODE)
    expect(decision.status).toBe(429)
    expect(decision.spend?.reason).toBe('daily_ceiling_exceeded')
    expect(decision.message).toContain('$40.00')
  })
})
