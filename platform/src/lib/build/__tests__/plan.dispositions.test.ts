// O-wave WP-3 (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.3, "total plans").
// Acceptance criteria under direct test:
//   (a) a layer plan's dispositions sum to the layer's registry count, always;
//   (b) a chart rebuild plans zero shared assets by default;
//   (c) a selector gap throws rather than drops (defensive; exercised indirectly
//       since the production code path has no reachable gap by construction).
import { describe, it, expect } from 'vitest'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(
  asset_id: string,
  layer: string,
  depends_on: string[],
  overrides: Partial<RegistryEntry> = {},
): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: 60, ...overrides }
}

function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

function dispositionsSum(result: ReturnType<typeof resolveBuildPlan>): number {
  return result.dispositions?.size ?? 0
}

describe('O-wave WP-3 — disposition totality', () => {
  it('a layer plan\'s dispositions always sum to the layer\'s registry count', () => {
    const registry = [
      reg('bg_a', 'brahmagyan', []),
      reg('bg_b', 'brahmagyan', ['bg_a']),
      reg('bg_c', 'brahmagyan', []),
      reg('ga_other', 'ganita', []),   // different layer -- must not be counted
    ]
    const throughput = new Map([tp('bg_a', 'lit'), tp('bg_c', 'dormant')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'build',
      registry, throughput,
    })
    expect(result.status).toBe('ok')
    expect(dispositionsSum(result)).toBe(3)
    expect([...(result.dispositions?.keys() ?? [])].sort()).toEqual(['bg_a', 'bg_b', 'bg_c'])
  })

  it('dispositions is undefined (not an empty map) for non-layer scopes', () => {
    const registry = [reg('bg_a', 'brahmagyan', [])]
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry, throughput: new Map(),
    })
    expect(result.dispositions).toBeUndefined()
  })

  it('assigns "build" to every actual candidate', () => {
    const registry = [reg('bg_a', 'brahmagyan', [])]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'build',
      registry, throughput: new Map(),
    })
    expect(result.dispositions?.get('bg_a')).toEqual({ disposition: 'build' })
  })

  it('assigns "skip_no_delta" to an already-lit asset a build action correctly excludes', () => {
    const registry = [reg('bg_a', 'brahmagyan', [])]
    const throughput = new Map([tp('bg_a', 'lit')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'build',
      registry, throughput,
    })
    expect(result.plan_waves.flat()).not.toContain('bg_a')
    expect(result.dispositions?.get('bg_a')).toEqual({ disposition: 'skip_no_delta' })
  })

  it('assigns "dormant" to a dormant asset this action\'s own logic did not select', () => {
    // cascade only rebuilds transitive downstream of stale assets; a dormant
    // root with no stale ancestor is never a cascade candidate.
    const registry = [reg('bg_a', 'brahmagyan', [])]
    const throughput = new Map([tp('bg_a', 'dormant')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'cascade',
      registry, throughput,
    })
    expect(result.plan_waves.flat()).not.toContain('bg_a')
    expect(result.dispositions?.get('bg_a')).toEqual({ disposition: 'dormant' })
  })

  it('assigns "deferred_no_writer" to a nonCandidateAssetIds entry', () => {
    const registry = [reg('bg_probe', 'brahmagyan', [])]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'build',
      registry, throughput: new Map(),
      nonCandidateAssetIds: new Set(['bg_probe']),
    })
    expect(result.dispositions?.get('bg_probe')).toEqual({ disposition: 'deferred_no_writer' })
  })

  it('assigns "withheld_protected" to a protected asset regardless of action', () => {
    const registry = [reg('bg_locked', 'brahmagyan', [])]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild',
      registry, throughput: new Map(),
      protectedAssetIds: new Set(['bg_locked']),
    })
    expect(result.plan_waves.flat()).not.toContain('bg_locked')
    expect(result.dispositions?.get('bg_locked')).toEqual({ disposition: 'withheld_protected' })
    expect(result.protected_assets).toEqual([{ asset_id: 'bg_locked', message: expect.any(String) }])
  })

  it('assigns "blocked_dependency" with a reason when the whole plan is blocked', () => {
    const registry = [
      reg('ph_result', 'phala', ['bo_analysis']),
      reg('bo_analysis', 'bodha', []),
    ]
    const throughput = new Map([tp('bo_analysis', 'stale')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'phala', action: 'build',
      registry, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.dispositions?.get('ph_result')).toEqual({
      disposition: 'blocked_dependency',
      reason: expect.stringContaining('bo_analysis'),
    })
  })
})

describe('O-wave WP-3 — domain-aware scoping (plan §3.3 "chart rebuild plans zero shared assets")', () => {
  it('excludes domain=shared assets from a layer sweep by default', () => {
    const registry = [
      reg('bg_shared_ref', 'brahmagyan', [], { domain: 'shared' }),
      reg('bg_chart_asset', 'brahmagyan', [], { domain: 'chart' }),
    ]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.plan_waves.flat()).toEqual(['bg_chart_asset'])
    expect(result.plan_waves.flat()).not.toContain('bg_shared_ref')
    expect(result.dispositions?.get('bg_shared_ref')).toEqual({ disposition: 'out_of_domain' })
    expect(result.dispositions?.get('bg_chart_asset')).toEqual({ disposition: 'build' })
  })

  it('a layer rebuild plans zero shared assets even when every asset in the layer is shared', () => {
    const registry = [
      reg('bg_a', 'brahmagyan', [], { domain: 'shared' }),
      reg('bg_b', 'brahmagyan', [], { domain: 'shared' }),
    ]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.plan_waves.flat()).toEqual([])
    expect([...(result.dispositions?.values() ?? [])].every(d => d.disposition === 'out_of_domain')).toBe(true)
  })

  it('missing/undefined domain defaults to chart -- never silently excluded', () => {
    const registry = [reg('bg_no_domain', 'brahmagyan', [])] // no domain field at all
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.plan_waves.flat()).toEqual(['bg_no_domain'])
    expect(result.dispositions?.get('bg_no_domain')).toEqual({ disposition: 'build' })
  })

  it('scope=asset_set still honors an explicitly named shared asset (explicit request is never filtered)', () => {
    const registry = [
      reg('bg_shared_ref', 'brahmagyan', [], { domain: 'shared' }),
    ]
    const result = resolveBuildPlan({
      scope: 'asset_set', scope_target: 'bg_shared_ref', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toEqual(['bg_shared_ref'])
  })

  it('scope=global remains unfiltered by domain ("global scope owns shared")', () => {
    const registry = [
      reg('bg_shared_ref', 'brahmagyan', [], { domain: 'shared' }),
      reg('ga_chart_asset', 'ganita', [], { domain: 'chart' }),
    ]
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.plan_waves.flat().sort()).toEqual(['bg_shared_ref', 'ga_chart_asset'])
  })
})
