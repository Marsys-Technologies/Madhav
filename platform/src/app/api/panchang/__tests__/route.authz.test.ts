/**
 * Cross-tenant PII disclosure on POST /api/panchang (and its ICS sibling).
 *
 * Same defect family as B-001/B-007/B-008/V3-E-010/V3-E-011: a caller-supplied
 * `chart_id` trusted after only "is anyone logged in". This one is sharper than
 * most, because what leaks is birth data rather than build metadata, and because
 * the component that reads the chart says in its own docstring that somebody
 * else is enforcing:
 *
 *   platform/python-sidecar/routers/panchang.py::_fetch_native_context
 *     "Security: caller must already have confirmed chart access (auth is
 *      enforced at the Next.js proxy layer; the sidecar trusts the proxy's
 *      chart_id)."
 *
 * This route IS that proxy. Before this fix it authenticated, forwarded the
 * request body verbatim — `chart_id` included — and returned the sidecar's
 * response verbatim. The sidecar then ran
 * `SELECT name, birth_date, birth_time, birth_lat, birth_lng FROM charts
 *  WHERE id = %s` and attached a `native_context` carrying `native_name`,
 * `birth_nakshatra_name`, `moon_sign_name` and `active_dasha_lord`.
 *
 * Confirmed LIVE against production before the fix: an authenticated guest
 * holding exactly one `chart_grants` row — on a DIFFERENT chart — POSTed the
 * native's real chart_id and received HTTP 200 with that chart's real
 * `native_name`, `birth_nakshatra_name` and `moon_sign_name`.
 *
 * `chart_id` is optional on this endpoint: without one the response is a
 * location-only panchang with no `native_context`, which is public-safe and
 * must keep working for any authenticated caller.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

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

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const ATTACKER_UID = 'attacker-uid'

/** Sentinel standing in for the victim's birth data. Must never reach a denied caller. */
const VICTIM_PII = 'VICTIM-NATIVE-NAME'

function req(body: unknown): Request {
  return new Request('http://localhost/api/panchang', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const basePayload = { date: '2026-08-28', lat: 20.2961, lon: 85.8245, tz_offset_minutes: 330 }

beforeEach(() => {
  vi.clearAllMocks()
  process.env.PYTHON_SIDECAR_URL = 'http://sidecar.invalid'
  mockGetServerUser.mockResolvedValue({ uid: ATTACKER_UID })
  // The sidecar WILL hand back the victim's birth data if it is ever called —
  // that is the whole point. The fix must prevent the call, not sanitise it.
  mockFetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      ok: true,
      panchang: { tithi: 'Shukla Tritiya' },
      native_context: {
        chart_id: VICTIM_CHART,
        native_name: VICTIM_PII,
        birth_nakshatra_name: 'Purva Bhadrapada',
        moon_sign_name: 'Kumbha',
      },
    }),
  })
  vi.stubGlobal('fetch', mockFetch)
})

describe('POST /api/panchang — cross-tenant native_context disclosure', () => {
  it('DENIES a caller with no permission on the requested chart', async () => {
    mockRequireChartPermission.mockResolvedValue(
      new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 })
    )
    const res = await POST(req({ ...basePayload, chart_id: VICTIM_CHART }))
    expect(res.status).toBe(403)
  })

  it('leaks NO birth data to a denied caller', async () => {
    mockRequireChartPermission.mockResolvedValue(
      new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 })
    )
    const res = await POST(req({ ...basePayload, chart_id: VICTIM_CHART }))
    const body = await res.text()
    expect(body).not.toContain(VICTIM_PII)
    expect(body).not.toContain('Purva Bhadrapada')
    expect(body).not.toContain('Kumbha')
  })

  it('never even CALLS the sidecar for a denied caller', async () => {
    mockRequireChartPermission.mockResolvedValue(
      new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 })
    )
    await POST(req({ ...basePayload, chart_id: VICTIM_CHART }))
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('checks permission at READ level against the caller-supplied chart_id', async () => {
    mockRequireChartPermission.mockResolvedValue(null)
    await POST(req({ ...basePayload, chart_id: VICTIM_CHART }))
    expect(mockRequireChartPermission).toHaveBeenCalledWith(
      expect.objectContaining({ uid: ATTACKER_UID, chartId: VICTIM_CHART, access: 'read' })
    )
  })

  it('ALLOWS an authorized caller — the legitimate personalised path still works', async () => {
    mockRequireChartPermission.mockResolvedValue(null)
    const res = await POST(req({ ...basePayload, chart_id: VICTIM_CHART }))
    expect(res.status).toBe(200)
    expect(JSON.stringify(await res.json())).toContain(VICTIM_PII)
  })

  it('ALLOWS a chart_id-less request without any authorization check — public-safe path', async () => {
    const res = await POST(req(basePayload))
    expect(res.status).toBe(200)
    expect(mockRequireChartPermission).not.toHaveBeenCalled()
    expect(mockFetch).toHaveBeenCalled()
  })

  it('DENIES an unauthenticated caller outright', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await POST(req({ ...basePayload, chart_id: VICTIM_CHART }))
    expect(res.status).toBe(401)
    expect(mockFetch).not.toHaveBeenCalled()
  })
})
