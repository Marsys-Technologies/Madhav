import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockGetServerUser, mockRequireChartPermission, mockFetch } = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockRequireChartPermission: vi.fn(),
  mockFetch: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/auth/requireChartPermission', () => ({
  requireChartPermission: mockRequireChartPermission,
}))

import { POST } from '../route'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const BASE_PAYLOAD = {
  event: 'vivah',
  date_from: '2027-01-01',
  date_to: '2027-01-31',
  lat: 20.27,
  lon: 85.84,
  tz_offset_minutes: 330,
  top_n: 10,
}

function req(body: unknown): Request {
  return new Request('http://localhost/api/compute/muhurat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.PYTHON_SIDECAR_URL = 'http://sidecar.invalid'
  mockGetServerUser.mockResolvedValue({ uid: 'caller-uid' })
  mockRequireChartPermission.mockResolvedValue(null)
  mockFetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ ok: true, count: 0, windows: [] }),
  })
  vi.stubGlobal('fetch', mockFetch)
})

describe('POST /api/compute/muhurat chart authorization', () => {
  it('denies a chart-scoped request before contacting the sidecar', async () => {
    mockRequireChartPermission.mockResolvedValue(
      new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 }),
    )

    const response = await POST(req({ ...BASE_PAYLOAD, chart_id: CHART_ID }))

    expect(response.status).toBe(403)
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('checks read permission for the requested chart', async () => {
    await POST(req({ ...BASE_PAYLOAD, chart_id: CHART_ID }))

    expect(mockRequireChartPermission).toHaveBeenCalledWith({
      uid: 'caller-uid',
      chartId: CHART_ID,
      access: 'read',
    })
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('allows a chart-less location search without a chart permission query', async () => {
    const response = await POST(req(BASE_PAYLOAD))

    expect(response.status).toBe(200)
    expect(mockRequireChartPermission).not.toHaveBeenCalled()
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('treats an explicit null chart_id as a chart-less search', async () => {
    const response = await POST(req({ ...BASE_PAYLOAD, chart_id: null }))

    expect(response.status).toBe(200)
    expect(mockRequireChartPermission).not.toHaveBeenCalled()
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it.each([123, [], {}, ''])('rejects malformed chart_id %j', async (chartId) => {
    const response = await POST(req({ ...BASE_PAYLOAD, chart_id: chartId }))

    expect(response.status).toBe(400)
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('rejects an unauthenticated request before permission or sidecar access', async () => {
    mockGetServerUser.mockResolvedValue(null)

    const response = await POST(req({ ...BASE_PAYLOAD, chart_id: CHART_ID }))

    expect(response.status).toBe(401)
    expect(mockRequireChartPermission).not.toHaveBeenCalled()
    expect(mockFetch).not.toHaveBeenCalled()
  })
})
