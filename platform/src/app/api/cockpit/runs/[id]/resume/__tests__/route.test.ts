import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const mockQuery = vi.fn()
const mockGetServerUser = vi.fn()
const mockInvokeRunJob = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))

const request = new NextRequest('http://localhost/api/cockpit/runs/run-1/resume', { method: 'POST' })
const context = { params: Promise.resolve({ id: 'run-1' }) }

beforeEach(() => {
  vi.clearAllMocks()
  mockGetServerUser.mockResolvedValue({ uid: 'admin-1' })
  mockQuery.mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
})

describe('POST /api/cockpit/runs/[id]/resume', () => {
  it('dispatches exactly the atomically claimed paused run', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ id: 'run-1', state: 'planned' }] })
    mockInvokeRunJob.mockResolvedValue(undefined)

    const { POST } = await import('../route')
    const res = await POST(request, context)

    expect(res.status).toBe(200)
    expect((await res.json()).data).toEqual({ run_id: 'run-1', resumed: true })
    expect(mockInvokeRunJob).toHaveBeenCalledTimes(1)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1')
  })

  it('claims paused work, invokes its job, and does not report it resumed when dispatch fails', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ id: 'run-1', state: 'planned' }] })
      .mockResolvedValueOnce({ rows: [{ id: 'run-1' }] })
    mockInvokeRunJob.mockRejectedValue(new Error('Cloud Run unavailable'))

    const { POST } = await import('../route')
    const res = await POST(request, context)

    expect(res.status).toBe(503)
    expect((await res.json()).code).toBe('JOB_DISPATCH_FAILED')
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1')
    expect(String(mockQuery.mock.calls[1][0])).toContain("state = 'planned'")
    expect(String(mockQuery.mock.calls[2][0])).toContain("state = 'paused'")
  })

  it('rejects a competing resume attempt without invoking another job', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ state: 'running', has_manifest: true }] })

    const { POST } = await import('../route')
    const res = await POST(request, context)

    expect(res.status).toBe(404)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('rejects a legacy paused run that has no immutable manifest', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ state: 'paused', has_manifest: false }] })

    const { POST } = await import('../route')
    const res = await POST(request, context)

    expect(res.status).toBe(409)
    expect((await res.json()).code).toBe('LEGACY_RUN_MANIFEST_MISSING')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })
})
