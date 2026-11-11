import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { __resetIdentityTokenCacheForTests, callPlatformPanchangaNow, platformServiceGet } from '../../client.js'
import type { Principal } from '../../types.js'
import { registerKalaAheadGetTool } from './ahead.js'
import { computeKalaNow, registerKalaNowGetTool } from './now.js'

const { fetchIdToken, createIdTokenClient } = vi.hoisted(() => {
  vi.stubEnv('PLATFORM_URL', 'https://fixture.invalid')
  vi.stubEnv('MCP_INTERNAL_TOKEN', 'fixture-internal')
  return { fetchIdToken: vi.fn(), createIdTokenClient: vi.fn() }
})

vi.mock('google-auth-library', async (importOriginal) => {
  const actual = await importOriginal<typeof import('google-auth-library')>()
  return {
    ...actual,
    GoogleAuth: class {
      getIdTokenClient(audience: string) {
        createIdTokenClient(audience)
        return Promise.resolve(new actual.IdTokenClient({
          targetAudience: audience,
          idTokenProvider: { fetchIdToken },
        }))
      }
    },
  }
})

const AUDIENCE = 'https://fixture.invalid'
const TOKEN = 'fixture.' + Buffer.from(JSON.stringify({ exp: 4_102_444_800 })).toString('base64url') + '.synthetic'
const DATE = '2026-11-11'
const A = '71000000-0000-4000-8000-000000000001'
const B = '71000000-0000-4000-8000-000000000002'
const OWNER: Principal = { user_uid: 'fixture-a', key_id: 'fixture-key-a', role: 'guest' }
const VIEWER: Principal = { user_uid: 'fixture-b', key_id: 'fixture-key-b', role: 'guest' }
const LAHIRI = 'lahiri_chitrapaksha'
const NOW_PANCHANGA = 'marsys://tool/L0/call_panchanga_service'
const DIGNITY = 'marsys://tool/L1/get_dignity'

const calendar = {
  vara: { id: 1, name: 'Ravivara', end_utc: null },
  planets: { moon: { sign_id: 8 } },
}

function overlay(chartId = A, frame = LAHIRI, moon = 1) {
  return {
    chart_id: chartId,
    ayanamsha_id: frame,
    moon_sign_id: moon,
    moon_sign_name: moon === 1 ? 'Aries' : 'Taurus',
    birth_nakshatra_id: 2,
    birth_nakshatra_name: 'Bharani',
    fact_ids: {
      moon_sign_id: chartId + '-moon-number',
      moon_sign_name: chartId + '-moon-name',
      birth_nakshatra_id: chartId + '-nakshatra-number',
      birth_nakshatra_name: chartId + '-nakshatra-name',
    },
  }
}

function payload(nativeContext: unknown, error: unknown = null) {
  return { mode: 'single', date: DATE, panchang: calendar, native_context: nativeContext, native_context_error: error }
}

function wrapped(content: unknown) {
  return Response.json({ ok: true, content: { content, is_error: false } })
}

interface RequestBody {
  uri?: string
  args?: { chart_id?: string; ayanamsha_id?: string }
  user_uid?: string
  chart_id?: string
}
interface RecordedCall {
  pathname: string
  body: RequestBody
  headers: Headers
  signal: AbortSignal | null | undefined
  redirect: RequestInit['redirect']
}

function transport(
  panchanga: (call: RecordedCall) => Response | Promise<Response>,
  opts: { moon?: number; authorize?: (call: RecordedCall) => boolean } = {},
) {
  const calls: RecordedCall[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const call = {
      pathname: new URL(url).pathname,
      body: JSON.parse(String(init?.body ?? '{}')) as RequestBody,
      headers: new Headers(init?.headers),
      signal: init?.signal,
      redirect: init?.redirect,
    }
    calls.push(call)
    if (call.pathname === '/api/mcp/authz') return Response.json({ authorized: opts.authorize?.(call) ?? true })
    if (call.body.uri === NOW_PANCHANGA) return panchanga(call)
    if (call.body.uri === DIGNITY && opts.moon !== undefined) {
      return wrapped({ rows: [{ fact_id: 'fixture-direct-moon', fact_subject: 'MOON', fact_key: 'sign_num', fact_value_num: opts.moon }] })
    }
    return wrapped({ rows: [] })
  }))
  return calls
}

function namedCalls(calls: RecordedCall[]) {
  return calls.filter(({ body }) => body.uri === NOW_PANCHANGA)
}

