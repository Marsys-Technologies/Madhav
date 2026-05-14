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

const MOCK_AUTH = { user: { uid: 'admin1' }, profile: { role: 'super_admin', status: 'active' } }

function makeParams(stack: string, call_type: string, param: string) {
  return { params: Promise.resolve({ stack, call_type, param }) }
}

function makePutRequest(body: unknown): Request {
  return new Request('http://localhost', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('PUT /api/admin/aiops/params/[stack]/[call_type]/[param]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
    mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('returns 403 when unauthenticated', async () => {
    mockRequireSuperAdmin.mockResolvedValue(NextResponse.json({}, { status: 403 }))
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ param_value: 0.5 }), makeParams('gemini', 'synthesis', 'temperature'))
    expect(res.status).toBe(403)
  })

  it('returns 400 for unknown param name', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ param_value: 42 }), makeParams('gemini', 'synthesis', 'unknown_param'))
    expect(res.status).toBe(400)
  })

  it('returns 400 for unknown stack', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ param_value: 0.5 }), makeParams('bad_stack', 'synthesis', 'temperature'))
    expect(res.status).toBe(400)
  })

  it('returns 200 on valid param update', async () => {
    const { PUT } = await import('../route')
    const res = await PUT(makePutRequest({ param_value: 0.2 }), makeParams('gemini', 'synthesis', 'temperature'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.param_name).toBe('temperature')
    expect(body.param_value).toBe(0.2)
  })

  it('calls invalidateRuntimeConfigCache', async () => {
    const { PUT } = await import('../route')
    await PUT(makePutRequest({ param_value: 4096 }), makeParams('gemini', 'synthesis', 'max_output_tokens'))
    expect(mockInvalidate).toHaveBeenCalled()
  })
})

describe('DELETE /api/admin/aiops/params/[stack]/[call_type]/[param]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
    mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('returns 400 for unknown param', async () => {
    const { DELETE } = await import('../route')
    const res = await DELETE(new Request('http://localhost', { method: 'DELETE' }), makeParams('gemini', 'synthesis', 'bad_param'))
    expect(res.status).toBe(400)
  })

  it('returns 200 with default source on valid reset', async () => {
    const { DELETE } = await import('../route')
    const res = await DELETE(new Request('http://localhost', { method: 'DELETE' }), makeParams('gemini', 'synthesis', 'temperature'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.source).toBe('default')
    expect(body.param_name).toBe('temperature')
  })

  it('calls invalidateRuntimeConfigCache', async () => {
    const { DELETE } = await import('../route')
    await DELETE(new Request('http://localhost', { method: 'DELETE' }), makeParams('gemini', 'synthesis', 'temperature'))
    expect(mockInvalidate).toHaveBeenCalled()
  })
})
