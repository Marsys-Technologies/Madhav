/**
 * session_gate.test.ts — unit tests for lib/security/session_gate.ts with
 * firebase-admin MOCKED (no real Firebase call, no network).
 *
 * The error objects below copy the real SDK messages (firebase-admin 13.x
 * lib/auth/token-verifier.js); `session_gate_real_sdk.test.ts` proves the
 * classifier against the REAL SDK for every failure that is reachable offline.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const verifyMock = vi.hoisted(() => vi.fn())

vi.mock('firebase-admin/app', () => ({
  initializeApp: vi.fn(() => ({})),
  getApps: vi.fn(() => []),
  cert: vi.fn(() => ({})),
}))
vi.mock('firebase-admin/auth', () => ({
  getAuth: vi.fn(() => ({ verifySessionCookie: verifyMock })),
}))

import {
  __resetSessionGateForTest,
  classifyVerifyError,
  getSessionGateStats,
  resolveSessionGateMode,
  safePathForLog,
  SESSION_GATE_BREAKER_MS,
  SESSION_GATE_CACHE_TTL_MS,
  SESSION_GATE_MAX_CACHE_ENTRIES,
  SESSION_GATE_VERIFY_TIMEOUT_MS,
  verifySessionForGate,
} from '../session_gate'

function authErr(code: string, message: string): Error & { code: string } {
  return Object.assign(new Error(message), { code })
}

const E_SIGNATURE = authErr('auth/argument-error', 'Firebase session cookie has invalid signature. See https://x for details.')
const E_EXPIRED = authErr('auth/session-cookie-expired', 'Firebase session cookie has expired. Get a fresh session cookie (auth/session-cookie-expired).')
const E_ISS = authErr(
  'auth/argument-error',
  'Firebase session cookie has incorrect "iss" (issuer) claim. Expected "https://session.firebase.google.com/p" but got "https://evil". Make sure ...',
)
const E_INFRA = authErr('app/invalid-credential', 'Service account object must contain a string "project_id" property.')

beforeEach(() => {
  __resetSessionGateForTest()
  verifyMock.mockReset()
})
afterEach(() => {
  vi.useRealTimers()
})

describe('resolveSessionGateMode', () => {
  it.each([
    [undefined, 'shadow'],
    ['', 'shadow'],
    ['garbage', 'shadow'],
    ['true', 'shadow'],
    ['1', 'shadow'],
    ['shadow', 'shadow'],
    ['off', 'off'],
    ['enforce', 'enforce'],
    [' Enforce ', 'enforce'],
    ['OFF', 'off'],
  ])('SESSION_GATE_MODE=%j resolves to %s', (raw, expected) => {
    expect(resolveSessionGateMode({ SESSION_GATE_MODE: raw })).toBe(expected)
  })

  it('NEVER resolves to enforce unless the value is exactly enforce', () => {
    for (const v of [undefined, '', 'enforced', 'enforce!', 'on', 'yes', 'strict', 'enforce enforce']) {
      expect(resolveSessionGateMode({ SESSION_GATE_MODE: v })).not.toBe('enforce')
    }
  })
})

describe('classifyVerifyError', () => {
  it('maps SDK rejections to coarse reason codes', () => {
    expect(classifyVerifyError(E_EXPIRED)).toEqual({ reason: 'expired', infra: false })
    expect(classifyVerifyError(E_SIGNATURE)).toEqual({ reason: 'bad_signature', infra: false })
    expect(classifyVerifyError(E_ISS)).toEqual({ reason: 'wrong_issuer', infra: false })
    expect(
      classifyVerifyError(authErr('auth/argument-error', 'Firebase session cookie has incorrect "aud" (audience) claim. Expected "p" but got "q".')),
    ).toEqual({ reason: 'wrong_audience', infra: false })
    expect(
      classifyVerifyError(authErr('auth/argument-error', 'Decoding Firebase session cookie failed. Make sure you passed the entire string JWT')),
    ).toEqual({ reason: 'bad_format', infra: false })
    expect(
      classifyVerifyError(authErr('auth/argument-error', 'Firebase session cookie has "kid" claim which does not correspond to a known public key.')),
    ).toEqual({ reason: 'unknown_kid', infra: false })
  })

  it('treats init / credential / key-fetch failures as infrastructure', () => {
    expect(classifyVerifyError(E_INFRA)).toEqual({ reason: 'verify_error', infra: true })
    expect(classifyVerifyError(new Error('getaddrinfo ENOTFOUND www.googleapis.com'))).toEqual({
      reason: 'verify_error',
      infra: true,
    })
    expect(classifyVerifyError(authErr('auth/internal-error', 'x'))).toEqual({ reason: 'verify_error', infra: true })
    expect(classifyVerifyError(authErr('auth/invalid-credential', 'no project id'))).toEqual({
      reason: 'verify_error',
      infra: true,
    })
    expect(
      classifyVerifyError(authErr('auth/argument-error', 'Error fetching public keys for Google certs: boom')),
    ).toEqual({ reason: 'verify_error', infra: true })
    expect(classifyVerifyError(undefined)).toEqual({ reason: 'verify_error', infra: true })
    expect(classifyVerifyError('boom')).toEqual({ reason: 'verify_error', infra: true })
  })

  it('attacker-controlled claim text cannot masquerade as infrastructure (breaker-trip DoS)', () => {
    const e = authErr(
      'auth/argument-error',
      'Firebase session cookie has incorrect "iss" (issuer) claim. Expected "https://session.firebase.google.com/p" but got "Error fetching public keys network".',
    )
    expect(classifyVerifyError(e)).toEqual({ reason: 'wrong_issuer', infra: false })
  })
})

describe('safePathForLog', () => {
  it('keeps plain route names and redacts ids and capability slugs', () => {
    expect(safePathForLog('/api/pariprashna')).toBe('/api/pariprashna')
    expect(safePathForLog('/api/charts/482012f1-710e-4a25-994a-93821f5871aa/ayanamsha-status')).toBe(
      '/api/charts/:id/ayanamsha-status',
    )
    expect(safePathForLog('/share/abcdefghij')).toBe('/share/:slug')
    expect(safePathForLog('/api/conversations/AbC123xYz9/messages/extra/deeper')).toBe('/api/conversations/:id/messages')
  })
})

describe('verifySessionForGate', () => {
  it('returns the verified sub and passes checkRevoked=false', async () => {
    verifyMock.mockResolvedValue({ sub: 'uid-1', exp: Math.floor(Date.now() / 1000) + 3600 })
    await expect(verifySessionForGate('c1')).resolves.toEqual({ ok: true, sub: 'uid-1' })
    expect(verifyMock).toHaveBeenCalledWith('c1', false)
  })

  it('maps SDK rejections to non-infra outcomes with a coarse reason', async () => {
    verifyMock.mockRejectedValueOnce(E_SIGNATURE)
    await expect(verifySessionForGate('forged')).resolves.toEqual({ ok: false, reason: 'bad_signature', infra: false })
    verifyMock.mockRejectedValueOnce(E_EXPIRED)
    await expect(verifySessionForGate('old')).resolves.toEqual({ ok: false, reason: 'expired', infra: false })
    verifyMock.mockRejectedValueOnce(E_ISS)
    await expect(verifySessionForGate('iss')).resolves.toEqual({ ok: false, reason: 'wrong_issuer', infra: false })
  })

  it('treats a verifier result without a subject as an infra failure, not a pass', async () => {
    verifyMock.mockResolvedValue({})
    await expect(verifySessionForGate('nosub')).resolves.toEqual({ ok: false, reason: 'verify_error', infra: true })
  })

  it('never throws, even for a non-string cookie reaching the SDK', async () => {
    verifyMock.mockImplementation(() => {
      throw authErr('auth/argument-error', 'First argument to verifySessionCookie() must be a Firebase session cookie string.')
    })
    await expect(verifySessionForGate('x')).resolves.toMatchObject({ ok: false, infra: false })
  })

  it('caches by fingerprint: a repeat is served without a second SDK call', async () => {
    verifyMock.mockResolvedValue({ sub: 'uid-1', exp: Math.floor(Date.now() / 1000) + 3600 })
    await verifySessionForGate('same')
    await verifySessionForGate('same')
    await verifySessionForGate('same')
    expect(verifyMock).toHaveBeenCalledTimes(1)
    await verifySessionForGate('other')
    expect(verifyMock).toHaveBeenCalledTimes(2)
  })

  it('caches definitive rejections too, but only briefly', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-10T00:00:00Z'))
    verifyMock.mockRejectedValue(E_SIGNATURE)
    await verifySessionForGate('forged')
    await verifySessionForGate('forged')
    expect(verifyMock).toHaveBeenCalledTimes(1)
    vi.setSystemTime(Date.now() + SESSION_GATE_CACHE_TTL_MS + 1)
    await verifySessionForGate('forged')
    expect(verifyMock).toHaveBeenCalledTimes(2)
  })

  it('never serves a cached accept past the cookie exp', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-10T00:00:00Z'))
    const expSec = Math.floor(Date.now() / 1000) + 5 // expires in 5 s, well inside the 30 s TTL
    verifyMock.mockResolvedValue({ sub: 'uid-1', exp: expSec })
    await verifySessionForGate('soon')
    vi.setSystemTime(Date.now() + 6_000)
    await verifySessionForGate('soon')
    expect(verifyMock).toHaveBeenCalledTimes(2)
  })

  it('does not cache infrastructure errors as verdicts; a short breaker avoids a retry storm', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-10T00:00:00Z'))
    verifyMock.mockRejectedValue(E_INFRA)
    const first = await verifySessionForGate('a')
    expect(first).toEqual({ ok: false, reason: 'verify_error', infra: true })
    expect(getSessionGateStats().cache_size).toBe(0)

    // Within the breaker window another cookie does not reach the SDK at all.
    const second = await verifySessionForGate('b')
    expect(second).toEqual({ ok: false, reason: 'verify_error', infra: true })
    expect(verifyMock).toHaveBeenCalledTimes(1)

    // After the breaker window the SDK is tried again (and can recover).
    vi.setSystemTime(Date.now() + SESSION_GATE_BREAKER_MS + 1)
    verifyMock.mockResolvedValue({ sub: 'uid-1', exp: Math.floor(Date.now() / 1000) + 3600 })
    await expect(verifySessionForGate('c')).resolves.toEqual({ ok: true, sub: 'uid-1' })
  })

  it('a hung verifier is cut off at the timeout and reported as infra', async () => {
    vi.useFakeTimers()
    verifyMock.mockImplementation(() => new Promise(() => {}))
    const pending = verifySessionForGate('hung')
    await vi.advanceTimersByTimeAsync(SESSION_GATE_VERIFY_TIMEOUT_MS + 1)
    await expect(pending).resolves.toEqual({ ok: false, reason: 'verify_error', infra: true })
  })

  it('the verdict cache is bounded and evicts oldest-first', async () => {
    verifyMock.mockResolvedValue({ sub: 'uid-1', exp: Math.floor(Date.now() / 1000) + 3600 })
    const total = SESSION_GATE_MAX_CACHE_ENTRIES + 120
    for (let i = 0; i < total; i++) await verifySessionForGate(`cookie-${i}`)
    expect(getSessionGateStats().cache_size).toBeLessThanOrEqual(SESSION_GATE_MAX_CACHE_ENTRIES)
    expect(getSessionGateStats().cache_size).toBe(SESSION_GATE_MAX_CACHE_ENTRIES)

    // newest is still cached, oldest was evicted
    verifyMock.mockClear()
    await verifySessionForGate(`cookie-${total - 1}`)
    expect(verifyMock).not.toHaveBeenCalled()
    await verifySessionForGate('cookie-0')
    expect(verifyMock).toHaveBeenCalledTimes(1)
  })
})
