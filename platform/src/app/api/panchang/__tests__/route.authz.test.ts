import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockGetServerUser, mockGetPrincipalRole, mockResolveNativeContext, mockFetch } = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockGetPrincipalRole: vi.fn(),
  mockResolveNativeContext: vi.fn(),
  mockFetch: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ getPrincipalRole: mockGetPrincipalRole }))
vi.mock('@/lib/panchang/resolveNativeContext', () => ({ resolveNativeContext: mockResolveNativeContext }))

import { POST } from '../route'

const CHART = '00000000-0000-4000-8000-000000000001'
const USER = 'fixture-browser-user'
const CALENDAR_REQUEST = { date: '2026-08-28', lat: 20.2961, lon: 85.8245, tz_offset_minutes: 330 }
const CALENDAR = {
  ok: true,
  panchang: { tithi: 'Fixture tithi' },
  native_context: null,
  native_context_error: null,
  cache_hit: false,
}
const UNAVAILABLE = { native_context: null, native_context_error: 'Chart overlay unavailable' }
const LEGACY_CONTEXT = { native_name: 'Legacy sidecar context', chart_id: 'legacy-chart' }
const STORED_CONTEXT = {
  chart_id: CHART,
  native_name: 'Fixture chart',
  ayanamsha_id: 'raman',
  birth_nakshatra_id: 3,
  birth_nakshatra_name: 'Krittika',
  moon_sign_id: 2,
  moon_sign_name: 'Vrishabha',
  active_dasha_lord: null,
  fact_ids: {
    birth_nakshatra_id: 'fixture-nakshatra-id',
    birth_nakshatra_name: 'fixture-nakshatra-name',
    moon_sign_id: 'fixture-moon-id',
    moon_sign_name: 'fixture-moon-name',
  },
}

