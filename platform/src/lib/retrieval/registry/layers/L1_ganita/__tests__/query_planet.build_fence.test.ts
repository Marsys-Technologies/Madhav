/**
 * query_planet is served-generation-safe (Packet A of the fence-and-successor-envelope follow-up).
 *
 * Every data section query_planet assembles reads build-scoped rows, so with a resolved generation
 * ALL of them are fenced to it; without one, none of them is read (never a fallback to the chart's
 * current rows). The tool then returns what does not depend on a generation, names every withheld
 * component in `components_unavailable`, and is NOT a whole-tool error. Errors never carry raw
 * exception or database text.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockResolve, positions, dignity, strength, avasthas, aspects, yogaDosha, yogaFirings, dispositors } = vi.hoisted(() => {
  function stubCapability() {
    return { handler: vi.fn().mockResolvedValue({ content: { rows: [] }, is_error: false }) }
  }
  return {
    mockResolve: vi.fn(),
    positions: stubCapability(),
    dignity: stubCapability(),
    strength: stubCapability(),
    avasthas: stubCapability(),
    aspects: stubCapability(),
    yogaDosha: stubCapability(),
    yogaFirings: stubCapability(),
    dispositors: stubCapability(),
  }
})

vi.mock('../../../generation/served_generation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../generation/served_generation')>()
  return {
    ...actual,
    resolveChartServedGeneration: (...args: unknown[]) => mockResolve(...args),
    servedGenerationIdentity: (generation: { served_build_ids: readonly string[] }) =>
      generation.served_build_ids.length ? 'generation:test' : null,
  }
})

vi.mock('../get_positions', () => ({ getPositionsCapability: positions }))
vi.mock('../get_dignity', () => ({ getDignityCapability: dignity }))
vi.mock('../get_strength', () => ({ getStrengthCapability: strength }))
vi.mock('../get_avasthas', () => ({ getAvasthsCapability: avasthas }))
vi.mock('../get_aspects', () => ({ getAspectsCapability: aspects }))
vi.mock('../get_yoga_dosha', () => ({ getYogaDoshaCapability: yogaDosha }))
vi.mock('../get_yoga_firings', () => ({ getYogaFiringsCapability: yogaFirings }))
vi.mock('../get_dispositors', () => ({ getDispositorsCapability: dispositors }))

import { QUERY_PLANET_COMPONENTS, queryPlanetCapability } from '../query_planet'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'
const LEGS = [positions, dignity, strength, avasthas, aspects, yogaDosha, yogaFirings, dispositors]
const SENSITIVE = Object.entries(QUERY_PLANET_COMPONENTS).filter(([, c]) => c.class === 'sensitive').map(([name]) => name).sort()
const ENVELOPE_KEYS = new Set(['chart_id', 'generation_fence', 'components_unavailable', 'judgment_flags', 'source_errors'])

type Content = Record<string, unknown>
const run = async (args: Record<string, unknown> = {}) =>
  queryPlanetCapability.handler({ chart_id: CHART_ID, planet: 'Saturn', ...args }, undefined) as Promise<{ content: Content; is_error: boolean }>

beforeEach(() => {
  vi.clearAllMocks()
  vi.spyOn(console, 'error').mockImplementation(() => undefined)
  for (const cap of LEGS) cap.handler.mockResolvedValue({ content: { rows: [] }, is_error: false })
})
afterEach(() => vi.restoreAllMocks())

describe('query_planet component audit', () => {
  it('classifies exactly the components the tool assembles, each with a reason', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED] })
    const { content } = await run()
    const assembled = Object.keys(content).filter((key) => !ENVELOPE_KEYS.has(key)).sort()
    expect(assembled).toEqual(Object.keys(QUERY_PLANET_COMPONENTS).sort())
    for (const entry of Object.values(QUERY_PLANET_COMPONENTS)) expect(entry.reason.length).toBeGreaterThan(20)
  })

  it('treats every chart-data component as generation-sensitive (only the request-derived identity is independent)', () => {
    expect(Object.entries(QUERY_PLANET_COMPONENTS).filter(([, c]) => c.class === 'independent').map(([n]) => n)).toEqual(['planet'])
    expect(SENSITIVE).toEqual(['aspects', 'avasthas', 'dignity', 'dispositor', 'functional_nature', 'position', 'shadbala', 'yogas'])
  })
})

describe('query_planet with a resolved served generation', () => {
  it('fences EVERY leg to the served build set and discloses a clean fence', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED] })
    const { content, is_error } = await run()
    expect(is_error).toBe(false)
    for (const cap of LEGS) expect(cap.handler).toHaveBeenCalledWith(expect.objectContaining({ build_id: [SERVED] }))
    expect(content['generation_fence']).toMatchObject({ fenced: true, build_ids: [SERVED], code: null })
    expect(content['components_unavailable']).toEqual([])
    expect(content['generation_fence']).not.toHaveProperty('unfenced_facets')
  })
})

describe('query_planet without a valid served generation', () => {
  it.each([
    ['no generation resolves', () => mockResolve.mockResolvedValue({ served_build_ids: [] }), 'no_served_generation'],
    ['resolution throws', () => mockResolve.mockRejectedValue(new Error('db unreachable: relation "asset_provenance_receipts"')), 'served_generation_unresolved'],
  ] as const)('%s: reads nothing generation-sensitive and returns a named partial response', async (_label, arrange, code) => {
    arrange()
    const { content, is_error } = await run()

    expect(is_error).toBe(false)
    for (const cap of LEGS) expect(cap.handler).not.toHaveBeenCalled()
    // Base output that does not depend on a generation is still there.
    expect(content['chart_id']).toBe(CHART_ID)
    expect(content['planet']).toMatchObject({ input: 'Saturn', code: 'SAT', name: expect.any(String) })
    // Every sensitive section is ABSENT (not an empty stand-in) and named, exactly.
    for (const name of SENSITIVE) expect(content, name).not.toHaveProperty(name)
    const unavailable = content['components_unavailable'] as Array<{ component: string; code: string; reason: string }>
    expect(unavailable.map((item) => item.component).sort()).toEqual(SENSITIVE)
    for (const item of unavailable) expect(item).toMatchObject({ code, reason: expect.any(String) })
    expect(content['generation_fence']).toMatchObject({ fenced: false, build_ids: null, code })
  })

  it('never puts raw exception or database text in the response, and logs it server-side', async () => {
    mockResolve.mockRejectedValue(new Error('db unreachable: relation "asset_provenance_receipts"'))
    const { content } = await run()
    expect(JSON.stringify(content)).not.toMatch(/db unreachable|asset_provenance_receipts/)
    expect(console.error).toHaveBeenCalledWith('[query_planet] served-generation resolution failed', expect.any(Error))
  })
})

describe('query_planet partial source failures (generation resolved)', () => {
  it('names the failing component by fixed code, never with raw handler text', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED] })
    strength.handler.mockResolvedValue({ content: 'error: relation "chart_facts" permission denied for role app', is_error: true })
    const { content, is_error } = await run()

    expect(is_error).toBe(false)
    expect(content['judgment_flags']).toEqual(['partial_source_error'])
    expect(content['source_errors']).toEqual([{ component: 'shadbala', code: 'component_read_failed' }])
    expect(JSON.stringify(content)).not.toMatch(/permission denied|chart_facts" permission/)
    expect(content).toHaveProperty('position') // the other components still serve
    expect(console.error).toHaveBeenCalled()
  })
})
