/**
 * The retired legacy POST keeps its original session/write guards and input
 * refusals. Authorized valid requests must disclose retirement, never append
 * old events, inspect legacy build identity, or start a canonical run.
 * Original V3-E-010/V3-E-011 cross-tenant regressions remain covered below.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'
const VALID_BODY = { chart_id: VICTIM_CHART }

function makeReq(body: unknown = VALID_BODY): NextRequest {
  return new NextRequest('http://localhost/api/build/continue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function setupMocks(opts: {
  uid: string
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
  legacyFailure?: Error
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null, legacyFailure } = opts
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({
        rows: ownerId !== null ? [{ owner_id: ownerId }] : [],
        rowCount: ownerId !== null ? 1 : 0,
      })
    }
    // Keep the pre-retirement fake success available for the old-source causal
    // run. A tombstone must never reach either legacy database operation.
    if (/\bbuilds\b|\bbuild_events\b/.test(sql)) {
      if (legacyFailure) throw legacyFailure
      return Promise.resolve({ rows: [{ build_id: 'legacy-build-1' }], rowCount: 1 })
    }
    throw new Error('Unexpected query outside chart permission checks')
  })
}

function expectPermissionReadsOnly() {
  for (const [sql] of mockQuery.mock.calls) {
    expect(sql).toMatch(/^\s*SELECT\b/i)
    expect(sql).toMatch(/\bFROM\s+(profiles|charts|chart_grants)\b/i)
    expect(sql).not.toMatch(/\b(builds|build_events|build_runs|build_run_assets)\b/i)
  }
}

async function expectGone(res: Response) {
  expect(res.status).toBe(410)
  const body = await res.json()
  expect(body.code).toBe('ENDPOINT_GONE')
  expect(body.error).toContain('/api/cockpit/runs')
  expect(body.ok).toBeUndefined()
  expect(body.build_id).toBeUndefined()
  expectPermissionReadsOnly()
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/build/continue — authorized retirement without operation effects', () => {
  it('DENIES a non-owner guest before revealing the tombstone', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID })
    const res = await POST(makeReq())
    expect(res.status).toBe(403)
    expect(await res.json()).toEqual({ error: 'Forbidden', code: 'FORBIDDEN_CHART' })
    expectPermissionReadsOnly()
  })

  it('DENIES a chart_grants view-grantee; read access is not write access', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await POST(makeReq())
    expect(res.status).toBe(403)
    expectPermissionReadsOnly()
  })

  it('DENIES a missing chart with the same response as a foreign chart', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: null })
    const res = await POST(makeReq())
    expect(res.status).toBe(403)
    expect(await res.json()).toEqual({ error: 'Forbidden', code: 'FORBIDDEN_CHART' })
    expectPermissionReadsOnly()
  })

  it('DENIES an unknown role instead of treating it as super_admin', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'ADMIN', ownerId: VICTIM_UID })
    const res = await POST(makeReq())
    expect(res.status).toBe(403)
    expectPermissionReadsOnly()
  })

  it('returns410 to the authorized owner without a legacy read or write', async () => {
    setupMocks({ uid: VICTIM_UID, ownerId: VICTIM_UID })
    await expectGone(await POST(makeReq()))
  })

  it('returns410 to super_admin without creating a replacement run', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    await expectGone(await POST(makeReq()))
  })

  it('returns410 even when the installed legacy schema cannot accept old SQL', async () => {
    setupMocks({ uid: VICTIM_UID, legacyFailure: new Error('synthetic missing legacy schema') })
    await expectGone(await POST(makeReq()))
  })

  it('does not swallow a failure of the retained permission lookup', async () => {
    mockGetServerUser.mockResolvedValue({ uid: VICTIM_UID })
    const failure = new Error('synthetic permission read failed')
    mockQuery.mockRejectedValue(failure)
    await expect(POST(makeReq())).rejects.toBe(failure)
  })

})

describe('legacy authentication and malformed-body compatibility', () => {
  it.each([
    ['null', 'null'], ['malformed JSON', '{'], ['array', '[]'], ['string', '"synthetic"'],
    ['number', '7'], ['boolean', 'false'], ['empty object', '{}'],
  ])('returns controlled400 for %s before any permission query', async (_name, body) => {
    mockGetServerUser.mockResolvedValue({ uid: VICTIM_UID })
    const res = await POST(new NextRequest('http://localhost/api/build/continue', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body,
    }))
    expect(res.status).toBe(400)
    expect(await res.json()).toEqual({ error: 'chart_id required' })
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('keeps session authentication before reading an invalid body', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const json = vi.fn(() => { throw new Error('body must not be read') })
    const res = await POST({ json } as unknown as NextRequest)
    expect(res.status).toBe(401)
    expect(await res.json()).toEqual({ error: 'unauthenticated' })
    expect(json).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })
})
