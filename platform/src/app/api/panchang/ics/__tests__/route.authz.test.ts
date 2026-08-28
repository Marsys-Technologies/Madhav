/**
 * Sibling of the POST /api/panchang cross-tenant disclosure guard.
 *
 * `GET /api/panchang/ics?chart_id=…` is the second Next.js proxy in front of
 * the sidecar's `/api/compute/panchanga`, and it had the same defect: it
 * authenticated, forwarded a caller-supplied `chart_id` to the sidecar, and
 * the sidecar attached the chart's `native_context` (native_name,
 * birth_nakshatra_name, moon_sign_name) on the strength of the proxy having
 * supposedly authorized it.
 *
 * This one is currently CONTAINED — `ics_builder.ts` never renders
 * `native_context`, so the calendar body discloses nothing today. It is
 * nonetheless the designated enforcement point and does not enforce, so it is
 * one refactor away from live. Guarding it now costs nothing and removes the
 * dependency on a downstream renderer's incidental silence.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockGetServerUser, mockRequireChartPermission, mockFetch } = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockRequireChartPermission: vi.fn(),
  mockFetch: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/auth/requireChartPermission', () => ({
  requireChartPermission: mockRequireChartPermission,
}))

import { GET } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const ATTACKER_UID = 'attacker-uid'

function req(qs: string): NextRequest {
  return new NextRequest(`http://localhost/api/panchang/ics?${qs}`, { method: 'GET' })
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.PYTHON_SIDECAR_URL = 'http://sidecar.invalid'
  mockGetServerUser.mockResolvedValue({ uid: ATTACKER_UID })
  mockFetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ ok: true, panchang: { tithi: 'Shukla Tritiya' } }),
  })
  vi.stubGlobal('fetch', mockFetch)
})

describe('GET /api/panchang/ics — cross-tenant chart_id guard', () => {
  it('DENIES a caller with no permission on the requested chart', async () => {
    mockRequireChartPermission.mockResolvedValue(
      new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 })
    )
    const res = await GET(req(`d=2026-08-28&chart_id=${VICTIM_CHART}`))
    expect(res.status).toBe(403)
  })

  it('never CALLS the sidecar for a denied caller', async () => {
    mockRequireChartPermission.mockResolvedValue(
      new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 })
    )
    await GET(req(`d=2026-08-28&chart_id=${VICTIM_CHART}`))
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('checks permission at READ level against the caller-supplied chart_id', async () => {
    mockRequireChartPermission.mockResolvedValue(null)
    await GET(req(`d=2026-08-28&chart_id=${VICTIM_CHART}`))
    expect(mockRequireChartPermission).toHaveBeenCalledWith(
      expect.objectContaining({ uid: ATTACKER_UID, chartId: VICTIM_CHART, access: 'read' })
    )
  })

  it('ALLOWS a chart_id-less request with no authorization check — public-safe path', async () => {
    const res = await GET(req('d=2026-08-28'))
    expect(mockRequireChartPermission).not.toHaveBeenCalled()
    expect(res.status).toBe(200)
  })

  it('DENIES an unauthenticated caller outright', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(req(`d=2026-08-28&chart_id=${VICTIM_CHART}`))
    expect(res.status).toBe(401)
    expect(mockFetch).not.toHaveBeenCalled()
  })
})
