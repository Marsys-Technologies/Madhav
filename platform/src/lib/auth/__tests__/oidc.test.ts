// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'

const { verifyIdTokenMock } = vi.hoisted(() => ({
  verifyIdTokenMock: vi.fn(),
}))

vi.mock('google-auth-library', () => ({
  OAuth2Client: class {
    verifyIdToken = verifyIdTokenMock
  },
}))

import { verifyOidcToken } from '../oidc'

const audience = 'https://amjis-web-938361928218.asia-south1.run.app'
const schedulerPrincipal = 'amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com'

function ticket(payload: Record<string, unknown>) {
  return { getPayload: () => payload }
}

describe('verifyOidcToken', () => {
  it.each([
    ['malformed', new Error('malformed token')],
    ['expired', new Error('token expired')],
    ['wrong audience', new Error('wrong audience')],
  ])('rejects a %s token', async (_case, error) => {
    verifyIdTokenMock.mockRejectedValueOnce(error)
    await expect(
      verifyOidcToken('bad-token', {
        expectedAudience: audience,
        expectedServiceAccount: schedulerPrincipal,
      }),
    ).rejects.toThrow(error)
    expect(verifyIdTokenMock).toHaveBeenCalledWith({
      idToken: 'bad-token',
      audience,
    })
  })

  it('rejects a token without an email claim', async () => {
    verifyIdTokenMock.mockResolvedValueOnce(ticket({ sub: 'scheduler-subject' }))
    await expect(
      verifyOidcToken('token', {
        expectedAudience: audience,
        expectedServiceAccount: schedulerPrincipal,
      }),
    ).resolves.toBeNull()
  })

  it('rejects a token issued for another service account', async () => {
    verifyIdTokenMock.mockResolvedValueOnce(
      ticket({
        email: 'other@madhav-astrology.iam.gserviceaccount.com',
        sub: 'scheduler-subject',
      }),
    )
    await expect(
      verifyOidcToken('token', {
        expectedAudience: audience,
        expectedServiceAccount: schedulerPrincipal,
      }),
    ).resolves.toBeNull()
  })

  it('accepts only the exact verified Scheduler principal', async () => {
    verifyIdTokenMock.mockResolvedValueOnce(ticket({ email: schedulerPrincipal, sub: 'scheduler-subject' }))
    await expect(
      verifyOidcToken('token', {
        expectedAudience: audience,
        expectedServiceAccount: schedulerPrincipal,
      }),
    ).resolves.toEqual({
      email: schedulerPrincipal,
      sub: 'scheduler-subject',
    })
  })
})
