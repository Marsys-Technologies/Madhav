/**
 * lahiri_primary_contract.test.ts — SS N-339 / N-342 PR-1 contract.
 * ================================================================
 * "Lahiri is the primary reading on EVERY web path." Every web dispatch (chat, pariprashna,
 * inquiry, /api/mcp/primitives, bundles) goes through `getToolByName().retrieve(plan, params)`.
 * For EVERY registered capability whose input schema declares `ayanamsha_id`, calling through
 * that bridge with ONLY `chart_id` must reach the handler with
 * `ayanamsha_id = 'lahiri_chitrapaksha'`; aliases/case normalise to the stored id; `"all"` is the
 * explicit unfiltered opt-out; an unknown id is an error listing the stored ids; and
 * doctrinal-KP capabilities are NOT injected.
 *
 * No DB: `@/lib/db/client` is mocked (every query recorded, returns no rows) and global fetch
 * is stubbed to reject, so a handler that reaches a service fails closed instead of calling out.
 */
import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
  getPool: () => Promise.reject(new Error('no database in unit tests')),
  withTransaction: () => Promise.reject(new Error('no database in unit tests')),
}))

import { getCatalog } from '../catalog'
import { getToolByName } from '../tool_name_bridge'
import {
  AYANAMSHA_SERVE_ORDER,
  INVARIANT_BEARING_CAPABILITY_URIS,
  KP_FRAME_CAPABILITY_URIS,
} from '../constants'
import type { CapabilityDescriptor } from '../types'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const LAHIRI = 'lahiri_chitrapaksha'

/** Capabilities the bridge deliberately does NOT default to Lahiri on omission (KP doctrine, INVARIANT rows). */
const NOT_INJECTED = new Set<string>([...KP_FRAME_CAPABILITY_URIS, ...INVARIANT_BEARING_CAPABILITY_URIS])

function hasAyanamshaInput(c: CapabilityDescriptor): boolean {
  return !!c.input_schema && Object.prototype.hasOwnProperty.call(c.input_schema, 'ayanamsha_id')
}

let withAya: CapabilityDescriptor[] = []
let perChartWithAya: CapabilityDescriptor[] = []

beforeAll(() => {
  const all = getCatalog()
  withAya = all.filter(hasAyanamshaInput).sort((a, b) => a.uri.localeCompare(b.uri))
  perChartWithAya = withAya.filter((c) => c.scope === 'per_chart')
})

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [], rowCount: 0 })
  vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('network disabled in unit tests'))))
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

/**
 * Run `uri` through the bridge and return the args the handler actually received. The handler is
 * replaced by a recording stub so the assertion is about the bridge contract, independent of how
 * any individual handler is implemented.
 */
async function handlerArgsViaBridge(
  cap: CapabilityDescriptor,
  params: Record<string, unknown> | undefined,
): Promise<Record<string, unknown>> {
  const spy = vi.spyOn(cap, 'handler').mockResolvedValue({ content: { rows: [] } } as never)
  try {
    const tool = getToolByName(cap.uri)
    expect(tool, `getToolByName(${cap.uri})`).toBeDefined()
    await tool!.retrieve({ chart_id: CHART_ID }, params)
    expect(spy).toHaveBeenCalledTimes(1)
    return spy.mock.calls[0]![0] as Record<string, unknown>
  } finally {
    spy.mockRestore()
  }
}

describe('catalog shape this contract depends on', () => {
  it('finds the capabilities that declare ayanamsha_id (guards against a vacuous pass)', () => {
    expect(perChartWithAya.length).toBeGreaterThanOrEqual(70)
    const uris = new Set(perChartWithAya.map((c) => c.uri))
    for (const must of [
      'marsys://tool/L1/get_positions',
      'marsys://tool/L2/query_chart_gestalt',
      'marsys://tool/L2/query_discoveries',
      'marsys://tool/L2/traverse_chart_graph',
      'marsys://tool/L4/query_rectification',
      'marsys://tool/L1/get_kp_cusps',
    ]) {
      expect(uris.has(must), must).toBe(true)
    }
  })
})

