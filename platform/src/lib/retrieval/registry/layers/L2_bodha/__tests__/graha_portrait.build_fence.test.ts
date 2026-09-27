/**
 * graha_portrait's best-effort served-generation fence (Pūrṇa R3 boundary review follow-up).
 *
 * get_strength.ts's own build_id doc comment claimed "composing callers (query_planet,
 * graha_portrait) pass the chart's served build set" — an independent semantic review of the
 * R0-R3 delta found this was false: graha_portrait never threaded build_id through its
 * getStrengthCapability call. This test proves the fix: graha_portrait resolves the served
 * generation itself, passes it to the strength leg, falls back to an unfenced read when
 * resolution fails, and discloses which mode ran via `generation_fence` — never silently
 * claiming a fence that didn't happen. `include: ['strength']` scopes each call to the one
 * section under test so no other leg capability needs stubbing.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockResolve, strength } = vi.hoisted(() => ({
  mockResolve: vi.fn(),
  strength: { handler: vi.fn().mockResolvedValue({ content: { rows: [] }, is_error: false }) },
}))

vi.mock('../../../generation/served_generation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../generation/served_generation')>()
  return {
    ...actual,
    resolveChartServedGeneration: (...args: unknown[]) => mockResolve(...args),
    servedGenerationIdentity: (generation: { served_build_ids: readonly string[] }) =>
      generation.served_build_ids.length ? 'generation:test' : null,
  }
})

vi.mock('../../L1_ganita/get_strength', () => ({ getStrengthCapability: strength }))

import { grahaPortraitCapability } from '../graha_portrait'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'

beforeEach(() => {
  vi.clearAllMocks()
  strength.handler.mockResolvedValue({ content: { rows: [] }, is_error: false })
})

describe('graha_portrait served-generation fence', () => {
  it('threads the resolved build set into the strength leg and discloses the fence', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED], generation_hash: 'h' })

    const result = await grahaPortraitCapability.handler(
      { chart_id: CHART_ID, graha: 'Saturn', include: ['strength'] }, undefined,
    )

    expect(result.is_error).toBe(false)
    expect(strength.handler).toHaveBeenCalledWith(
      expect.objectContaining({ build_id: [SERVED] }), undefined,
    )
    const content = result.content as Record<string, unknown>
    expect(content['generation_fence']).toMatchObject({ fenced: true, build_ids: [SERVED] })
  })

  it('falls back to an unfenced read and honestly discloses the miss when no generation resolves', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [], generation_hash: 'h' })

    const result = await grahaPortraitCapability.handler(
      { chart_id: CHART_ID, graha: 'Saturn', include: ['strength'] }, undefined,
    )

    expect(result.is_error).toBe(false)
    const [args] = strength.handler.mock.calls[0]!
    expect(args).not.toHaveProperty('build_id')
    const content = result.content as Record<string, unknown>
    expect(content['generation_fence']).toMatchObject({ fenced: false })
    expect((content['generation_fence'] as Record<string, unknown>)['note']).toContain('unfenced current rows')
  })

  it('falls back to an unfenced read (never fails the whole portrait) when resolution throws', async () => {
    mockResolve.mockRejectedValue(new Error('db unreachable'))

    const result = await grahaPortraitCapability.handler(
      { chart_id: CHART_ID, graha: 'Saturn', include: ['strength'] }, undefined,
    )

    expect(result.is_error).toBe(false)
    const [args] = strength.handler.mock.calls[0]!
    expect(args).not.toHaveProperty('build_id')
    const content = result.content as Record<string, unknown>
    expect(content['generation_fence']).toMatchObject({ fenced: false })
    expect((content['generation_fence'] as Record<string, unknown>)['note']).toContain('resolution failed')
  })
})
