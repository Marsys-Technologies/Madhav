/**
 * SF-004 (PARIŚEṢA-V4): POST /api/mcp/oauth/clients registration hygiene.
 * Confirms the redirect_uri policy (§5 of the SF-004 contract) is actually
 * enforced at the real DB write path, not only unit-tested in isolation.
 *
 * See 00_ARCHITECTURE/briefs/parisesa/SF004_OAUTH_BINDING_CONTRACT_v1_0.md §5.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockValidateServiceToken, mockRegisterClient } = vi.hoisted(() => ({
  mockValidateServiceToken: vi.fn(),
  mockRegisterClient: vi.fn(),
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: mockValidateServiceToken }))
vi.mock('@/lib/mcp/oauth/store', () => ({ registerClient: mockRegisterClient }))

import { POST } from '../route'

function makeReq(body: unknown): Request {
  return new Request('http://localhost/api/mcp/oauth/clients', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'firebase_uid_owner',
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  mockValidateServiceToken.mockReset()
  mockRegisterClient.mockReset()
  mockValidateServiceToken.mockReturnValue(true)
  mockRegisterClient.mockResolvedValue({ client_id: 'mcp_client_new', client_secret: 'mcp_cs_test' })
})

describe('POST /api/mcp/oauth/clients — SF-004 registration hygiene', () => {
  it('javascript: redirect_uri -> 400 invalid_redirect_uri, registerClient never called', async () => {
    const res = await makeReqAndPost({ redirect_uris: ['javascript:alert(1)'] })
    expect(res.status).toBe(400)
    expect((await res.json() as { error: string }).error).toBe('invalid_redirect_uri')
    expect(mockRegisterClient).not.toHaveBeenCalled()
  })

  it('data: redirect_uri -> 400 invalid_redirect_uri', async () => {
    const res = await makeReqAndPost({ redirect_uris: ['data:text/html,x'] })
    expect(res.status).toBe(400)
    expect(mockRegisterClient).not.toHaveBeenCalled()
  })

  it('http://evil.example (non-loopback http) -> 400 invalid_redirect_uri', async () => {
    const res = await makeReqAndPost({ redirect_uris: ['http://evil.example/cb'] })
    expect(res.status).toBe(400)
    expect(mockRegisterClient).not.toHaveBeenCalled()
  })

  it('fragment-bearing https URI -> 400 invalid_redirect_uri', async () => {
    const res = await makeReqAndPost({ redirect_uris: ['https://example.com/cb#frag'] })
    expect(res.status).toBe(400)
    expect(mockRegisterClient).not.toHaveBeenCalled()
  })

  it('one bad URI among several good ones still rejects the whole registration', async () => {
    const res = await makeReqAndPost({
      redirect_uris: ['https://good.example/cb', 'javascript:alert(1)'],
    })
    expect(res.status).toBe(400)
    expect(mockRegisterClient).not.toHaveBeenCalled()
  })

  it('valid https redirect_uris -> 201, registerClient called', async () => {
    const res = await makeReqAndPost({ redirect_uris: ['https://good.example/cb'] })
    expect(res.status).toBe(201)
    expect(mockRegisterClient).toHaveBeenCalledTimes(1)
  })

  it('valid loopback http redirect_uri (dev) -> 201', async () => {
    const res = await makeReqAndPost({ redirect_uris: ['http://localhost:3000/cb'] })
    expect(res.status).toBe(201)
    expect(mockRegisterClient).toHaveBeenCalledTimes(1)
  })

  async function makeReqAndPost(body: unknown) {
    return POST(makeReq(body))
  }
})
