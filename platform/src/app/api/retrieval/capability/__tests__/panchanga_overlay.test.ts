import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { callPanchangaServiceCapability } from '@/lib/retrieval/registry/layers/L0_brahmagyan/call_panchanga_service'
import { POST } from '../route'

const { getCapability, verifyIdToken, query, resolveNativeContext, cache, cacheKey } = vi.hoisted(() => ({
  getCapability: vi.fn(),
  verifyIdToken: vi.fn(),
  query: vi.fn(),
  resolveNativeContext: vi.fn(),
  cache: new Map<string, unknown>(),
  cacheKey: vi.fn((surface: string, args: unknown) => JSON.stringify([surface, args])),
}))

vi.mock('@/lib/retrieval/registry', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/lib/retrieval/registry')>(),
  getCapability,
}))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: vi.fn() }))
vi.mock('google-auth-library', async (importOriginal) => ({
  ...await importOriginal<typeof import('google-auth-library')>(),
  OAuth2Client: class {
    verifyIdToken = verifyIdToken
  },
}))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('@/lib/panchang/resolveNativeContext', () => ({ resolveNativeContext }))
vi.mock('@/lib/cache/shared_cache', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/lib/cache/shared_cache')>(),
  buildKey: cacheKey,
  cacheGet: async (_surface: string, key: string) => cache.get(key),
  cacheSet: async (_surface: string, key: string, value: unknown) => { cache.set(key, structuredClone(value)) },
}))

const uri = callPanchangaServiceCapability.uri
const calendarArgs = { date: '2026-05-20', lat: 20.27, lon: 85.84, tz_offset_minutes: 330 }
const audience = 'https://web.fixture.invalid'
const workload = 'named-mcp@fixture.invalid'
const chartA = '11111111-1111-4111-8111-111111111111'
const chartB = '22222222-2222-4222-8222-222222222222'
const privateA = overlay(chartA, 'a')
const privateB = overlay(chartB, 'b')
const unavailable = { native_context: null, native_context_error: 'Chart overlay unavailable' }
const chartless = { native_context: null, native_context_error: null }
const fetchMock = vi.fn<typeof fetch>()
const profiles = new Map<string, { status: string; role: string }>()

function overlay(chartId: string, suffix: string) {
  return {
    native_context: {
      chart_id: chartId,
      native_name: `Synthetic private ${suffix}`,
      birth_nakshatra_id: 8,
      birth_nakshatra_name: 'Fixture star',
      moon_sign_id: 4,
      moon_sign_name: 'Fixture sign',
      active_dasha_lord: null,
      ayanamsha_id: 'true_chitra',
      fact_ids: {
        birth_nakshatra_id: `private-${suffix}-1`,
        birth_nakshatra_name: `private-${suffix}-2`,
        moon_sign_id: `private-${suffix}-3`,
        moon_sign_name: `private-${suffix}-4`,
      },
    },
    native_context_error: null,
  }
}

function makeRequest(args: Record<string, unknown>, {
  user = 'fixture-a', bearer = 'verified', capability = uri, extraHeaders = {},
}: {
  user?: string
  bearer?: string | null
  capability?: string
  extraHeaders?: Record<string, string>
} = {}) {
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'x-mcp-internal-token': 'fixture-internal-token',
    'x-mcp-key-id': 'fixture-key',
    'x-mcp-user': user,
    ...extraHeaders,
  }
  if (bearer) headers.authorization = `Bearer ${bearer}`
  return new Request('https://web.fixture.invalid/api/retrieval/capability', {
    method: 'POST',
    headers,
    body: JSON.stringify({ uri: capability, args }),
  })
}

function sidecarDay() {
  return Response.json({
    panchang: {
      date: calendarArgs.date,
      tithi: { name: 'Public day', number: 1 },
      native_context: privateB.native_context,
      native_context_error: 'stale private marker',
    },
    native_context: privateB.native_context,
  })
}

async function read(req: Request) {
  const response = await POST(req)
  expect(response.status).toBe(200)
  return response.json()
}

function assertNoPrivate(value: unknown) {
  const serialized = JSON.stringify(value)
  expect(serialized).not.toContain('Synthetic private')
  expect(serialized).not.toContain('private-a-')
  expect(serialized).not.toContain('private-b-')
  expect(serialized).not.toContain('stale private marker')
}

