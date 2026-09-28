/**
 * query_planet's best-effort served-generation fence (Pūrṇa R3 boundary review follow-up).
 *
 * get_strength.ts's own build_id doc comment claimed "composing callers (query_planet,
 * graha_portrait) pass the chart's served build set" — an independent semantic review of the
 * R0-R3 delta found this was false: neither caller ever threaded build_id through. This test
 * proves the fix: query_planet resolves the served generation itself, passes it to the two legs
 * that support fencing (get_strength, get_yoga_firings), falls back to each leg's own unfenced
 * read when resolution fails, and discloses which mode ran via `generation_fence` — never
 * silently claiming a fence that didn't happen.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

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

vi.mock('../../../generation/served_generation', () => ({
  resolveChartServedGeneration: (...args: unknown[]) => mockResolve(...args),
  servedGenerationIdentity: (generation: { served_build_ids: readonly string[] }) =>
    generation.served_build_ids.length ? 'generation:test' : null,
}))

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
const SERVED = '11111111-1111-4111-8111-111111111111'

beforeEach(() => {
  vi.clearAllMocks()
  for (const cap of [positions, dignity, strength, avasthas, aspects, yogaDosha, yogaFirings, dispositors]) {
    cap.handler.mockResolvedValue({ content: { rows: [] }, is_error: false })
  }
})

describe('query_planet served-generation fence', () => {
  it('threads the resolved build set into get_strength and get_yoga_firings only, and discloses the fence', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED], generation_hash: 'h' })

    const result = await queryPlanetCapability.handler({ chart_id: CHART_ID, planet: 'Saturn' }, undefined)

    expect(result.is_error).toBe(false)
    expect(strength.handler).toHaveBeenCalledWith(expect.objectContaining({ build_id: [SERVED] }))
    expect(yogaFirings.handler).toHaveBeenCalledWith(expect.objectContaining({ build_id: [SERVED] }))
    for (const cap of [positions, dignity, avasthas, aspects, yogaDosha, dispositors]) {
      expect(cap.handler).toHaveBeenCalledWith(expect.not.objectContaining({ build_id: expect.anything() }))
    }
    const content = result.content as Record<string, unknown>
    expect(content['generation_fence']).toMatchObject({ fenced: true, build_ids: [SERVED] })
  })

  it('falls back to unfenced reads and honestly discloses the miss when no generation resolves', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [], generation_hash: 'h' })

    const result = await queryPlanetCapability.handler({ chart_id: CHART_ID, planet: 'Saturn' }, undefined)

    expect(result.is_error).toBe(false)
    expect(strength.handler).toHaveBeenCalledWith(expect.not.objectContaining({ build_id: expect.anything() }))
    expect(yogaFirings.handler).toHaveBeenCalledWith(expect.not.objectContaining({ build_id: expect.anything() }))
    const content = result.content as Record<string, unknown>
    expect(content['generation_fence']).toMatchObject({ fenced: false })
    expect((content['generation_fence'] as Record<string, unknown>)['note']).toContain('unfenced current rows')
  })

  it('falls back to unfenced reads (never fails the whole composite) when resolution throws', async () => {
    mockResolve.mockRejectedValue(new Error('db unreachable'))

    const result = await queryPlanetCapability.handler({ chart_id: CHART_ID, planet: 'Saturn' }, undefined)

    expect(result.is_error).toBe(false)
    expect(strength.handler).toHaveBeenCalledWith(expect.not.objectContaining({ build_id: expect.anything() }))
    const content = result.content as Record<string, unknown>
    expect(content['generation_fence']).toMatchObject({ fenced: false })
    expect((content['generation_fence'] as Record<string, unknown>)['note']).toContain('resolution failed')
    // The underlying error stays server-side; callers get a fixed disclosure only.
    expect(JSON.stringify(content)).not.toContain('db unreachable')
  })
})
