import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'
import { createHash } from 'crypto'

const { mockQuery, mockGetPool, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetPool: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST as EXECUTE } from '../execute/route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OWNER_UID = 'owner-uid'
const OTHER_UID = 'other-uid'

function previewHash(scope: string, scopeTarget: string | null, affected: string[]): string {
  const timeSlot = Math.floor(Date.now() / (15 * 60 * 1000))
  return createHash('sha256')
    .update(JSON.stringify({ chart_id: CHART, scope, scope_target: scopeTarget, affectedAssetIds: [...affected].sort(), timeSlot }))
    .digest('hex')
    .slice(0, 32)
}

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/clear/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('NIR-05 POST /api/cockpit/clear/execute — restricted-role fail-closed & rollback', () => {
  beforeEach(() => vi.clearAllMocks())

  it('denies view-grantee on preparation layer clear before touching pool or issuing any DELETE', async () => {
    mockGetServerUser.mockResolvedValue({ uid: OTHER_UID })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
      if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
      if (/FROM chart_grants/.test(sql)) return Promise.resolve({ rows: [{ permission: 'view' }], rowCount: 1 })
      return Promise.resolve({ rows: [], rowCount: 0 })
    })

    const res = await EXECUTE(makeReq({
      chart_id: CHART,
      scope: 'layer',
      scope_target: 'ganita',
      preview_hash: previewHash('layer', 'ganita', ['ga_positions']),
    }))
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_CHART')
    expect(mockGetPool).not.toHaveBeenCalled()
  })

  it('denies non-super-admin brahmagyan clear before opening transaction', async () => {
    mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'client' }], rowCount: 1 })
      if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
      return Promise.resolve({ rows: [], rowCount: 0 })
    })

    const res = await EXECUTE(makeReq({
      chart_id: CHART,
      scope: 'layer',
      scope_target: 'brahmagyan',
      preview_hash: previewHash('layer', 'brahmagyan', ['bg_ephemeris']),
    }))
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_L0')
    expect(mockGetPool).not.toHaveBeenCalled()
  })

  it('rolls back open transaction before returning 500 on INVALID_TABLE target_table fallback', async () => {
    mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'client' }], rowCount: 1 })
      if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
      if (/FROM asset_registry/.test(sql)) {
        return Promise.resolve({
          rows: [{
            asset_id: 'ga_bad_table',
            layer: 'ganita',
            depends_on: [],
            estimated_seconds: 10,
            scope: 'per_chart',
            target_table: 'bad;DROP TABLE charts',
            count_sql: null,
            is_active: true,
          }],
          rowCount: 1,
        })
      }
      if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
      return Promise.resolve({ rows: [], rowCount: 0 })
    })

    const clientQueries: string[] = []
    const release = vi.fn()
    mockGetPool.mockResolvedValue({
      connect: vi.fn().mockResolvedValue({
        query: vi.fn((sql: string) => {
          clientQueries.push(sql)
          return Promise.resolve({ rows: [], rowCount: 0 })
        }),
        release,
      }),
    })

    const res = await EXECUTE(makeReq({
      chart_id: CHART,
      scope: 'layer',
      scope_target: 'ganita',
      preview_hash: previewHash('layer', 'ganita', ['ga_bad_table']),
    }))
    expect(res.status).toBe(500)
    expect((await res.json()).code).toBe('INVALID_TABLE')
    expect(clientQueries).toContain('BEGIN')
    expect(clientQueries).toContain('ROLLBACK')
    expect(clientQueries).not.toContain('COMMIT')
    expect(release).toHaveBeenCalledTimes(1)
  })
})
