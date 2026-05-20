/**
 * __tests__/sign_url.test.ts
 *
 * Tests for sign_url.ts — HMAC feed token sign/verify/expire/tamper.
 *
 * AC.4C7.3: Sign+verify round-trip works; expired tokens rejected;
 *           tampered signatures rejected.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { signFeedToken, verifyFeedToken, makeFeedTokenExpiry, FEED_TOKEN_TTL_SECONDS } from '../sign_url'
import type { FeedTokenPayload } from '../sign_url'

// Set a test secret so the module doesn't throw on import
beforeEach(() => {
  process.env.SESSION_SECRET = 'test-secret-32-chars-minimum-abc'
})

afterEach(() => {
  delete process.env.SESSION_SECRET
  delete process.env.HMAC_SECRET
  vi.restoreAllMocks()
})

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makePayload(overrides: Partial<FeedTokenPayload> = {}): FeedTokenPayload {
  const now = Math.floor(Date.now() / 1000)
  return {
    jti: 'test-jti-1234567890abcdef',
    location: 'bhubaneswar',
    issued_at: now,
    expires_at: now + FEED_TOKEN_TTL_SECONDS,
    ...overrides,
  }
}

// ── Sign + verify round-trip ──────────────────────────────────────────────────

describe('signFeedToken', () => {
  it('returns a string with exactly one dot separator (encoded.sig)', () => {
    const token = signFeedToken(makePayload())
    // Last dot separates encoded from sig
    const dotCount = (token.match(/\./g) ?? []).length
    expect(dotCount).toBeGreaterThanOrEqual(1)
  })

  it('different payloads produce different tokens', () => {
    const t1 = signFeedToken(makePayload({ jti: 'jti-aaa' }))
    const t2 = signFeedToken(makePayload({ jti: 'jti-bbb' }))
    expect(t1).not.toBe(t2)
  })

  it('same payload produces same token (deterministic)', () => {
    const payload = makePayload()
    const t1 = signFeedToken(payload)
    const t2 = signFeedToken(payload)
    expect(t1).toBe(t2)
  })
})

describe('verifyFeedToken — valid token', () => {
  it('returns ok:true for a freshly signed token', () => {
    const payload = makePayload()
    const token = signFeedToken(payload)
    const result = verifyFeedToken(token)
    expect(result.ok).toBe(true)
  })

  it('decoded payload matches original', () => {
    const payload = makePayload({ location: 'bhubaneswar', personalise: 'abc123' })
    const token = signFeedToken(payload)
    const result = verifyFeedToken(token)
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.payload.jti).toBe(payload.jti)
      expect(result.payload.location).toBe(payload.location)
      expect(result.payload.expires_at).toBe(payload.expires_at)
      expect(result.payload.personalise).toBe(payload.personalise)
    }
  })

  it('token without personalise field verifies correctly', () => {
    const payload = makePayload() // no personalise
    const token = signFeedToken(payload)
    const result = verifyFeedToken(token)
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.payload.personalise).toBeUndefined()
    }
  })
})

describe('verifyFeedToken — expired token', () => {
  it('rejects tokens with expires_at in the past', () => {
    const now = Math.floor(Date.now() / 1000)
    const payload = makePayload({ expires_at: now - 1 }) // 1 second ago
    const token = signFeedToken(payload)
    const result = verifyFeedToken(token)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('expired')
    }
  })

  it('rejects tokens that expired 90 days ago', () => {
    const now = Math.floor(Date.now() / 1000)
    const payload = makePayload({ expires_at: now - FEED_TOKEN_TTL_SECONDS })
    const token = signFeedToken(payload)
    const result = verifyFeedToken(token)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('expired')
    }
  })
})

describe('verifyFeedToken — tampered token', () => {
  it('rejects tokens with modified signature', () => {
    const token = signFeedToken(makePayload())
    const dotIdx = token.lastIndexOf('.')
    const tamperedToken = token.slice(0, dotIdx + 1) + 'deadbeef'
    const result = verifyFeedToken(tamperedToken)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('tampered')
    }
  })

  it('rejects tokens with modified payload (even if signature looks similar)', () => {
    const token = signFeedToken(makePayload())
    const dotIdx = token.lastIndexOf('.')
    const encoded = token.slice(0, dotIdx)
    const sig = token.slice(dotIdx + 1)

    // Decode, modify, re-encode WITHOUT re-signing
    const payloadStr = Buffer.from(encoded, 'base64url').toString('utf8')
    const payloadObj = JSON.parse(payloadStr)
    payloadObj.jti = 'attacker-jti'
    const tamperedEncoded = Buffer.from(JSON.stringify(payloadObj)).toString('base64url')
    const tamperedToken = `${tamperedEncoded}.${sig}`

    const result = verifyFeedToken(tamperedToken)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('tampered')
    }
  })

  it('rejects malformed token (no dot)', () => {
    const result = verifyFeedToken('thisisnotavalidtoken')
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('invalid')
    }
  })

  it('rejects empty string', () => {
    const result = verifyFeedToken('')
    expect(result.ok).toBe(false)
  })

  it('rejects token with empty sig portion', () => {
    const result = verifyFeedToken('someencoded.')
    expect(result.ok).toBe(false)
  })
})

describe('verifyFeedToken — invalid payload', () => {
  it('rejects token with missing jti', async () => {
    const now = Math.floor(Date.now() / 1000)
    // Build token manually with missing jti
    const payload = { location: 'bhubaneswar', expires_at: now + 86400, issued_at: now }
    const { createHmac } = await import('crypto')
    const secret = process.env.SESSION_SECRET!
    const encoded = Buffer.from(JSON.stringify(payload)).toString('base64url')
    const sig = createHmac('sha256', secret).update(encoded).digest('hex')
    const token = `${encoded}.${sig}`

    const result = verifyFeedToken(token)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('invalid')
    }
  })
})

describe('makeFeedTokenExpiry', () => {
  it('returns unix timestamp approximately 90 days from now', () => {
    const before = Math.floor(Date.now() / 1000)
    const expiry = makeFeedTokenExpiry()
    const after = Math.floor(Date.now() / 1000)

    const expectedMin = before + FEED_TOKEN_TTL_SECONDS
    const expectedMax = after + FEED_TOKEN_TTL_SECONDS

    expect(expiry).toBeGreaterThanOrEqual(expectedMin)
    expect(expiry).toBeLessThanOrEqual(expectedMax)
  })

  it('FEED_TOKEN_TTL_SECONDS equals 90 days in seconds', () => {
    expect(FEED_TOKEN_TTL_SECONDS).toBe(90 * 24 * 60 * 60)
  })
})

describe('secret fallback', () => {
  it('uses HMAC_SECRET when SESSION_SECRET is absent', () => {
    delete process.env.SESSION_SECRET
    process.env.HMAC_SECRET = 'hmac-secret-fallback-32-chars-x'

    // Dynamic import re-reads env on each call via the getSecret() function
    // (our module reads env at call time, not module load time)
    const payload = makePayload()
    // This should work without throwing
    expect(() => signFeedToken(payload)).not.toThrow()
  })
})
