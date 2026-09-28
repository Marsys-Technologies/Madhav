/**
 * PATCH /api/charts/[id] — computation-safe birthplace edits end to end through
 * the real correction service (Jātaka Phase-A hardening, item 4). A new place
 * that keeps the former coordinates is a 422 naming the fields to reselect,
 * refused inside the transaction with no mutation and no dispatch.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

vi.mock('server-only', () => ({}))

const { statements, mockDispatch } = vi.hoisted(() => ({ statements: [] as string[], mockDispatch: vi.fn() }))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: vi.fn(async () => null) }))
vi.mock('@/lib/build/runDispatch', () => ({ dispatchPreparedRun: mockDispatch }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
  getPool: vi.fn(async () => ({
    connect: async () => ({
      query: vi.fn(async (sql: string) => {
        statements.push(sql)
        if (/FROM charts[\s\S]*FOR UPDATE/.test(sql)) {
          return {
            rows: [{
              id: 'c1', name: 'N', preferred_name: null, subject_name: null, birth_date: '1984-02-05',
              birth_time: '10:43:00', birth_place: 'Bhubaneswar', birth_lat: 20.2961, birth_lng: 85.8245,
              timezone_id: 'Asia/Kolkata', ayanamsa: 'lahiri', owner_id: 'owner-uid', client_id: 'owner-uid',
            }],
          }
        }
        return { rows: [] }
      }),
      release: vi.fn(),
    }),
  })),
}))

import { PATCH } from '../route'

const BODY = {
  name: 'N', preferred_name: null, subject_name: null, birth_date: '1984-02-05', birth_time: '10:43',
  birth_place: 'Bhubaneswar', lat: 20.2961, lon: 85.8245, timezone_id: 'Asia/Kolkata', tz_offset: 5.5, ayanamshas: ['lahiri'],
}

function patch(body: object) {
  return new NextRequest('http://localhost/api/charts/c1', {
    method: 'PATCH',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  statements.length = 0
  mockDispatch.mockReset()
})

describe('PATCH /api/charts/[id] — birthplace safety', () => {
  it('422 VALIDATION_FAILED when the place changes but the coordinates do not', async () => {
    const res = await PATCH(patch({ ...BODY, birth_place: 'Cuttack' }), { params: Promise.resolve({ id: 'c1' }) })
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('VALIDATION_FAILED')
    expect(Object.keys(body.fields).sort()).toEqual(['birth_place', 'lat', 'lon'])
    expect(statements.some((s) => /^\s*(UPDATE|INSERT|DELETE)/i.test(s))).toBe(false)
    expect(statements).toContain('ROLLBACK')
    expect(mockDispatch).not.toHaveBeenCalled()
  })

  it('422 on timezone_id when a new place keeps the former place\'s timezone', async () => {
    const res = await PATCH(
      patch({ ...BODY, birth_place: 'New York, USA', lat: 40.7128, lon: -74.006, timezone_id: 'Asia/Kolkata' }),
      { params: Promise.resolve({ id: 'c1' }) },
    )
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('VALIDATION_FAILED')
    expect(Object.keys(body.fields)).toEqual(['timezone_id'])
    expect(statements.some((s) => /^\s*(UPDATE|INSERT|DELETE)/i.test(s))).toBe(false)
    expect(statements).toContain('ROLLBACK')
    expect(mockDispatch).not.toHaveBeenCalled()
  })

  it('a display-only rename is unaffected', async () => {
    const res = await PATCH(patch({ ...BODY, name: 'Renamed' }), { params: Promise.resolve({ id: 'c1' }) })
    expect(res.status).toBe(200)
    expect((await res.json()).data.mode).toBe('display-only')
  })
})
