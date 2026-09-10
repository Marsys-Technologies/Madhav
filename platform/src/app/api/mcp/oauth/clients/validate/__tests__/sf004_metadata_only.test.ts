/**
 * SF-004 (PARIŚEṢA-V4): POST /api/mcp/oauth/clients/validate's new
 * `metadata_only` lookup mode.
 *
 * `/authorize` needs the client's registered redirect_uris to validate
 * against, but runs before any client secret is available (it's a browser
 * redirect, not a service-to-service call). `metadata_only: true` is a
 * secretless lookup mode, fully separate from the existing secret-required
 * branch (validateClient), that returns ONLY { found, redirect_uris, scopes }
 * — never owner_uid or anything secret-derived.
 *
 * This test also carries the SF-002 regression guard the plan explicitly
 * asks for: the secret-required branch must still reject
 * clientSecret === undefined after this change. See
 * store.validate_client_security.test.ts for the original SF-002 fix's own
 * test — this file complements it at the route layer rather than duplicating
 * store.ts-level coverage.
 *
 * See 00_ARCHITECTURE/briefs/parisesa/SF004_OAUTH_BINDING_CONTRACT_v1_0.md §4.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockValidateServiceToken, mockValidateClient, mockGetClientMetadata } = vi.hoisted(() => ({
  mockValidateServiceToken: vi.fn(),
  mockValidateClient: vi.fn(),
  mockGetClientMetadata: vi.fn(),
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: mockValidateServiceToken }))
vi.mock('@/lib/mcp/oauth/store', () => ({
  validateClient: mockValidateClient,
  getClientMetadata: mockGetClientMetadata,
}))

import { POST } from '../route'

function makeReq(body: unknown): Request {
  return new Request('http://localhost/api/mcp/oauth/clients/validate', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-internal-token': 'test-token' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  mockValidateServiceToken.mockReset()
  mockValidateClient.mockReset()
  mockGetClientMetadata.mockReset()
  mockValidateServiceToken.mockReturnValue(true) // service-token gate passes by default in these tests
})

describe('POST /api/mcp/oauth/clients/validate — metadata_only mode (SF-004)', () => {
  it('metadata_only: true, found client -> returns { found: true, redirect_uris, scopes }, no owner_uid', async () => {
    mockGetClientMetadata.mockResolvedValueOnce({
      redirect_uris: ['https://example.com/cb'],
      scopes: ['mcp:tools'],
    })

    const res = await POST(makeReq({ client_id: 'test_client', metadata_only: true }))
    expect(res.status).toBe(200)
    const body = await res.json() as Record<string, unknown>

    expect(body.found).toBe(true)
    expect(body.redirect_uris).toEqual(['https://example.com/cb'])
    expect(body.scopes).toEqual(['mcp:tools'])
    // The load-bearing assertion: never leaks owner_uid or anything secret-derived.
    expect(body.owner_uid).toBeUndefined()
    expect(body.client_secret_hash).toBeUndefined()
    expect(body.valid).toBeUndefined()

    // validateClient (the secret-required path) must never be called in this mode.
    expect(mockValidateClient).not.toHaveBeenCalled()
    expect(mockGetClientMetadata).toHaveBeenCalledWith('test_client')
  })

  it('metadata_only: true, unknown client -> { found: false }, no owner_uid, no 500', async () => {
    mockGetClientMetadata.mockResolvedValueOnce(null)

    const res = await POST(makeReq({ client_id: 'nonexistent_client', metadata_only: true }))
    expect(res.status).toBe(200)
    const body = await res.json() as Record<string, unknown>

    expect(body.found).toBe(false)
    expect(body.owner_uid).toBeUndefined()
    expect(mockValidateClient).not.toHaveBeenCalled()
  })

  it('metadata_only: true with a client_secret also present -> secret is ignored, still metadata-only response shape', async () => {
    mockGetClientMetadata.mockResolvedValueOnce({
      redirect_uris: ['https://example.com/cb'],
      scopes: ['mcp:tools'],
    })

    const res = await POST(makeReq({
      client_id: 'test_client',
      client_secret: 'fake-secret-xyz', // weak/placeholder-shaped test value — this is the point of the test (must be ignored)
      metadata_only: true,
    }))
    const body = await res.json() as Record<string, unknown>

    expect(body.found).toBe(true)
    expect(body.owner_uid).toBeUndefined()
    // Presence of client_secret alongside metadata_only:true must not divert
    // this request into the authenticating branch.
    expect(mockValidateClient).not.toHaveBeenCalled()
  })

  it('metadata_only: "true" (string, not boolean true) -> falls through to the secret-required branch, NOT metadata mode', async () => {
    mockValidateClient.mockResolvedValueOnce(null)

    const res = await POST(makeReq({ client_id: 'test_client', metadata_only: 'true' as unknown as boolean }))
    await res.json()

    // Strict `=== true` check: a truthy-but-not-literal-true value must not
    // divert this request away from the authenticating path.
    expect(mockValidateClient).toHaveBeenCalledTimes(1)
    expect(mockGetClientMetadata).not.toHaveBeenCalled()
  })

  it('service token missing/invalid -> 401 even in metadata_only mode (the trust boundary is unchanged)', async () => {
    mockValidateServiceToken.mockReturnValue(false)

    const res = await POST(makeReq({ client_id: 'test_client', metadata_only: true }))
    expect(res.status).toBe(401)
    expect(mockGetClientMetadata).not.toHaveBeenCalled()
  })

  it('client_id missing in metadata_only mode -> 400, never reaches getClientMetadata', async () => {
    const res = await POST(makeReq({ metadata_only: true }))
    expect(res.status).toBe(400)
    expect(mockGetClientMetadata).not.toHaveBeenCalled()
  })
})

describe('POST /api/mcp/oauth/clients/validate — secret-required branch untouched (SF-002 regression guard)', () => {
  it('SF-002 regression guard: clientSecret === undefined is still rejected by the authenticating path after SF-004', async () => {
    // The route forwards body.client_secret (undefined here) straight to
    // validateClient, exactly as before SF-004. This test asserts SF-004's
    // new branch did not change that call at all.
    mockValidateClient.mockResolvedValueOnce(null) // simulates the real validateClient's SF-002 rejection

    const res = await POST(makeReq({ client_id: 'victim_client' })) // no client_secret key, no metadata_only
    const body = await res.json() as Record<string, unknown>

    expect(mockValidateClient).toHaveBeenCalledWith('victim_client', undefined)
    expect(body.valid).toBe(false)
    expect(mockGetClientMetadata).not.toHaveBeenCalled()
  })

  it('secret-required branch still returns owner_uid on a real valid credential (unchanged shape)', async () => {
    mockValidateClient.mockResolvedValueOnce({
      client_id: 'test_client',
      owner_uid: 'firebase_uid_owner',
      redirect_uris: ['https://example.com/cb'],
      scopes: ['mcp:tools'],
      created_at: '2026-01-01',
    })

    const res = await POST(makeReq({ client_id: 'test_client', client_secret: 'test-secret' }))
    const body = await res.json() as Record<string, unknown>

    expect(body.valid).toBe(true)
    expect(body.owner_uid).toBe('firebase_uid_owner')
    // Unchanged: this branch does NOT return redirect_uris (that's metadata_only's job).
    expect(body.redirect_uris).toBeUndefined()
  })
})
