/**
 * auth_url_token.test.ts — URL-token (?api_key=) fallback auth path, verified
 * in-process (no network, no live credential).
 *
 * B-MCP-LOG-REDACT (DVA Ruling 64 / SAMAPTI_DVARAPALA_LEDGER.md INC-4).
 *
 * This is where the "the URL-token auth path is wired correctly" assertion now
 * lives, replacing `scripts/operator/mcp_end_to_end_smoke.sh`'s old Probe 4, which
 * round-tripped the real `mcp-canary-key` Secret Manager value through a live
 * `?api_key=...` URL on every deploy. Cloud Run logs `httpRequest.requestUrl`
 * (full path + query string) automatically for every request, independent of
 * application code — so that live probe wrote a real, production-capable bearer
 * credential to Cloud Logging in plaintext on every single deploy. See
 * `platform-mcp/src/lib/auth_url_token.ts`'s module doc for the full rationale.
 *
 * Two things are asserted, together proving the path end-to-end:
 *   1. `resolveAuthHeader()` (server.ts's request-framing logic, extracted to a
 *      pure function) correctly synthesizes a `Bearer <key>` Authorization header
 *      from a `?api_key=` query value when no real header is present, and defers
 *      to a real header when both are present.
 *   2. `validateMcpKeyFromHeader()` (auth.ts) — the SAME validator server.ts calls
 *      for both the header path and the URL-token path — accepts a synthesized
 *      `Bearer <key>` header exactly as it would accept a hand-set one. Proven via
 *      a mocked platform response (same pattern as m5_oauth.test.ts), so no real
 *      Secret Manager value or network call is ever involved.
 *
 * A fake, obviously-non-production placeholder ('test-fake-key-do-not-use') is
 * used throughout — never a real credential.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { resolveAuthHeader } from '../lib/auth_url_token.js'

const FAKE_KEY = 'test-fake-key-do-not-use'
const TEST_PLATFORM_URL = 'http://platform.test'
const TEST_INTERNAL_TOKEN = 'test-internal-secret'

describe('resolveAuthHeader — URL-token fallback request framing (pure)', () => {
  it('synthesizes "Bearer <key>" from ?api_key= when no Authorization header is present', () => {
    const { authHeader, fromUrlParam } = resolveAuthHeader(undefined, FAKE_KEY)
    expect(authHeader).toBe(`Bearer ${FAKE_KEY}`)
    expect(fromUrlParam).toBe(true)
  })

  it('prefers a real Authorization header over ?api_key= when both are present', () => {
    const { authHeader, fromUrlParam } = resolveAuthHeader(`Bearer real-header-value`, FAKE_KEY)
    expect(authHeader).toBe('Bearer real-header-value')
    expect(fromUrlParam).toBe(false)
  })

  it('returns undefined when neither is present', () => {
    const { authHeader, fromUrlParam } = resolveAuthHeader(undefined, undefined)
    expect(authHeader).toBeUndefined()
    expect(fromUrlParam).toBe(false)
  })
})

describe('validateMcpKeyFromHeader — accepts a URL-token-synthesized Bearer header', () => {
  beforeEach(() => {
    vi.resetModules()
    process.env['PLATFORM_URL'] = TEST_PLATFORM_URL
    process.env['MCP_INTERNAL_TOKEN'] = TEST_INTERNAL_TOKEN
  })

  afterEach(() => {
    delete process.env['PLATFORM_URL']
    delete process.env['MCP_INTERNAL_TOKEN']
    vi.restoreAllMocks()
  })

  it('a Bearer header synthesized from ?api_key= validates identically to a hand-set one', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = typeof input === 'string' ? input : input.toString()
      expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/keys/validate`)
      return Promise.resolve(
        new Response(
          JSON.stringify({ valid: true, user_uid: 'uid-url-token-test', key_id: 'key-url-token-test' }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
    })

    // Dynamic import AFTER env vars are set (module reads them at import time).
    const { validateMcpKeyFromHeader } = await import('../auth.js')

    const { authHeader } = resolveAuthHeader(undefined, FAKE_KEY)
    const principal = await validateMcpKeyFromHeader(authHeader)

    expect(principal).not.toBeNull()
    expect(principal?.user_uid).toBe('uid-url-token-test')
    expect(principal?.key_id).toBe('key-url-token-test')
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    // The fetch call must forward the synthesized header, not a raw query string.
    const callArgs = fetchSpy.mock.calls[0]
    const headers = (callArgs?.[1] as RequestInit | undefined)?.headers as Record<string, string> | undefined
    expect(headers?.['Authorization']).toBe(`Bearer ${FAKE_KEY}`)
  })

  it('an invalid key via the URL-token path is rejected, same as an invalid header key', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ valid: false }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    )

    const { validateMcpKeyFromHeader } = await import('../auth.js')
    const { authHeader } = resolveAuthHeader(undefined, 'not-a-real-key')
    const principal = await validateMcpKeyFromHeader(authHeader)

    expect(principal).toBeNull()
  })
})
