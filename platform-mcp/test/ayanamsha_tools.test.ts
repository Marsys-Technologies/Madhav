/**
 * ayanamsha_tools.test.ts — SS N-339 / N-342 PR-1, MCP side.
 *
 * 1. The MCP normaliser (src/lib/ayanamsha.ts) pinned against a golden table (the platform twin
 *    is pinned against the same table; cross-package parity lives in
 *    platform/src/lib/retrieval/registry/__tests__/ayanamsha_parity.test.ts).
 * 2. The two tools whose BirthBase enum used to reject stored ids
 *    (ganita_special_lagnas_get, ganita_natal_positions_compute) now accept every stored long id
 *    plus the historical short spellings, and send ONE normalised id on.
 * 3. The two raw-id tools (mechanism_retrodiction_get, scan_fetch_signals) normalise through the
 *    helper and reject unknown ids with the stored ids listed.
 *
 * No network: global fetch is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'

process.env['SERVICE_TOKEN'] = 'test-service-token'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// remoteAuthorize would call the platform; the tool under test is not the authz layer.
vi.mock('../src/lib/authz.js', () => ({ remoteAuthorize: vi.fn().mockResolvedValue(true) }))

import {
  AYANAMSHA_SERVE_ORDER,
  normalizeAyanamshaId,
  resolveAyanamshaArg,
  resolveChartFactsAyanamsha,
} from '../src/lib/ayanamsha.js'
import { registerP1AliasTools } from '../src/tools/register_p1_aliases.js'
import { registerMechanismRetrodictionTool } from '../src/tools/mechanism_retrodiction.js'
import { registerScanFetchTool } from '../src/tools/scan_fetch_signals.js'

const LAHIRI = 'lahiri_chitrapaksha'
const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const PRINCIPAL = { user_uid: 'test-uid', audience_tier: 'super_admin' as const, key_id: 'test-key-001' }

type Handler = (args: Record<string, unknown>) => Promise<{ isError?: boolean; content?: Array<{ text?: string }>; structuredContent?: unknown }>
interface Captured { schema: Record<string, z.ZodTypeAny>; handler: Handler }

function capture(register: (server: never, principal: never) => void): Map<string, Captured> {
  const tools = new Map<string, Captured>()
  const server = {
    tool: (name: string, _desc: string, schema: Record<string, z.ZodTypeAny>, handler: Handler) => {
      tools.set(name, { schema, handler })
    },
  }
  register(server as never, PRINCIPAL as never)
  return tools
}

function textOf(r: { content?: Array<{ text?: string }> }): string {
  return (r.content ?? []).map((c) => c.text ?? '').join('\n')
}

function okJson(body: unknown) {
  return { ok: true, status: 200, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) }
}

/** Parse the JSON bodies of every fetch call so far, with its URL. */
function fetched(): Array<{ url: string; body: Record<string, unknown> }> {
  return mockFetch.mock.calls.map((c) => ({
    url: String(c[0]),
    body: JSON.parse(String((c[1] as { body?: string } | undefined)?.body ?? '{}')) as Record<string, unknown>,
  }))
}

beforeEach(() => {
  mockFetch.mockReset()
})

// ── 1. golden table ────────────────────────────────────────────────────────────