describe('omitted ayanamsha_id -> Lahiri on every per_chart capability that declares it', () => {
  it('the set of capabilities NOT defaulted to Lahiri is exactly the declared KP-frame + INVARIANT-bearing set', () => {
    expect([...NOT_INJECTED].sort()).toEqual([
      'marsys://tool/L1/get_kp_cusps',
      'marsys://tool/L1/get_nakshatra',
      'marsys://tool/L1/get_panchanga',
      'marsys://tool/L1/get_strength',
      'marsys://tool/L1/query_planet',
    ])
    const all = new Set(getCatalog().map((c) => c.uri as string))
    for (const uri of NOT_INJECTED) expect(all.has(uri), `stale exclusion ${uri}`).toBe(true)
    for (const uri of NOT_INJECTED) expect(perChartWithAya.some((c) => c.uri === uri), `${uri} has no ayanamsha_id input`).toBe(true)
  })

  it('reaches EVERY other such handler with ayanamsha_id = lahiri_chitrapaksha', async () => {
    const failures: string[] = []
    let injected = 0
    for (const cap of perChartWithAya) {
      if (NOT_INJECTED.has(cap.uri)) continue
      injected += 1
      const args = await handlerArgsViaBridge(cap, undefined)
      if (args['ayanamsha_id'] !== LAHIRI) failures.push(`${cap.uri}: got ${JSON.stringify(args['ayanamsha_id'])}`)
      if (args['chart_id'] !== CHART_ID) failures.push(`${cap.uri}: chart_id not forwarded`)
    }
    expect(failures).toEqual([])
    expect(injected).toBe(perChartWithAya.length - NOT_INJECTED.size)
  })

  it('INVARIANT-bearing capabilities keep their pre-N-342 omitted behaviour (no id injected), but still normalise an explicit one', async () => {
    for (const uri of INVARIANT_BEARING_CAPABILITY_URIS) {
      const cap = perChartWithAya.find((c) => c.uri === uri)!
      expect('ayanamsha_id' in (await handlerArgsViaBridge(cap, undefined)), uri).toBe(false)
      expect((await handlerArgsViaBridge(cap, { ayanamsha_id: 'LAHIRI' }))['ayanamsha_id'], uri).toBe(LAHIRI)
    }
  })

  it('get_positions asked for an INVARIANT-stored category (nakshatra_cross_ayanamsha) is not narrowed to Lahiri', async () => {
    const cap = perChartWithAya.find((c) => c.uri === 'marsys://tool/L1/get_positions')!
    const cross = await handlerArgsViaBridge(cap, { categories: ['nakshatra_cross_ayanamsha'] })
    expect('ayanamsha_id' in cross).toBe(false)
    const plain = await handlerArgsViaBridge(cap, { categories: ['graha_position'] })
    expect(plain['ayanamsha_id']).toBe(LAHIRI)
  })

  it.each([[{}], [{ ayanamsha_id: undefined }], [{ ayanamsha_id: null }], [{ ayanamsha_id: '' }], [{ ayanamsha_id: '   ' }]])(
    'blank params %j also inject Lahiri',
    async (params) => {
      const cap = perChartWithAya.find((c) => c.uri === 'marsys://tool/L2/query_discoveries')!
      expect((await handlerArgsViaBridge(cap, params))['ayanamsha_id']).toBe(LAHIRI)
    },
  )

  it('the real handlers put lahiri_chitrapaksha into their SQL params (mocked query, chart_id only)', async () => {
    // A representative spread of handlers that previously treated "omitted" as "all five".
    const probes = [
      'marsys://tool/L1/get_positions',
      'marsys://tool/L1/get_dignity',
      'marsys://tool/L1/get_yoga_dosha',
      'marsys://tool/L1/get_divisionals',
      'marsys://tool/L2/query_chart_gestalt',
      'marsys://tool/L2/query_cdlm_summary',
      'marsys://tool/L2/query_discoveries',
      'marsys://tool/L2/query_pratijna',
      'marsys://tool/L2/query_cgm_motifs',
      'marsys://tool/L4/query_rectification',
    ]
    for (const uri of probes) {
      queryMock.mockClear()
      const tool = getToolByName(uri)!
      await tool.retrieve({ chart_id: CHART_ID }, {}).catch(() => undefined)
      const paramSets = queryMock.mock.calls.map((c) => c[1] as unknown[] | undefined).filter((p): p is unknown[] => Array.isArray(p))
      expect(paramSets.length, `${uri} issued no parameterised SQL`).toBeGreaterThan(0)
      // query_rectification stores the SHORT code 'lahiri'; every other probe stores the long id.
      const expected = uri.endsWith('query_rectification') ? 'lahiri' : LAHIRI
      expect(
        paramSets.some((p) => p.includes(expected)),
        `${uri}: no SQL param equals ${expected}; params=${JSON.stringify(paramSets)}`,
      ).toBe(true)
    }
  })
})

