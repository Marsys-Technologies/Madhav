/**
 * PATCH /api/charts/[id] — chart-details correction (Jātaka chart workspace, Task 7).
 *
 * HTTP contract over updateChartAndMaybeRecompute: authentication, write
 * authority through requireChartPermission (non-enumerating 403), structured
 * error codes, and status per result mode. No stack traces or SQL leak out.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const { mockGetServerUser, mockRequirePermission, mockUpdate } = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockRequirePermission: vi.fn(),
  mockUpdate: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(), getPool: vi.fn() }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: mockRequirePermission }))
vi.mock('@/lib/charts/recomputeChart', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/charts/recomputeChart')>()),
  updateChartAndMaybeRecompute: mockUpdate,
}))

import { PATCH } from '../route'
import { ChartUpdateError } from '@/lib/charts/recomputeChart'

const CHART = '482012f1-0000-4000-8000-000000000001'
const ctx = { params: Promise.resolve({ id: CHART }) }

function req(body: unknown, raw = false) {
  return new NextRequest(`http://localhost/api/charts/${CHART}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: raw ? (body as string) : JSON.stringify(body),
  })
}

const BODY = { name: 'Test' }

beforeEach(() => {
  vi.clearAllMocks()
  mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
  mockRequirePermission.mockResolvedValue(null)
})

describe('PATCH /api/charts/[id] — authority', () => {
  it('401 UNAUTHENTICATED without a session, and no mutation', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(401)
    expect(await res.json()).toEqual({ error: 'Authentication required', code: 'UNAUTHENTICATED' })
    expect(mockUpdate).not.toHaveBeenCalled()
  })

  it('requires write authority through the shared permission helper', async () => {
    await PATCH(req(BODY), ctx)
    expect(mockRequirePermission).toHaveBeenCalledWith({ uid: 'owner-uid', chartId: CHART, access: 'write' })
  })

  it('403 FORBIDDEN_CHART for view grants, unrelated callers and absent charts — no mutation', async () => {
    mockRequirePermission.mockResolvedValue(NextResponse.json({ error: 'Forbidden', code: 'FORBIDDEN_CHART' }, { status: 403 }))
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_CHART')
    expect(mockUpdate).not.toHaveBeenCalled()
  })
})

describe('PATCH /api/charts/[id] — results', () => {
  it('200 for a no-op', async () => {
    mockUpdate.mockResolvedValue({ mode: 'noop', chartId: CHART, changedFields: [] })
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ data: { mode: 'noop', chartId: CHART, changedFields: [] } })
  })

  it('200 for a display-only edit', async () => {
    mockUpdate.mockResolvedValue({ mode: 'display-only', chartId: CHART, changedFields: ['name'] })
    expect((await PATCH(req(BODY), ctx)).status).toBe(200)
    expect(mockUpdate).toHaveBeenCalledWith({ chartId: CHART, principalId: 'owner-uid', input: BODY })
  })

  it('202 when a recompute started', async () => {
    mockUpdate.mockResolvedValue({ mode: 'recompute-started', chartId: CHART, changedFields: ['birth_time'], runId: 'run-1' })
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(202)
    expect((await res.json()).data.runId).toBe('run-1')
  })

  it('503 JOB_DISPATCH_FAILED with the committed run when dispatch failed', async () => {
    const result = { mode: 'needs-rebuild', chartId: CHART, changedFields: ['birth_time'], runId: 'run-1', error: 'spawn ENOENT' }
    mockUpdate.mockResolvedValue(result)
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(503)
    expect(await res.json()).toEqual({
      error: 'Chart details were saved, but the rebuild did not start.',
      code: 'JOB_DISPATCH_FAILED',
      data: result,
    })
  })
})

describe('PATCH /api/charts/[id] — structured failures', () => {
  it('422 VALIDATION_FAILED with field errors', async () => {
    mockUpdate.mockRejectedValue(new ChartUpdateError('VALIDATION_FAILED', 'Some chart details are invalid.', { lat: 'Too big' }))
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(422)
    expect(await res.json()).toEqual({ error: 'Some chart details are invalid.', code: 'VALIDATION_FAILED', fields: { lat: 'Too big' } })
  })

  it('422 VALIDATION_FAILED for a malformed JSON body, without calling the service', async () => {
    const res = await PATCH(req('{not json', true), ctx)
    expect(res.status).toBe(422)
    expect((await res.json()).code).toBe('VALIDATION_FAILED')
    expect(mockUpdate).not.toHaveBeenCalled()
  })

  it.each([
    ['RUN_ACTIVE', 409],
    ['PROTECTED', 422],
    ['INVALID_BUILD_PLAN', 422],
    ['CLEAR_SPEC_MISSING', 422],
    ['CHART_NOT_FOUND', 404],
    ['RECOMPUTE_PREPARATION_FAILED', 500],
  ] as const)('%s → HTTP %i with its code', async (code, status) => {
    mockUpdate.mockRejectedValue(new ChartUpdateError(code, `message for ${code}`))
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(status)
    const body = await res.json()
    expect(body.code).toBe(code)
    expect(body.error).toBe(`message for ${code}`)
  })

  it('an unexpected error is a 500 RECOMPUTE_PREPARATION_FAILED with no internals', async () => {
    mockUpdate.mockRejectedValue(new Error('relation "charts" does not exist at pg/lib/client.js:42'))
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(500)
    const text = await res.text()
    expect(JSON.parse(text).code).toBe('RECOMPUTE_PREPARATION_FAILED')
    expect(text).not.toMatch(/relation|pg\/lib|stack/)
  })
})