describe('MCP normaliser golden table', () => {
  const GOLDEN: Array<[unknown, string | null]> = [
    [undefined, LAHIRI], [null, LAHIRI], ['', LAHIRI], ['  ', LAHIRI],
    ['lahiri', LAHIRI], ['LAHIRI', LAHIRI], ['lahiri_chitrapaksha', LAHIRI],
    ['true_chitra', 'true_chitra'], ['true_citra', 'true_chitra'], ['true_chitra_paksha', 'true_chitra'], ['chitra', 'true_chitra'],
    ['kp', 'krishnamurti'], ['KP', 'krishnamurti'], ['krishnamurti', 'krishnamurti'], ['krishnamurti_paddhati', 'krishnamurti'],
    ['raman', 'raman'],
    ['surya_siddhanta', 'surya_siddhanta_classical'], ['surya_siddhanta_classical', 'surya_siddhanta_classical'], ['ss', 'surya_siddhanta_classical'],
    ['INVARIANT', 'INVARIANT'], ['invariant', 'INVARIANT'],
    ['all', null], ['ALL', null],
  ]

  it.each(GOLDEN)('%j -> %j', (input, expected) => {
    expect(normalizeAyanamshaId(input)).toBe(expected)
  })

  it('unknown ids throw an error that lists the stored ids', () => {
    expect(() => normalizeAyanamshaId('nonsense')).toThrow(/lahiri_chitrapaksha.*true_chitra.*krishnamurti.*raman.*surya_siddhanta_classical/s)
  })

  it('serve order: Lahiri first, then true_chitra, krishnamurti, raman, surya_siddhanta_classical', () => {
    expect([...AYANAMSHA_SERVE_ORDER]).toEqual([LAHIRI, 'true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical'])
  })

  it('the lenient wrapper resolver keeps its historical contract (unknown passes through, falsy -> Lahiri, "all" -> "all")', () => {
    expect(resolveChartFactsAyanamsha(undefined)).toBe(LAHIRI)
    expect(resolveChartFactsAyanamsha('')).toBe(LAHIRI)
    expect(resolveChartFactsAyanamsha('KP')).toBe('krishnamurti')
    expect(resolveChartFactsAyanamsha('true_chitra')).toBe('true_chitra')
    expect(resolveChartFactsAyanamsha('ALL')).toBe('all')
    expect(resolveChartFactsAyanamsha('mystery')).toBe('mystery')
  })
})

// ── 2. BirthBase enum tools ────────────────────────────────────────────────────

