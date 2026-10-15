/**
 * query_planet (Lahiri primary, PR-2): the ayanamsha is resolved ONCE and forwarded to EVERY leg,
 * including the yoga-firings leg that used to receive none (a caller-supplied id never reached it).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockResolve, positions, dignity, strength, avasthas, aspects, yogaDosha, yogaFirings, dispositors } = vi.hoisted(() => {
  const stub = () => ({ handler: vi.fn().mockResolvedValue({ content: { rows: [] }, is_error: false }) })
  return { mockResolve: vi.fn(), positions: stub(), dignity: stub(), strength: stub(), avasthas: stub(), aspects: stub(), yogaDosha: stub(), yogaFirings: stub(), dispositors: stub() }
})

vi.mock('../../../generation/served_generation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../generation/served_generation')>()
  return {
    ...actual,
    resolveChartServedGeneration: (...a: unknown[]) => mockResolve(...a),
    servedGenerationIdentity: (g: { served_build_ids: readonly string[] }) => (g.served_build_ids.length ? 'generation:test' : null),
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

import { queryPlanetCapability } from '../query_planet'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LEGS = [positions, dignity, strength, avasthas, aspects, yogaDosha, yogaFirings, dispositors]
const run = (extra: Record<string, unknown> = {}) =>
  queryPlanetCapability.handler({ chart_id: CHART_ID, planet: 'Saturn', ...extra }, undefined)

beforeEach(() => {
  vi.clearAllMocks()
  mockResolve.mockResolvedValue({ served_build_ids: ['11111111-1111-4111-8111-111111111111'] })
  for (const l of LEGS) l.handler.mockResolvedValue({ content: { rows: [] }, is_error: false })
})

describe('query_planet ayanamsha scope', () => {
  it('omitted -> every leg (yoga firings included) gets lahiri_chitrapaksha', async () => {
    const res = await run()
    expect(res.is_error).toBe(false)
    for (const l of LEGS) {
      expect(l.handler).toHaveBeenCalledTimes(1)
      expect((l.handler.mock.calls[0]![0] as Record<string, unknown>)['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    }
    expect((res.content as Record<string, unknown>)['ayanamsha_id']).toBe('lahiri_chitrapaksha')
  })

  it('a caller-supplied alias reaches the yoga-firings leg too, normalised', async () => {
    await run({ ayanamsha_id: 'kp' })
    for (const l of LEGS) expect((l.handler.mock.calls[0]![0] as Record<string, unknown>)['ayanamsha_id']).toBe('krishnamurti')
  })

  it.each([[{ ayanamsha_id: 'all' }], [{ ayanamsha_scope: 'all' }]])('%j -> every leg pooled with ayanamsha_scope:"all"', async (extra) => {
    const res = await run(extra)
    for (const l of LEGS) {
      const a = l.handler.mock.calls[0]![0] as Record<string, unknown>
      expect('ayanamsha_id' in a).toBe(false)
      expect(a['ayanamsha_scope']).toBe('all')
    }
    expect((res.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
  })

  it('unknown id -> is_error listing the stored ids; no leg runs', async () => {
    const res = await run({ ayanamsha_id: 'nope' })
    expect(res.is_error).toBe(true)
    expect(JSON.stringify(res.content)).toContain('lahiri_chitrapaksha')
    for (const l of LEGS) expect(l.handler).not.toHaveBeenCalled()
  })
})
