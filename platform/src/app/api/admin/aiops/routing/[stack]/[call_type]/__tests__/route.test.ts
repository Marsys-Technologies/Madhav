import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const { mockRequireSuperAdmin, mockQuery, mockInvalidate } = vi.hoisted(() => ({
  mockRequireSuperAdmin: vi.fn(),
  mockQuery:             vi.fn(),
  mockInvalidate:        vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: mockRequireSuperAdmin }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/models/runtime_config', () => ({ invalidateRuntimeConfigCache: mockInvalidate }))
vi.mock('@/lib/models/registry', async () => {
  const actual = await vi.importActual<typeof import('@/lib/models/registry')>('@/lib/models/registry')
  return {
    ...actual,
    STACK_ROUTING: {
      gemini: { synthesis: { primary: 'gemini-2.5-pro', fallback: 'gemini-2.0-flash' } },
    },
  }
})

const MOCK_AUTH = { user: { uid: 'admin1' }, profile: { role: 'super_admin', status: 'active' } }

function makeParams(stack: string, call_type: string) {
  return { params: { stack, call_type } }
}

function makePutRequest(body: unknown): Request {
  return new Request('http://localhost', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('PUT /api/admin/aiops/routing/[stack]/[call_type]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
    mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('returns 403 when unauthenticated', async () => {
    mockRequireSuperAdmin.mockResolvedValue(NextResponse.json({}, { status: 403 }))
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ primary_model: 'a', fallback_model: 'b' }), makeParams('gemini', 'synthesis'))
    expect(res.status).toBe(403)
  })

  it('returns 400 for unknown stack', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ primary_model: 'a', fallback_model: 'b' }), makeParams('unknown', 'synthesis'))
    expect(res.status).toBe(400)
  })

  it('returns 400 for unknown call_type', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ primary_model: 'a', fallback_model: 'b' }), makeParams('gemini', 'bad_type'))
    expect(res.status).toBe(400)
  })

  it('returns 200 and writes routing on valid input', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(
      makePutRequest({ primary_model: 'gemini-exp', fallback_model: 'gemini-2.0-flash' }),
      makeParams('gemini', 'synthesis'),
    )
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.primary_model).toBe('gemini-exp')
    expect(body.call_type).toBe('synthesis')
  })

  it('calls invalidateRuntimeConfigCache', async () => {
    const { PUT } = await import('../route')
    await PUT(makePutRequest({ primary_model: 'a', fallback_model: 'b' }), makeParams('gemini', 'synthesis'))
    expect(mockInvalidate).toHaveBeenCalled()
  })
})

describe('DELETE /api/admin/aiops/routing/[stack]/[call_type]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
    mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('returns 400 for unknown call_type', async () => {
    const { DELETE } = await import('../route')
    const res = await DELETE(new Request('http://localhost', { method: 'DELETE' }), makeParams('gemini', 'bad_type'))
    expect(res.status).toBe(400)
  })

  it('returns 200 with registry source on valid reset', async () => {
    const { DELETE } = await import('../route')
    const res = await DELETE(new Request('http://localhost', { method: 'DELETE' }), makeParams('gemini', 'synthesis'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.source).toBe('registry')
  })

  it('calls invalidateRuntimeConfigCache on reset', async () => {
    const { DELETE } = await import('../route')
    await DELETE(new Request('http://localhost', { method: 'DELETE' }), makeParams('gemini', 'synthesis'))
    expect(mockInvalidate).toHaveBeenCalled()
  })
})
