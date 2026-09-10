/**
 * proxy.test.ts — the request boundary (`src/proxy.ts`), G1-D additions.
 *
 * `src/proxy.ts` is Next 16's renamed `middleware.ts` and ALREADY EXISTED as the
 * app-wide session gate. G1-D added per-caller rate limiting to it rather than a
 * second competing boundary file, so these tests assert BOTH:
 *
 *   • the pre-existing session gate still behaves exactly as before (a
 *     regression guard on code this lane did not own but did touch), and
 *   • the new door rate limit: flag-OFF by default, one shared window
 *     implementation, and a designed 429 rather than a thrown error.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { NextRequest } from 'next/server'

import { configService } from '@/lib/config/index'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'
import { proxy } from '@/proxy'

/** A structurally-valid, unexpired Firebase session cookie payload. */
function sessionCookie(uid: string): string {
  const payload = {
    sub: uid,
    exp: Math.floor(Date.now() / 1000) + 3600,
    iss: 'https://session.firebase.google.com/marsys',
  }
  const b64 = Buffer.from(JSON.stringify(payload)).toString('base64url')
  return `header.${b64}.signature`
}

function req(
  path: string,
  init?: { method?: string; headers?: Record<string, string>; uid?: string },
): NextRequest {
  const headers: Record<string, string> = { ...init?.headers }
  if (init?.uid) headers.cookie = `__session=${sessionCookie(init.uid)}`
  return new NextRequest(`http://localhost${path}`, {
    method: init?.method ?? 'POST',
    headers,
  })
}

const MCP_HEADERS = { 'x-mcp-key-id': 'mcp_test_KEY001' }

beforeEach(() => __resetRpmCountersForTest())
afterEach(() => configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', false))

// ── Regression guard on the pre-existing session gate ────────────────────────

describe('pre-existing session gate is unchanged', () => {
  it('401s an unauthenticated API request', async () => {
    const response = await proxy(req('/api/pariprashna'))
    expect(response.status).toBe(401)
  })

  it('redirects an unauthenticated page request to /login', async () => {
    const response = await proxy(req('/clients/abc', { method: 'GET' }))
    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toContain('/login')
  })

  it('lets /api/mcp/* through without a session (service-to-service path)', async () => {
    const response = await proxy(req('/api/mcp/prashna_ask', { headers: MCP_HEADERS }))
    expect(response.status).toBe(200)
  })

  it('lets an authenticated request through', async () => {
    const response = await proxy(req('/api/pariprashna', { uid: 'uid-1' }))
    expect(response.status).toBe(200)
  })
})

// ── G1-D additions ───────────────────────────────────────────────────────────

describe('door rate limit — flag OFF (the shipped default)', () => {
  it('passes an unlimited number of door requests through', async () => {
    for (let i = 0; i < 400; i++) {
      const response = await proxy(req('/api/mcp/prashna_ask', { headers: MCP_HEADERS }))
      expect(response.status).toBe(200)
    }
  })
})

describe('door rate limit — flag ON', () => {
  beforeEach(() => configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true))

  it('refuses a flood with 429 and Retry-After — not a thrown error, not a 500', async () => {
    let response = await proxy(req('/api/mcp/prashna_ask', { headers: MCP_HEADERS }))
    // MARSYS_PROXY_RPM_LIMIT defaults to 120.
    for (let i = 1; i < 121; i++) {
      response = await proxy(req('/api/mcp/prashna_ask', { headers: MCP_HEADERS }))
    }

    expect(response.status).toBe(429)
    expect(response.status).not.toBe(500)
    expect(response.headers.get('retry-after')).toBeTruthy()

    const body = await response.json()
    expect(body.error.code).toBe('LIMIT_RATE_LIMIT_EXCEEDED')
    expect(body.error.retry).toBe(true)
    expect(body.error.detail).toContain('120 requests/minute')
  })

  it('keys the web door per user, so one noisy user does not lock out another', async () => {
    for (let i = 0; i < 121; i++) {
      await proxy(req('/api/pariprashna', { uid: 'noisy' }))
    }
    const noisy = await proxy(req('/api/pariprashna', { uid: 'noisy' }))
    expect(noisy.status).toBe(429)

    const quiet = await proxy(req('/api/pariprashna', { uid: 'quiet' }))
    expect(quiet.status).toBe(200)
  })

  it('separates MCP credentials from each other', async () => {
    for (let i = 0; i < 121; i++) {
      await proxy(req('/api/mcp/prashna_ask', { headers: { 'x-mcp-key-id': 'noisy' } }))
    }
    const other = await proxy(req('/api/mcp/prashna_ask', { headers: { 'x-mcp-key-id': 'quiet' } }))
    expect(other.status).toBe(200)
  })

  it('the session gate still wins over the rate limit for an unauthenticated caller', async () => {
    for (let i = 0; i < 200; i++) {
      const response = await proxy(req('/api/pariprashna'))
      // 401, never 429 — a caller must not be told "slow down" when the real
      // answer is "sign in".
      expect(response.status).toBe(401)
    }
  })

  it('does not meter a GET — only the request that starts a turn', async () => {
    for (let i = 0; i < 300; i++) {
      const response = await proxy(req('/api/pariprashna/resume', { method: 'GET', uid: 'u' }))
      expect(response.status).toBe(200)
    }
  })

  it('leaves non-door paths untouched', async () => {
    for (let i = 0; i < 300; i++) {
      const response = await proxy(req('/api/chat/consult', { uid: 'u' }))
      expect(response.status).toBe(200)
    }
  })
})
