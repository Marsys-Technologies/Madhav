/**
 * SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 — resolveBuildPlan's
 * build_protected_assets planner guard, at the pure-function level.
 *
 * Mirrors plan.test.ts's fixture idiom. Covers both directions per the task
 * spec: a protected pair is withheld/surfaced (never silently built/rebuilt/
 * updated/cascaded), and a non-protected pair proceeds normally.
 */
import { describe, it, expect } from 'vitest'
import { resolveBuildPlan, PROTECTED_ASSET_MESSAGE, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[], estimated_seconds: number | null = 60): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds }
}

function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

const LINEAR = [
  reg('a', 'l1', []),
  reg('b', 'l1', ['a']),
  reg('c', 'l1', ['b']),
]

describe('resolveBuildPlan — protectedAssetIds (build_protected_assets guard)', () => {
  it('a protected pair is withheld from build and surfaced in protected_assets', () => {
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput: new Map(),
      protectedAssetIds: new Set(['b']),
    })
    const plan = result.plan_waves.flat()
    expect(plan).not.toContain('b')
    // Its non-protected dependency and dependent still proceed normally.
    expect(plan).toContain('a')
    expect(plan).toContain('c')
    expect(result.protected_assets).toEqual([{ asset_id: 'b', message: PROTECTED_ASSET_MESSAGE }])
  })

  it('a non-protected pair proceeds normally — protected_assets is empty, never omitted', () => {
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput: new Map(),
    })
    const plan = result.plan_waves.flat()
    expect(plan).toEqual(['a', 'b', 'c'])
    expect(result.protected_assets).toEqual([])
  })

  it('omitting protectedAssetIds entirely behaves exactly like an empty set (backward compatible)', () => {
    const withUndefined = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput: new Map(),
    })
    const withEmptySet = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput: new Map(),
      protectedAssetIds: new Set(),
    })
    expect(withUndefined.plan_waves).toEqual(withEmptySet.plan_waves)
    expect(withUndefined.protected_assets).toEqual(withEmptySet.protected_assets)
  })

  it('a protected asset that is the ONLY candidate reports protected_assets, not a bare no-op', () => {
    const throughput = new Map([tp('a', 'lit'), tp('c', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput,
      protectedAssetIds: new Set(['b']),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toEqual([])
    // Distinguishable from the ordinary "already lit" no-op: something was
    // withheld, not merely absent.
    expect(result.protected_assets).toEqual([{ asset_id: 'b', message: PROTECTED_ASSET_MESSAGE }])
  })

  it('rebuild also withholds a protected candidate', () => {
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry: LINEAR, throughput: new Map(),
      protectedAssetIds: new Set(['a']),
    })
    const plan = result.plan_waves.flat()
    expect(plan).not.toContain('a')
    expect(plan).toContain('b')
    expect(plan).toContain('c')
    expect(result.protected_assets).toEqual([{ asset_id: 'a', message: PROTECTED_ASSET_MESSAGE }])
  })

  it('update also withholds a protected candidate', () => {
    const throughput = new Map([tp('a', 'stale')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'update',
      registry: LINEAR, throughput,
      protectedAssetIds: new Set(['a']),
    })
    const plan = result.plan_waves.flat()
    expect(plan).not.toContain('a')
    expect(result.protected_assets.map(p => p.asset_id)).toContain('a')
  })

  it('cascade also withholds a protected candidate', () => {
    const throughput = new Map([tp('a', 'stale')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'cascade',
      registry: LINEAR, throughput,
      protectedAssetIds: new Set(['b']),
    })
    const plan = result.plan_waves.flat()
    expect(plan).not.toContain('b')
    expect(result.protected_assets.map(p => p.asset_id)).toContain('b')
  })

  it('a protected asset outside the requested scope is never reported (scope-correct)', () => {
    // scope=asset targeting only 'a' — 'b' is protected but out of scope, so it
    // must never appear in either plan_waves or protected_assets.
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'a', action: 'build',
      registry: LINEAR, throughput: new Map(),
      protectedAssetIds: new Set(['b']),
    })
    expect(result.plan_waves.flat()).toEqual(['a'])
    expect(result.protected_assets).toEqual([])
  })
})