function req(body: unknown): Request {
  return new Request('http://localhost/api/panchang', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function expectNoOverlayRead() {
  expect(mockGetPrincipalRole).not.toHaveBeenCalled()
  expect(mockResolveNativeContext).not.toHaveBeenCalled()
}

beforeEach(() => {
  vi.resetAllMocks()
  vi.stubEnv('PYTHON_SIDECAR_URL', 'http://sidecar.invalid')
  mockGetServerUser.mockResolvedValue({ uid: USER })
  mockGetPrincipalRole.mockResolvedValue('guest')
  mockResolveNativeContext.mockResolvedValue(UNAVAILABLE)
  mockFetch.mockImplementation(async () => Response.json(CALENDAR))
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('POST /api/panchang', () => {
  it.each([undefined, null])('preserves chartless calendar response for chart_id %j', async (chart_id) => {
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id }))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual(CALENDAR)
    expect(mockFetch).toHaveBeenCalledOnce()
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toEqual(CALENDAR_REQUEST)
    expectNoOverlayRead()
  })

  it('preserves a chartless response with an older calendar envelope', async () => {
    const legacyCalendar = { ok: true, panchang: CALENDAR.panchang }
    mockFetch.mockResolvedValueOnce(Response.json(legacyCalendar))
    const response = await POST(req(CALENDAR_REQUEST))
    expect(await response.json()).toEqual(legacyCalendar)
    expectNoOverlayRead()
  })

  it('sends only calendar parameters and omits available stored context', async () => {
    mockFetch.mockResolvedValueOnce(Response.json({ ...CALENDAR, native_context: LEGACY_CONTEXT }))
    mockResolveNativeContext.mockResolvedValueOnce({ native_context: STORED_CONTEXT, native_context_error: null })
    const fields = ['tithi']
    const response = await POST(req({
      ...CALENDAR_REQUEST,
      fields,
      chart_id: CHART,
      ayanamsha_id: 'RAMAN',
      uid: 'other-user',
      role: 'super_admin',
      principal: { uid: 'other-user', role: 'super_admin' },
      birth_details: { name: 'Unrelated request data' },
    }))

    expect(response.status).toBe(200)
    expect(mockFetch).toHaveBeenCalledOnce()
    expect(mockFetch.mock.calls[0][0]).toBe('http://sidecar.invalid/api/compute/panchanga')
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toEqual({ ...CALENDAR_REQUEST, fields })
    expect(await response.json()).toEqual({ ...CALENDAR, ...UNAVAILABLE })
    expectNoOverlayRead()
  })

  it('preserves the calendar for an older chart request without a frame', async () => {
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ ...CALENDAR, ...UNAVAILABLE })
    expectNoOverlayRead()
  })

  it.each([
    ['denied', CHART],
    ['unknown', '00000000-0000-4000-8000-000000000002'],
    ['incomplete', '00000000-0000-4000-8000-000000000003'],
  ])('returns the same calendar and generic overlay result for %s chart context', async (_case, chartId) => {
    mockFetch.mockResolvedValueOnce(Response.json({
      ...CALENDAR,
      native_context: LEGACY_CONTEXT,
      native_context_error: 'Legacy private detail',
    }))
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: chartId }))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ ...CALENDAR, ...UNAVAILABLE })
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toEqual(CALENDAR_REQUEST)
    expectNoOverlayRead()
  })

  it('drops legacy context from a chartless response without looking up chart data', async () => {
    mockFetch.mockResolvedValueOnce(Response.json({
      ...CALENDAR,
      native_context: LEGACY_CONTEXT,
      native_context_error: 'Legacy private detail',
    }))
    const response = await POST(req(CALENDAR_REQUEST))
    expect(await response.json()).toEqual(CALENDAR)
    expectNoOverlayRead()
  })

  it('keeps the calendar available without consulting an unavailable identity store', async () => {
    mockGetPrincipalRole.mockRejectedValueOnce(new Error('Private identity-store detail'))
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ ...CALENDAR, ...UNAVAILABLE })
    expectNoOverlayRead()
  })

  it.each([12345, [CHART], { chart_id: CHART }, '', '   '].map((chart_id) => ({ chart_id })))(
    'refuses malformed chart_id %j before sidecar or overlay reads',
    async ({ chart_id }) => {
      const response = await POST(req({ ...CALENDAR_REQUEST, chart_id }))
      expect(response.status).toBe(400)
      expect(mockFetch).not.toHaveBeenCalled()
      expectNoOverlayRead()
    },
  )

  it.each([{ lat: { chart_id: CHART } }, { fields: [{ chart_id: CHART }] }])('refuses nested calendar input %j without forwarding it', async (input) => {
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART, ...input }))
    expect(response.status).toBe(500)
    expect(mockFetch).not.toHaveBeenCalled()
    expectNoOverlayRead()
  })

  it('refuses unauthenticated callers before either read', async () => {
    mockGetServerUser.mockResolvedValueOnce(null)
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(response.status).toBe(401)
    expect(mockFetch).not.toHaveBeenCalled()
    expectNoOverlayRead()
  })

  it.each([[422, 500], [500, 503], [503, 503]])('maps sidecar HTTP %i to %i without an overlay read', async (sidecarStatus, routeStatus) => {
    mockFetch.mockResolvedValueOnce(Response.json({ detail: 'Fixture error' }, { status: sidecarStatus }))
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(response.status).toBe(routeStatus)
    expectNoOverlayRead()
  })

  it('preserves service unavailability on a transport failure without an overlay read', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Fixture transport failure'))
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(response.status).toBe(503)
    expectNoOverlayRead()
  })

  it('reports a malformed sidecar response without an overlay read', async () => {
    mockFetch.mockResolvedValueOnce(new Response('malformed JSON'))
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(response.status).toBe(500)
    expectNoOverlayRead()
  })

  it('does not load overlay context from an unsuccessful calendar envelope', async () => {
    const failedCalendar = { ok: false, panchang: null }
    mockFetch.mockResolvedValueOnce(Response.json(failedCalendar))
    const response = await POST(req({ ...CALENDAR_REQUEST, chart_id: CHART }))
    expect(await response.json()).toEqual(failedCalendar)
    expectNoOverlayRead()
  })
})
