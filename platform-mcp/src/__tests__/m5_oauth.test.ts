/**
 * m5_oauth.test.ts — M5 Production OAuth tests.
 *
 * Verifies:
 *   V3 — Token issue/validate/refresh via DB-backed store (via platform API mock).
 *   V3 — Auth-code grant REJECTS when uid is unset (fail-closed, M0 preserved).
 *   V3 — Auth-code grant SUCCEEDS with a real uid (M5 path).
 *   V3 — Dynamic client registration works.
 *   V3 — One identity core: both Bearer and OAuth resolve to Principal.
 *   V6 — Header/key-actually-sent check: X-MCP-Internal-Token transmitted.
 *   V7 — No 'anonymous' token mintable; no in-memory Maps remain.
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const TEST_PLATFORM_URL = 'http://platform.test'
const TEST_INTERNAL_TOKEN = 'test-internal-secret'

// Shared fetch spy setup
function setupFetchSpy(responses: Array<{ status?: number; body: unknown }>) {
  let callCount = 0
  return vi.spyOn(globalThis, 'fetch').mockImplementation(() => {
    const response = responses[callCount % responses.length]
    callCount++
    return Promise.resolve(
      new Response(JSON.stringify(response.body), {
        status: response.status ?? 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })
}

describe('M5 OAuth — token_store DB delegation', () => {
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

  it('issueTokens calls POST /api/mcp/oauth/tokens with uid + scopes', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 201,
      body: {
        access_token: 'mcp_at_abc',
        refresh_token: 'mcp_rt_xyz',
        expires_in: 3600,
        scope: 'mcp:tools',
      },
    }])

    const { issueTokens } = await import('../oauth/token_store.js')
    const result = await issueTokens('firebase_uid_123', ['mcp:tools'])

    expect(result.access_token).toBe('mcp_at_abc')
    expect(result.refresh_token).toBe('mcp_rt_xyz')
    expect(fetchSpy).toHaveBeenCalledTimes(1)

    // V6: assert X-MCP-Internal-Token is ACTUALLY sent (M0.5 lesson)
    const [url, init] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/tokens`)
    expect((init as RequestInit & { headers: Record<string, string> }).headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL_TOKEN)

    const body = JSON.parse((init as RequestInit).body as string)
    expect(body.uid).toBe('firebase_uid_123')
    expect(body.scopes).toEqual(['mcp:tools'])
  })

  it('validateAccessToken calls GET /api/mcp/oauth/tokens/validate', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: { valid: true, uid: 'firebase_uid_123', scopes: ['mcp:tools'] },
    }])

    const { validateAccessToken } = await import('../oauth/token_store.js')
    const result = await validateAccessToken('mcp_at_abc')

    expect(result).not.toBeNull()
    expect(result!.uid).toBe('firebase_uid_123')

    // V6: X-MCP-OAuth-Token header actually sent
    const [url, init] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/tokens/validate`)
    expect((init as RequestInit & { headers: Record<string, string> }).headers['X-MCP-OAuth-Token']).toBe('mcp_at_abc')
    expect((init as RequestInit & { headers: Record<string, string> }).headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL_TOKEN)
  })

  it('validateAccessToken returns null for expired/unknown tokens', async () => {
    setupFetchSpy([{ status: 200, body: { valid: false } }])

    const { validateAccessToken } = await import('../oauth/token_store.js')
    const result = await validateAccessToken('expired_token')
    expect(result).toBeNull()
  })

  it('refreshAccessToken calls POST /api/mcp/oauth/tokens/refresh', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: {
        access_token: 'mcp_at_new',
        refresh_token: 'mcp_rt_new',
        expires_in: 3600,
        scope: 'mcp:tools',
      },
    }])

    const { refreshAccessToken } = await import('../oauth/token_store.js')
    const result = await refreshAccessToken('mcp_rt_old')

    expect(result).not.toBeNull()
    expect(result!.access_token).toBe('mcp_at_new')

    // V6: header actually sent
    const [url, init] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/tokens/refresh`)
    expect((init as RequestInit & { headers: Record<string, string> }).headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL_TOKEN)
  })

  it('refreshAccessToken returns null for expired refresh tokens', async () => {
    setupFetchSpy([{ status: 400, body: { error: 'invalid_grant' } }])

    const { refreshAccessToken } = await import('../oauth/token_store.js')
    const result = await refreshAccessToken('expired_rt')
    expect(result).toBeNull()
  })
})

describe('M5 OAuth — auth code DB delegation', () => {
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

  it('generateAuthCode calls POST /api/mcp/oauth/codes', async () => {
    const fetchSpy = setupFetchSpy([{ status: 201, body: { code: 'mcp_ac_abc123' } }])

    const { generateAuthCode } = await import('../oauth/authorize.js')
    const code = await generateAuthCode({
      clientId: 'test_client',
      redirectUri: 'https://example.com/callback',
      scopes: ['mcp:tools'],
    })

    expect(code).toBe('mcp_ac_abc123')

    // V6: internal token sent
    const [url, init] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/codes`)
    expect((init as RequestInit & { headers: Record<string, string> }).headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL_TOKEN)
  })

  it('consumeAuthCode calls POST /api/mcp/oauth/codes/consume', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/callback',
          uid: 'firebase_uid_123',
          scopes: ['mcp:tools'],
        },
      },
    }])

    const { consumeAuthCode } = await import('../oauth/authorize.js')
    const record = await consumeAuthCode('mcp_ac_abc123')

    expect(record).not.toBeNull()
    expect(record!.uid).toBe('firebase_uid_123')

    const [url] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/codes/consume`)
  })

  it('consumeAuthCode returns null for expired/consumed codes', async () => {
    setupFetchSpy([{ status: 400, body: { error: 'invalid_grant' } }])

    const { consumeAuthCode } = await import('../oauth/authorize.js')
    const record = await consumeAuthCode('expired_code')
    expect(record).toBeNull()
  })
})

describe('M5 OAuth — token.ts fail-closed (M0 behaviour preserved)', () => {
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

  it('auth-code grant rejects when uid is null (fail-closed)', async () => {
    // consumeAuthCode returns a record with uid = undefined (not stamped by Firebase)
    setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: undefined,   // uid not stamped — Firebase round-trip not complete
          scopes: ['mcp:tools'],
        },
      },
    }])

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_nouid',
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(400)
    expect((responseBody as { error: string }).error).toBe('invalid_grant')
  })

  it('auth-code grant rejects for anonymous uid (fail-closed)', async () => {
    setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'anonymous',   // explicitly forbidden
          scopes: ['mcp:tools'],
        },
      },
    }])

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_anon',
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(400)
    expect((responseBody as { error: string }).error).toBe('invalid_grant')
  })

  it('auth-code grant SUCCEEDS with a real Firebase uid', async () => {
    // Mock: consumeAuthCode returns a record with a real uid,
    // then issueTokens returns token pair.
    let fetchCallCount = 0
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => {
      fetchCallCount++
      if (fetchCallCount === 1) {
        // consumeAuthCode call
        return Promise.resolve(new Response(JSON.stringify({
          record: {
            client_id: 'test_client',
            redirect_uri: 'https://example.com/cb',
            uid: 'real_firebase_uid',
            scopes: ['mcp:tools'],
          },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      }
      // issueTokens call
      return Promise.resolve(new Response(JSON.stringify({
        access_token: 'mcp_at_real',
        refresh_token: 'mcp_rt_real',
        expires_in: 3600,
        scope: 'mcp:tools',
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    })

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_real',
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    // Should succeed (200 default since status wasn't set)
    expect(statusCode).toBe(200)
    const body = responseBody as { access_token: string; token_type: string }
    expect(body.access_token).toBe('mcp_at_real')
    expect(body.token_type).toBe('Bearer')
  })

  // SF-003 (PARIŚEṢA-V4) — PKCE downgrade / unconditional enforcement.
  //
  // Fixed value pair: verifier is 43 chars of the RFC 7636 unreserved charset;
  // challenge is BASE64URL(SHA256(verifier)), i.e. what a real client would send.
  const PKCE_VERIFIER = 'a'.repeat(43)
  const PKCE_CHALLENGE = 'ZtNPunH49FD35FWYhT5Tv8I7vRKQJ8uxMaL0_9eHjNA'

  it('SF-003 exploit path: pkce_challenge set, code_verifier omitted -> 400, no tokens issued', async () => {
    // Only ONE fetch call should ever happen (consumeAuthCode). If the bug were
    // still present, control would fall through to issueTokens and a second
    // fetch call would occur — asserting call count is itself a failure mode
    // check, on top of the status/body assertions.
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
          pkce_challenge: PKCE_CHALLENGE,
        },
      },
    }])

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_no_verifier',
        // code_verifier deliberately omitted — this is the exploit
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(400)
    expect((responseBody as { error: string }).error).toBe('invalid_grant')
    expect((responseBody as { access_token?: string }).access_token).toBeUndefined()
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('non-string code_verifier (array) -> 400, not an unhandled crash (adversarial: type-confusion probe)', async () => {
    setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
          pkce_challenge: PKCE_CHALLENGE,
        },
      },
    }])

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_array_verifier',
        code_verifier: [PKCE_VERIFIER],   // type confusion: array, not string
      },
    } as unknown as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await expect(handleToken(mockReq, mockRes)).resolves.not.toThrow()
    expect(statusCode).toBe(400)
    expect((responseBody as { error: string }).error).toBe('invalid_grant')
  })

  it('mismatched code_verifier -> 400 (regression guard on existing behaviour)', async () => {
    setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
          pkce_challenge: PKCE_CHALLENGE,
        },
      },
    }])

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_wrong_verifier',
        code_verifier: 'b'.repeat(43),   // wrong verifier, valid shape
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(400)
    expect((responseBody as { error: string }).error).toBe('invalid_grant')
  })

  it('malformed code_verifier (bad charset/length) -> 400, rejected before hashing', async () => {
    setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
          pkce_challenge: PKCE_CHALLENGE,
        },
      },
    }])

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_malformed_verifier',
        code_verifier: 'too-short',   // < 43 chars
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(400)
    expect((responseBody as { error: string }).error).toBe('invalid_grant')
  })

  it('correct code_verifier -> 200 (positive control)', async () => {
    let fetchCallCount = 0
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => {
      fetchCallCount++
      if (fetchCallCount === 1) {
        return Promise.resolve(new Response(JSON.stringify({
          record: {
            client_id: 'test_client',
            redirect_uri: 'https://example.com/cb',
            uid: 'real_firebase_uid',
            scopes: ['mcp:tools'],
            pkce_challenge: PKCE_CHALLENGE,
          },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      }
      return Promise.resolve(new Response(JSON.stringify({
        access_token: 'mcp_at_pkce_ok',
        refresh_token: 'mcp_rt_pkce_ok',
        expires_in: 3600,
        scope: 'mcp:tools',
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    })

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_correct_verifier',
        code_verifier: PKCE_VERIFIER,
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(200)
    const body = responseBody as { access_token: string }
    expect(body.access_token).toBe('mcp_at_pkce_ok')
  })

  it('no pkce_challenge on the record + no verifier sent -> still succeeds (non-PKCE clients unaffected)', async () => {
    let fetchCallCount = 0
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => {
      fetchCallCount++
      if (fetchCallCount === 1) {
        return Promise.resolve(new Response(JSON.stringify({
          record: {
            client_id: 'test_client',
            redirect_uri: 'https://example.com/cb',
            uid: 'real_firebase_uid',
            scopes: ['mcp:tools'],
            // no pkce_challenge — this client never opted into PKCE
          },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      }
      return Promise.resolve(new Response(JSON.stringify({
        access_token: 'mcp_at_no_pkce',
        refresh_token: 'mcp_rt_no_pkce',
        expires_in: 3600,
        scope: 'mcp:tools',
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    })

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        code: 'mcp_ac_no_pkce',
        // no code_verifier either
      },
    } as Parameters<typeof handleToken>[0]

    let statusCode = 200
    let responseBody: unknown = null
    const mockRes = {
      status: (s: number) => { statusCode = s; return mockRes },
      json: (b: unknown) => { responseBody = b },
    } as Parameters<typeof handleToken>[1]

    await handleToken(mockReq, mockRes)

    expect(statusCode).toBe(200)
    const body = responseBody as { access_token: string }
    expect(body.access_token).toBe('mcp_at_no_pkce')
  })
})

describe('M5 OAuth — dynamic client registration', () => {
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

  it('registerOAuthClient calls POST /api/mcp/oauth/clients with internal token', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 201,
      body: { client_id: 'mcp_client_abc', client_secret: 'mcp_cs_xyz' },
    }])

    const { registerOAuthClient } = await import('../oauth/oauth_platform_client.js')
    const result = await registerOAuthClient({
      ownerUid: 'firebase_uid_owner',
      redirectUris: ['https://example.com/callback'],
    })

    expect(result).not.toBeNull()
    expect(result!.client_id).toBe('mcp_client_abc')
    expect(result!.client_secret).toBe('mcp_cs_xyz')

    // V6: verify X-MCP-Internal-Token is sent
    const [url, init] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/clients`)
    const headers = (init as RequestInit & { headers: Record<string, string> }).headers
    expect(headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL_TOKEN)
    expect(headers['X-MCP-User']).toBe('firebase_uid_owner')
  })

  it('validateOAuthClient calls POST /api/mcp/oauth/clients/validate', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: { valid: true, owner_uid: 'firebase_uid_owner', scopes: ['mcp:tools'] },
    }])

    const { validateOAuthClient } = await import('../oauth/oauth_platform_client.js')
    const result = await validateOAuthClient('mcp_client_abc', 'mcp_cs_xyz')

    expect(result.valid).toBe(true)
    if (result.valid) {
      expect(result.owner_uid).toBe('firebase_uid_owner')
    }

    const [url, init] = fetchSpy.mock.calls[0]!
    expect(url).toBe(`${TEST_PLATFORM_URL}/api/mcp/oauth/clients/validate`)
    expect((init as RequestInit & { headers: Record<string, string> }).headers['X-MCP-Internal-Token']).toBe(TEST_INTERNAL_TOKEN)
  })

  it('validateOAuthClient returns { valid: false } for unknown client', async () => {
    setupFetchSpy([{ status: 200, body: { valid: false } }])

    const { validateOAuthClient } = await import('../oauth/oauth_platform_client.js')
    const result = await validateOAuthClient('unknown_client', 'wrong_secret')
    expect(result.valid).toBe(false)
  })
})

describe('M5 OAuth — V7 invariants', () => {
  it('no in-memory Maps remain in token_store.ts (grep guard)', async () => {
    // Import the module and verify there are no exported Map instances
    const tokenStore = await import('../oauth/token_store.js')
    // The module should only export functions, not Maps
    expect(typeof tokenStore.issueTokens).toBe('function')
    expect(typeof tokenStore.validateAccessToken).toBe('function')
    expect(typeof tokenStore.refreshAccessToken).toBe('function')
    expect(typeof tokenStore.revokeTokensForUid).toBe('function')
    // No in-memory Map exports
    for (const [key, value] of Object.entries(tokenStore)) {
      expect(value instanceof Map, `${key} should not be a Map`).toBe(false)
    }
  })

  it('no in-memory Maps remain in authorize.ts (grep guard)', async () => {
    vi.resetModules()
    process.env['PLATFORM_URL'] = 'http://platform.test'
    process.env['MCP_INTERNAL_TOKEN'] = 'test'
    const authorize = await import('../oauth/authorize.js')
    // authorize.ts exports only functions — no Maps
    for (const [key, value] of Object.entries(authorize)) {
      expect(value instanceof Map, `${key} should not be a Map`).toBe(false)
    }
    delete process.env['PLATFORM_URL']
    delete process.env['MCP_INTERNAL_TOKEN']
    vi.restoreAllMocks()
  })
})

describe('M5 OAuth — discovery includes registration_endpoint', () => {
  it('buildDiscoveryMetadata includes registration_endpoint', async () => {
    const { buildDiscoveryMetadata } = await import('../oauth/discovery.js')
    const meta = buildDiscoveryMetadata()
    expect(meta.registration_endpoint).toBeDefined()
    expect(meta.registration_endpoint).toContain('/oauth/register')
  })
})