describe('explicit values are normalised at the boundary', () => {
  it.each([
    ['LAHIRI', LAHIRI],
    ['lahiri', LAHIRI],
    ['Lahiri', LAHIRI],
    ['  lahiri  ', LAHIRI],
    ['kp', 'krishnamurti'],
    ['KP', 'krishnamurti'],
    ['krishnamurti', 'krishnamurti'],
    ['true_citra', 'true_chitra'],
    ['TRUE_CHITRA', 'true_chitra'],
    ['surya_siddhanta', 'surya_siddhanta_classical'],
    ['raman', 'raman'],
    ['INVARIANT', 'INVARIANT'],
  ])('%j -> %j on every per_chart capability that declares ayanamsha_id', async (input, stored) => {
    const failures: string[] = []
    for (const cap of perChartWithAya) {
      const args = await handlerArgsViaBridge(cap, { ayanamsha_id: input })
      if (args['ayanamsha_id'] !== stored) failures.push(`${cap.uri}: got ${JSON.stringify(args['ayanamsha_id'])}`)
    }
    expect(failures).toEqual([])
  })

  it('all five stored ids pass through unchanged', async () => {
    const cap = perChartWithAya.find((c) => c.uri === 'marsys://tool/L1/get_positions')!
    for (const id of AYANAMSHA_SERVE_ORDER) {
      expect((await handlerArgsViaBridge(cap, { ayanamsha_id: id }))['ayanamsha_id']).toBe(id)
    }
  })

  it('other caller params survive untouched alongside the injected id', async () => {
    const cap = perChartWithAya.find((c) => c.uri === 'marsys://tool/L1/get_positions')!
    const args = await handlerArgsViaBridge(cap, { planet: 'Saturn', limit: 7 })
    expect(args).toMatchObject({ chart_id: CHART_ID, planet: 'Saturn', limit: 7, ayanamsha_id: LAHIRI })
  })
})

describe('"all" is the explicit opt-out: raw multi-row access, passes through unfiltered', () => {
  it.each(['all', 'ALL', ' All '])('%j: no ayanamsha_id reaches the handler, scope marker set', async (input) => {
    for (const cap of perChartWithAya) {
      const args = await handlerArgsViaBridge(cap, { ayanamsha_id: input })
      expect('ayanamsha_id' in args, cap.uri).toBe(false)
      expect(args['ayanamsha_scope'], cap.uri).toBe('all')
    }
  })

  it('a real handler given "all" issues SQL with NO ayanamsha param (the raw five-row path)', async () => {
    const tool = getToolByName('marsys://tool/L1/get_positions')!
    await tool.retrieve({ chart_id: CHART_ID }, { ayanamsha_id: 'all' })
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).not.toMatch(/ayanamsha_id\s*=/)
    for (const id of AYANAMSHA_SERVE_ORDER) expect(params).not.toContain(id)
    expect(params).not.toContain('all')
  })
})