describe('ganita_special_lagnas_get / ganita_natal_positions_compute: stored ids accepted', () => {
  const tools = capture(registerP1AliasTools)
  const ACCEPTED_INPUTS = [
    ...AYANAMSHA_SERVE_ORDER, // every stored long id (the old enum rejected all but nothing)
    'lahiri', 'raman', 'kp', 'true_citra', // the old enum members still work
    'LAHIRI', 'Lahiri_Chitrapaksha', 'surya_siddhanta',
  ]

  for (const name of ['ganita_special_lagnas_get', 'ganita_natal_positions_compute']) {
    describe(name, () => {
      const t = tools.get(name)!
      const BIRTH = { datetime_iso: '1984-02-05T10:43:00', latitude_deg: 20.2961, longitude_deg: 85.8245, tz_offset_hours: 5.5 }

      it('is registered', () => expect(t).toBeDefined())

      it.each(ACCEPTED_INPUTS.map((v) => [v]))('schema accepts ayanamsha_id %j', (id) => {
        const parsed = z.object(t.schema).safeParse({ ...BIRTH, ayanamsha_id: id })
        expect(parsed.success).toBe(true)
      })

      it('schema accepts an omitted ayanamsha_id (no longer forces a default short id)', () => {
        const parsed = z.object(t.schema).safeParse({ ...BIRTH })
        expect(parsed.success).toBe(true)
      })

      it.each([
        ['kp', 'krishnamurti'],
        ['true_citra', 'true_chitra'],
        ['LAHIRI', LAHIRI],
        ['surya_siddhanta', 'surya_siddhanta_classical'],
        ['raman', 'raman'],
        [undefined, LAHIRI],
      ])('birth-data mode: %j reaches the sidecar as %j', async (input, sent) => {
        mockFetch.mockResolvedValue(okJson({ status: 'ok', graha_sthana: [] }))
        const r = await t.handler({ ...BIRTH, ...(input === undefined ? {} : { ayanamsha_id: input }) })
        expect(r.isError).not.toBe(true)
        const calls = fetched()
        expect(calls).toHaveLength(1)
        expect(calls[0]!.url).toContain('/api/pyhora/compute')
        expect(calls[0]!.body['ayanamsha_id']).toBe(sent)
      })

      it('birth-data mode: an unknown id is an error listing the stored ids and never reaches the sidecar', async () => {
        const r = await t.handler({ ...BIRTH, ayanamsha_id: 'yukteshwar' })
        expect(r.isError).toBe(true)
        const text = textOf(r)
        for (const id of AYANAMSHA_SERVE_ORDER) expect(text).toContain(id)
        expect(mockFetch).not.toHaveBeenCalled()
      })

      it.each(['all', 'INVARIANT'])('birth-data mode: %j cannot be recomputed -> error, no sidecar call', async (id) => {
        const r = await t.handler({ ...BIRTH, ayanamsha_id: id })
        expect(r.isError).toBe(true)
        expect(mockFetch).not.toHaveBeenCalled()
      })
    })
  }

  describe('ganita_special_lagnas_get chart_id mode (stored facts)', () => {
    const t = tools.get('ganita_special_lagnas_get')!

    it.each([
      ['krishnamurti', 'krishnamurti'],
      ['true_chitra', 'true_chitra'],
      ['surya_siddhanta_classical', 'surya_siddhanta_classical'],
      ['kp', 'krishnamurti'],
      ['LAHIRI', LAHIRI],
      [undefined, LAHIRI],
    ])('%j is sent to get_sensitive_points as %j', async (input, sent) => {
      mockFetch.mockResolvedValue(okJson({ ok: true, content: { content: { rows: [] } } }))
      const r = await t.handler({ chart_id: CHART, ...(input === undefined ? {} : { ayanamsha_id: input }) })
      expect(r.isError).not.toBe(true)
      const calls = fetched()
      expect(calls[0]!.url).toContain('/api/retrieval/capability')
      expect((calls[0]!.body['args'] as Record<string, unknown>)['ayanamsha_id']).toBe(sent)
    })

    it('an unknown id is an error listing the stored ids, with no platform call', async () => {
      const r = await t.handler({ chart_id: CHART, ayanamsha_id: 'nope' })
      expect(r.isError).toBe(true)
      expect(textOf(r)).toContain('surya_siddhanta_classical')
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })
})

// ── 3. raw-id tools ────────────────────────────────────────────────────────────

describe('mechanism_retrodiction_get: ayanamsha_id normalised through the helper', () => {
  const t = capture(registerMechanismRetrodictionTool).get('mechanism_retrodiction_get')!

  it.each([
    ['kp', 'krishnamurti'],
    ['LAHIRI', LAHIRI],
    ['true_citra', 'true_chitra'],
    [undefined, LAHIRI],
    ['all', 'all'],
  ])('%j -> primitive receives %j', async (input, sent) => {
    mockFetch.mockResolvedValue(okJson({ ok: true, result: { results: [{ content: JSON.stringify({ mechanisms: [] }) }] } }))
    await t.handler({ chart_id: CHART, ...(input === undefined ? {} : { ayanamsha_id: input }) })
    const calls = fetched()
    expect(calls.length).toBeGreaterThan(0)
    const body = calls[calls.length - 1]!.body
    const params = (body['params'] ?? body['args'] ?? body) as Record<string, unknown>
    expect(params['ayanamsha_id']).toBe(sent)
  })

  it('unknown id: error listing the stored ids, no primitive call', async () => {
    const r = await t.handler({ chart_id: CHART, ayanamsha_id: 'bogus' })
    expect(r.isError).toBe(true)
    const text = textOf(r)
    for (const id of AYANAMSHA_SERVE_ORDER) expect(text).toContain(id)
    expect(mockFetch).not.toHaveBeenCalled()
  })
})

describe('scan_fetch_signals: ayanamsha_id normalised through the helper', () => {
  const t = capture(registerScanFetchTool).get('scan_fetch_signals')!

  it.each([
    ['kp', 'krishnamurti'],
    ['Lahiri', LAHIRI],
    ['true_chitra', 'true_chitra'],
    [undefined, LAHIRI],
  ])('%j -> query_signals receives %j', async (input, sent) => {
    mockFetch.mockResolvedValue(okJson({ ok: true, content: { content: { signals: [] } } }))
    await t.handler({ chart_id: CHART, mode: 'scan', ...(input === undefined ? {} : { ayanamsha_id: input }) })
    const calls = fetched()
    expect(calls[0]!.url).toContain('/api/retrieval/capability')
    expect((calls[0]!.body['args'] as Record<string, unknown>)['ayanamsha_id']).toBe(sent)
  })

  it('unknown id: error listing the stored ids, no platform call', async () => {
    const r = await t.handler({ chart_id: CHART, mode: 'scan', ayanamsha_id: 'bogus' })
    expect(r.isError).toBe(true)
    const text = textOf(r)
    for (const id of AYANAMSHA_SERVE_ORDER) expect(text).toContain(id)
    expect(mockFetch).not.toHaveBeenCalled()
  })
})

describe('resolveAyanamshaArg is total (never throws)', () => {
  it.each([[Symbol.iterator], [() => 1], [BigInt(1)]])('%s', (v) => {
    expect(() => resolveAyanamshaArg(v)).not.toThrow()
  })
})
