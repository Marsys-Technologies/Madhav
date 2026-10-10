/* eslint-disable @typescript-eslint/no-explicit-any -- fixture-shaped JSON in a test */
/**
 * SS N-360 — the ONE shared `identity_cross_check` block (Lagna sign, Moon sign, Moon nakshatra, current
 * Mahadasha lord), built by the same builder as `ayanamsha_cross_check`:
 *
 *   chart_snapshot   always on, compact (all four facts)
 *   graha_portrait   the MOON always (Moon sign + nakshatra); any other graha only with include_cross_check:true
 *   get_chart_header NO cross-check key (it rides on every envelope)
 *
 * No database: `query` is a router over a five-ayanamsha fixture (helpers/identity_cross_check_fixtures.ts).
 * The "rest of the response is unchanged" assertions compare against a golden produced by the PRE-CHANGE
 * handlers on the same fixture (fixtures/identity_cross_check.pre_change_golden.json).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import golden from './fixtures/identity_cross_check.pre_change_golden.json'

const { queryMock, mockResolve, positions, dignity, strength, avasthas, yogaDosha, dashas, signals, traverse } = vi.hoisted(() => {
  const ok = (content: unknown = { rows: [] }) => ({ handler: vi.fn().mockResolvedValue({ content, is_error: false }) })
  return {
    queryMock: vi.fn(), mockResolve: vi.fn(),
    positions: ok(), dignity: ok(), strength: ok(), avasthas: ok(), yogaDosha: ok(), dashas: ok(),
    signals: ok({ signals: [] }), traverse: ok({ nodes: [], edges: [], node_count: 0, edge_count: 0 }),
  }
})
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('../generation/served_generation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../generation/served_generation')>()
  return { ...actual, resolveChartServedGeneration: (...a: unknown[]) => mockResolve(...a) }
})
vi.mock('../layers/L1_ganita/get_positions', () => ({ getPositionsCapability: positions }))
vi.mock('../layers/L1_ganita/get_dignity', () => ({ getDignityCapability: dignity }))
vi.mock('../layers/L1_ganita/get_strength', () => ({ getStrengthCapability: strength }))
vi.mock('../layers/L1_ganita/get_avasthas', () => ({ getAvasthsCapability: avasthas }))
vi.mock('../layers/L1_ganita/get_yoga_dosha', () => ({ getYogaDoshaCapability: yogaDosha }))
vi.mock('../layers/L1_ganita/get_dashas', () => ({ getDashasCapability: dashas }))
vi.mock('../layers/L2_bodha/query_signals', () => ({ querySignalsCapability: signals }))
vi.mock('../layers/L2_bodha/traverse_chart_graph', () => ({ traverseChartGraphCapability: traverse }))

import { getChartSnapshotCapability } from '../layers/L1_ganita/get_chart_snapshot'
import { getChartHeaderCapability } from '../layers/L1_ganita/get_chart_header'
import { grahaPortraitCapability } from '../layers/L2_bodha/graha_portrait'
import { IDENTITY_CROSS_CHECK_KEY, CROSS_CHECK_KEY } from '../../ayanamsha_cross_check'
import {
  CHART, LAHIRI, KEY, OTHERS_IN_ORDER, POSITION_BUILD, DASHA_BUILD, SERVED_GENERATION, installIdentityDb,
} from './helpers/identity_cross_check_fixtures'
import { installPortraitLeaves } from './helpers/graha_portrait_leaves'
import {
  fetchDossierIdentityCrossCheck, attachIdentityCrossCheckToPage,
} from '../../../../../../platform-mcp/src/lib/identity_cross_check'

type Cc = Record<string, any>
const roundTrip = (x: unknown): any => JSON.parse(JSON.stringify(x))
const withoutKey = (content: unknown): Cc => {
  const { [KEY]: _drop, ...rest } = roundTrip(content) as Cc
  void _drop
  return rest
}

beforeEach(() => {
  queryMock.mockReset()
  mockResolve.mockReset()
  mockResolve.mockResolvedValue(SERVED_GENERATION)
  vi.spyOn(console, 'error').mockImplementation(() => undefined)
})

it('the key is the same one platform-mcp registers as trimmable (identity_cross_check), distinct from ayanamsha_cross_check', () => {
  expect(IDENTITY_CROSS_CHECK_KEY).toBe(KEY)
  expect(KEY).not.toBe(CROSS_CHECK_KEY)
})

// ── chart_snapshot ────────────────────────────────────────────────────────────────────────────────
describe('chart_snapshot: identity_cross_check always on, compact', () => {
  const snap = async (args: Record<string, unknown> = {}) =>
    getChartSnapshotCapability.handler({ chart_id: CHART, ...args }, undefined)

  it('agree case: ONE line; degrees differ across ayanamshas but signs agree -> "Agrees across all five ayanamshas"', async () => {
    installIdentityDb(queryMock)
    const res = await snap()
    expect(res.is_error).toBe(false)
    const x = (res.content as Cc)[KEY]
    expect(x.heading).toBe('Cross-check, not the reading')
    expect(x.scope).toBe('identity_facts')
    expect(x.primary_id).toBe(LAHIRI)
    expect(x.agreement).toBe('all_agree')
    expect(x.summary).toBe('Agrees across all five ayanamshas')
    expect(x.others.map((o: Cc) => o.ayanamsha_id)).toEqual(OTHERS_IN_ORDER)
    expect(Object.keys(x.primary.values)).toEqual(['lagna_sign', 'moon_sign', 'moon_nakshatra', 'maha_lord'])
    expect(x.primary.values.maha_lord.value).toBe('Venus')
    // degrees are SHOWN and differ per ayanamsha; they are never compared
    const degs = new Set([x.primary.values.moon_sign.degrees, ...x.others.map((o: Cc) => o.values.moon_sign.degrees)])
    expect(degs.size).toBe(5)
  })

  it('dissent case: the dissenting ayanamsha is NAMED with its value', async () => {
    installIdentityDb(queryMock, { override: { raman: { 'MOON.sign': 'Pisces', 'MOON.nakshatra': 'Uttara Bhadrapada' }, krishnamurti: { maha_lord: 'Mercury' } } })
    const x = ((await snap()).content as Cc)[KEY]
    expect(x.agreement).toBe('dissent')
    expect(x.summary).toBe(
      'Dissent: Krishnamurti: current Mahadasha lord Mercury (primary Venus); '
      + 'Raman: Moon sign Pisces (primary Aquarius), Moon nakshatra Uttara Bhadrapada (primary Purva Bhadrapada)')
    expect(x.others.filter((o: Cc) => o.status === 'dissents').map((o: Cc) => o.ayanamsha_id)).toEqual(['krishnamurti', 'raman'])
    // the primary answer is not touched by the dissent
    expect(x.primary.values.moon_sign.value).toBe('Aquarius')
  })

  it('single-ayanamsha chart: not_available / single_ayanamsha_chart, never "1/1"', async () => {
    installIdentityDb(queryMock, { stored: [LAHIRI] })
    const x = ((await snap()).content as Cc)[KEY]
    expect(x).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(JSON.stringify(x)).not.toMatch(/1\/1|agree/i)
  })

  it('a failed cross-check read never fails the grid', async () => {
    installIdentityDb(queryMock)
    const original = (queryMock.getMockImplementation() as (s: string, p?: unknown[]) => Promise<unknown>)
    queryMock.mockImplementation(async (sql: string, params?: unknown[]) => {
      if (sql.includes("fact_subject = 'LAGNA'") || sql.includes('FROM chart_dashas')) throw new Error('db down')
      return original(sql, params)
    })
    const res = await snap()
    expect(res.is_error).toBe(false)
    expect((res.content as Cc)[KEY]).toMatchObject({ not_available: true, reason: 'cross_check_read_failed' })
    expect((res.content as Cc)['snapshot_text']).toContain('Lagna Ari')
  })

  it('reads are fenced to the served generation (chart_facts) and to the served ga_dashas build', async () => {
    const calls = installIdentityDb(queryMock)
    await snap()
    const pos = calls.find((c) => c.sql.includes("fact_subject = 'LAGNA'"))!
    expect(pos.params[2]).toEqual([POSITION_BUILD])
    const dasha = calls.find((c) => c.sql.includes('FROM chart_dashas'))!
    expect(dasha.params).toContain(DASHA_BUILD)
    // ONE query per source, covering all five ayanamshas (no per-ayanamsha loop)
    expect(calls.filter((c) => c.sql.includes("fact_subject = 'LAGNA'"))).toHaveLength(1)
    expect(calls.filter((c) => c.sql.includes('FROM chart_dashas'))).toHaveLength(1)
    expect(pos.params[1]).toHaveLength(5)
  })

  it('an unresolved served generation reads unfenced exactly as get_positions does, and still never throws', async () => {
    mockResolve.mockRejectedValue(new Error('no receipts'))
    const calls = installIdentityDb(queryMock)
    const x = ((await snap()).content as Cc)[KEY]
    expect(x.summary).toBe('Agrees across all five ayanamshas')
    expect(calls.find((c) => c.sql.includes("fact_subject = 'LAGNA'"))!.params).toHaveLength(2)
  })

  it('the rest of the response is identical to the pre-change output (default, and with D9 + extra vargas)', async () => {
    installIdentityDb(queryMock)
    expect(withoutKey((await snap()).content)).toEqual(golden.chart_snapshot_default.content)
    expect(withoutKey((await snap({ include_navamsa: true, vargas: ['D10'] })).content)).toEqual(golden.chart_snapshot_navamsa_vargas.content)
  })

  it('the 2KB snapshot cap still measures the grid alone', async () => {
    installIdentityDb(queryMock)
    const c = (await snap()).content as Cc
    expect(c['byte_length']).toBe(Buffer.byteLength(c['snapshot_text'], 'utf8'))
    expect(c['within_budget']).toBe(true)
  })
})

// ── graha_portrait ────────────────────────────────────────────────────────────────────────────────
describe('graha_portrait: the Moon always, another graha only on request', () => {
  const portrait = async (graha: string, extra: Record<string, unknown> = {}) =>
    grahaPortraitCapability.handler({ chart_id: CHART, graha, ...extra }, undefined) as Promise<{ content: Cc; is_error: boolean }>

  beforeEach(() => {
    installPortraitLeaves({ positions, dignity, strength, avasthas, yogaDosha, dashas, signals, traverse })
  })

  it('Moon, agree case: always on, Moon sign + Moon nakshatra only, one line', async () => {
    installIdentityDb(queryMock)
    const { content, is_error } = await portrait('Moon')
    expect(is_error).toBe(false)
    const x = content[KEY]
    expect(x.scope).toBe('identity_facts')
    expect(x.summary).toBe('Agrees across all five ayanamshas')
    expect(Object.keys(x.primary.values)).toEqual(['moon_sign', 'moon_nakshatra'])
    expect(x.others.map((o: Cc) => o.ayanamsha_id)).toEqual(OTHERS_IN_ORDER)
    const degs = new Set([x.primary.values.moon_sign.degrees, ...x.others.map((o: Cc) => o.values.moon_sign.degrees)])
    expect(degs.size).toBe(5)
  })

  it('Moon, dissent case: the dissenting ayanamsha is named with its value', async () => {
    installIdentityDb(queryMock, { override: { raman: { 'MOON.sign': 'Pisces', 'MOON.nakshatra': 'Uttara Bhadrapada' } } })
    const x = (await portrait('Moon')).content[KEY]
    expect(x.agreement).toBe('dissent')
    expect(x.summary).toBe('Dissent: Raman: Moon sign Pisces (primary Aquarius), Moon nakshatra Uttara Bhadrapada (primary Purva Bhadrapada)')
  })

  it('Moon, single-ayanamsha chart: not_available / single_ayanamsha_chart, never "1/1"', async () => {
    installIdentityDb(queryMock, { stored: [LAHIRI] })
    const x = (await portrait('chandra')).content[KEY]
    expect(x).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(JSON.stringify(x)).not.toMatch(/1\/1|agree/i)
  })

  it('another graha (Saturn) default: ABSENT, and no cross-check read is even made', async () => {
    const calls = installIdentityDb(queryMock)
    const { content } = await portrait('Saturn')
    expect(KEY in content).toBe(false)
    expect(calls.some((c) => c.sql.includes('fact_subject = ANY($3::text[])'))).toBe(false)
  })

  it('another graha with include_cross_check:true: that graha\'s sign and nakshatra, same builder, requested_facts scope', async () => {
    installIdentityDb(queryMock, { override: { true_chitra: { 'SAT.sign': 'Virgo' } } })
    const x = (await portrait('Saturn', { include_cross_check: true })).content[KEY]
    expect(x.scope).toBe('requested_facts')
    expect(Object.keys(x.primary.values)).toEqual(['sat_sign', 'sat_nakshatra'])
    expect(x.agreement).toBe('dissent')
    expect(x.summary).toBe('Dissent: True Chitrapaksha: Saturn sign Virgo (primary Libra)')
  })

  it('include_cross_check:true on the Moon changes nothing (already on)', async () => {
    installIdentityDb(queryMock)
    const a = (await portrait('Moon')).content[KEY]
    const b = (await portrait('Moon', { include_cross_check: true })).content[KEY]
    expect(b).toEqual(a)
  })

  it('reads are fenced to the served generation build set, and the position leg is unchanged', async () => {
    const calls = installIdentityDb(queryMock)
    await portrait('Moon')
    const read = calls.find((c) => c.sql.includes('fact_subject = ANY($3::text[])'))!
    expect(read.params[2]).toEqual(['MOON'])
    expect(read.params[3]).toEqual([POSITION_BUILD])
  })

  it('no served generation: nothing is read for the block (no fallback to current rows) and it is absent', async () => {
    mockResolve.mockResolvedValue({ ...SERVED_GENERATION, served_build_ids: [] })
    const calls = installIdentityDb(queryMock)
    const { content } = await portrait('Moon')
    expect(KEY in content).toBe(false)
    expect(calls.some((c) => c.sql.includes('fact_subject = ANY($3::text[])'))).toBe(false)
  })

  it('the block rides with the position section: include without "position" -> absent', async () => {
    installIdentityDb(queryMock)
    expect(KEY in (await portrait('Moon', { include: ['dashas'] })).content).toBe(false)
  })

  it('ayanamsha_id:"all" carries no block', async () => {
    installIdentityDb(queryMock)
    expect(KEY in (await portrait('Moon', { ayanamsha_id: 'all' })).content).toBe(false)
  })

  it('a failed cross-check read never fails the portrait', async () => {
    installIdentityDb(queryMock)
    const original = (queryMock.getMockImplementation() as (s: string, p?: unknown[]) => Promise<unknown>)
    queryMock.mockImplementation(async (sql: string, params?: unknown[]) => {
      if (sql.includes('fact_subject = ANY($3::text[])')) throw new Error('db down')
      return original(sql, params)
    })
    const { content, is_error } = await portrait('Moon')
    expect(is_error).toBe(false)
    expect(content[KEY]).toMatchObject({ not_available: true, reason: 'cross_check_read_failed' })
    expect(content['position'].count).toBe(1)
  })

  it('the rest of the response is identical to the pre-change output (Saturn default, Moon minus the block)', async () => {
    installIdentityDb(queryMock)
    expect(withoutKey((await portrait('Saturn')).content)).toEqual(golden.graha_portrait_Saturn.content)
    expect(withoutKey((await portrait('Moon')).content)).toEqual(golden.graha_portrait_Moon.content)
  })

  it('declares the optional include_cross_check boolean input', () => {
    expect((grahaPortraitCapability.input_schema as Cc)['include_cross_check']).toMatchObject({ type: 'boolean' })
    expect(grahaPortraitCapability.required_inputs).toEqual(['chart_id', 'graha'])
  })
})

// ── get_chart_header ──────────────────────────────────────────────────────────────────────────────
describe('get_chart_header carries NO cross-check (it rides on every envelope: noise)', () => {
  // the header resolution is cached for 60 s per (chart, ayanamsha, as_of_date): a distinct date per case
  it.each([
    [{ as_of_date: '2026-01-01' }],
    [{ as_of_date: '2026-01-02', include_cross_check: true }],
    [{ as_of_date: '2026-01-03', ayanamsha_id: 'all' }],
  ])('args %j: the header is served as before, with no cross-check key and no five-way read', async (extra) => {
    const calls: Array<{ sql: string; params: unknown[] }> = []
    queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
      calls.push({ sql, params })
      if (sql.includes('FROM charts')) return { rows: [{ name: 'Abhisek' }] }
      if (sql.includes("fact_subject IN ('LAGNA', 'MOON', 'SUN')")) {
        return { rows: [
          { fact_subject: 'LAGNA', fact_key: 'sign', fact_value_text: 'Aries', fact_value_num: null },
          { fact_subject: 'MOON', fact_key: 'sign', fact_value_text: 'Aquarius', fact_value_num: null },
          { fact_subject: 'SUN', fact_key: 'sign', fact_value_text: 'Capricorn', fact_value_num: null },
        ] }
      }
      if (sql.includes('FROM chart_dashas')) return { rows: [{ lord_graha: 'Venus', level_n: 1 }] }
      return { rows: [] }
    })
    const res = await getChartHeaderCapability.handler({ chart_id: CHART, ...extra }, undefined)
    expect(res.is_error).toBe(false)
    expect(res.content).toMatchObject({ lagna_sign: 'Aries', moon_sign: 'Aquarius', ayanamsha: LAHIRI, current_maha_antar: 'Venus MD' })
    expect(calls).toHaveLength(3)
    expect(JSON.stringify(res)).not.toMatch(/cross_check|Cross-check|identity_cross/)
    // every header read is a single-ayanamsha read: no ayanamsha list parameter anywhere
    expect(calls.some((c) => c.params.some((p) => Array.isArray(p)))).toBe(false)
  })

  it('declares no include_cross_check input', () => {
    expect(Object.keys(getChartHeaderCapability.input_schema ?? {})).not.toContain('include_cross_check')
  })
})

// ── dossier (through the MCP seam, the block built by the REAL platform handler) ──────────────────
describe('dossier: page 1 carries the block the platform builds (agree / dissent / single), uncompared by the MCP package', () => {
  const PRINCIPAL = { user_uid: 'u', key_id: 'k', role: 'super_admin' } as never
  // the MCP package reaches the platform over HTTP; here the "platform" is the real chart_snapshot handler
  const platformFetch = (async (_url: string, init: { body: string }) => {
    const { uri, args } = JSON.parse(init.body) as { uri: string; args: Record<string, unknown> }
    expect(uri).toBe('marsys://tool/L1/chart_snapshot')
    return { ok: true, json: async () => ({ ok: true, content: await getChartSnapshotCapability.handler(args, undefined) }) }
  }) as unknown as typeof fetch
  const page1 = () => ({ page_n: 1, budget_kb_applied: 24, judgment_flags: [] as string[], page_units: [{ serving_tool: 'x' }] })

  it('agree case', async () => {
    installIdentityDb(queryMock)
    const block = await fetchDossierIdentityCrossCheck(CHART, PRINCIPAL, platformFetch)
    const out = attachIdentityCrossCheckToPage(page1(), block) as Cc
    expect(out[KEY].summary).toBe('Agrees across all five ayanamshas')
    expect(out[KEY].heading).toBe('Cross-check, not the reading')
    expect(Object.keys(out[KEY].primary.values)).toEqual(['lagna_sign', 'moon_sign', 'moon_nakshatra', 'maha_lord'])
    expect(out.page_units).toEqual([{ serving_tool: 'x' }])
  })

  it('dissent case: the dissenting ayanamsha is named with its value', async () => {
    installIdentityDb(queryMock, { override: { krishnamurti: { maha_lord: 'Mercury' } } })
    const out = attachIdentityCrossCheckToPage(page1(), await fetchDossierIdentityCrossCheck(CHART, PRINCIPAL, platformFetch)) as Cc
    expect(out[KEY].summary).toBe('Dissent: Krishnamurti: current Mahadasha lord Mercury (primary Venus)')
  })

  it('single-ayanamsha case: not_available / single_ayanamsha_chart, never "1/1"', async () => {
    installIdentityDb(queryMock, { stored: [LAHIRI] })
    const out = attachIdentityCrossCheckToPage(page1(), await fetchDossierIdentityCrossCheck(CHART, PRINCIPAL, platformFetch)) as Cc
    expect(out[KEY]).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(JSON.stringify(out[KEY])).not.toMatch(/1\/1|agree/i)
  })
})