describe('an unknown ayanamsha_id is an ERROR that lists the stored ids, never zero rows', () => {
  it.each(['nonsense', 'lahiri_x', 'yukteshwar', 'kp_newcomb'])('%j rejects before any handler or SQL runs', async (bad) => {
    for (const cap of perChartWithAya) {
      const spy = vi.spyOn(cap, 'handler').mockResolvedValue({ content: {} } as never)
      try {
        const tool = getToolByName(cap.uri)!
        let message = ''
        await tool.retrieve({ chart_id: CHART_ID }, { ayanamsha_id: bad }).catch((e: Error) => { message = e.message })
        expect(message, cap.uri).toContain('Unknown ayanamsha_id')
        for (const id of AYANAMSHA_SERVE_ORDER) expect(message, cap.uri).toContain(id)
        expect(spy, cap.uri).not.toHaveBeenCalled()
      } finally {
        spy.mockRestore()
      }
    }
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('a real handler: unknown id errors instead of returning an empty result', async () => {
    const tool = getToolByName('marsys://tool/L1/get_positions')!
    await expect(tool.retrieve({ chart_id: CHART_ID }, { ayanamsha_id: 'bogus' })).rejects.toThrow(/lahiri_chitrapaksha.*surya_siddhanta_classical/s)
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('doctrinal-KP capabilities are NOT injected', () => {
  it('get_kp_cusps: omitted stays omitted, so the handler default (krishnamurti) applies', async () => {
    const cap = withAya.find((c) => c.uri === 'marsys://tool/L1/get_kp_cusps')!
    const args = await handlerArgsViaBridge(cap, undefined)
    expect('ayanamsha_id' in args).toBe(false)
  })

  it('get_kp_cusps: the real handler queries krishnamurti when omitted', async () => {
    const tool = getToolByName('marsys://tool/L1/get_kp_cusps')!
    await tool.retrieve({ chart_id: CHART_ID }, {})
    const params = queryMock.mock.calls[0]![1] as unknown[]
    expect(params).toContain('krishnamurti')
    expect(params).not.toContain(LAHIRI)
  })

  it('get_kp_cusps: an explicit value is still normalised (kp -> krishnamurti, LAHIRI -> stored Lahiri)', async () => {
    const cap = withAya.find((c) => c.uri === 'marsys://tool/L1/get_kp_cusps')!
    expect((await handlerArgsViaBridge(cap, { ayanamsha_id: 'kp' }))['ayanamsha_id']).toBe('krishnamurti')
    expect((await handlerArgsViaBridge(cap, { ayanamsha_id: 'LAHIRI' }))['ayanamsha_id']).toBe(LAHIRI)
  })

  it('every capability that mentions KP/Krishnamurti in its uri or name and declares ayanamsha_id is in KP_FRAME_CAPABILITY_URIS', () => {
    const kpLike = withAya.filter((c) => /(^|[^a-z])kp([^a-z]|$)|krishnamurti/i.test(`${c.uri} ${c.name}`))
    const missing = kpLike.filter((c) => !KP_FRAME_CAPABILITY_URIS.has(c.uri)).map((c) => c.uri)
    expect(missing).toEqual([])
  })

  it('every URI in KP_FRAME_CAPABILITY_URIS is a registered capability (no stale entries)', () => {
    const all = new Set(getCatalog().map((c) => c.uri))
    for (const uri of KP_FRAME_CAPABILITY_URIS) expect(all.has(uri as never), uri).toBe(true)
  })
})

describe('capabilities WITHOUT an ayanamsha_id input are left alone', () => {
  it('lel_query (no ayanamsha_id in schema) receives no ayanamsha_id and a bad value is not rejected by the bridge', async () => {
    const cap = getCatalog().find((c) => c.uri === 'marsys://tool/L5/lel_query')!
    expect(hasAyanamshaInput(cap)).toBe(false)
    const none = await handlerArgsViaBridge(cap, undefined)
    expect('ayanamsha_id' in none).toBe(false)
    const passthrough = await handlerArgsViaBridge(cap, { ayanamsha_id: 'garbage' })
    expect(passthrough['ayanamsha_id']).toBe('garbage')
  })
})

describe('global capabilities that declare ayanamsha_id are normalised too (no chart_id needed)', () => {
  it('call_ephemeris_at_t / call_muhurta_score: omitted -> Lahiri, "kp" -> krishnamurti', async () => {
    for (const uri of ['marsys://tool/L3/call_ephemeris_at_t', 'marsys://tool/L3/call_muhurta_score']) {
      const cap = withAya.find((c) => c.uri === uri)!
      expect(cap.scope).toBe('global')
      const spy = vi.spyOn(cap, 'handler').mockResolvedValue({ content: {} } as never)
      try {
        const tool = getToolByName(uri)!
        await tool.retrieve({}, {})
        expect((spy.mock.calls[0]![0] as Record<string, unknown>)['ayanamsha_id']).toBe(LAHIRI)
        await tool.retrieve({}, { ayanamsha_id: 'kp' })
        expect((spy.mock.calls[1]![0] as Record<string, unknown>)['ayanamsha_id']).toBe('krishnamurti')
      } finally {
        spy.mockRestore()
      }
    }
  })
})
