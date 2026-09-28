/**
 * graha_portrait is served-generation-safe (Packet A of the fence-and-successor-envelope follow-up).
 *
 * Seven of its eight sections read build-scoped rows: with a resolved generation each is fenced to it;
 * without one none is read (no fallback to current rows) and each requested one is named in
 * `components_unavailable`. `dashas` is self-fenced (get_dashas applies the served generation itself
 * and has no unfenced fallback), so it is still served — which makes the no-generation response a
 * genuine partial portrait. Errors never carry raw exception or database text.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockResolve, positions, dignity, strength, avasthas, yogaDosha, dashas, signals, traverse } = vi.hoisted(() => {
  const ok = (content: unknown = { rows: [] }) => ({ handler: vi.fn().mockResolvedValue({ content, is_error: false }) })
  return {
    mockResolve: vi.fn(),
    positions: ok(), dignity: ok(), strength: ok(), avasthas: ok(), yogaDosha: ok(), dashas: ok(),
    signals: ok({ signals: [] }), traverse: ok({ nodes: [], edges: [], node_count: 0, edge_count: 0 }),
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
vi.mock('../../L1_ganita/get_positions', () => ({ getPositionsCapability: positions }))
vi.mock('../../L1_ganita/get_dignity', () => ({ getDignityCapability: dignity }))
vi.mock('../../L1_ganita/get_strength', () => ({ getStrengthCapability: strength }))
vi.mock('../../L1_ganita/get_avasthas', () => ({ getAvasthsCapability: avasthas }))
vi.mock('../../L1_ganita/get_yoga_dosha', () => ({ getYogaDoshaCapability: yogaDosha }))
vi.mock('../../L1_ganita/get_dashas', () => ({ getDashasCapability: dashas }))
vi.mock('../query_signals', () => ({ querySignalsCapability: signals }))
vi.mock('../traverse_chart_graph', () => ({ traverseChartGraphCapability: traverse }))

import { GRAHA_PORTRAIT_COMPONENTS, grahaPortraitCapability } from '../graha_portrait'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'
const FENCED_LEGS = [positions, dignity, strength, avasthas, yogaDosha, signals, traverse]
const SENSITIVE = Object.entries(GRAHA_PORTRAIT_COMPONENTS).filter(([, c]) => c.class === 'sensitive').map(([n]) => n).sort()

type Content = Record<string, unknown>
const run = async (extra: Record<string, unknown> = {}) =>
  grahaPortraitCapability.handler({ chart_id: CHART_ID, graha: 'Saturn', ...extra }, undefined) as Promise<{ content: Content; is_error: boolean }>

beforeEach(() => {
  vi.clearAllMocks()
  vi.spyOn(console, 'error').mockImplementation(() => undefined)
  for (const cap of [positions, dignity, strength, avasthas, yogaDosha, dashas]) cap.handler.mockResolvedValue({ content: { rows: [] }, is_error: false })
  signals.handler.mockResolvedValue({ content: { signals: [] }, is_error: false })
  traverse.handler.mockResolvedValue({ content: { nodes: [], edges: [], node_count: 0, edge_count: 0 }, is_error: false })
})
afterEach(() => vi.restoreAllMocks())

describe('graha_portrait component audit', () => {
  it('classifies exactly the sections the include enum offers, each with a reason', () => {
    const enumSections = (grahaPortraitCapability.input_schema!['include'] as { items: { enum: string[] } }).items.enum
      .filter((section) => section !== 'special_states').sort()
    expect(Object.keys(GRAHA_PORTRAIT_COMPONENTS).sort()).toEqual(enumSections)
    for (const entry of Object.values(GRAHA_PORTRAIT_COMPONENTS)) expect(entry.reason.length).toBeGreaterThan(20)
  })

  it('treats every chart-data section as sensitive except dashas, which get_dashas fences itself', () => {
    expect(SENSITIVE).toEqual(['avasthas', 'cgm_neighborhood', 'dignity', 'functional_nature', 'position', 'strength', 'yogas'])
    expect(GRAHA_PORTRAIT_COMPONENTS['dashas']?.class).toBe('self_fenced')
  })
})

describe('graha_portrait with a resolved served generation', () => {
  it('fences every generation-sensitive leg (incl. all three signal reads) and discloses a clean fence', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED] })
    const { content, is_error } = await run()

    expect(is_error).toBe(false)
    for (const cap of FENCED_LEGS) {
      expect(cap.handler).toHaveBeenCalled()
      for (const [args] of cap.handler.mock.calls) expect(args).toMatchObject({ build_id: [SERVED] })
    }
    expect(signals.handler).toHaveBeenCalledTimes(3)
    // get_dashas fences itself; the composite must not hand it a competing fence.
    expect(dashas.handler.mock.calls[0]![0]).not.toHaveProperty('build_id')
    expect(content['generation_fence']).toMatchObject({ fenced: true, build_ids: [SERVED], code: null })
    expect(content['components_unavailable']).toEqual([])
    expect(content['generation_fence']).not.toHaveProperty('unfenced_sections')
  })
})

describe('graha_portrait without a valid served generation', () => {
  it.each([
    ['no generation resolves', () => mockResolve.mockResolvedValue({ served_build_ids: [] }), 'no_served_generation'],
    ['resolution throws', () => mockResolve.mockRejectedValue(new Error('db unreachable: relation "asset_provenance_receipts"')), 'served_generation_unresolved'],
  ] as const)('%s: withholds every sensitive section, still serves the self-fenced one', async (_label, arrange, code) => {
    arrange()
    const { content, is_error } = await run()

    expect(is_error).toBe(false)
    for (const cap of FENCED_LEGS) expect(cap.handler).not.toHaveBeenCalled()
    expect(dashas.handler).toHaveBeenCalledTimes(1)
    expect(content).toHaveProperty('dashas')
    expect(content).toMatchObject({ graha: expect.any(String), graha_code: 'SAT', chart_id: CHART_ID })
    for (const section of SENSITIVE) expect(content, section).not.toHaveProperty(section)
    const unavailable = content['components_unavailable'] as Array<{ component: string; code: string; reason: string }>
    expect(unavailable.map((item) => item.component).sort()).toEqual(SENSITIVE)
    for (const item of unavailable) expect(item).toMatchObject({ code, reason: expect.any(String) })
    expect(content['generation_fence']).toMatchObject({ fenced: false, build_ids: null, code })
    const completeness = content['completeness'] as Record<string, string>
    for (const section of SENSITIVE) expect(completeness[section], section).toBe('unavailable')
    expect(completeness['dashas']).not.toBe('unavailable')
  })

  it('names ONLY the requested sensitive sections (the unavailable list equals the omitted set)', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [] })
    const { content } = await run({ include: ['strength', 'dashas'] })
    expect((content['components_unavailable'] as Array<{ component: string }>).map((c) => c.component)).toEqual(['strength'])
    expect(content).toHaveProperty('dashas')
    expect(content).not.toHaveProperty('strength')
    expect(strength.handler).not.toHaveBeenCalled()
  })

  it('never puts raw exception or database text in the response, and logs it server-side', async () => {
    mockResolve.mockRejectedValue(new Error('db unreachable: relation "asset_provenance_receipts"'))
    const { content } = await run()
    expect(JSON.stringify(content)).not.toMatch(/db unreachable|asset_provenance_receipts/)
    expect(console.error).toHaveBeenCalledWith('[graha_portrait] served-generation resolution failed', expect.any(Error))
  })
})

describe('graha_portrait section failures (generation resolved)', () => {
  it('reports a failing section by fixed code, never raw text, and still serves the others', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED] })
    strength.handler.mockRejectedValue(new Error('permission denied for relation chart_facts (role app_reader)'))
    const { content, is_error } = await run({ include: ['strength', 'position'] })

    expect(is_error).toBe(false)
    expect(content['errors']).toEqual({ strength: 'component_read_failed' })
    expect((content['completeness'] as Record<string, string>)['strength']).toBe('error')
    expect(content).toHaveProperty('position')
    expect(JSON.stringify(content)).not.toMatch(/permission denied|app_reader/)
    expect(console.error).toHaveBeenCalled()
  })
})
