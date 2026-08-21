/**
 * sf003_authorize_pkce_method.test.ts
 *
 * SF-003 fold-in (PARIŚEṢA-V4): /authorize must reject any code_challenge_method
 * other than 'S256'. Before this fix, a client could register a code_challenge
 * with code_challenge_method: 'plain' (or omitted — RFC 7636's default) and the
 * auth code record would be stored with it, even though discovery.ts advertises
 * `code_challenge_methods_supported: ['S256']` only and token.ts's verifier
 * unconditionally SHA-256s. This closes that inconsistency at the source rather
 * than leaving an unenforced, unverifiable 'plain' record type on the books.
 *
 * No HTTP layer — handleAuthorize is called directly with hand-rolled req/res
 * mocks, mirroring the harness in m5_oauth.test.ts.
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
  const res = {
    status: (s: number) => { statusCode = s; return res },
    json: (b: unknown) => { jsonBody = b },
    redirect: (_s: number, _url: string) => { redirected = true },
    cookie: () => res,
  }
  return {
    res,
    get statusCode() { return statusCode },
    get jsonBody() { return jsonBody },
    get redirected() { return redirected },
  }
}

describe('SF-003 fold-in — /authorize rejects non-S256 code_challenge_method', () => {
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

  it('code_challenge_method: plain -> 400, no auth code created, no redirect', async () => {
    const fetchSpy = setupFetchSpy([{ status: 201, body: { code: 'should_not_be_created' } }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb',
        scope: 'mcp:tools',
        code_challenge: 'somechallenge',
        code_challenge_method: 'plain',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(400)
    expect((mocked.jsonBody as { error: string }).error).toBe('invalid_request')
    expect(mocked.redirected).toBe(false)
    // No auth-code-creation fetch call should have happened.
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('code_challenge present, code_challenge_method omitted -> 400 (RFC 7636 default is plain, must not silently accept)', async () => {
    const fetchSpy = setupFetchSpy([{ status: 201, body: { code: 'should_not_be_created' } }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb',
        scope: 'mcp:tools',
        code_challenge: 'somechallenge',
        // code_challenge_method omitted
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    expect(mocked.statusCode).toBe(400)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('code_challenge_method: S256 -> passes the guard (proceeds to auth-code creation)', async () => {
    setupFetchSpy([{ status: 201, body: { code: 'mcp_ac_ok' } }])
    const { handleAuthorize } = await import('../oauth/authorize.js')

    const mockReq = {
      body: {
        response_type: 'code',
        client_id: 'test_client',
        redirect_uri: 'https://example.com/cb',
        scope: 'mcp:tools',
        code_challenge: 'somechallenge',
        code_challenge_method: 'S256',
      },
    } as Parameters<typeof handleAuthorize>[0]

    const mocked = makeRes()
    await handleAuthorize(mockReq, mocked.res as unknown as Parameters<typeof handleAuthorize>[1])

    // Should NOT be rejected by the guard — it proceeds to redirect to Firebase login.
    expect(mocked.statusCode).toBe(200) // status() never called on the success path
    expect(mocked.redirected).toBe(true)
  })

  it('no code_challenge at all -> guard does not fire (non-PKCE clients unaffected)', async () => {
    setupFetchSpy([{ status: 201, body: { code: 'mcp_ac_ok' } }])
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

    expect(mocked.statusCode).toBe(200)
    expect(mocked.redirected).toBe(true)
  })
})
