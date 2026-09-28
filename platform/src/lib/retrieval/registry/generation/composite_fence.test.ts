import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockResolve } = vi.hoisted(() => ({ mockResolve: vi.fn() }))
vi.mock('./served_generation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./served_generation')>()
  return {
    ...actual,
    resolveChartServedGeneration: (...args: unknown[]) => mockResolve(...args),
    servedGenerationIdentity: (generation: { served_build_ids: readonly string[] }) =>
      generation.served_build_ids.length ? 'generation:test' : null,
  }
})

import {
  compositeGenerationFence,
  resolveCompositeFence,
  splitByGenerationClass,
  unavailableComponents,
  type ComponentClassification,
} from './composite_fence'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'

beforeEach(() => {
  mockResolve.mockReset()
  vi.spyOn(console, 'error').mockImplementation(() => undefined)
})

describe('resolveCompositeFence', () => {
  it('returns the served build set when a generation resolves', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [SERVED] })
    await expect(resolveCompositeFence(CHART_ID, 'query_planet')).resolves.toEqual({ fenced: true, build_ids: [SERVED] })
  })

  it('reports no_served_generation when nothing resolves', async () => {
    mockResolve.mockResolvedValue({ served_build_ids: [] })
    await expect(resolveCompositeFence(CHART_ID, 'query_planet')).resolves.toEqual({ fenced: false, code: 'no_served_generation' })
  })

  it('reports served_generation_unresolved when resolution throws, logging server-side only', async () => {
    mockResolve.mockRejectedValue(new Error('relation "asset_provenance_receipts" does not exist'))
    const fence = await resolveCompositeFence(CHART_ID, 'graha_portrait')
    expect(fence).toEqual({ fenced: false, code: 'served_generation_unresolved' })
    expect(JSON.stringify(fence)).not.toContain('asset_provenance_receipts')
    expect(console.error).toHaveBeenCalledWith('[graha_portrait] served-generation resolution failed', expect.any(Error))
  })
})

describe('unavailable-component schema', () => {
  it('names each omitted component with a stable code and a fixed reason (no raw text)', () => {
    const list = unavailableComponents(['shadbala', 'yogas'], 'served_generation_unresolved')
    expect(list).toEqual([
      { component: 'shadbala', code: 'served_generation_unresolved', reason: expect.any(String) },
      { component: 'yogas', code: 'served_generation_unresolved', reason: expect.any(String) },
    ])
    expect(list[0]!.reason).toBe(list[1]!.reason)
    expect(unavailableComponents(['x'], 'no_served_generation')[0]!.reason).not.toBe(list[0]!.reason)
  })

  it('discloses the fence machine-readably in both states', () => {
    expect(compositeGenerationFence({ fenced: true, build_ids: [SERVED] })).toEqual({
      fenced: true, build_ids: [SERVED], code: null, note: expect.any(String),
    })
    expect(compositeGenerationFence({ fenced: false, code: 'no_served_generation' })).toEqual({
      fenced: false, build_ids: null, code: 'no_served_generation', note: expect.any(String),
    })
  })
})

describe('splitByGenerationClass', () => {
  const table: Record<string, ComponentClassification> = {
    identity: { class: 'independent', reason: 'pure function of the request' },
    strength: { class: 'sensitive', reason: 'reads build-scoped chart_facts' },
    dashas: { class: 'self_fenced', reason: 'handler applies the served generation itself' },
  }

  it('serves everything when the generation is fenced', () => {
    expect(splitByGenerationClass(table, ['identity', 'strength', 'dashas'], true)).toEqual({
      serve: ['identity', 'strength', 'dashas'], withhold: [],
    })
  })

  it('withholds ONLY the sensitive components when there is no fence', () => {
    expect(splitByGenerationClass(table, ['identity', 'strength', 'dashas'], false)).toEqual({
      serve: ['identity', 'dashas'], withhold: ['strength'],
    })
  })

  it('refuses a component that was never classified, so the audit cannot silently rot', () => {
    expect(() => splitByGenerationClass(table, ['brand_new_section'], false)).toThrow(/brand_new_section/)
  })
})

describe('shared build-fence declaration', () => {
  it('is frozen so no descriptor can mutate the one declaration every binding shares', async () => {
    const { BUILD_FENCE_INPUT } = await import('./served_generation')
    expect(Object.isFrozen(BUILD_FENCE_INPUT)).toBe(true)
    expect(() => { (BUILD_FENCE_INPUT as unknown as Record<string, unknown>)['type'] = 'array' }).toThrow()
    expect(BUILD_FENCE_INPUT.type).toBe('string')
  })
})

describe('isChartUuid', () => {
  it('accepts any hex UUID (test and eval ids included) and rejects everything else', async () => {
    const { isChartUuid } = await import('./composite_fence')
    for (const ok of ['482012f1-710e-4a25-994a-93821f5871aa', '1c826d5a-0000-0000-0000-000000000000', 'AAAAAAAA-1111-4000-8000-00000000000B']) expect(isChartUuid(ok), ok).toBe(true)
    for (const bad of ['', 'not-a-uuid', '1c826d5a', "482012f1-710e-4a25-994a-93821f5871aa'; DROP", 42, null, undefined]) expect(isChartUuid(bad), String(bad)).toBe(false)
  })
})
