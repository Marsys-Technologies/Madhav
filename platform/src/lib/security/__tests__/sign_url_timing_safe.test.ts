// @vitest-environment node
/**
 * SS N-373 item 5 — verifyFeedToken must compare the HMAC with a timing-safe
 * primitive, not `!==`. `crypto.timingSafeEqual` is wrapped in a spy: a plain
 * string compare never reaches it.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const tse = vi.hoisted(() => ({ calls: 0 }))
vi.mock('crypto', async (importOriginal) => {
  const actual = await importOriginal<typeof import('crypto')>()
  return {
    ...actual,
    default: actual,
    timingSafeEqual: (a: NodeJS.ArrayBufferView, b: NodeJS.ArrayBufferView) => {
      tse.calls++
      return actual.timingSafeEqual(a, b)
    },
  }
})

import { signFeedToken, verifyFeedToken, makeFeedTokenExpiry } from '../sign_url'

beforeEach(() => {
  tse.calls = 0
  process.env.SESSION_SECRET = 'test-secret-32-chars-minimum-abc'
})

describe('verifyFeedToken uses a timing-safe comparison', () => {
  const payload = () => ({
    jti: 'jti-1234567890abcdef',
    location: 'bhubaneswar',
    issued_at: Math.floor(Date.now() / 1000),
    expires_at: makeFeedTokenExpiry(),
  })

  it('a valid token verifies through timingSafeEqual', () => {
    const r = verifyFeedToken(signFeedToken(payload()))
    expect(r.ok).toBe(true)
    expect(tse.calls).toBeGreaterThan(0)
  })

  it('a forged token is rejected through timingSafeEqual', () => {
    const [encoded] = signFeedToken(payload()).split('.')
    const r = verifyFeedToken(`${encoded}.${'0'.repeat(64)}`)
    expect(r).toEqual({ ok: false, reason: 'tampered' })
    expect(tse.calls).toBeGreaterThan(0)
  })
})