beforeEach(() => {
  vi.stubEnv('MCP_INTERNAL_TOKEN', 'fixture-internal-token')
  vi.stubEnv('MCP_CALLER_OIDC_AUDIENCE', audience)
  vi.stubEnv('MCP_CALLER_OIDC_SERVICE_ACCOUNT', workload)
  vi.stubEnv('MCP_CALLER_OIDC_DISABLED_FOR_LOCAL_DEV', undefined)
  vi.stubEnv('MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED', 'true')
  vi.stubEnv('PYTHON_SIDECAR_URL', 'https://sidecar.fixture.invalid')
  vi.stubEnv('PYTHON_SIDECAR_API_KEY', 'fixture-sidecar-token')
  vi.stubGlobal('fetch', fetchMock)
  fetchMock.mockReset().mockImplementation(async () => sidecarDay())
  cache.clear()
  cacheKey.mockClear()
  profiles.clear()
  profiles.set('fixture-a', { status: 'active', role: 'guest' })
  profiles.set('fixture-b', { status: 'active', role: 'super_admin' })
  getCapability.mockReset().mockImplementation((requested) => requested === uri ? callPanchangaServiceCapability : undefined)
  verifyIdToken.mockReset().mockImplementation(async ({ idToken, audience: requestedAudience }) => {
    if (requestedAudience !== audience || idToken === 'wrong-audience' || idToken === 'expired') {
      throw new Error('Synthetic token verification rejected')
    }
    return { getPayload: () => ({ email: idToken === 'wrong-service-account' ? 'other@fixture.invalid' : workload }) }
  })
  query.mockReset().mockImplementation(async (sql, [uid]) => {
    expect(sql).toContain('FROM profiles WHERE id = $1')
    const profile = profiles.get(uid)
    return { rows: profile ? [profile] : [] }
  })
  resolveNativeContext.mockReset().mockImplementation(async ({ chartId }) => chartId === chartA ? privateA : privateB)
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('raw Panchanga calendar-only recovery', () => {
  it('keeps a chartless request neutral and strips unsolicited context from the calendar and cache', async () => {
    const result = await read(makeRequest({ ...calendarArgs, unrelated: { chart_id: chartA } }, {
      extraHeaders: { 'x-mcp-chart-id': chartA },
    }))
    expect(result).toMatchObject({ ok: true, content: {
      is_error: false,
      content: { mode: 'single', panchang: { date: calendarArgs.date, tithi: { name: 'Public day' } }, ...chartless },
    } })
    expect(result.content.content.panchang).not.toHaveProperty('native_context')
    expect(result.content.content.panchang).not.toHaveProperty('native_context_error')
    assertNoPrivate(result)
    assertNoPrivate([...cache.values()])
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })

  it('preserves the calendar for a workload and chart that would qualify for stored facts', async () => {
    const result = await read(makeRequest({
      ...calendarArgs, chart_id: chartA, ayanamsha_id: 'true_chitra', role: 'super_admin',
    }, { extraHeaders: { 'x-mcp-role': 'super_admin', 'x-mcp-chart-id': chartB } }))
    expect(result.content.content).toMatchObject({ panchang: { date: calendarArgs.date }, ...unavailable })
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
    assertNoPrivate(result)
    expect(cacheKey).toHaveBeenCalledWith('mcp-capability', { uri, args: calendarArgs })
    const [url, init] = fetchMock.mock.calls[0] ?? []
    expect(url).toBe('https://sidecar.fixture.invalid/api/compute/panchanga')
    expect(JSON.parse(String(init?.body))).toEqual(calendarArgs)
    assertNoPrivate([...cache.values()])
    expect([...cache.values()][0]).not.toHaveProperty('content.native_context')
  })

  it.each([null, 'wrong-service-account', 'wrong-audience', 'expired'])(
    'serves the same generic calendar for unverified bearer %s without a profile or chart read',
    async (bearer) => {
      const result = await read(makeRequest({ ...calendarArgs, chart_id: chartA }, { bearer }))
      expect(result.content.content).toMatchObject({ panchang: { date: calendarArgs.date }, ...unavailable })
      assertNoPrivate(result)
      expect(verifyIdToken).not.toHaveBeenCalled()
      expect(query).not.toHaveBeenCalled()
      expect(resolveNativeContext).not.toHaveBeenCalled()
    },
  )

  it('keeps the local shared-token bypass calendar-only', async () => {
    vi.stubEnv('MCP_CALLER_OIDC_DISABLED_FOR_LOCAL_DEV', 'true')
    const result = await read(makeRequest({ ...calendarArgs, chart_id: chartA }, { bearer: null }))
    expect(result.content.content).toMatchObject(unavailable)
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })

  it('serves the same warm calendar across available, denied, disabled and unknown principals', async () => {
    const make = () => makeRequest({ ...calendarArgs, chart_id: chartA })
    const first = await read(make())
    expect(first.content.content).toMatchObject({ panchang: { date: calendarArgs.date }, ...unavailable })

    resolveNativeContext.mockResolvedValueOnce(unavailable)
    expect(await read(make())).toEqual(first)
    profiles.set('fixture-a', { status: 'disabled', role: 'super_admin' })
    expect(await read(make())).toEqual(first)
    profiles.delete('fixture-a')
    expect(await read(make())).toEqual(first)

    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    assertNoPrivate([first, ...cache.values()])
  })

  it('keeps the requested frame out of public cache and private reads', async () => {
    const result = await read(makeRequest({ ...calendarArgs, chart_id: chartA, ayanamsha_id: 'raman' }))
    expect(result.content.content).toMatchObject({ panchang: { date: calendarArgs.date }, ...unavailable })
    expect(cacheKey).toHaveBeenCalledWith('mcp-capability', { uri, args: calendarArgs })
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })

  it('removes old context from a pre-existing cache hit without resolving a new overlay', async () => {
    cache.set(cacheKey('mcp-capability', { uri, args: calendarArgs }), {
      is_error: false,
      native_context: privateB.native_context,
      content: { mode: 'single', panchang: { date: calendarArgs.date, ...privateB }, ...privateB },
    })
    const result = await read(makeRequest({ ...calendarArgs, chart_id: chartA }))
    expect(result.content.content).toMatchObject({ panchang: { date: calendarArgs.date }, ...unavailable })
    assertNoPrivate(result)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })

  it('preserves range and calendar failure output without optional chart reads', async () => {
    fetchMock.mockResolvedValueOnce(Response.json({
      panchangs: [{ date: calendarArgs.date, ...privateB }], count: 1,
    })).mockResolvedValueOnce(Response.json({ error: 'Synthetic service error', ...privateB }, { status: 500 }))

    const range = await read(makeRequest({
      mode: 'range', date_from: calendarArgs.date, date_to: calendarArgs.date, chart_id: chartA,
    }))
    expect(range.content).toMatchObject({ is_error: false, content: {
      mode: 'range', panchangs: [{ date: calendarArgs.date }], count: 1,
    } })
    expect(range.content.content).not.toHaveProperty('native_context')
    const failure = await read(makeRequest({ ...calendarArgs, chart_id: chartA }))
    expect(failure.content).toMatchObject({ is_error: true, content: {
      error: 'Sidecar 500', detail: { error: 'Synthetic service error' },
    } })
    assertNoPrivate([range, failure, ...cache.values()])
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })

  it('keeps malformed optional inputs out of public args and chart authority', async () => {
    const result = await read(makeRequest({ ...calendarArgs, chart_id: { chart_id: chartA }, mode: { chart_id: chartB } }))
    expect(result.content.content).toMatchObject(unavailable)
    expect(cacheKey).toHaveBeenCalledWith('mcp-capability', { uri, args: calendarArgs })
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })

  it('coalesces public work across concurrent callers without exposing an overlay', async () => {
    let finishDay!: (value: Response) => void
    fetchMock.mockReturnValueOnce(new Promise((resolve) => { finishDay = resolve }))
    const first = read(makeRequest({ ...calendarArgs, chart_id: chartA }))
    const second = read(makeRequest({ ...calendarArgs, chart_id: chartB }, { user: 'fixture-b' }))
    await vi.waitFor(() => expect(cacheKey).toHaveBeenCalledTimes(2))
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(query).not.toHaveBeenCalled()

    finishDay(sidecarDay())
    const [a, b] = await Promise.all([first, second])
    expect(a.content.content).toMatchObject({ panchang: { date: calendarArgs.date }, ...unavailable })
    expect(b).toEqual(a)
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
    assertNoPrivate([a, b])
    expect(cache.size).toBe(1)
    assertNoPrivate([...cache.values()])
  })

  it('preserves the outer service token and principal header guards', async () => {
    const forbidden = await POST(makeRequest({ ...calendarArgs, chart_id: chartA }, {
      extraHeaders: { 'x-mcp-internal-token': 'fixture-wrong-token' },
    }))
    expect(forbidden.status).toBe(403)
    expect(await forbidden.json()).toEqual({ ok: false, error: 'Forbidden' })
    const missingPrincipal = await POST(makeRequest({ ...calendarArgs, chart_id: chartA }, { user: '' }))
    expect(missingPrincipal.status).toBe(401)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(verifyIdToken).not.toHaveBeenCalled()
  })

  it('leaves an unrelated global capability on its existing cache and wire path', async () => {
    const otherUri = 'marsys://tool/L0/fixture_other'
    const args = { chart_id: chartA, extra: 'ordinary argument' }
    const expected = { content: { native_context: 'fixture for unrelated capability' }, is_error: false }
    const handler = vi.fn().mockResolvedValue(expected)
    getCapability.mockReturnValue({
      ...callPanchangaServiceCapability, uri: otherUri, handler, input_schema: {},
    })
    for (let i = 0; i < 2; i++) {
      expect(await read(makeRequest(args, { capability: otherUri, bearer: null }))).toEqual({ ok: true, content: expected })
    }
    expect(handler).toHaveBeenCalledExactlyOnceWith(args)
    expect(verifyIdToken).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
    expect(resolveNativeContext).not.toHaveBeenCalled()
  })
})
