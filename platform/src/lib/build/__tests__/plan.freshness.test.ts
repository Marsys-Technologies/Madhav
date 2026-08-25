import { describe, expect, it } from 'vitest'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

const registry: RegistryEntry[] = [
  { asset_id: 'bg_input', layer: 'brahmagyan', depends_on: [], estimated_seconds: null },
  { asset_id: 'ga_output', layer: 'ganita', depends_on: ['bg_input'], estimated_seconds: null },
]

function throughput(entries: ThroughputEntry[]) {
  return new Map(entries.map((entry) => [entry.asset_id, entry]))
}

describe('resolveBuildPlan — sidecar freshness projection', () => {
  it('blocks a dependency missing from the registry as unknown', () => {
    const incompleteRegistry = [
      { asset_id: 'ga_output', layer: 'ganita', depends_on: ['missing_upstream'], estimated_seconds: null },
    ]
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_output', action: 'build', registry: incompleteRegistry,
      throughput: throughput([]), freshness: new Map(),
    })
    expect(result.status).toBe('blocked')
    expect(result.blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'missing_upstream', dep_state: 'unknown' }),
    ]))
  })

  it('withholds a lit dependency whose receipt is unknown', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_output', action: 'build', registry,
      throughput: throughput([{ asset_id: 'bg_input', state: 'lit' }]),
      freshness: new Map([['bg_input', { state: 'unknown' as const, reasons: ['output_digest_unavailable'] }]]),
    })
    expect(result.status).toBe('blocked')
    expect(result.blockers[0]).toMatchObject({ dep_asset_id: 'bg_input', dep_state: 'unknown' })
  })

  it('accepts only a lit dependency with a fresh receipt', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_output', action: 'build', registry,
      throughput: throughput([{ asset_id: 'bg_input', state: 'lit' }]),
      freshness: new Map([['bg_input', { state: 'fresh' as const, reasons: [] }]]),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves).toEqual([['ga_output']])
  })

  it('rebuilds a lit in-scope asset when its receipt is missing', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_output', action: 'build', registry,
      throughput: throughput([{ asset_id: 'ga_output', state: 'lit' }]),
      freshness: new Map(),
    })
    expect(result.status).toBe('blocked')
    expect(result.blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_input', dep_state: 'unknown' }),
    ]))
  })

  it('rebuilds a lit root asset when its receipt is stale', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'bg_input', action: 'build', registry,
      throughput: throughput([{ asset_id: 'bg_input', state: 'lit' }]),
      freshness: new Map([['bg_input', { state: 'stale' as const, reasons: ['code_digest_changed'] }]]),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves).toEqual([['bg_input']])
  })
})
