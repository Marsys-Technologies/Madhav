// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const verifyOidcTokenMock = vi.fn()
const readinessMock = vi.fn()
const recordReadinessMock = vi.fn()
const evaluateMock = vi.fn()

vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: (...args: unknown[]) => verifyOidcTokenMock(...args) }))
vi.mock('@/lib/nirmana-elevation/conductor', () => ({
  NIRMANA_CONDUCTOR_AUDIENCE: 'https://amjis-web-938361928218.asia-south1.run.app',
  NIRMANA_CONDUCTOR_PRINCIPAL: 'amjis-nirmana-conductor@madhav-astrology.iam.gserviceaccount.com',
  NIRMANA_VERIFIER_PRINCIPAL: 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com',
  verifyNirmanaUnattendedReadiness: () => readinessMock(),
  recordNirmanaUnattendedReadiness: (...args: unknown[]) => recordReadinessMock(...args),
  evaluateNirmanaConductor: (...args: unknown[]) => evaluateMock(...args),
}))

const conductor = 'amjis-nirmana-conductor@madhav-astrology.iam.gserviceaccount.com'
const verifier = 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com'
const audience = 'https://amjis-web-938361928218.asia-south1.run.app'

function request(body: unknown, authorization = 'Bearer signed-token') {
  return new Request('https://example.test/api/admin/internal/nirmana-elevation-conductor', {
    method: 'POST', headers: { Authorization: authorization, 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}

describe('POST /api/admin/internal/nirmana-elevation-conductor', () => {
  beforeEach(() => {
    vi.resetModules()
    verifyOidcTokenMock.mockReset().mockResolvedValue({ email: conductor, sub: 'subject' })
    readinessMock.mockReset().mockResolvedValue({ verdict: 'fail', checks: [], expires_at: '2026-09-01T00:00:00.000Z' })
    recordReadinessMock.mockReset().mockResolvedValue('recorded')
    evaluateMock.mockReset().mockResolvedValue({ state: 'readiness_required' })
  })

  it('rejects a missing bearer token before parsing or touching the conductor', async () => {
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'evaluate' }, ''))
    expect(response.status).toBe(401)
    expect(verifyOidcTokenMock).not.toHaveBeenCalled()
    expect(evaluateMock).not.toHaveBeenCalled()
  })

  it('binds evaluate to only the dedicated conductor OIDC subject', async () => {
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'evaluate' }))
    expect(response.status).toBe(200)
    expect(verifyOidcTokenMock).toHaveBeenCalledWith('signed-token', { expectedAudience: audience, expectedServiceAccount: conductor })
    expect(evaluateMock).toHaveBeenCalledWith(conductor)
    expect(recordReadinessMock).not.toHaveBeenCalled()
  })

  it('binds readiness recording to only the distinct verifier subject', async () => {
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'verify_readiness' }))
    expect(response.status).toBe(200)
    expect(verifyOidcTokenMock).toHaveBeenCalledWith('signed-token', { expectedAudience: audience, expectedServiceAccount: verifier })
    expect(recordReadinessMock).toHaveBeenCalledWith(verifier, expect.objectContaining({ verdict: 'fail' }))
    expect(evaluateMock).not.toHaveBeenCalled()
  })

  it('rejects arbitrary commands instead of exposing a generic evidence writer', async () => {
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'record_evidence', event_type: 'asset_frozen' }))
    expect(response.status).toBe(400)
    expect(verifyOidcTokenMock).not.toHaveBeenCalled()
    expect(evaluateMock).not.toHaveBeenCalled()
    expect(recordReadinessMock).not.toHaveBeenCalled()
  })
})
