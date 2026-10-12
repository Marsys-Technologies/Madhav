/**
 * getServerUser() must stop honouring a still-valid session cookie once the user's
 * profile is not 'active' (SS N-413, S10). Real `getServerUser` + real
 * `verifySessionCookie` wrapper run here; only firebase-admin, the cookie jar and
 * the DB are faked.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const cookieJar = vi.hoisted(() => ({ value: 'cookie-value' as string | undefined }))
vi.mock('next/headers', () => ({
  cookies: async () => ({
    get: (name: string) =>
      name === '__session' && cookieJar.value !== undefined ? { value: cookieJar.value } : undefined,
  }),
}))

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { getServerUser } from '@/lib/firebase/server'
import { installFakeFirebaseAdmin, verifySessionCookieMock } from './fakeFirebaseAdmin'

const mockQuery = vi.mocked(query)
let restore: () => void

beforeAll(() => {
  restore = installFakeFirebaseAdmin()
})
afterAll(() => restore())

function profileStatus(status: string | null) {
  mockQuery.mockResolvedValue({
    rows: status === null ? [] : [{ status }],
    rowCount: status === null ? 0 : 1,
    command: '',
    oid: 0,
    fields: [],
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  cookieJar.value = 'cookie-value'
  verifySessionCookieMock.mockResolvedValue({ uid: 'user-1', email: 'u@example.test' })
})

describe('getServerUser: profile status gate', () => {
  it('returns the decoded user when the profile is active', async () => {
    profileStatus('active')
    const user = await getServerUser()
    expect(user?.uid).toBe('user-1')
    expect(verifySessionCookieMock).toHaveBeenCalledWith('cookie-value', true)
  })

  it('returns null for a disabled profile even though the cookie verifies', async () => {
    profileStatus('disabled')
    expect(await getServerUser()).toBeNull()
    expect(verifySessionCookieMock).toHaveBeenCalledTimes(1)
  })

  it('returns null for a pending profile', async () => {
    profileStatus('pending')
    expect(await getServerUser()).toBeNull()
  })

  it('keeps today\'s behaviour when NO profile row exists (user returned)', async () => {
    profileStatus(null)
    const user = await getServerUser()
    expect(user?.uid).toBe('user-1')
  })

  it('reads the status of the verified uid with one primary-key query', async () => {
    profileStatus('active')
    await getServerUser()
    expect(mockQuery).toHaveBeenCalledTimes(1)
    expect(mockQuery).toHaveBeenCalledWith(expect.stringMatching(/FROM profiles WHERE id=\$1/), ['user-1'])
  })

  it('fails closed (null) when the status lookup throws', async () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    mockQuery.mockRejectedValue(new Error('db down'))
    expect(await getServerUser()).toBeNull()
    spy.mockRestore()
  })

  it('returns null without touching the DB when there is no cookie', async () => {
    cookieJar.value = undefined
    expect(await getServerUser()).toBeNull()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns null without touching the DB when the cookie does not verify', async () => {
    verifySessionCookieMock.mockRejectedValue(new Error('revoked'))
    expect(await getServerUser()).toBeNull()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('re-enabling takes effect on the very next call (no cache)', async () => {
    profileStatus('disabled')
    expect(await getServerUser()).toBeNull()
    profileStatus('active')
    expect((await getServerUser())?.uid).toBe('user-1')
  })
})