beforeEach(() => {
  __resetIdentityTokenCacheForTests()
  fetchIdToken.mockReset().mockResolvedValue(TOKEN)
  createIdTokenClient.mockClear()
  vi.stubEnv('SERVICE_TOKEN', 'fixture-static')
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('Kāla Now workload-bound Panchanga transport', () => {
  it('uses real locked Google IdTokenClient header shape and one 20s request', async () => {
    const timeout = vi.spyOn(AbortSignal, 'timeout')
    const calls = transport(() => wrapped(payload(overlay())))
    const result = await callPlatformPanchangaNow(DATE, OWNER, { chartId: A, ayanamshaId: LAHIRI })
    expect(result).toMatchObject({ ok: true, wrapped: true, overlayRequested: true })
    expect(createIdTokenClient.mock.calls).toEqual([[AUDIENCE]])
    expect(fetchIdToken.mock.calls).toEqual([[AUDIENCE]])
    expect(timeout.mock.calls).toEqual([[20_000]])
    expect(calls).toHaveLength(1)
    const [call] = calls
    expect(call?.pathname).toBe('/api/retrieval/capability')
    expect(call?.redirect).toBe('error')
    expect(call?.signal).toBe(timeout.mock.results[0]?.value)
    expect(call?.body).toEqual({ uri: NOW_PANCHANGA, args: { mode: 'single', date: DATE, chart_id: A, ayanamsha_id: LAHIRI } })
    expect(call?.headers.get('authorization')).toBe('Bearer ' + TOKEN)
    expect(call?.headers.get('x-mcp-internal-token')).toBe('fixture-internal')
    expect(call?.headers.get('x-mcp-user')).toBe(OWNER.user_uid)
    expect(call?.headers.get('x-mcp-key-id')).toBe(OWNER.key_id)
  })

  it.each(['unavailable', 'fixture-internal', 'fixture-static'])('uses a single chartless request for identity %s', async (identity) => {
    if (identity === 'unavailable') fetchIdToken.mockRejectedValue(new Error('fixture credential unavailable'))
    else fetchIdToken.mockResolvedValue(identity)
    const calls = transport(() => wrapped(payload(overlay())))
    const result = await computeKalaNow(A, { as_of: DATE }, OWNER)
    expect(namedCalls(calls)).toHaveLength(1)
    const [call] = namedCalls(calls)
    expect(call?.body.args).toEqual({ mode: 'single', date: DATE })
    expect(call?.headers.get('authorization')).toBeNull()
    expect(call?.headers.get('x-mcp-internal-token')).toBe('fixture-internal')
    expect(result.disha_shula?.avoid_direction).toBe('West')
    expect(result.chandrashtama).toBeNull()
    expect(result.provenance_envelope.panchanga_native_context_error).toBeNull()
  })

  it('keeps the existing SERVICE_TOKEN override for other client calls', async () => {
    const calls = transport(() => wrapped(payload(null)))
    await platformServiceGet('/api/mcp/health/migrations', 1234)
    expect(calls[0]?.headers.get('authorization')).toBe('Bearer fixture-static')
    expect(createIdTokenClient).not.toHaveBeenCalled()
  })

  it.each([
    ['307 redirect', () => new Response(null, { status: 307, headers: { Location: 'https://unexpected.invalid' } })],
    ['503', () => new Response(null, { status: 503 })],
    ['network failure', () => { throw new Error('fixture network failure') }],
    ['malformed JSON', () => new Response('not json')],
    ['inner failure', () => Response.json({ ok: true, content: { is_error: true, content: payload(overlay()) } })],
  ] as const)('does not retry or issue a fallback probe on %s', async (_reason, fail) => {
    const calls = transport(fail)
    const result = await callPlatformPanchangaNow(DATE, OWNER, { chartId: A, ayanamshaId: LAHIRI })
    expect(result).toMatchObject({ content: null, ok: false, overlayRequested: true })
    expect(calls).toHaveLength(1)
  })
})

describe('Kāla Now stored overlay admission', () => {
  it('uses canonical requested frame and cites the distinct stored Moon fact', async () => {
    const calls = transport(() => wrapped(payload(overlay(A, 'krishnamurti'))))
    const result = await computeKalaNow(A, { as_of: DATE, ayanamsha_id: 'KP' }, OWNER)
    expect(namedCalls(calls)[0]?.body.args).toMatchObject({ chart_id: A, ayanamsha_id: 'krishnamurti' })
    expect(result.chandrashtama).toMatchObject({
      is_chandrashtama: true,
      natal_moon_sign_source: 'panchanga_native_context',
      natal_moon_sign_fact_id: overlay().fact_ids.moon_sign_id,
      native_context_agrees_with_l1: null,
    })
    expect(result.provenance_envelope.panchanga_native_context_error).toBeNull()
    expect(result.ayanamsha_frame).toMatchObject({
      natal_ayanamsha_id: 'krishnamurti', transit_ayanamsha_id: LAHIRI, frame_mixed: true,
    })
    expect(result.ayanamsha_frame.lahiri_only_sections).toHaveLength(5)
    const unrelated = calls.filter(({ pathname, body }) => pathname === '/api/retrieval/capability' && body.uri !== NOW_PANCHANGA)
    expect(unrelated.length).toBeGreaterThan(0)
    expect(unrelated.every(({ headers }) => !headers.has('authorization'))).toBe(true)
  })

  it('does not request a private overlay for an unbound frame', async () => {
    const calls = transport(() => wrapped(payload(overlay())))
    const result = await computeKalaNow(A, { as_of: DATE, ayanamsha_id: 'all' }, OWNER)
    expect(namedCalls(calls)[0]?.body.args).toEqual({ mode: 'single', date: DATE })
    expect(result.chandrashtama).toBeNull()
  })

  it('prefers the direct L1 Moon when the admitted overlay differs', async () => {
    transport(() => wrapped(payload(overlay())), { moon: 2 })
    const result = await computeKalaNow(A, { as_of: DATE }, OWNER)
    expect(result.chandrashtama).toMatchObject({
      natal_moon_sign_id: 2,
      natal_moon_sign_source: 'l1_chart_facts',
      natal_moon_sign_fact_id: 'fixture-direct-moon',
      native_context_agrees_with_l1: false,
    })
  })

  it.each([
    ['old web private payload', () => wrapped(payload({ chart_id: A, moon_sign_id: 1, native_name: 'legacy-private' }))],
    ['old flat web envelope', () => Response.json({ ok: true, content: payload(overlay()) })],
    ['new calendar-only envelope', () => wrapped(payload(null, 'Chart overlay unavailable'))],
    ['different chart', () => wrapped(payload(overlay(B)))],
    ['different frame', () => wrapped(payload(overlay(A, 'true_chitra')))],
    ['different date', () => wrapped({ ...payload(overlay()), date: '2026-11-12' })],
    ['non-null error and values', () => wrapped(payload(overlay(), 'legacy-private'))],
    ['duplicated provenance', () => {
      const context = overlay()
      context.fact_ids.birth_nakshatra_name = context.fact_ids.birth_nakshatra_id
      return wrapped(payload(context))
    }],
    ['unnamed fourth provenance', () => {
      const { moon_sign_name: missing, ...factIds } = overlay().fact_ids
      return wrapped(payload({ ...overlay(), fact_ids: { ...factIds, other: missing } }))
    }],
    ['non-verbatim provenance', () => {
      const context = overlay()
      context.fact_ids.moon_sign_id += ' '
      return wrapped(payload(context))
    }],
    ['out-of-range natal Moon', () => wrapped(payload(overlay(A, LAHIRI, 13)))],
  ] as const)('keeps calendar without accepting %s', async (_reason, response) => {
    const calls = transport(response)
    const result = await computeKalaNow(A, { as_of: DATE }, OWNER)
    expect(namedCalls(calls)).toHaveLength(1)
    expect(result.disha_shula?.avoid_direction).toBe('West')
    expect(result.chandrashtama).toBeNull()
    expect(result.provenance_envelope.panchanga_native_context_error).toBe('the birth-chart overlay was not available for this chart on this call')
    expect(JSON.stringify(result)).not.toContain('legacy-private')
  })

  it('gates and binds concurrent tool calls to their registered principals, preserving SDK names', async () => {
    let arrived = 0
    let release!: () => void
    const overlap = new Promise<void>((resolve) => { release = resolve })
    const calls = transport(async (call) => {
      const chart = call.body.args?.chart_id
      const frame = call.body.args?.ayanamsha_id
      arrived += 1
      if (arrived === 2) release()
      await overlap
      return wrapped(payload(overlay(chart, frame, chart === A ? 1 : 2)))
    }, { authorize: ({ body }) => (body.user_uid === OWNER.user_uid && body.chart_id === A)
      || (body.user_uid === VIEWER.user_uid && body.chart_id === B) })
    const register = (principal: Principal) => {
      const tool = vi.fn()
      registerKalaNowGetTool({ tool } as unknown as McpServer, principal)
      expect(tool.mock.calls[0]?.[0]).toBe('kala_now_get')
      return tool.mock.calls[0]?.[3] as (input: Record<string, unknown>) => Promise<{ isError?: boolean; structuredContent: { object: Record<string, unknown> } }>
    }
    const ahead = vi.fn()
    registerKalaAheadGetTool({ tool: ahead } as unknown as McpServer, OWNER)
    expect(ahead.mock.calls[0]?.[0]).toBe('kala_ahead_get')
    const nowA = register(OWNER)
    const nowB = register(VIEWER)
    const denied = await nowA({ chart_id: B, as_of: DATE })
    expect(denied.isError).toBe(true)
    expect(namedCalls(calls)).toHaveLength(0)
    const [first, second] = await Promise.all([
      nowA({ chart_id: A, as_of: DATE, user_uid: VIEWER.user_uid, key_id: VIEWER.key_id }),
      nowB({ chart_id: B, as_of: DATE, ayanamsha_id: 'kp' }),
    ])
    expect(first.structuredContent.object['chandrashtama']).toMatchObject({ natal_moon_sign_id: 1 })
    expect(second.structuredContent.object['chandrashtama']).toMatchObject({ natal_moon_sign_id: 2 })
    expect(namedCalls(calls).map(({ body, headers }) => [
      body.args?.chart_id, body.args?.ayanamsha_id, headers.get('x-mcp-user'), headers.get('x-mcp-key-id'),
    ]).sort()).toEqual([
      [A, LAHIRI, OWNER.user_uid, OWNER.key_id],
      [B, 'krishnamurti', VIEWER.user_uid, VIEWER.key_id],
    ])
  })
})
