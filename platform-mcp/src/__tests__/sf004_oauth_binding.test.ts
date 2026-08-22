/**
 * sf004_oauth_binding.test.ts
 *
 * SF-004 (PARIŚEṢA-V4): OAuth RFC 6749 §4.1.3 — redirect_uri allowlist +
 * authorization-code binding.
 *
 * Two prior holes, closed here:
 *   1. `/authorize` (handleAuthorize) never validated redirect_uri against the
 *      client's registered allowlist — validateOAuthClient/fetchOAuthClient-
 *      Metadata was never called on this path. A registered client_id (not
 *      secret — it travels in authorize URLs) combined with an attacker-
 *      chosen redirect_uri was accepted, round-tripped through `state`, and
 *      used as the final 302 target in handleCallback AFTER a real Firebase
 *      session verification succeeded.
 *   2. `/token`'s authorization_code branch never compared the redeeming
 *      request's client_id/redirect_uri against the values stamped on the
 *      auth code at issuance. No client authentication of any kind gated
 *      code redemption.
 *
 * See 00_ARCHITECTURE/briefs/parisesa/SF004_OAUTH_BINDING_CONTRACT_v1_0.md
 * for the full exact-match rule, error-response table, and adversarial
 * self-review this fix implements against.
 *
 * No HTTP layer — handleAuthorize/handleToken called directly with
 * hand-rolled req/res mocks, mirroring the harness in m5_oauth.test.ts and
 * sf003_authorize_pkce_method.test.ts.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const TEST_PLATFORM_URL = 'http://platform.test'
const TEST_INTERNAL_TOKEN = 'test-internal-secret'

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

function makeRes() {
  let statusCode = 200
  let jsonBody: unknown = null
  let redirected = false
  let redirectUrl: string | null = null
  const res = {
    status: (s: number) => { statusCode = s; return res },
    json: (b: unknown) => { jsonBody = b },
    redirect: (_s: number, url: string) => { redirected = true; redirectUrl = url },
    cookie: () => res,
  }
  return {
    res,
    get statusCode() { return statusCode },
    get jsonBody() { return jsonBody },
    get redirected() { return redirected },
    get redirectUrl() { return redirectUrl },
  }
}

describe('SF-004 — /authorize redirect_uri allowlist', () => {
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

  it('unregistered redirect_uri -> 400, no 302, no auth code created', async () => {
    // Client exists but its allowlist does NOT contain the attacker-chosen URI.
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: { found: true, redirect_uris: ['https://legit-app.example/cb'], scopes: ['mcp:tools'] },
    }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'victim_client',
        redirect_uri: 'https://attacker.evil/steal',
        scope: 'mcp:tools',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.jsonBody as { error: string }).error).toBe('invalid_request')
    // The core exploit assertion: NEVER a redirect on this failure (RFC 6749 §4.1.2.1).
    expect(mocked.redirected).toBe(false)
    // Only the metadata lookup happened — no auth-code creation.
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('unknown client_id -> 400, no 302 (the FK-error-500 path is now a clean 400)', async () => {
    const fetchSpy = setupFetchSpy([{ status: 200, body: { found: false } }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'nonexistent_client',
        redirect_uri: 'https://attacker.evil/steal',
        scope: 'mcp:tools',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.jsonBody as { error: string }).error).toBe('invalid_request')
    expect(mocked.redirected).toBe(false)
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('prefix match is NOT accepted — a registered exact URI does not authorize a longer URI sharing its prefix', async () => {
    setupFetchSpy([{
      status: 200,
      body: { found: true, redirect_uris: ['https://example.com/cb'], scopes: ['mcp:tools'] },
    }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb.evil.example/',
        scope: 'mcp:tools',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(400)
    expect(mocked.redirected).toBe(false)
  })

  it('trailing-slash mismatch is NOT accepted — exact match only, no normalization', async () => {
    setupFetchSpy([{
      status: 200,
      body: { found: true, redirect_uris: ['https://example.com/cb'], scopes: ['mcp:tools'] },
    }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb/',
        scope: 'mcp:tools',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(400)
    expect(mocked.redirected).toBe(false)
  })

  it('registered redirect_uri -> normal flow (200/redirect to Firebase, auth code created)', async () => {
    const fetchSpy = setupFetchSpy([
      { status: 200, body: { found: true, redirect_uris: ['https://example.com/cb'], scopes: ['mcp:tools'] } },
      { status: 201, body: { code: 'mcp_ac_ok' } },
    ])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb',
        scope: 'mcp:tools',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(200) // status() never called on the success path
    expect(mocked.redirected).toBe(true)
    expect(fetchSpy).toHaveBeenCalledTimes(2)
  })

  it('one of several registered redirect_uris matches -> accepted (set membership, still exact per element)', async () => {
    setupFetchSpy([
      {
        status: 200,
        body: {
          found: true,
          redirect_uris: ['https://a.example/cb', 'https://b.example/cb', 'https://c.example/cb'],
          scopes: ['mcp:tools'],
        },
      },
      { status: 201, body: { code: 'mcp_ac_ok' } },
    ])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'multi_uri_client',
        redirect_uri: 'https://b.example/cb',
        scope: 'mcp:tools',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(200)
    expect(mocked.redirected).toBe(true)
  })
})

describe('SF-004 — /token authorization_code binding', () => {
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

  function mockRes() {
    let statusCode = 200
    let responseBody: unknown = null
    const res = {
      status: (s: number) => { statusCode = s; return res },
      json: (b: unknown) => { responseBody = b },
    }
    return { res, get statusCode() { return statusCode }, get responseBody() { return responseBody } }
  }

  it('client_id mismatch -> 400 invalid_grant, no tokens issued', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'real_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
        },
      },
    }])
    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'attacker_client',   // does NOT match the code's stamped client_id
        redirect_uri: 'https://example.com/cb',
        code: 'mcp_ac_stolen',
      },
    } as Parameters<typeof handleToken>[0]

    const mocked = mockRes()
    await handleToken(mockReq, mocked.res as unknown as Parameters<typeof handleToken>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.responseBody as { error: string }).error).toBe('invalid_grant')
    expect((mocked.responseBody as { access_token?: string }).access_token).toBeUndefined()
    // Only the consumeAuthCode call — never reaches issueTokens.
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('redirect_uri mismatch -> 400 invalid_grant, no tokens issued', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
        },
      },
    }])
    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        redirect_uri: 'https://attacker.evil/cb',   // does NOT match the code's stamped redirect_uri
        code: 'mcp_ac_valid',
      },
    } as Parameters<typeof handleToken>[0]

    const mocked = mockRes()
    await handleToken(mockReq, mocked.res as unknown as Parameters<typeof handleToken>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.responseBody as { error: string }).error).toBe('invalid_grant')
    expect((mocked.responseBody as { access_token?: string }).access_token).toBeUndefined()
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('redirect_uri omitted -> 400 invalid_grant (REQUIRED per RFC 6749 §4.1.3 — the column is NOT NULL, so it was always sent originally)', async () => {
    const fetchSpy = setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
        },
      },
    }])
    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        // redirect_uri deliberately omitted
        code: 'mcp_ac_valid',
      },
    } as Parameters<typeof handleToken>[0]

    const mocked = mockRes()
    await handleToken(mockReq, mocked.res as unknown as Parameters<typeof handleToken>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.responseBody as { error: string }).error).toBe('invalid_grant')
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })

  it('empty-string redirect_uri -> 400 invalid_grant (not treated as "present")', async () => {
    setupFetchSpy([{
      status: 200,
      body: {
        record: {
          client_id: 'test_client',
          redirect_uri: 'https://example.com/cb',
          uid: 'real_firebase_uid',
          scopes: ['mcp:tools'],
        },
      },
    }])
    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        redirect_uri: '',
        code: 'mcp_ac_valid',
      },
    } as Parameters<typeof handleToken>[0]

    const mocked = mockRes()
    await handleToken(mockReq, mocked.res as unknown as Parameters<typeof handleToken>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.responseBody as { error: string }).error).toBe('invalid_grant')
  })

  it('matching client_id + redirect_uri pair -> 200, tokens issued (positive control)', async () => {
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
          },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      }
      return Promise.resolve(new Response(JSON.stringify({
        access_token: 'mcp_at_sf004_ok',
        refresh_token: 'mcp_rt_sf004_ok',
        expires_in: 3600,
        scope: 'mcp:tools',
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    })

    const { handleToken } = await import('../oauth/token.js')

    const mockReq = {
      body: {
        grant_type: 'authorization_code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb',
        code: 'mcp_ac_matching',
      },
    } as Parameters<typeof handleToken>[0]

    const mocked = mockRes()
    await handleToken(mockReq, mocked.res as unknown as Parameters<typeof handleToken>[1])

    expect(mocked.statusCode).toBe(200)
    expect((mocked.responseBody as { access_token: string }).access_token).toBe('mcp_at_sf004_ok')
  })
})
